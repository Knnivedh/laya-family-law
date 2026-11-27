# Kaanoon Eval Set + Study Sample (LANE 11, LAYA v7.1 recall swarm)

Public source: https://www.kaanoon.com/ — "Legal answers online from lawyers -
Indian Kaanoon". Collected 2026-11-27 via public web search + page-text fetch
(no sign-in, no paywall, no live browser). **Question text only.** Lawyers'
answers were never copied, never cited as authority, and appear nowhere in
this directory.

## Files

| File | Contents | Contract |
|---|---|---|
| `heldout.jsonl` | 28 eval records `{id, source_url, category, lang, text, issues, facts, enums, expected_sections, annotation_notes}` | R6 — EVALUATION ONLY. Never training / templates / anchors / tuning. Only Lane 07 scores it (`python3 tests/recall_eval.py --suite kaanoon`). |
| `study_sample.jsonl` | 16 study records `{id, source_url, category, text, note}` | R7 — pattern extraction only. Feeds `docs/kaanoon_phrasing_patterns.md` (Lanes 02/03/08). Disjoint from eval (verified below). Study texts are search-result excerpts of the question portion; `[...]` marks snippet truncation. |
| `build_heldout.py` | The single source of both JSONL files + machine validation of every `expected_sections` list against the live Stage-2 code. Re-run: `python3 data/kaanoon_eval/build_heldout.py` | — |
| `check_disjoint.py` | 8-gram disjointness + cosine checks (R6/R7). Re-run: `python3 data/kaanoon_eval/check_disjoint.py` | — |
| `leakage_report.json` | Exact output of the last `check_disjoint.py` run | — |

## Sample

44 questions total. Eval (28): custody 5, maintenance 5, divorce 5, stridhan 2,
eviction 3, restitution 4, joint_property 2, violence 2. Study (16): custody 2,
maintenance 3, divorce 1, stridhan 2, eviction 2, restitution 1,
joint_property 1, violence 3, other (dowry) 1.

## Annotation method (eval set)

1. Each question was read in full and hand-annotated with the 11 issues
   (intent: requested / incidental / denied / uncertain) and 28 facts (state:
   supported / denied / unknown / conflicting) of
   `data/synthetic_v7_1/schema.json`, plus `enums` (`claimant_sex` M/F/U,
   `claimant_role` spouse/parent/child/other). Every record carries all 11
   issues and all 28 facts (defaults: uncertain / unknown).
2. `expected_sections` was derived deterministically from the Stage-2 rules in
   `src/laya_v7_graph.py` (`evaluate_stage2_v7`, `custody_vocab="v3_bundled"`,
   i.e. custody companions `hmga-1956-s6` + `welfare-principle` appended), in
   Stage-2 emission order (maintenance → matrimonial → custody → property →
   PWDVA; companions last).
3. Machine check: `build_heldout.py` re-runs `evaluate_stage2_v7` on the
   annotated issues/facts (with the pipeline-equivalence mapping of the
   schema enum to the graph's `claimant_sex` values male/female/unknown, and
   denied-intent issues as `negated_issues`) and fails loudly on any mismatch.
   Last run: `VALIDATION PASSED: all expected_sections match live
   evaluate_stage2_v7 (v3_bundled) exactly, in order.`
4. Honest empties: 7 of the 28 eval items have `expected_sections == []`
   (E11 prenup validity, E16 judicial separation with no graph route, E19
   husband asking to evict his wife, E21 landlord eviction suit
   out-of-scope, E25 wife resisting a restitution complaint, E27 prospective
   purchase planning, E10 male child-only claim with unverified minority —
   see notes). Each carries an `annotation_notes` entry saying why, instead
   of a forced section. Where the graph's behaviour itself looks like a gap
   (E10, E16, E19, E26 hma-27 gated by D2), the note says so for Lane 08/09.
5. Text handling: wording is verbatim from the public pages; only whitespace
   was normalised to single spaces. One record (E14) is Hinglish (Roman Hindi
   + English); the schema has no hi_roman label, so `lang` is recorded as
   `en` and flagged in its note. Third-party askers are annotated from the
   claimant's perspective (e.g. E18 claimant is Sindhu, not the friend who
   posted; E23 claimant is the sister).

## Leakage / disjointness — exact outputs

Run: `python3 data/kaanoon_eval/check_disjoint.py --out
data/kaanoon_eval/leakage_report.json` (2026-11-27):

```
eval=28 study=16 train=7500 validation=500
A eval vs train+val: shared_8grams=0
B eval vs study: shared_8grams=0 shared_questions=0 shared_ids=0
C study vs train+val (info only): shared_8grams=18
D max cosine eval vs train+val: (0.6614, 'KAN-E17', 'SYN-TR-7085') (threshold 0.9)
D max cosine eval vs study: (0.6454, 'KAN-E27', 'KAN-S05')
-> PASS
```

Notes on the numbers:
- The training file on disk currently holds **7,500** records (not the 4,500
  in `data/synthetic_v7_1/manifest.json` — Lane 02 has expanded it in the
  working copy). The gate ran against the actual files (7,500 train + 500
  validation).
- The FIRST check run FAILED check A (18 shared 8-grams, all from one item,
  then-KAN-E04): the two generic 8-grams "i want to live separately from my
  husband" and "want to live separately from my husband with", shared with 9
  train records. That item was REMOVED from eval and moved to the study
  sample as KAN-S16 (its overlap is why check C shows 18 — info only, study
  is never training data). After the move, check A is 0 and the run passes.
- The official gate script (`scripts/check_ngram_leakage.py`) was not used
  for this check because its `--refs` loader expects JSON files with
  `question` keys and cannot read the JSONL training corpus; `check_disjoint.py`
  reuses its `tokenize`/`ngrams` functions and the same 8-gram / 0.90-cosine
  thresholds, so the check is equivalent.

## What is still unverified

- Lane 09 spot-check of the annotations (queued; Lane 09 owns verification).
- The Kaanoon baseline number itself: only Lane 07 may score the held-out
  set (`--suite kaanoon`). Lane 11 did NOT run the harness on it and reports
  no score.
- Two pages fetched on 2026-11-27 had no question text at all (answer-only
  pages: `497240/6-month-waiver-demand-draft`,
  `497670/property-rights-in-a-joint-ownership-property-after-husband-wife-separation`)
  and were excluded, not reconstructed.
- Study-sample texts are excerpts (search snippets), not full page fetches,
  for 13 of 16 items; the patterns doc uses only short fragments from them.
