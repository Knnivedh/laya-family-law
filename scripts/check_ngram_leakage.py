#!/usr/bin/env python3
"""LAYA v7.1 V71-P1-2 — n-gram / cosine leakage gate for the synthetic corpus.

Enforces, against every readable (non-sealed) reference bank:
  * 0 shared word 8-grams between the synthetic corpus and the reference, and
  * max normalised TF cosine overlap < 0.90 between any synthetic example and
    any reference question.

Readable references (all non-sealed, safe to open):
  * ground-truth/ground-truth-v2-hma27-A.json        (16-Q)
  * test-bank/brutal-bank-v1-frozen.json             (Brutal-230)
  * tests/fixtures/laya_maintenance_*.json           (162 maintenance items)

Sealed references (test-bank/sealed/*.json) are NEVER opened by this script
in gate mode. They are checked only through a blind hash index:
  * --sealed-index <path>  reads a JSON file of the form
    {"version": 1, "n": 8, "hashes": ["<sha256 hex>", ...]} holding the
    SHA-256 of each normalised word 8-gram in the sealed banks. The gate
    hashes the corpus 8-grams the same way and reports the intersection
    count. No sealed wording is loaded, printed or stored.
  * --build-hash-index <sealed.json...> --hash-index-out <path> builds such
    an index. TRUSTED RUN ONLY: it reads sealed files, so it must be run by
    a trusted operator (coordinator / rater), never by an ordinary lane
    agent, and it writes hashes only — it never prints question text.
  * If --sealed-index is given but the file does not exist, the sealed
    check is reported QUEUED (exit code 2) with the exact trusted command;
    the readable-reference checks still run and decide exit 0/1 on their own.

Overlap reporting never prints reference text: overlapping 8-grams are
reported as SHA-256 hashes plus the synthetic record ids involved, and
cosine hits are reported as (synthetic id, reference id, cosine) triples.
--show-synthetic-context additionally prints the SYNTHETIC record text only
(our own text, safe to print) for the top cosine hits, to help fix templates.

Exit codes: 0 = gate PASS (0 eight-grams, max cosine < threshold, sealed
hash overlap 0 when an index was supplied); 1 = gate FAIL; 2 = sealed-index
run QUEUED (index file missing) — readable checks still reported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

TOKEN_RE = re.compile(r"[^\s.,;:!?\"'“”‘’()\[\]{}]+", re.UNICODE)
# NOTE: do NOT tokenise with \w — Python's \w excludes combining marks, so
# it shreds Kannada words (e.g. vowel signs) into single characters and
# makes "8-grams" meaningless for KN. Splitting on whitespace/punctuation
# keeps each Kannada word whole.
DEFAULT_N = 8
DEFAULT_COSINE_THRESHOLD = 0.90

DEFAULT_CORPUS = ["data/synthetic_v7_1/train.jsonl",
                  "data/synthetic_v7_1/validation.jsonl"]
DEFAULT_REFS = ["ground-truth/ground-truth-v2-hma27-A.json",
                "test-bank/brutal-bank-v1-frozen.json",
                "tests/fixtures/laya_maintenance_development.json",
                "tests/fixtures/laya_maintenance_verification.json",
                "tests/fixtures/laya_maintenance_challenge.json",
                "tests/fixtures/laya_maintenance_final_check.json"]


def tokenize(text):
    return TOKEN_RE.findall(text.lower())


def ngrams(tokens, n):
    return {tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def ngram_hash(ng):
    return hashlib.sha256(" ".join(ng).encode("utf-8")).hexdigest()


def load_corpus(paths):
    """Return list of (id, text)."""
    out = []
    for p in paths:
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            out.append((rec.get("id", "?"), rec["text"]))
    return out


def extract_questions(obj):
    """Recursively collect every string value under a 'question' key."""
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "question" and isinstance(v, str):
                found.append(v)
            else:
                found.extend(extract_questions(v))
    elif isinstance(obj, list):
        for v in obj:
            found.extend(extract_questions(v))
    return found


def load_refs(paths):
    """Return list of (ref_file, ref_id, text). ref_id from 'id' if present."""
    out = []
    for p in paths:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        questions = extract_questions(data)
        ids = []
        if isinstance(data, dict) and isinstance(data.get("questions"), list):
            ids = [str(q.get("id", "?")) for q in data["questions"]]
        elif isinstance(data, list):
            ids = [str(q.get("id", "?")) if isinstance(q, dict) else "?"
                   for q in data]
        for i, q in enumerate(questions):
            rid = ids[i] if i < len(ids) else f"q{i}"
            out.append((p, rid, q))
    return out


def tf_cosine(c1, c2, norm1, norm2):
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    dot = sum(c * c2.get(w, 0) for w, c in c1.items())
    return dot / (norm1 * norm2)


def check_readable(corpus, refs, n, cosine_threshold, show_context):
    """Return (report dict, passed bool)."""
    corpus_grams = {}
    corpus_tf = {}
    for cid, text in corpus:
        toks = tokenize(text)
        corpus_grams[cid] = ngrams(toks, n)
        tf = Counter(toks)
        corpus_tf[cid] = (tf, math.sqrt(sum(v * v for v in tf.values())))
    # Inverted index: word -> corpus ids, for cheap cosine candidates.
    word_to_ids = defaultdict(set)
    for cid, text in corpus:
        for w in set(tokenize(text)):
            word_to_ids[w].add(cid)

    ref_grams = {}
    ref_tf = {}
    for rfile, rid, text in refs:
        toks = tokenize(text)
        ref_grams[(rfile, rid)] = ngrams(toks, n)
        tf = Counter(toks)
        ref_tf[(rfile, rid)] = (tf, math.sqrt(sum(v * v for v in tf.values())))

    per_ref = {}
    all_overlap_hashes = set()
    top_cosine = []  # (cosine, syn_id, ref_file, ref_id)
    for (rfile, rid), grams in ref_grams.items():
        overlap_ids = set()
        overlap_hashes = set()
        for cid, cgrams in corpus_grams.items():
            shared = grams & cgrams
            if shared:
                overlap_ids.add(cid)
                overlap_hashes.update(ngram_hash(g) for g in shared)
        all_overlap_hashes.update(overlap_hashes)
        # Cosine vs candidate synthetics sharing >= 1 word.
        rtf, rnorm = ref_tf[(rfile, rid)]
        cand = set()
        for w in rtf:
            cand.update(word_to_ids.get(w, ()))
        best = (0.0, None)
        for cid in cand:
            ctf, cnorm = corpus_tf[cid]
            cos = tf_cosine(rtf, ctf, rnorm, cnorm)
            if cos > best[0]:
                best = (cos, cid)
        if best[1] is not None:
            top_cosine.append((round(best[0], 4), best[1], rfile, rid))
        pr = per_ref.setdefault(
            rfile, {"ref_questions": 0, "overlap_8grams": 0,
                    "synthetic_ids_with_overlap": [],
                    "max_cosine": 0.0, "overlap_8gram_hashes": set()})
        pr["ref_questions"] += 1
        pr["overlap_8grams"] = len(pr["overlap_8gram_hashes"]
                                   | overlap_hashes)
        pr["overlap_8gram_hashes"] = (pr["overlap_8gram_hashes"]
                                      | overlap_hashes)
        pr["synthetic_ids_with_overlap"] = sorted(
            set(pr["synthetic_ids_with_overlap"]) | overlap_ids)[:5]
        pr["max_cosine"] = round(max(pr["max_cosine"], best[0]), 4)
    for pr in per_ref.values():
        pr["overlap_8gram_hashes"] = sorted(pr["overlap_8gram_hashes"])[:10]
    top_cosine.sort(reverse=True)
    max_cos = top_cosine[0][0] if top_cosine else 0.0
    total_overlap_grams = len(all_overlap_hashes)
    report = {
        "n": n,
        "cosine_threshold": cosine_threshold,
        "n_corpus": len(corpus),
        "n_ref_questions": len(refs),
        "total_overlap_8grams": total_overlap_grams,
        "max_cosine": max_cos,
        "top_cosine_hits": [
            {"cosine": c, "synthetic_id": s, "ref_file": f, "ref_id": r}
            for c, s, f, r in top_cosine[:5]],
        "per_ref_file": per_ref,
    }
    if show_context:
        by_id = dict(corpus)
        report["top_hit_synthetic_texts"] = [
            {"synthetic_id": s, "cosine": c, "text": by_id.get(s, "")}
            for c, s, f, r in top_cosine[:5]]
    passed = total_overlap_grams == 0 and max_cos < cosine_threshold
    return report, passed


def build_hash_index(sealed_paths, n, out_path):
    hashes = set()
    n_q = 0
    for p in sealed_paths:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        for q in extract_questions(data):
            n_q += 1
            hashes.update(ngram_hash(g) for g in ngrams(tokenize(q), n))
    payload = {"version": 1, "n": n, "n_questions": n_q,
               "n_hashes": len(hashes), "hashes": sorted(hashes)}
    Path(out_path).write_text(json.dumps(payload), encoding="utf-8")
    print(f"wrote {len(hashes)} blind 8-gram hashes from {n_q} sealed "
          f"questions -> {out_path} (hashes only; no sealed text stored)")
    return 0


def check_sealed_index(corpus, index_path, n):
    payload = json.loads(Path(index_path).read_text(encoding="utf-8"))
    if payload.get("n", n) != n:
        raise ValueError(f"sealed index n={payload.get('n')} != gate n={n}")
    sealed = set(payload["hashes"])
    overlap = Counter()
    for cid, text in corpus:
        for g in ngrams(tokenize(text), n):
            if ngram_hash(g) in sealed:
                overlap[cid] += 1
    return {"index_file": str(index_path),
            "index_hashes": len(sealed),
            "overlap_8grams": sum(overlap.values()),
            "synthetic_ids_with_overlap": sorted(overlap)[:5]}, \
        sum(overlap.values()) == 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", nargs="+", default=DEFAULT_CORPUS)
    ap.add_argument("--refs", nargs="+", default=DEFAULT_REFS)
    ap.add_argument("--n", type=int, default=DEFAULT_N)
    ap.add_argument("--cosine-threshold", type=float,
                    default=DEFAULT_COSINE_THRESHOLD)
    ap.add_argument("--sealed-index", default=None,
                    help="path to a precomputed blind-hash index JSON")
    ap.add_argument("--build-hash-index", nargs="+", default=None,
                    help="TRUSTED RUN ONLY: sealed JSON files to hash")
    ap.add_argument("--hash-index-out", default=None)
    ap.add_argument("--out", default=None, help="write JSON report here")
    ap.add_argument("--show-synthetic-context", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="plan §7 interface (python -m scripts.check_ngram_leakage "
                         "--strict). Accepted for CI compatibility: the default "
                         "gate already enforces the strict criteria (0 word "
                         "8-grams, cosine < 0.90), so --strict changes nothing; "
                         "it exists so ci_gate.py / laya-ci.yml can invoke the "
                         "plan-mandated command. Added by coordinator at Lane 02 "
                         "merge (PC-4).")
    args = ap.parse_args(argv)

    if args.build_hash_index:
        if not args.hash_index_out:
            ap.error("--build-hash-index needs --hash-index-out")
        return build_hash_index(args.build_hash_index, args.n,
                                args.hash_index_out)

    corpus = load_corpus(args.corpus)
    refs = load_refs(args.refs)
    report, passed = check_readable(corpus, refs, args.n,
                                    args.cosine_threshold,
                                    args.show_synthetic_context)
    report["sealed"] = None
    sealed_queued = False
    if args.sealed_index:
        idx = Path(args.sealed_index)
        if not idx.exists():
            sealed_queued = True
            report["sealed"] = {
                "status": "QUEUED",
                "reason": "hash index file does not exist; sealed files "
                          "were NOT opened",
                "trusted_command":
                    "python3 scripts/check_ngram_leakage.py "
                    "--build-hash-index test-bank/sealed/sealed-fresh-20.json "
                    "test-bank/sealed/sealed-kannada-8.json "
                    "--hash-index-out data/synthetic_v7_1/sealed-hash-index.json "
                    "&& python3 scripts/check_ngram_leakage.py "
                    "--sealed-index data/synthetic_v7_1/sealed-hash-index.json",
            }
            print("SEALED CHECK QUEUED: no hash index exists; sealed files "
                  "were not opened.")
            print("Trusted run: " + report["sealed"]["trusted_command"])
        else:
            sealed_report, sealed_ok = check_sealed_index(corpus, idx, args.n)
            sealed_report["status"] = "PASS" if sealed_ok else "FAIL"
            report["sealed"] = sealed_report
            passed = passed and sealed_ok

    report["verdict"] = "PASS" if passed else "FAIL"
    if sealed_queued:
        # Readable refs passed, but the sealed check has not run yet: do not
        # let the bare word PASS hide that.
        report["verdict"] = ("PASS-READABLE-ONLY (sealed QUEUED)"
                             if passed else "FAIL")
    if args.out:
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False,
                                             indent=1), encoding="utf-8")
    print(f"corpus={report['n_corpus']} refs={report['n_ref_questions']} "
          f"overlap_{args.n}grams={report['total_overlap_8grams']} "
          f"max_cosine={report['max_cosine']} "
          f"(threshold {args.cosine_threshold}) -> {report['verdict']}")
    for f, pr in report["per_ref_file"].items():
        print(f"  {f}: overlap={pr['overlap_8grams']} "
              f"max_cosine={pr['max_cosine']} "
              f"synthetic_ids={pr['synthetic_ids_with_overlap']}")
    if report["top_cosine_hits"]:
        print("  top cosine hits:", report["top_cosine_hits"][:3])
    if sealed_queued:
        return 2
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
