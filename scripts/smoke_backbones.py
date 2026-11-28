"""Phase A gate A4 — 3-backbone smoke benchmark (code for Colab GPU).

Compares, with NO predetermined winner (GPT-RERUN §7, binding):

  - jhu-clsp/mmBERT-base          (MIT, 307M, 1,833 languages)
  - google/muril-base-cased       (Apache-2.0, Indian-language focus,
                                   transliteration-aware pretraining —
                                   a serious Kanglish challenger)
  - FacebookAI/xlm-roberta-base   (MIT)

Licences above are as stated in the GPT-RERUN consultation (§7, "verified
from published model cards"); this script re-verifies them at run time
via the Hugging Face Hub API when it is reachable and marks them
UNVERIFIED otherwise — do not train on a backbone whose licence was not
confirmed in the run log.

Part (a) — tokenizer fertility + truncation audit (needs transformers
only): for each backbone, tokenize the corpus stratified by language
(en / kn / kanglish) and report tokens-per-whitespace-word (median, p95),
length inflation vs English, truncation rate at max_seq_len 320, and
evidence retention (fraction of annotated spans fully inside the first
320 tokens). No claim about Kanglish fragmentation is made until these
measurements exist (GPT-RERUN: do not assume mmBERT fragments Kanglish
worse until tokenization establishes it; fewer tokens does not
automatically mean better semantics).

Part (b) — 1-fold smoke-F1 code path (needs torch + a GPU): train all
three backbones on the SAME grouped 2,000-example subset with identical
exposure, loss and partitions, and report per-language section-exact via
Graph v4. Grouping is by template-block signature (``meta.blocks``) —
the corpus carries no ``template_family_id`` (see A5 audit), so the fold
holds out whole block-signatures, not random rows. This is a smoke test
(20-minute compatibility check), NOT a reliable winner decision: prefer
the model with the highest worst-language exact match among comparable
candidates; if the difference is < ~3pp, repeat with more seeds/data.

This VM has NO transformers and NO torch, so part (a) cannot run here:
the script exits 2 with "code ready, run on Colab" and prints the plan.
Do NOT fake numbers.

Usage (Colab T4):

    python3 scripts/smoke_backbones.py --part a \\
        --train-file data/synthetic_v7_1/train.jsonl \\
        --val-file data/synthetic_v7_1/validation.jsonl \\
        --json-out /tmp/smoke_backbones_a.json
    python3 scripts/smoke_backbones.py --part b --n-train 2000 --epochs 1 \\
        --train-file data/synthetic_v7_1/train.jsonl \\
        --val-file data/synthetic_v7_1/validation.jsonl \\
        --json-out /tmp/smoke_backbones_b.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from laya_v7_classifier import load_corpus_jsonl  # noqa: E402

BACKBONES = [
    ("jhu-clsp/mmBERT-base", "MIT",
     "primary candidate (307M, 1,833 languages)"),
    ("google/muril-base-cased", "Apache-2.0",
     "Indian-language focus, transliteration-aware — Kanglish challenger"),
    ("FacebookAI/xlm-roberta-base", "MIT",
     "multilingual baseline"),
]

MAX_SEQ_LEN = 320  # adopted (FALLBACK-2); supersedes the plan's 288.
SMOKE_N_TRAIN = 2000


def require_transformers():
    try:
        import transformers  # noqa: F401
        return True
    except ImportError:
        print("transformers is NOT installed on this VM.", file=sys.stderr)
        print("Part (a) cannot run here. Code ready — run on Colab "
              "(pip install transformers, then re-run this script).",
              file=sys.stderr)
        return False


def verify_licences() -> dict[str, str]:
    """Best-effort licence check via the HF Hub API (online only)."""
    expected = {name: lic for name, lic, _ in BACKBONES}
    out: dict[str, str] = {}
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        for name, lic, _ in BACKBONES:
            try:
                info = api.model_info(name)
                card = (info.cardData or {}).get("license") or "unknown"
                out[name] = (f"expected {lic}; hub reports {card}"
                             + (" — MATCH" if card.lower() == lic.lower()
                                else " — MISMATCH, do not train until resolved"))
            except Exception as exc:  # noqa: BLE001 - network/model errors
                out[name] = f"expected {lic}; hub lookup failed ({exc}) — UNVERIFIED"
    except ImportError:
        for name, lic, _ in BACKBONES:
            out[name] = (f"expected {lic} (GPT-RERUN §7); huggingface_hub "
                         "not installed — UNVERIFIED in this run")
    return out


def part_a_tokenizer_audit(train_file: str, val_file: str,
                           sample_per_lang: int = 500) -> dict:
    from transformers import AutoTokenizer  # noqa: PLC0415 - guarded path
    train, _ = load_corpus_jsonl(train_file)
    val, _ = load_corpus_jsonl(val_file)
    records = train + val
    by_lang: dict[str, list] = defaultdict(list)
    for r in records:
        by_lang[r["lang"]].append(r)
    report: dict = {"max_seq_len": MAX_SEQ_LEN, "backbones": {}}
    for name, lic, note in BACKBONES:
        tok = AutoTokenizer.from_pretrained(name)
        per_lang: dict = {}
        for lang, recs in sorted(by_lang.items()):
            sample = recs[:sample_per_lang]
            fertilities: list[float] = []
            trunc = 0
            spans_total = spans_kept = 0
            for r in sample:
                words = max(1, len(r["text"].split()))
                ids = tok(r["text"], add_special_tokens=True)["input_ids"]
                fertilities.append(len(ids) / words)
                if len(ids) > MAX_SEQ_LEN:
                    trunc += 1
                # Evidence retention: a span is kept iff every token
                # covering its character range lies inside the first
                # MAX_SEQ_LEN tokens.
                enc = tok(r["text"], add_special_tokens=True,
                          return_offsets_mapping=True)
                offsets = enc["offset_mapping"]
                for sp in r.get("spans") or []:
                    spans_total += 1
                    tok_idx = [i for i, (s, e) in enumerate(offsets)
                               if s <= sp["start"] < e or s < sp["end"] <= e]
                    if tok_idx and max(tok_idx) < MAX_SEQ_LEN:
                        spans_kept += 1
            fertilities.sort()
            p50 = statistics.median(fertilities)
            p95 = fertilities[int(0.95 * (len(fertilities) - 1))]
            per_lang[lang] = {
                "n": len(sample),
                "tokens_per_word_median": round(p50, 3),
                "tokens_per_word_p95": round(p95, 3),
                "truncation_rate_at_320": round(trunc / len(sample), 4),
                "spans_total": spans_total,
                "spans_kept_within_320": spans_kept,
                "span_retention": round(spans_kept / spans_total, 4)
                if spans_total else None,
            }
        en_med = per_lang.get("en", {}).get("tokens_per_word_median") or 0
        for lang in per_lang:
            med = per_lang[lang]["tokens_per_word_median"]
            per_lang[lang]["length_inflation_vs_en"] = (
                round(med / en_med, 3) if en_med else None)
        report["backbones"][name] = {"licence_expected": lic, "note": note,
                                     "per_language": per_lang}
    return report


def part_b_smoke_f1(train_file: str, val_file: str, n_train: int,
                    epochs: int, work_dir: str = "/tmp/smoke_backbones") -> dict:
    """1-fold smoke-F1 on a grouped 2k subset. Torch + GPU required.

    Real code path (Colab): builds grouped subset files (whole
    template-block signatures held out — see A5 audit, the corpus has no
    template_family_id), then drives the Lane 04 train script once per
    backbone with identical exposure, and scores per-language section-exact
    via the Lane 07 harness. Pre-flight: the train script must accept all
    three backbones in its --backbone choices (Lane B owns that change —
    today it accepts only ModernBERT / DeBERTa / PIXMELT). If a backbone
    is not accepted, that backbone is reported NOT-RUN with the exact
    missing change, and no number is faked for it.
    """
    try:
        import torch  # noqa: F401
    except ImportError as exc:
        print(f"ERROR: part (b) needs torch ({exc}). Do not run here; "
              "run on Colab T4.", file=sys.stderr)
        return {"error": "torch not installed"}
    import subprocess
    import importlib.util

    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    train, _ = load_corpus_jsonl(train_file)
    groups: dict[tuple, list] = defaultdict(list)
    for r in train:
        groups[tuple(sorted((r.get("meta") or {}).get("blocks", [])))].append(r)
    sigs = sorted(groups, key=lambda s: -len(groups[s]))
    dev_sigs = set(sigs[::7])  # ~1/7 of signatures held out
    smoke_train = [r for s in sigs if s not in dev_sigs
                   for r in groups[s]][:n_train]
    smoke_dev = [r for s in dev_sigs for r in groups[s]]

    def _dump(recs: list, path: Path) -> None:
        with path.open("w", encoding="utf-8") as fh:
            for r in recs:
                fh.write(json.dumps({
                    "id": r["id"], "lang": r["lang"], "text": r["text"],
                    "issues": r["issues"], "facts": r["facts"],
                    "enums": r["enums"], "spans": r["spans"],
                    "meta": r.get("meta") or {},
                }, ensure_ascii=False) + "\n")

    train_path = work / "smoke_train.jsonl"
    dev_path = work / "smoke_dev.jsonl"
    _dump(smoke_train, train_path)
    _dump(smoke_dev, dev_path)

    # Pre-flight: which backbones does the train script accept?
    # Authoritative check: parse_args() with the backbone — argparse
    # exits 2 on an invalid --backbone choice.
    train_script = REPO_ROOT / "scripts" / "train_v71_classifier.py"
    spec = importlib.util.spec_from_file_location(
        "train_v71_for_smoke", train_script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    accepted: dict[str, bool] = {}
    for bb, _, _ in BACKBONES:
        try:
            parsed = mod.parse_args(["--backbone", bb])
            accepted[bb] = (parsed.backbone == bb)
        except SystemExit:
            accepted[bb] = False

    results: dict = {
        "n_smoke_train": len(smoke_train),
        "n_smoke_dev": len(smoke_dev),
        "n_dev_signatures_held_out": len(dev_sigs),
        "subset_files": [str(train_path), str(dev_path)],
        "backbones": {},
    }
    # Load the harness for per-language section-exact scoring.
    spec_h = importlib.util.spec_from_file_location(
        "recall_eval_smoke", REPO_ROOT / "tests" / "recall_eval.py")
    harness = importlib.util.module_from_spec(spec_h)
    spec_h.loader.exec_module(harness)
    from laya_v7_classifier import evaluate_checkpoint  # noqa: PLC0415

    for bb, lic, _note in BACKBONES:
        if not accepted.get(bb):
            results["backbones"][bb] = {
                "status": "NOT-RUN — train script --backbone choices do "
                          "not include this backbone yet (Lane B: add it "
                          "to scripts/train_v71_classifier.py parse_args "
                          "and to BACKBONES in src/laya_v7_classifier.py). "
                          "No number faked.",
            }
            continue
        out_dir = work / ("model_" + bb.replace("/", "_"))
        cmd = [sys.executable, str(train_script),
               "--train-file", str(train_path),
               "--val-file", str(dev_path),
               "--backbone", bb,
               "--epochs", str(epochs), "--batch-size", "4",
               "--grad-accum", "2", "--lr", "2e-5",
               "--max-seq-len", str(MAX_SEQ_LEN), "--max-clauses", "8",
               "--output-dir", str(out_dir), "--device", "cuda", "--fp16",
               "--grad-checkpoint", "--seed", "42"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            results["backbones"][bb] = {
                "status": f"NOT-RUN — training failed (exit "
                          f"{proc.returncode}): {proc.stderr[-800:]}",
            }
            continue
        ckpt = out_dir / "best" / "model.pt"
        metrics, gold, preds = evaluate_checkpoint(
            str(ckpt), str(dev_path), device="cuda", return_predictions=True)
        sections = [harness.predict_sections_from_stage1(
            p["issues"], p["facts"], p["enums"]) for p in preds]
        sec = harness.score_predictions(gold, sections)
        sec.pop("rows", None)
        by_lang: dict[str, dict] = {}
        for lang in ("en", "kn", "kn_roman"):
            idx = [i for i, g in enumerate(gold) if g["lang"] == lang]
            if not idx:
                continue
            ex = sum(1 for i in idx
                     if sections[i] == harness.expected_sections(gold[i]))
            by_lang[lang] = {"n": len(idx), "exact": ex,
                             "exact_rate": round(ex / len(idx), 4)}
        worst = min((v["exact_rate"] for v in by_lang.values()), default=None)
        results["backbones"][bb] = {
            "status": "RUN",
            "section_exact_overall": f"{sec['exact_count']}/{sec['n']}",
            "section_exact_rate": sec["exact_rate"],
            "per_language": by_lang,
            "worst_language_exact_rate": worst,
            "label_metrics": metrics,
        }
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="3-backbone smoke benchmark (A4).")
    ap.add_argument("--part", choices=["a", "b", "both"], default="both")
    ap.add_argument("--train-file", default="data/synthetic_v7_1/train.jsonl")
    ap.add_argument("--val-file", default="data/synthetic_v7_1/validation.jsonl")
    ap.add_argument("--n-train", type=int, default=SMOKE_N_TRAIN)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args(argv)

    print("3-backbone smoke benchmark (A4) — no predetermined winner.")
    print("Backbones:")
    for name, lic, note in BACKBONES:
        print(f"  {name} [{lic}] — {note}")
    print("Licence verification:")
    for name, status in verify_licences().items():
        print(f"  {name}: {status}")
    print()

    if not require_transformers():
        print("CODE READY, RUN ON COLAB: part (a) needs transformers, "
              "part (b) needs torch + GPU. No numbers are reported from "
              "this VM (exit 2).")
        return 2

    report: dict = {"backbones": [b[0] for b in BACKBONES]}
    if args.part in ("a", "both"):
        report["part_a_tokenizer_audit"] = part_a_tokenizer_audit(
            args.train_file, args.val_file)
        print(json.dumps(report["part_a_tokenizer_audit"], indent=2,
                         ensure_ascii=False))
    if args.part in ("b", "both"):
        report["part_b_smoke_f1"] = part_b_smoke_f1(
            args.train_file, args.val_file, args.n_train, args.epochs)
        print(json.dumps(report["part_b_smoke_f1"], indent=2,
                         ensure_ascii=False))
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
