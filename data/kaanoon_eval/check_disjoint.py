#!/usr/bin/env python3
"""LANE 11 — 8-gram disjointness + cosine checks for the Kaanoon sets (R6/R7).

Checks (word 8-grams, same tokeniser as scripts/check_ngram_leakage.py):
  A. heldout (eval) vs train + validation   — must be 0 shared 8-grams (R6 gate).
  B. heldout (eval) vs study sample        — must be 0 shared 8-grams, no shared
                                             question (R7 split contract).
  C. study sample vs train + validation    — informational only (study is never
                                             training data; patterns only).
  D. Max TF-cosine of any eval item vs any train/validation item (< 0.90 gate,
     same threshold as the leakage gate).

Overlap reporting prints 8-gram SHA-256 hashes + record ids only — never the
other side's text. Exit 0 iff A, B and D all pass.

Usage: python3 data/kaanoon_eval/check_disjoint.py [--out FILE]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from check_ngram_leakage import tokenize, ngrams, ngram_hash  # noqa: E402

N = 8
COSINE_THRESHOLD = 0.90


def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(
        encoding="utf-8").splitlines() if line.strip()]


def grams_by_id(records):
    out = {}
    for rec in records:
        out[rec["id"]] = ngrams(tokenize(rec["text"]), N)
    return out


def shared(a, b):
    """Return {a_id: [(b_id, {hashes})]} for pairs sharing >= 1 8-gram."""
    hits = {}
    for aid, ag in a.items():
        for bid, bg in b.items():
            common = ag & bg
            if common:
                hits.setdefault(aid, []).append(
                    (bid, sorted(ngram_hash(g) for g in common)))
    return hits


def max_cosine(a_recs, b_recs):
    """Max TF-cosine between any a-record and any b-record (candidate-pruned)."""
    from collections import defaultdict
    b_tf, b_norm, word_to_b = {}, {}, defaultdict(set)
    for rec in b_recs:
        tf = Counter(tokenize(rec["text"]))
        b_tf[rec["id"]] = tf
        b_norm[rec["id"]] = math.sqrt(sum(v * v for v in tf.values()))
        for w in tf:
            word_to_b[w].add(rec["id"])
    best = (0.0, None, None)
    for rec in a_recs:
        tf = Counter(tokenize(rec["text"]))
        norm = math.sqrt(sum(v * v for v in tf.values()))
        if norm == 0.0:
            continue
        cand = set()
        for w in tf:
            cand.update(word_to_b.get(w, ()))
        for bid in cand:
            btf, bnorm = b_tf[bid], b_norm[bid]
            if bnorm == 0.0:
                continue
            dot = sum(c * btf.get(w, 0) for w, c in tf.items())
            cos = dot / (norm * bnorm)
            if cos > best[0]:
                best = (round(cos, 4), rec["id"], bid)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    eval_recs = load_jsonl(ROOT / "data/kaanoon_eval/heldout.jsonl")
    study_recs = load_jsonl(ROOT / "data/kaanoon_eval/study_sample.jsonl")
    train_recs = load_jsonl(ROOT / "data/synthetic_v7_1/train.jsonl")
    val_recs = load_jsonl(ROOT / "data/synthetic_v7_1/validation.jsonl")
    corpus = train_recs + val_recs

    eg, sg, cg = (grams_by_id(r) for r in (eval_recs, study_recs, corpus))
    overlap_a = shared(eg, cg)
    overlap_b = shared(eg, sg)
    overlap_c = shared(sg, cg)
    n_a = sum(len(h) for v in overlap_a.values() for h in v)
    n_b = sum(len(h) for v in overlap_b.values() for h in v)
    n_c = sum(len(h) for v in overlap_c.values() for h in v)
    cos_eval_train = max_cosine(eval_recs, corpus)
    cos_eval_study = max_cosine(eval_recs, study_recs)
    # No shared question text between the two Kaanoon splits.
    shared_text = sorted({r["text"] for r in eval_recs}
                         & {r["text"] for r in study_recs})
    shared_ids = sorted({r["id"] for r in eval_recs}
                        & {r["id"] for r in study_recs})

    report = {
        "n": N, "cosine_threshold": COSINE_THRESHOLD,
        "n_eval": len(eval_recs), "n_study": len(study_recs),
        "n_train": len(train_recs), "n_validation": len(val_recs),
        "A_eval_vs_train_val": {"shared_8grams": n_a,
                                "pairs": {k: v for k, v in overlap_a.items()}},
        "B_eval_vs_study": {"shared_8grams": n_b,
                            "shared_questions": shared_text,
                            "shared_ids": shared_ids,
                            "pairs": {k: v for k, v in overlap_b.items()}},
        "C_study_vs_train_val_info_only": {"shared_8grams": n_c,
                                           "pairs": {k: v for k, v in
                                                     overlap_c.items()}},
        "D_max_cosine_eval_vs_train_val": {"cosine": cos_eval_train[0],
                                           "eval_id": cos_eval_train[1],
                                           "train_id": cos_eval_train[2]},
        "D_max_cosine_eval_vs_study": {"cosine": cos_eval_study[0],
                                       "eval_id": cos_eval_study[1],
                                       "study_id": cos_eval_study[2]},
    }
    passed = (n_a == 0 and n_b == 0 and not shared_text and not shared_ids
              and cos_eval_train[0] < COSINE_THRESHOLD)
    report["verdict"] = "PASS" if passed else "FAIL"
    if args.out:
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False,
                                             indent=1), encoding="utf-8")
    print(f"eval={len(eval_recs)} study={len(study_recs)} "
          f"train={len(train_recs)} validation={len(val_recs)}")
    print(f"A eval vs train+val: shared_8grams={n_a}")
    print(f"B eval vs study: shared_8grams={n_b} "
          f"shared_questions={len(shared_text)} shared_ids={len(shared_ids)}")
    print(f"C study vs train+val (info only): shared_8grams={n_c}")
    print(f"D max cosine eval vs train+val: {cos_eval_train} "
          f"(threshold {COSINE_THRESHOLD})")
    print(f"D max cosine eval vs study: {cos_eval_study}")
    print(f"-> {report['verdict']}")
    if overlap_a:
        print("  A pairs:", overlap_a)
    if overlap_b:
        print("  B pairs:", overlap_b)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
