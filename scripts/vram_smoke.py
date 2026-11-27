"""Phase A gate A6 — VRAM smoke test (code for Colab T4 / RTX 5050).

Measures the ADOPTED config (FALLBACK-2, as amended by GPT-RERUN):
1-pass span pooling, max_seq_len 320, bf16, gradient checkpointing,
dynamic padding. Micro-batch 8 is a TARGET, not a guarantee (GPT-RERUN
§4: the fallback's VRAM claim was overstated — 8.1x padded tokens, not
proven VRAM; the script must VERIFY that 8 actually fits).

What this script does (GPU only — it cannot run on this VM, which has
no torch; it exits 2 there with a clear message pointing at Colab):

  1. Micro-batch sweep 1, 2, 4, 8: forward + backward + optimizer step
     on REAL tokenized corpus batches (dynamic padding to the longest
     sequence in the batch), bf16 autocast, gradient checkpointing on.
     Records peak allocated memory per size and the largest size that
     fits without OOM. An OOM at 8 is a GATE FAILURE for the target, not
     a reason to silently shrink the batch — the report names the
     largest fitting size as the fallback for Lane B.
  2. Loss-decrease check: 32 real records, 10 optimizer steps at the
     largest fitting micro-batch, lr 2e-5 — loss must decrease
     (final < initial). A non-decreasing loss means the probe training
     loop itself is broken, not that the model is bad.
  3. Truncation audit: tokenize the training corpus at max_seq_len 320;
     count records truncated, and count ANNOTATED SPANS whose tokens fall
     beyond 320 (annotated labels lost). Gate: 0 annotated labels lost.

The probe is a standalone encoder + heads (AutoModel mmBERT-base +
linear heads sized 11x4 / 28x4 / enums) — it measures the ADOPTED
1-pass architecture independently of whether Lane B has landed the
1-pass change in ``src/laya_v7_classifier.py`` yet. The script also
detects and reports which architecture the repo classifier currently
implements (9-pass if ``forward`` still takes ``clause_input_ids``).

Expected-gate table (all must pass for A6 PASS):
  peak memory at micro-batch 8 ......... < 6.5 GB (Gemini gate; the
                                          RTX 5050 has 8 GB — on a 16 GB
                                          Colab T4 the same number is the
                                          portability target, not the cap)
  largest fitting micro-batch .......... 8 (target; else record fallback)
  loss decreases on 32-example subset .. yes
  truncation events .................... recorded (count + % of records)
  annotated labels lost to truncation .. 0

Exit codes: 0 gates pass; 1 a gate fails (report names the failing gate
and the fallback); 2 torch/transformers missing (run on Colab).

Usage (Colab T4 / RTX 5050, from the repo root):

    python3 scripts/vram_smoke.py --backbone jhu-clsp/mmBERT-base \\
        --train-file data/synthetic_v7_1/train.jsonl \\
        --max-seq-len 320 --json-out /tmp/vram_smoke.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from laya_v7_classifier import (  # noqa: E402
    ENUMS, FACT_STATES, FACTS, ISSUE_INTENTS, ISSUES, encode_labels,
    load_corpus_jsonl,
)

PEAK_MEMORY_TARGET_GB = 6.5
MAX_SEQ_LEN = 320
MICRO_BATCH_SWEEP = (1, 2, 4, 8)
LOSS_SUBSET_N = 32
LOSS_STEPS = 10
LR = 2e-5


def require_torch():
    try:
        import torch  # noqa: F401
        return True
    except ImportError:
        print("torch is NOT installed on this VM. Do not run here.",
              file=sys.stderr)
        print("Run this script on Colab (T4 GPU) or the RTX 5050 machine:",
              file=sys.stderr)
        print("  python3 scripts/vram_smoke.py --backbone "
              "jhu-clsp/mmBERT-base --train-file "
              "data/synthetic_v7_1/train.jsonl", file=sys.stderr)
        return False


def detect_repo_architecture() -> str:
    """What does the repo classifier implement today: 9-pass or 1-pass?"""
    src = (REPO_ROOT / "src" / "laya_v7_classifier.py").read_text(
        encoding="utf-8")
    if 'pooling: str = "one_pass"' in src:
        return ("1-pass (default, pooling='one_pass': the full question "
                "is encoded ONCE; clause vectors come from "
                "span_pool_clauses() over that encoding). A 9-pass "
                "fallback still exists (pooling='nine_pass'). This probe "
                "measures the same adopted 1-pass architecture.")
    if "clause_input_ids" in src:
        return ("9-pass (forward takes clause_input_ids; clause logits "
                "come from separate clause encodings) — the 1-pass "
                "span-pooling change (Lane B) has NOT landed yet. This "
                "probe measures the ADOPTED 1-pass architecture directly, "
                "not the repo code.")
    return "unknown — inspect src/laya_v7_classifier.py forward() manually"


def build_probe(backbone: str, device: str):
    """Standalone 1-pass encoder + heads (adopted architecture)."""
    import torch
    from torch import nn
    from transformers import AutoConfig, AutoModel

    hf_cfg = AutoConfig.from_pretrained(backbone)
    encoder = AutoModel.from_pretrained(backbone, config=hf_cfg)
    hidden = hf_cfg.hidden_size

    class Probe(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = encoder
            self.issue_head = nn.Linear(
                hidden, len(ISSUES) * len(ISSUE_INTENTS))
            self.fact_head = nn.Linear(
                hidden, len(FACTS) * len(FACT_STATES))
            self.enum_heads = nn.ModuleDict({
                h: nn.Linear(hidden, len(v)) for h, v in ENUMS.items()})
            # Span-attention pooling (1-pass): token scores -> weighted
            # mean over the single full-question encoding.
            self.span_attn = nn.Linear(hidden, 1)

        def forward(self, input_ids, attention_mask):
            out = self.encoder(input_ids=input_ids,
                               attention_mask=attention_mask)
            h = out.last_hidden_state
            scores = self.span_attn(h).squeeze(-1)
            scores = scores.masked_fill(attention_mask == 0, float("-inf"))
            w = torch.softmax(scores, dim=-1)
            pooled = torch.sum(h * w.unsqueeze(-1), dim=1)
            cls = h[:, 0, :]
            vec = pooled + cls  # span-pooled + CLS (probe fusion)
            return {
                "issue_logits": self.issue_head(vec).view(
                    -1, len(ISSUES), len(ISSUE_INTENTS)),
                "fact_logits": self.fact_head(vec).view(
                    -1, len(FACTS), len(FACT_STATES)),
                "enum_logits": {h: layer(vec)
                                for h, layer in self.enum_heads.items()},
            }

    model = Probe()
    model.to(device)
    try:
        model.encoder.gradient_checkpointing_enable()
        grad_ckpt = True
    except Exception as exc:  # noqa: BLE001 - backbone-dependent
        print(f"WARNING: gradient checkpointing unavailable: {exc}")
        grad_ckpt = False
    return model, grad_ckpt


def tokenize_records(tokenizer, records: list, max_len: int):
    return [tokenizer(r["text"], truncation=True, max_length=max_len)
            for r in records]


def make_batch(tokenizer, encodings: list, labels: list, device: str):
    import torch
    pad = tokenizer.pad_token_id or 0
    maxlen = max(len(e["input_ids"]) for e in encodings)
    b = len(encodings)
    ids = torch.full((b, maxlen), pad, dtype=torch.long)
    mask = torch.zeros((b, maxlen), dtype=torch.long)
    for i, e in enumerate(encodings):
        ids[i, :len(e["input_ids"])] = torch.tensor(e["input_ids"])
        mask[i, :len(e["attention_mask"])] = torch.tensor(e["attention_mask"])
    issue = torch.tensor([lb["issue"] for lb in labels], dtype=torch.long)
    fact = torch.tensor([lb["fact"] for lb in labels], dtype=torch.long)
    enums = {h: torch.tensor([lb["enums"][h] for lb in labels],
                             dtype=torch.long) for h in ENUMS}
    return {"ids": ids.to(device), "mask": mask.to(device),
            "issue": issue.to(device), "fact": fact.to(device),
            "enums": {h: v.to(device) for h, v in enums.items()}}


def loss_for(model, batch) -> "torch.Tensor":
    import torch
    from torch import nn
    out = model(batch["ids"], batch["mask"])
    ce = nn.CrossEntropyLoss()
    li = ce(out["issue_logits"].reshape(-1, len(ISSUE_INTENTS)),
            batch["issue"].reshape(-1))
    lf = ce(out["fact_logits"].reshape(-1, len(FACT_STATES)),
            batch["fact"].reshape(-1))
    le = sum(ce(out["enum_logits"][h], batch["enums"][h])
             for h in ENUMS) / len(ENUMS)
    return 0.35 * li + 0.35 * lf + 0.15 * le


def sweep_micro_batches(model, tokenizer, records, device: str,
                        max_len: int) -> dict:
    import torch
    labels = [encode_labels(r) for r in records]
    enc = tokenize_records(tokenizer, records, max_len)
    results: dict = {}
    for mb in MICRO_BATCH_SWEEP:
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        batch = make_batch(tokenizer, enc[:mb], labels[:mb], device)
        opt = torch.optim.AdamW(model.parameters(), lr=LR)
        try:
            t0 = time.perf_counter()
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                loss = loss_for(model, batch)
            loss.backward()
            opt.step()
            opt.zero_grad()
            dt = time.perf_counter() - t0
            peak_gb = torch.cuda.max_memory_allocated() / 1e9
            tokens = int(batch["mask"].sum())
            results[str(mb)] = {
                "fits": True, "peak_gb": round(peak_gb, 3),
                "loss": round(float(loss), 4),
                "seconds": round(dt, 3),
                "tokens_per_sec": round(tokens / max(dt, 1e-6), 1),
            }
            print(f"  micro-batch {mb}: fits, peak "
                  f"{peak_gb:.2f} GB, loss {float(loss):.4f}")
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            results[str(mb)] = {"fits": False, "peak_gb": None,
                                "loss": None, "note": "OOM"}
            print(f"  micro-batch {mb}: OOM (does not fit)")
        finally:
            opt.zero_grad(set_to_none=True)
            del batch
            torch.cuda.empty_cache()
    return results


def loss_decrease_check(model, tokenizer, records, device: str,
                        max_len: int, micro_batch: int) -> dict:
    import torch
    labels = [encode_labels(r) for r in records[:LOSS_SUBSET_N]]
    enc = tokenize_records(tokenizer, records[:LOSS_SUBSET_N], max_len)
    opt = torch.optim.AdamW(model.parameters(), lr=LR)
    losses: list[float] = []
    for step in range(LOSS_STEPS):
        chunk_enc = enc[step * micro_batch:(step + 1) * micro_batch] or enc[:micro_batch]
        chunk_lab = labels[step * micro_batch:(step + 1) * micro_batch] or labels[:micro_batch]
        batch = make_batch(tokenizer, chunk_enc, chunk_lab, device)
        opt.zero_grad()
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            loss = loss_for(model, batch)
        loss.backward()
        opt.step()
        losses.append(round(float(loss), 4))
        del batch
        torch.cuda.empty_cache()
    return {"steps": LOSS_STEPS, "subset_n": LOSS_SUBSET_N,
            "micro_batch": micro_batch, "losses": losses,
            "initial": losses[0], "final": losses[-1],
            "decreased": losses[-1] < losses[0]}


def truncation_audit(tokenizer, records: list, max_len: int) -> dict:
    total_truncated = 0
    spans_total = spans_lost = 0
    for r in records:
        enc = tokenizer(r["text"], add_special_tokens=True,
                        return_offsets_mapping=True)
        offsets = enc["offset_mapping"]
        ids = enc["input_ids"]
        if len(ids) > max_len:
            total_truncated += 1
        for sp in r.get("spans") or []:
            spans_total += 1
            tok_idx = [i for i, (s, e) in enumerate(offsets)
                       if s <= sp["start"] < e or s < sp["end"] <= e]
            if tok_idx and max(tok_idx) >= max_len:
                spans_lost += 1
    return {"n_records": len(records), "max_seq_len": max_len,
            "records_truncated": total_truncated,
            "truncation_rate": round(total_truncated / max(1, len(records)), 4),
            "spans_total": spans_total, "spans_lost": spans_lost,
            "annotated_labels_lost": spans_lost}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="VRAM smoke test (A6).")
    ap.add_argument("--backbone", default="jhu-clsp/mmBERT-base")
    ap.add_argument("--train-file", default="data/synthetic_v7_1/train.jsonl")
    ap.add_argument("--max-seq-len", type=int, default=MAX_SEQ_LEN)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--audit-limit", type=int, default=0,
                    help="Records for the truncation audit (0 = all).")
    args = ap.parse_args(argv)

    if not require_torch():
        return 2
    import torch
    from transformers import AutoTokenizer

    if not torch.cuda.is_available():
        print("ERROR: no CUDA device visible. Run on Colab (T4) or the "
              "RTX 5050 machine with --device cuda.", file=sys.stderr)
        return 2
    device = args.device
    print(f"VRAM smoke test (A6) — backbone {args.backbone}, "
          f"max_seq_len {args.max_seq_len}, device {device}")
    print(f"GPU: {torch.cuda.get_device_name(0)} "
          f"({torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB)")
    print(f"Repo classifier architecture: {detect_repo_architecture()}")
    print(f"Config: 1-pass span pooling, bf16, grad checkpointing, "
          f"dynamic padding. Micro-batch 8 is a TARGET to verify.")
    print()

    records, _ = load_corpus_jsonl(args.train_file)
    tokenizer = AutoTokenizer.from_pretrained(args.backbone)
    model, grad_ckpt = build_probe(args.backbone, device)
    print(f"Probe built (grad checkpointing: {grad_ckpt}). "
          "Micro-batch sweep (forward + backward + step):")
    sweep = sweep_micro_batches(model, tokenizer, records, device,
                                args.max_seq_len)
    fitting = [int(k) for k, v in sweep.items() if v["fits"]]
    largest = max(fitting) if fitting else 0
    print(f"Largest fitting micro-batch: {largest} "
          f"(target 8: {'MET' if largest >= 8 else 'NOT MET — fallback ' + str(largest)})")
    print()
    loss_check = {"decreased": False, "note": "skipped (no fitting batch)"}
    if largest:
        print(f"Loss-decrease check ({LOSS_SUBSET_N} records, "
              f"{LOSS_STEPS} steps, micro-batch {largest}):")
        loss_check = loss_decrease_check(model, tokenizer, records, device,
                                         args.max_seq_len, largest)
        print(f"  losses: {loss_check['losses']}")
        print(f"  decreased: {loss_check['decreased']} "
              f"({loss_check['initial']} -> {loss_check['final']})")
    print()
    print("Truncation audit:")
    audit_recs = records[:args.audit_limit] if args.audit_limit else records
    audit = truncation_audit(tokenizer, audit_recs, args.max_seq_len)
    print(f"  records truncated at {args.max_seq_len}: "
          f"{audit['records_truncated']}/{audit['n_records']} "
          f"({audit['truncation_rate']:.1%}); annotated spans lost: "
          f"{audit['spans_lost']}/{audit['spans_total']}")
    print()

    peak8 = sweep.get("8", {}).get("peak_gb")
    gates = {
        "peak_memory_lt_6.5GB_at_mb8": (
            peak8 is not None and peak8 < PEAK_MEMORY_TARGET_GB),
        "micro_batch_8_fits": sweep.get("8", {}).get("fits") is True,
        "loss_decreases_on_subset": bool(loss_check.get("decreased")),
        "zero_annotated_labels_lost": audit["spans_lost"] == 0,
    }
    print("Expected-gate table (A6):")
    for gate, ok in gates.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {gate}")
    if peak8 is not None:
        print(f"  peak at micro-batch 8: {peak8} GB "
              f"(target < {PEAK_MEMORY_TARGET_GB} GB)")
    print(f"  largest fitting micro-batch: {largest} "
          f"(fallback for Lane B if 8 fails)")
    report = {"backbone": args.backbone, "max_seq_len": args.max_seq_len,
              "device": device,
              "gpu": torch.cuda.get_device_name(0),
              "grad_checkpointing": grad_ckpt,
              "micro_batch_sweep": sweep,
              "largest_fitting_micro_batch": largest,
              "loss_decrease_check": loss_check,
              "truncation_audit": audit, "gates": gates,
              "peak_memory_target_gb": PEAK_MEMORY_TARGET_GB}
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {args.json_out}")
    if all(gates.values()):
        print("A6 PASS (exit 0).")
        return 0
    print("A6 FAIL on at least one gate (exit 1) — see the table above; "
          "the fallback micro-batch is recorded, nothing was silently "
          "shrunk.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
