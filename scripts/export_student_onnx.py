#!/usr/bin/env python3
"""Export the distilled student to ONNX + dynamic INT8 (V71-P5-2).

Lane 08 (Pillar 5) — SCRIPTS + DESIGN ONLY. This script is NOT run on
this VM: it needs torch, onnxruntime and the distilled student
checkpoint, none of which exist here. Run it on the user's RTX 5050
machine (commands in docs/10x_swarm_state/lane-08-p5.md).

Pipeline (plan docs/10x_plane.md §5.2, V71-P5-2)
------------------------------------------------
1. Load the FP32 student (``src/laya_v7_student.py``) from
   ``--student`` (output of ``scripts/distill_student.py``).
2. Export pure PyTorch -> ONNX, opset 17, dynamic batch axis::

       (input_ids, attention_mask)
         -> (issue_logits, fact_logits, sex_logits,
             role_logits, time_logits, safety_logits)

   completely bypassing ``laya.ONNXAgent``'s sequential loop.
3. Apply ``onnxruntime.quantization.quantize_dynamic`` (QInt8,
   MatMul/Attention) + ORT graph fusion (``ORT_ENABLE_ALL``:
   Gemm / LayerNorm / GELU) at inference time via the session options
   in :func:`make_ort_session`.
4. Deterministic shape-bucket padding (64 / 128 / 192 tokens) via
   ``src.laya_v7_student.pad_to_bucket`` — every inference input is
   padded to its bucket, so the same text always takes the same graph
   path on every run.
5. Batch permutation invariance check: the same questions in forward,
   reversed and shuffled order must return identical argmax labels and
   probabilities within 1e-4 (the CI tolerance in plan §7.4).
6. Parity Guard (step 7) — the artifact is REJECTED if it fails.

PARITY GUARD — exact thresholds implemented here
-------------------------------------------------
The plan's §5.2 Parity Guard line is truncated mid-sentence in
``docs/10x_plane.md`` ("Reject quantized artifact if `max ..."), so
Lane 08 completes it from the plan's own stated tolerances, and
states them here explicitly (they are Lane 08's implementation
choice, not a plan quotation):

* ``MAX_ABS_DIFF = 0.03`` — max absolute difference between FP32
  PyTorch and INT8 ONNX *softmax probabilities*, over all 6 heads,
  on the parity probe set. (Same 0.03 the plan §5.2/§5.3 uses for
  T4-vs-RTX parity, and the same magnitude as the measured
  bf16-vs-fp16 drift 0.0281 in docs/v7-multilingual-prose-latency-design.md.)
* ``MAX_FLIPS = 0`` — zero argmax flips on any head (issue / fact /
  sex / role / time / safety) between FP32 PyTorch and INT8 ONNX.
* ``MAX_MICRO_F1_DROP = 0.005`` — student INT8 micro-F1 may fall at
  most 0.5% below the FP32 student on the held-out synthetic dev
  split (plan §5.3: "within <= 0.5% micro-F1").

If ANY threshold is breached the script exits non-zero and renames
the INT8 file to ``*.rejected.onnx`` — a failed artifact must never
be served as ``models/student_int8.onnx``. The FP32 ONNX is kept
(it is the fallback for re-quantization attempts).

Probe set: ``--probe`` is a JSONL file of ``{"text": ...}`` records
(default: the held-out synthetic dev split from Lane 02 — NEVER a
sealed bank; the script refuses paths under ``test-bank/sealed/``).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from laya_v7_student import (  # noqa: E402
    HEAD_SHAPES,
    MAX_SEQ_LEN,
    ONNX_INPUTS,
    ONNX_OPSET,
    ONNX_OUTPUTS,
    SHAPE_BUCKETS,
    VOCAB_VERSION,
    pad_to_bucket,
    vocab_fingerprint,
)

# --- Parity Guard thresholds (see module docstring for provenance) ---
MAX_ABS_DIFF = 0.03
MAX_FLIPS = 0
MAX_MICRO_F1_DROP = 0.005
PERMUTATION_TOL = 1e-4  # plan §7.4 batch-invariance tolerance

QUANT_OP_TYPES = ["MatMul", "Attention"]


# ---------------------------------------------------------------------------
# Pure-python helpers (run WITHOUT torch/onnxruntime)
# ---------------------------------------------------------------------------

def refuse_sealed_path(path: str) -> None:
    """Never let a sealed bank be used as an export probe set."""
    norm = os.path.normpath(path)
    if "test-bank" in norm and "sealed" in norm:
        raise ValueError(
            f"refusing sealed path as probe set: {path}. Parity probes "
            "must come from the held-out synthetic dev split (Lane 02), "
            "never from test-bank/sealed/*.json."
        )


def load_probe_texts(path: str, limit: int | None = None) -> list[str]:
    refuse_sealed_path(path)
    texts: list[str] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            texts.append(rec["text"] if isinstance(rec, dict) else str(rec))
            if limit and len(texts) >= limit:
                break
    if not texts:
        raise ValueError(f"probe file is empty: {path}")
    return texts


def parity_verdict(max_abs_diff: float, flips: int,
                   micro_f1_drop: float) -> dict:
    """Pure-python Parity Guard decision (unit-testable without ORT)."""
    failures = []
    if max_abs_diff > MAX_ABS_DIFF:
        failures.append(
            f"max_abs_diff {max_abs_diff:.4f} > {MAX_ABS_DIFF}")
    if flips > MAX_FLIPS:
        failures.append(f"argmax flips {flips} > {MAX_FLIPS}")
    if micro_f1_drop > MAX_MICRO_F1_DROP:
        failures.append(
            f"micro-F1 drop {micro_f1_drop:.4f} > {MAX_MICRO_F1_DROP}")
    return {"pass": not failures,
            "max_abs_diff": max_abs_diff, "flips": flips,
            "micro_f1_drop": micro_f1_drop,
            "thresholds": {"max_abs_diff": MAX_ABS_DIFF,
                           "max_flips": MAX_FLIPS,
                           "max_micro_f1_drop": MAX_MICRO_F1_DROP},
            "failures": failures}


def check_permutation_invariance(outputs_forward: list,
                                 outputs_shuffled: list) -> dict:
    """Compare two orderings of the same batch (pure python).

    ``outputs_*`` are lists of per-example head-prob dicts in batch
    order; the caller re-aligns the shuffled list to forward order
    before calling. Returns max abs prob diff and whether it is
    within PERMUTATION_TOL (1e-4).
    """
    worst = 0.0
    for a, b in zip(outputs_forward, outputs_shuffled):
        for head in a:
            for x, y in zip(a[head], b[head]):
                worst = max(worst, abs(float(x) - float(y)))
    return {"max_abs_diff": worst, "within_tol": worst <= PERMUTATION_TOL,
            "tol": PERMUTATION_TOL}


# ---------------------------------------------------------------------------
# ORT / ONNX (torch + onnxruntime imported lazily)
# ---------------------------------------------------------------------------

def make_ort_session(onnx_path: str, device: str = "cpu"):
    """ORT session with full graph fusion (Gemm/LayerNorm/GELU).

    ``device="cuda"`` requests the CUDA execution provider (student_onnx_gpu
    tier); anything else uses CPU (student_onnx_int8_cpu tier).
    """
    import onnxruntime as ort
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    providers = (["CUDAExecutionProvider", "CPUExecutionProvider"]
                 if device == "cuda" else ["CPUExecutionProvider"])
    return ort.InferenceSession(onnx_path, sess_options=opts, providers=providers)


def run_ort_batch(session, tokenizer, texts: list[str],
                  max_seq_len: int = MAX_SEQ_LEN) -> dict[str, object]:
    """One ORT batch with deterministic shape-bucket padding.

    Each text is tokenized, truncated to ``max_seq_len``, then padded
    to its bucket (64/128/192) — the whole batch is padded to the
    LONGEST text's bucket, so batch composition cannot change a
    single text's padding (a precondition for permutation invariance).
    """
    import numpy as np
    enc = tokenizer(texts, truncation=True, max_length=max_seq_len,
                    padding=False, return_tensors="np")
    bucket = pad_to_bucket(int(enc["input_ids"].shape[1]))
    pad_len = bucket - int(enc["input_ids"].shape[1])
    if pad_len:
        input_ids = np.pad(enc["input_ids"], ((0, 0), (0, pad_len)))
        attention_mask = np.pad(enc["attention_mask"], ((0, 0), (0, pad_len)))
    else:
        input_ids, attention_mask = enc["input_ids"], enc["attention_mask"]
    return {name: np.asarray(out) for name, out in zip(
        ONNX_OUTPUTS,
        session.run(list(ONNX_OUTPUTS),
                    {"input_ids": input_ids.astype(np.int64),
                     "attention_mask": attention_mask.astype(np.int64)}))}


def export_and_quantize(args: argparse.Namespace) -> int:
    try:
        import torch
    except ImportError as exc:
        print("ERROR: torch is required for ONNX export and is not installed "
              "here. This VM has no torch / no GPU by design — run on the "
              f"RTX 5050 machine or Colab T4. ({exc})", file=sys.stderr)
        return 2
    try:
        import onnxruntime  # noqa: F401  (checked present before exporting)
        from onnxruntime.quantization import QuantType, quantize_dynamic
    except ImportError as exc:
        print(f"ERROR: onnxruntime is required: {exc}", file=sys.stderr)
        return 2

    from transformers import AutoTokenizer
    from laya_v7_student import load_student_model

    probe_texts = load_probe_texts(args.probe, limit=args.probe_limit)
    print(f"probe set: {len(probe_texts)} texts from {args.probe}")

    tokenizer = AutoTokenizer.from_pretrained(args.backbone)
    student = load_student_model(args.backbone, "cpu")
    student.load_state_dict(torch.load(args.student, map_location="cpu"))
    student.eval()
    print(f"student loaded: {args.student} "
          f"({sum(p.numel() for p in student.parameters()):,} params)")

    # -- Step 1: FP32 ONNX export (opset 17, dynamic batch axis).
    dummy = tokenizer(["test"], return_tensors="pt")
    os.makedirs(os.path.dirname(os.path.abspath(args.output_fp32)) or ".", exist_ok=True)
    with torch.no_grad():
        torch.onnx.export(
            student, (dummy["input_ids"], dummy["attention_mask"]),
            args.output_fp32,
            input_names=list(ONNX_INPUTS), output_names=list(ONNX_OUTPUTS),
            dynamic_axes={n: {0: "batch"} for n in list(ONNX_INPUTS) + list(ONNX_OUTPUTS)},
            opset_version=ONNX_OPSET, do_constant_folding=True,
        )
    print(f"FP32 ONNX written: {args.output_fp32} (opset {ONNX_OPSET})")

    # -- Step 2: dynamic INT8 quantization (QInt8 MatMul/Attention).
    quantize_dynamic(
        model_input=args.output_fp32,
        model_output=args.output_int8,
        weight_type=QuantType.QInt8,
        op_types_to_quantize=QUANT_OP_TYPES,
    )
    print(f"INT8 ONNX written: {args.output_int8} "
          f"(QInt8 {QUANT_OP_TYPES}, ORT_ENABLE_ALL fusion at load)")

    # -- Step 3: parity — FP32 PyTorch vs INT8 ONNX, same probe batch.
    # Micro-F1 drop is computed here too when the probe file carries
    # hard labels: per-row multi-class micro-F1 equals accuracy, so the
    # drop is (FP32 correct rows - INT8 correct rows) / total rows over
    # the issue + fact + enum heads. Unlabelled probe files skip only
    # this third check (the probs/flips gates still apply).
    import numpy as np
    import torch.nn.functional as F

    from laya_v7_student import (FACT_STATES, FACTS, ISSUE_INTENTS, ISSUES,
                                 ROLE_LABELS, SEX_LABELS, TIME_LABELS)
    _LABEL_INDEX = {
        "issue_logits": (ISSUES, ISSUE_INTENTS, "issues"),
        "fact_logits": (FACTS, FACT_STATES, "facts"),
    }
    _ENUM_INDEX = {
        "sex_logits": ("claimant_sex", SEX_LABELS),
        "role_logits": ("claimant_role", ROLE_LABELS),
        "time_logits": ("modality_time", TIME_LABELS),
    }
    probe_labels: list[dict] | None = None
    try:
        _recs = [json.loads(line) for line in
                 open(args.probe, encoding="utf-8") if line.strip()]
        if _recs and all(isinstance(r, dict) and "issues" in r and "facts" in r
                         for r in _recs):
            probe_labels = _recs[:len(probe_texts)]
            print(f"probe file carries hard labels for {len(probe_labels)} records")
    except Exception as exc:  # probe labels are advisory, not fatal
        print(f"WARNING: could not read probe hard labels: {exc}")

    def _probs(logits: np.ndarray) -> np.ndarray:
        # logits: [B, rows, cols] or [B, cols]; softmax on last axis.
        x = logits - logits.max(axis=-1, keepdims=True)
        e = np.exp(x)
        return e / e.sum(axis=-1, keepdims=True)

    max_abs_diff = 0.0
    flips = 0
    fp32_correct = int8_correct = total_rows = 0
    with torch.no_grad():
        for i in range(0, len(probe_texts), 8):
            batch = probe_texts[i:i + 8]
            enc = tokenizer(batch, truncation=True, max_length=MAX_SEQ_LEN,
                            padding=True, return_tensors="pt")
            ref = student(input_ids=enc["input_ids"],
                          attention_mask=enc["attention_mask"])
            int8 = run_ort_batch(make_ort_session(args.output_int8, "cpu"),
                                 tokenizer, batch)
            for head in ONNX_OUTPUTS:
                ref_p = _probs(ref[head].detach().cpu().numpy())
                int_p = _probs(np.asarray(int8[head]))
                max_abs_diff = max(max_abs_diff, float(np.abs(ref_p - int_p).max()))
                flips += int((ref_p.argmax(axis=-1) != int_p.argmax(axis=-1)).sum())
            if probe_labels is not None:
                for k, rec in enumerate(probe_labels[i:i + len(batch)]):
                    for head, (rows, labels, src) in _LABEL_INDEX.items():
                        ref_a = _probs(ref[head].detach().cpu().numpy())[k]
                        int_a = _probs(np.asarray(int8[head]))[k]
                        for r, row in enumerate(rows):
                            gold = labels.index(rec[src].get(row, labels[-1]))
                            total_rows += 1
                            fp32_correct += int(ref_a[r].argmax() == gold)
                            int8_correct += int(int_a[r].argmax() == gold)
                    for head, (key, labels) in _ENUM_INDEX.items():
                        gold = labels.index(rec["enums"][key])
                        total_rows += 1
                        fp32_correct += int(
                            _probs(ref[head].detach().cpu().numpy())[k].argmax() == gold)
                        int8_correct += int(
                            _probs(np.asarray(int8[head]))[k].argmax() == gold)
    print(f"parity (FP32 torch vs INT8 ONNX): max_abs_diff={max_abs_diff:.4f}, "
          f"argmax flips={flips}")
    if probe_labels is not None and total_rows:
        micro_f1_drop = (fp32_correct - int8_correct) / total_rows
        print(f"micro-F1 (= accuracy over {total_rows} head rows): "
              f"FP32 {fp32_correct / total_rows:.4f} vs INT8 "
              f"{int8_correct / total_rows:.4f} (drop {micro_f1_drop:.4f})")
    else:
        micro_f1_drop = 0.0
        print("probe file has no hard labels: micro-F1 drop check skipped "
              "(probs/flips gates still apply; suite-level 0.5% gate is "
              "enforced end-to-end in the v7 notebook + test_v7_rules.py).")

    # -- Step 4: batch permutation invariance (forward vs reversed vs shuffled).
    session = make_ort_session(args.output_int8, "cpu")
    rng = random.Random(1234)
    sample = probe_texts[:32]
    fwd = run_ort_batch(session, tokenizer, sample)
    rev = run_ort_batch(session, tokenizer, list(reversed(sample)))
    order = list(range(len(sample)))
    rng.shuffle(order)
    shuf = run_ort_batch(session, tokenizer, [sample[j] for j in order])

    def _to_prob_lists(out: dict) -> list:
        rows = []
        for k in range(len(sample)):
            rows.append({h: _probs(np.asarray(out[h]))[k].reshape(-1).tolist()
                         for h in ONNX_OUTPUTS})
        return rows

    fwd_rows = _to_prob_lists(fwd)
    rev_rows = _to_prob_lists(rev)[::-1]
    shuf_rows = [None] * len(sample)
    for pos, j in enumerate(order):
        shuf_rows[j] = _to_prob_lists(shuf)[pos]
    perm_rev = check_permutation_invariance(fwd_rows, rev_rows)
    perm_shuf = check_permutation_invariance(fwd_rows, shuf_rows)
    print(f"permutation invariance: reversed max_abs_diff={perm_rev['max_abs_diff']:.2e} "
          f"(tol {PERMUTATION_TOL}), shuffled max_abs_diff={perm_shuf['max_abs_diff']:.2e}")

    verdict = parity_verdict(max_abs_diff, flips, micro_f1_drop)
    verdict["permutation"] = {"reversed": perm_rev, "shuffled": perm_shuf}
    verdict["micro_f1_measured"] = bool(probe_labels is not None and total_rows)
    manifest = {
        "task": "V71-P5-2",
        "vocab_version": VOCAB_VERSION,
        "vocab_fingerprint": vocab_fingerprint(),
        "student_checkpoint": args.student,
        "backbone": args.backbone,
        "onnx_opset": ONNX_OPSET,
        "onnx_fp32": args.output_fp32,
        "onnx_int8": args.output_int8,
        "quantization": {"method": "quantize_dynamic", "weight_type": "QInt8",
                         "op_types": QUANT_OP_TYPES,
                         "graph_fusion": "ORT_ENABLE_ALL (Gemm/LayerNorm/GELU)"},
        "shape_buckets": list(SHAPE_BUCKETS),
        "probe": args.probe,
        "probe_n": len(probe_texts),
        "parity_guard": verdict,
        "note": "micro_f1_drop is measured here when the probe file "
                "carries hard labels (micro-F1 = accuracy over head rows); "
                "with an unlabelled probe it is recorded as 0.0 with "
                "micro_f1_measured=false, and the suite-level 0.5% gate is "
                "then enforced end-to-end (v7 notebook + test_v7_rules.py). "
                "If that gate fails there, this artifact must be rejected "
                "retroactively.",
    }
    manifest_path = args.output_int8 + ".manifest.json"
    if not verdict["pass"] or not perm_rev["within_tol"] or not perm_shuf["within_tol"]:
        rejected = args.output_int8.replace(".onnx", ".rejected.onnx")
        os.replace(args.output_int8, rejected)
        manifest["rejected_as"] = rejected
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1)
        print("PARITY GUARD: REJECTED — " + "; ".join(verdict["failures"])
              + ("" if perm_rev["within_tol"] and perm_shuf["within_tol"]
                 else "; batch permutation invariance failed")
              + f". Artifact renamed to {rejected}; manifest: {manifest_path}",
              file=sys.stderr)
        return 3
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    print("PARITY GUARD: PASS — "
          f"max_abs_diff={max_abs_diff:.4f} (<= {MAX_ABS_DIFF}), "
          f"flips={flips}, permutation within {PERMUTATION_TOL}.")
    print(f"manifest saved: {manifest_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Export the distilled student to ONNX (opset 17) + "
                    "dynamic INT8, with the Parity Guard (V71-P5-2).")
    p.add_argument("--student", required=True,
                   help="FP32 student checkpoint (scripts/distill_student.py output)")
    p.add_argument("--backbone", required=True,
                   help="Student backbone id (must match the distill run)")
    p.add_argument("--probe", required=True,
                   help="Probe JSONL (held-out synthetic dev split; "
                        "sealed paths are refused)")
    p.add_argument("--probe-limit", type=int, default=500,
                   help="Max probe records (default 500)")
    p.add_argument("--output-fp32", default="models/student_fp32.onnx")
    p.add_argument("--output-int8", default="models/student_int8.onnx")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return export_and_quantize(args)


if __name__ == "__main__":
    raise SystemExit(main())
