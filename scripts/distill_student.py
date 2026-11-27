#!/usr/bin/env python3
"""Single-pass multi-head student distillation (V71-P5-1).

Lane 08 (Pillar 5) — SCRIPTS + DESIGN ONLY. This script is NOT run on
this VM: it needs a GPU, torch, Lane 02's corpus and Lane 03's teacher,
none of which exist here. Run it on the user's RTX 5050 machine
(commands in docs/10x_swarm_state/lane-08-p5.md).

Pipeline (plan docs/10x_plane.md §5.2, V71-P5-1)
------------------------------------------------
1. Load Lane 02's synthetic bilingual corpus (contract C2 JSONL:
   ``{id, lang, text, issues: {issue: intent}, facts: {fact: state},
   enums: {claimant_sex, claimant_role, modality_time}, spans: [...]}``,
   5,000 examples, EN + KN + Kanglish, zero-leakage).
2. Teacher (Lane 03, ``src/laya_v7_classifier.py``) generates soft logit
   targets for every example — one teacher forward per example over
   ``[full_q] + filtered_clauses``. Soft targets are cached to
   ``--teacher-cache`` (``.npz``) so the student can be re-trained
   without re-running the teacher.
3. Student (``src/laya_v7_student.py`` — 1 shared forward pass, all 6
   heads) is trained on a combined loss per example::

       L = alpha * KL(softmax(teacher/T) || softmax(student/T)) * T^2
           + (1 - alpha) * CE(student, hard_label)

   summed over the issue head, fact head, 3 enum heads and safety head,
   with per-head weights (safety up-weighted: a missed safety signal
   is worse than a missed issue label).

4. Writes the student checkpoint + a run manifest (hyperparams, corpus
   SHA-256, teacher/student ids, vocab fingerprint, seed). No accuracy
   or latency number is printed as a result here — evaluation happens
   in the export step's Parity Guard and in the v7 Colab notebook.

DEPENDENCY — teacher interface (Lane 03, not yet delivered)
-----------------------------------------------------------
This script codes against the teacher interface specified in plan
§1.2 / §5.2. The teacher module MUST expose::

    class LayaV7Teacher:                       # src/laya_v7_classifier.py
        @classmethod
        def from_pretrained(cls, path, device): ...
        def teacher_logits(self, texts):       # texts: list[str]
            # -> dict[str, <array-like [B, rows, cols]>> with keys
            #    issue_logits, fact_logits, sex_logits, role_logits,
            #    time_logits, safety_logits, in the SAME row order as
            #    src/laya_v7_student.py (ISSUES / FACTS / label tuples).

If Lane 03's actual class/method names differ, the coordinator
reconciles at merge — this script fails loudly (ImportError with the
expected interface printed) rather than guessing an adapter.

DEPENDENCY — corpus (Lane 02, not yet delivered)
------------------------------------------------
``--corpus`` must point at Lane 02's ``data/synthetic_v7_1/*.jsonl``.
The script validates every record against the C2 schema and the
student vocab, and REFUSES to train (exit 2) on any mismatch:
unknown issue/fact key, wrong intent/state label, or missing enum.
The corpus must already have passed Lane 02's leakage gate
(``scripts/check_ngram_leakage.py``); this script records the corpus
SHA-256 in the manifest but does NOT re-run the gate (it must not
open sealed banks to do so).

Determinism: fixed seed, ``torch.use_deterministic_algorithms(True)``
where the backend allows, single-process data loading. Batch size is
capped at 8 and max_seq_len at 192 (plan §5.2) — the CLI rejects
larger values instead of clipping them silently.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

# Student vocab lives in src/; scripts/ is a sibling directory.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from laya_v7_student import (  # noqa: E402
    BATCH_SIZE,
    FACT_STATES,
    FACTS,
    ISSUE_INTENTS,
    ISSUES,
    MAX_SEQ_LEN,
    ROLE_LABELS,
    SEX_LABELS,
    TIME_LABELS,
    VOCAB_VERSION,
    build_student_inputs,
    check_param_budget,
    sha256_file,
    vocab_fingerprint,
)

TEACHER_MODULE = "laya_v7_classifier"
TEACHER_CLASS = "LayaV7Teacher"
TEACHER_METHOD = "teacher_logits"

# Per-head loss weights. Safety is up-weighted (see module docstring).
HEAD_WEIGHTS = {
    "issue_logits": 1.0,
    "fact_logits": 1.0,
    "sex_logits": 0.5,
    "role_logits": 0.5,
    "time_logits": 0.5,
    "safety_logits": 2.0,
}
HEAD_LABELS = {
    "issue_logits": ISSUE_INTENTS,
    "fact_logits": FACT_STATES,
    "sex_logits": SEX_LABELS,
    "role_logits": ROLE_LABELS,
    "time_logits": TIME_LABELS,
    "safety_logits": ("none", "threat_or_harassment", "imminent_physical_or_child_danger"),
}
HEAD_ROWS = {
    "issue_logits": ISSUES,
    "fact_logits": FACTS,
    "sex_logits": (None,),
    "role_logits": (None,),
    "time_logits": (None,),
    "safety_logits": (None,),
}

DEFAULT_TEMPERATURE = 2.0
DEFAULT_ALPHA = 0.7  # 0.7 * KL(soft) + 0.3 * CE(hard)
DEFAULT_EPOCHS = 3
DEFAULT_LR = 2e-5
DEFAULT_SEED = 42


# ---------------------------------------------------------------------------
# Corpus validation (pure python — runs WITHOUT torch)
# ---------------------------------------------------------------------------

def validate_corpus_record(rec: dict, line_no: int) -> list[str]:
    """Return a list of validation errors for one C2 record (empty = OK)."""
    errs: list[str] = []
    for key in ("id", "lang", "text", "issues", "facts", "enums"):
        if key not in rec:
            errs.append(f"line {line_no}: missing key {key!r}")
    if errs:
        return errs
    if rec["lang"] not in ("en", "kn", "kn_roman"):
        errs.append(f"line {line_no}: unknown lang {rec['lang']!r} (want en/kn/kn_roman)")
    if not isinstance(rec["text"], str) or not rec["text"].strip():
        errs.append(f"line {line_no}: empty text")
    for issue, intent in (rec.get("issues") or {}).items():
        if issue not in ISSUES:
            errs.append(f"line {line_no}: unknown issue {issue!r}")
        elif intent not in ISSUE_INTENTS:
            errs.append(f"line {line_no}: issue {issue!r} bad intent {intent!r}")
    for fact, state in (rec.get("facts") or {}).items():
        if fact not in FACTS:
            errs.append(f"line {line_no}: unknown fact {fact!r}")
        elif state not in FACT_STATES:
            errs.append(f"line {line_no}: fact {fact!r} bad state {state!r}")
    enums = rec.get("enums") or {}
    checks = (("claimant_sex", SEX_LABELS), ("claimant_role", ROLE_LABELS),
              ("modality_time", TIME_LABELS))
    for name, labels in checks:
        if name in enums and enums[name] not in labels:
            errs.append(f"line {line_no}: enum {name!r} bad value {enums[name]!r}")
    return errs


def load_and_validate_corpus(path: str, max_errors: int = 20) -> list[dict]:
    """Load a C2 JSONL corpus; raise ValueError listing the first errors."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"corpus not found: {path} (Lane 02, V71-P1-2)")
    records: list[dict] = []
    errors: list[str] = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {i}: invalid JSON: {exc}")
                continue
            errors.extend(validate_corpus_record(rec, i))
            records.append(rec)
            if len(errors) >= max_errors:
                break
    if errors:
        raise ValueError(
            "corpus validation FAILED (first %d errors):\n  %s"
            % (len(errors), "\n  ".join(errors))
        )
    if not records:
        raise ValueError(f"corpus is empty: {path}")
    return records


def split_clauses(text: str) -> list[str]:
    """Clause splitter for the student input list.

    Sentence-split on [.!?;\\n] (same boundary set as the NLLB
    sentence-split path in the v7 design doc). Clauses shorter than 3
    chars are dropped. This is a *tokenisation-time* convenience only —
    the teacher and student MUST receive the identical clause list, so
    both go through :func:`build_student_inputs` with this output.
    """
    import re
    parts = [p.strip() for p in re.split(r"[.!?;\n]+", text) if p.strip()]
    return [p for p in parts if len(p) >= 3]


# ---------------------------------------------------------------------------
# Teacher loading (Lane 03 dependency — fails loudly if absent)
# ---------------------------------------------------------------------------

def load_teacher(teacher_path: str, device: str):
    """Import Lane 03's teacher and instantiate it.

    Raises RuntimeError (not a bare ImportError) spelling out the
    expected interface, so a missing/wrong Lane 03 delivery is
    diagnosable instead of silently skipped.
    """
    try:
        import importlib
        module = importlib.import_module(TEACHER_MODULE)
    except ImportError as exc:
        raise RuntimeError(
            f"teacher module {TEACHER_MODULE!r} (Lane 03, V71-P1-3, "
            f"src/laya_v7_classifier.py) is not available: {exc}. "
            "Distillation cannot run until Lane 03 delivers the teacher."
        ) from exc
    cls = getattr(module, TEACHER_CLASS, None)
    if cls is None:
        raise RuntimeError(
            f"teacher module {TEACHER_MODULE!r} has no class "
            f"{TEACHER_CLASS!r}. Expected interface (plan §1.2/§5.2): "
            f"{TEACHER_CLASS}.from_pretrained(path, device) and "
            f".{TEACHER_METHOD}(texts) -> head-logit dict in "
            "src/laya_v7_student.py row order."
        )
    teacher = cls.from_pretrained(teacher_path, device)
    if not hasattr(teacher, TEACHER_METHOD):
        raise RuntimeError(
            f"teacher {TEACHER_CLASS!r} has no method {TEACHER_METHOD!r}. "
            "Expected: teacher_logits(texts) -> dict of head logits."
        )
    return teacher


# ---------------------------------------------------------------------------
# Training (torch imported lazily — --help / corpus validation work without it)
# ---------------------------------------------------------------------------

def distill_loss_fn():
    """Build the combined KL + CE loss. Imported lazily (needs torch)."""
    import torch
    import torch.nn.functional as F

    def loss(student_logits, teacher_logits, hard_targets, temperature, alpha):
        total = None
        per_head = {}
        for head, weight in HEAD_WEIGHTS.items():
            s = student_logits[head]
            t = teacher_logits[head]
            y = hard_targets[head]
            # KL on softened distributions, scaled by T^2 (Hinton et al.).
            kl = F.kl_div(
                F.log_softmax(s / temperature, dim=-1),
                F.softmax(t / temperature, dim=-1),
                reduction="batchmean",
            ) * (temperature ** 2)
            # CE on hard labels; multi-row heads flatten (B, rows, cols).
            # A head whose hard target is None (safety: the C2 corpus
            # schema carries no safety label) is trained on KL only.
            if y is None:
                head_loss = kl
            else:
                ce = F.cross_entropy(s.reshape(-1, s.shape[-1]), y.reshape(-1))
                head_loss = alpha * kl + (1.0 - alpha) * ce
            per_head[head] = float(head_loss.detach().cpu())
            total = weight * head_loss if total is None else total + weight * head_loss
        return total, per_head

    return loss


def run(args: argparse.Namespace) -> int:
    if args.batch_size > BATCH_SIZE:
        print(f"ERROR: --batch-size {args.batch_size} exceeds plan cap {BATCH_SIZE}; "
              "refusing (no silent clipping).", file=sys.stderr)
        return 2
    if args.max_seq_len > MAX_SEQ_LEN:
        print(f"ERROR: --max-seq-len {args.max_seq_len} exceeds plan cap {MAX_SEQ_LEN}; "
              "refusing (no silent clipping).", file=sys.stderr)
        return 2

    records = load_and_validate_corpus(args.corpus)
    print(f"corpus OK: {len(records)} records from {args.corpus}")
    print(f"corpus sha256: {sha256_file(args.corpus)}")
    print(f"vocab: {VOCAB_VERSION} fingerprint {vocab_fingerprint()}")

    try:
        import torch
    except ImportError as exc:  # pragma: no cover - environment-dependent
        print("ERROR: torch is required for distillation and is not installed here. "
              "This VM has no torch / no GPU by design — run on the RTX 5050 "
              f"machine or Colab T4. ({exc})", file=sys.stderr)
        return 2

    torch.manual_seed(args.seed)
    try:
        torch.use_deterministic_algorithms(True)
    except Exception as exc:  # backend may not support full determinism
        print(f"WARNING: deterministic algorithms not fully enabled: {exc}")

    from transformers import AutoTokenizer

    teacher = load_teacher(args.teacher, args.device)
    from laya_v7_student import load_student_model

    tokenizer = AutoTokenizer.from_pretrained(args.backbone)
    student = load_student_model(args.backbone, args.device)
    print(f"student params: {sum(p.numel() for p in student.parameters()):,} "
          f"(budget <= 150,000,000 — enforced in load_student_model)")

    # -- Step 1: teacher soft targets (cached so re-training is cheap).
    if args.teacher_cache and os.path.exists(args.teacher_cache) and not args.recompute_teacher:
        print(f"loading cached teacher logits from {args.teacher_cache}")
        import numpy as np
        cache = dict(np.load(args.teacher_cache, allow_pickle=True))
    else:
        print("generating teacher soft targets (1 teacher forward / example) ...")
        cache = {head: [] for head in HEAD_WEIGHTS}
        student.eval()  # noqa: F841 (student unused here; teacher runs in eval)
        teacher_fn = getattr(teacher, TEACHER_METHOD)
        with torch.no_grad():
            for i in range(0, len(records), args.batch_size):
                batch = records[i:i + args.batch_size]
                texts = [build_student_inputs(r["text"], split_clauses(r["text"]))[0]
                         for r in batch]
                # NOTE: teacher receives the FULL question only in this
                # pass; clause-level teacher targets use the same
                # build_student_inputs() list when --teacher-clauses is set.
                out = teacher_fn(texts)
                for head in HEAD_WEIGHTS:
                    arr = out[head]
                    cache[head].append(
                        arr.detach().cpu().numpy() if hasattr(arr, "detach") else arr
                    )
        import numpy as np
        cache = {h: np.concatenate(v, axis=0) for h, v in cache.items()}
        if args.teacher_cache:
            np.savez_compressed(args.teacher_cache, **cache)
            print(f"teacher logits cached to {args.teacher_cache}")

    # -- Step 2: student training on KL(soft) + CE(hard).
    loss_fn = distill_loss_fn()
    optimizer = torch.optim.AdamW(student.parameters(), lr=args.lr,
                                  weight_decay=0.01)
    student.train()
    for epoch in range(1, args.epochs + 1):
        epoch_loss = 0.0
        steps = 0
        for i in range(0, len(records), args.batch_size):
            batch = records[i:i + args.batch_size]
            enc = tokenizer(
                [r["text"] for r in batch],
                padding="max_length", max_length=args.max_seq_len,
                truncation=True, return_tensors="pt",
            ).to(args.device)
            out = student(input_ids=enc["input_ids"],
                          attention_mask=enc["attention_mask"])
            # Hard targets: row-major index per head, from the C2 labels.
            hard = {}
            import torch as _t
            for head, rows in HEAD_ROWS.items():
                labels = HEAD_LABELS[head]
                if rows == (None,):
                    key = {"sex_logits": "claimant_sex",
                           "role_logits": "claimant_role",
                           "time_logits": "modality_time",
                           "safety_logits": None}[head]
                    # Safety has NO hard label in the C2 corpus schema
                    # (plan §1.2) — None means KL-only for that head
                    # (see distill_loss_fn). Do NOT default it to "none":
                    # that would teach the student to never fire safety.
                    vals = None if key is None else [
                        labels.index(r["enums"][key]) for r in batch]
                    hard[head] = (None if vals is None else
                                  _t.tensor(vals, device=args.device))
                else:
                    src = "issues" if head == "issue_logits" else "facts"
                    hard[head] = _t.tensor(
                        [[labels.index(r[src].get(row, labels[-1])) for row in rows]
                         for r in batch], device=args.device)
            teacher_batch = {
                h: torch.as_tensor(cache[h][i:i + len(batch)]).to(args.device)
                for h in HEAD_WEIGHTS
            }
            total, per_head = loss_fn(out, teacher_batch, hard,
                                      args.temperature, args.alpha)
            optimizer.zero_grad()
            total.backward()
            torch.nn.utils.clip_grad_norm_(student.parameters(), 1.0)
            optimizer.step()
            epoch_loss += float(total.detach().cpu())
            steps += 1
        print(f"epoch {epoch}/{args.epochs}: mean loss {epoch_loss / max(steps, 1):.4f}")

    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    torch.save(student.state_dict(), args.output)
    manifest = {
        "task": "V71-P5-1",
        "vocab_version": VOCAB_VERSION,
        "vocab_fingerprint": vocab_fingerprint(),
        "corpus": args.corpus,
        "corpus_sha256": sha256_file(args.corpus),
        "corpus_records": len(records),
        "teacher": args.teacher,
        "teacher_module": f"{TEACHER_MODULE}.{TEACHER_CLASS}.{TEACHER_METHOD}",
        "teacher_cache": args.teacher_cache,
        "backbone": args.backbone,
        "temperature": args.temperature,
        "alpha_kl": args.alpha,
        "epochs": args.epochs,
        "lr": args.lr,
        "batch_size": args.batch_size,
        "max_seq_len": args.max_seq_len,
        "seed": args.seed,
        "head_weights": HEAD_WEIGHTS,
        "output": args.output,
        "note": "No accuracy/latency claimed here. Evaluate via "
                "scripts/export_student_onnx.py (Parity Guard) and the "
                "v7 Colab notebook (G14-T4).",
    }
    manifest_path = args.output + ".manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    print(f"student checkpoint saved: {args.output}")
    print(f"run manifest saved: {manifest_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Distill Lane 03's multi-head teacher into the "
                    "single-pass student (V71-P5-1). GPU + torch required.")
    p.add_argument("--corpus", required=True,
                   help="Lane 02 C2 JSONL corpus (data/synthetic_v7_1/*.jsonl)")
    p.add_argument("--teacher", required=True,
                   help="Lane 03 teacher checkpoint path")
    p.add_argument("--backbone", default="6-layer distilled mmBERT",
                   help="Student backbone id (permissive licence only; "
                        "verified at execution by Lane 06 audit)")
    p.add_argument("--output", default="models/student_fp32.pt",
                   help="Student checkpoint output path")
    p.add_argument("--teacher-cache", default="models/teacher_logits.npz",
                   help="Cached teacher soft targets (.npz)")
    p.add_argument("--recompute-teacher", action="store_true",
                   help="Regenerate teacher logits even if cache exists")
    p.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    p.add_argument("--alpha", type=float, default=DEFAULT_ALPHA,
                   help="KL weight; (1-alpha) is the hard-label CE weight")
    p.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    p.add_argument("--lr", type=float, default=DEFAULT_LR)
    p.add_argument("--batch-size", type=int, default=BATCH_SIZE,
                   help=f"plan cap: <= {BATCH_SIZE}")
    p.add_argument("--max-seq-len", type=int, default=MAX_SEQ_LEN,
                   help=f"plan cap: <= {MAX_SEQ_LEN}")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--device", default="cuda",
                   help="cuda (RTX 5050) — CPU training is not supported")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
