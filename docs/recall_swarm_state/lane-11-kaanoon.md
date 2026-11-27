# Lane 11 — Kaanoon Eval Set + Phrasing Patterns: DONE

**Status:** done — both halves of the user order (voice call 2026-11-27 ~19:23 IST,
blanket permission) delivered. Working copy only: `~/workspace/laya-v71-work`.
No other lane's files touched. No sealed files opened. No GPU/torch used.

## What changed (files owned by Lane 11 only)

- `data/kaanoon_eval/heldout.jsonl` — 28 held-out eval records (NEW).
- `data/kaanoon_eval/study_sample.jsonl` — 16 study records (NEW).
- `data/kaanoon_eval/build_heldout.py` — single source of both JSONL files +
  machine validation of every `expected_sections` list against live Stage-2
  code (NEW).
- `data/kaanoon_eval/check_disjoint.py` — 8-gram disjointness + cosine checks
  (NEW).
- `data/kaanoon_eval/leakage_report.json` — exact output of the last check run
  (NEW).
- `data/kaanoon_eval/README.md` — annotation method + file guide + exact gate
  outputs (NEW).
- `docs/kaanoon_phrasing_patterns.md` — phrasing patterns from the study
  sample only, for Lanes 02/03/08 (NEW).

## Sample size and per-category counts

- **Total sample: 44 real Kaanoon questions** (public pages, question text
  only — lawyers' answers never copied, never cited).
- **Eval set: 28** — custody 5, maintenance 5, divorce 5, stridhan 2,
  eviction 3, restitution 4, joint_property 2, violence 2.
- **Study sample: 16** — custody 2, maintenance 3, divorce 1, stridhan 2,
  eviction 2, restitution 1, joint_property 1, violence 3, other (dowry) 1.
- **Split sizes:** eval 28 / study 16 (task targets were ~25–35 eval and
  ~15–25 study; both met).

## Annotation method

- Each eval item read in full and hand-annotated with the 11 issues / 28
  facts of `data/synthetic_v7_1/schema.json` (all keys present in every
  record) + enums (claimant_sex M/F/U, claimant_role).
- `expected_sections` derived deterministically from Stage-2 rules in
  `src/laya_v7_graph.py` (`evaluate_stage2_v7`, `custody_vocab="v3_bundled"`),
  in Stage-2 emission order; then machine-checked by re-running that function
  on the annotations (pipeline-equivalence mapping of the schema sex enum to
  the graph's male/female/unknown; denied-intent issues as `negated_issues`).
- 7 of 28 eval items honestly have `expected_sections == []` (E10, E11, E16,
  E19, E21, E25, E27) — each with an `annotation_notes` entry saying why
  instead of a forced section. Graph-behaviour findings flagged in notes:
  E10 (male child-only claim with unverified minority yields nothing — the
  existing-order branch is shadowed), E16 (judicial separation has no graph
  route), E19 (male asker, residence relief is female-claimant only),
  E26 (hma-27 gated by D2 — divorce planned but not filed).
- Text is verbatim from the public pages (whitespace normalised only). E14 is
  Hinglish; schema has no hi_roman label, so `lang` is `en` + flagged note.

## Leakage-check exact outputs

`python3 data/kaanoon_eval/build_heldout.py`:
```
eval=28 study=16 total=44
VALIDATION PASSED: all expected_sections match live evaluate_stage2_v7 (v3_bundled) exactly, in order.
```

`python3 data/kaanoon_eval/check_disjoint.py --out data/kaanoon_eval/leakage_report.json`:
```
eval=28 study=16 train=7500 validation=500
A eval vs train+val: shared_8grams=0
B eval vs study: shared_8grams=0 shared_questions=0 shared_ids=0
C study vs train+val (info only): shared_8grams=18
D max cosine eval vs train+val: (0.6614, 'KAN-E17', 'SYN-TR-7085') (threshold 0.9)
D max cosine eval vs study: (0.6454, 'KAN-E27', 'KAN-S05')
-> PASS
```

- The first check run FAILED check A (18 shared 8-grams, all from one item,
  then-KAN-E04): the generic 8-grams "i want to live separately from my
  husband" / "want to live separately from my husband with", shared with 9
  train records. That item was removed from eval and moved to the study
  sample as KAN-S16 (hence check C = 18, info only). After the move, A = 0.
- The training file on disk holds **7,500** records, not the 4,500 in
  `data/synthetic_v7_1/manifest.json` (Lane 02 expansion in the working
  copy); the gate ran against the actual files.
- `scripts/check_ngram_leakage.py` itself was not run for this check: its
  `--refs` loader cannot read the JSONL training corpus. `check_disjoint.py`
  reuses its `tokenize`/`ngrams` and the same 8-gram / 0.90-cosine thresholds.
- Patterns doc verified separately: 0 shared 8-grams with the eval set; all
  16 study IDs cited, no eval item cited.

## Commands run

- `python3 data/kaanoon_eval/build_heldout.py` — exit 0 (see output above).
- `python3 data/kaanoon_eval/check_disjoint.py --out data/kaanoon_eval/leakage_report.json` — exit 0, verdict PASS.
- `python3 tests/test_graph_v4.py` — `GRAPH V4 + FROZEN SHA TEST PASS: 34 sections / 66 nodes / 99 edges, 0 dangling edges, 7/7 frozen hashes intact.`
- `python3 tests/test_prose_renderer_v2.py` — `PROSE VALIDATION PASS: 246 cases, Fp=0, quality_flags=0, 15/15 adversarial mutants caught, mean=0.0175ms, max=0.131ms`
- Source collection: 9 public web searches + 5 page-text fetches on
  kaanoon.com (question pages only). Two fetched pages had no question text
  (answer-only pages 497240, 497670) and were excluded, not reconstructed.

## Still unverified / open

- **Lane 09 spot-check of the annotations** — queued; Lane 09 owns
  verification (disjointness re-check + annotation spot-check).
- **Kaanoon baseline number** — only Lane 07 may score the held-out set
  (`python3 tests/recall_eval.py --suite kaanoon`). Lane 11 did NOT run the
  harness on it and reports no score.
- Study-sample texts are search-result excerpts (13 of 16), not full page
  fetches; the patterns doc uses only short fragments from them.
- No claim of ≥70% is made from this work; the number comes only from a real
  Lane 07 run.
