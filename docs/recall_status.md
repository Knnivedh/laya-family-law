# LAYA v7.1 — Recall Swarm Live Status Tracker

Owner: Lane 10 (docs/merge). Coordinator owns the merge/push; this file is the live tracker only.
Baseline: 10x swarm merged, HEAD `1cb0bff`, 22 commits ahead of `origin/main`. Working copy: `~/workspace/laya-v71-work`.
Last updated: 2026-11-27 ~20:20 IST (Lane 10, update 8 — ChatGPT consultation + both-model synthesis ADOPTED as working decision; nothing implemented yet).
Rule: every status line cites its source lane file or a command Lane 10 ran. Nothing here is invented.

## Target (user, voice call 2026-11-27 ~19:19 IST)

Unseen law-related questions must reach a MINIMUM of **70% exact**. Current measured:
Sealed Fresh-20 **7/20 (35%)**, Sealed Kannada-8 **4/8 (50%)**. Brutal-230 is 230/230
but that set is already known — the gap is unseen paraphrase recall.
**Do NOT claim 70% until a real run measures it.**
**Swarm outcome: 261/500 = 52.2% (frozen split) and Kaanoon 14/28 = 50.0% — the 70% target was
NOT reached.** The swarm closes with real, measured progress (+17.8pp on the frozen split from the
corrected 204/500 baseline), not with the target met.

## How to read this file

- `pending` = no lane status file has landed yet for that task.
- `done / blocked / needs-RTX / needs-human` are only used when a lane file or a run states them.
- Test pass lines are recorded ONLY for suites Lane 10 actually ran on this VM (see §2).
- The current held-out validation exact number (§3) comes ONLY from Lane 07's harness
  (`tests/recall_eval.py`) on the FROZEN validation split (`data/synthetic_v7_1/validation.jsonl`,
  sha256 `7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e`, 500 records).
  Every validation number must cite its split sha + code state — the corpus moved under the
  swarm, so unpinned numbers are meaningless.

## 1. Recall-swarm tasks — ALL 11 LANES DONE

| Task | Lane | Owner files | Status | Source |
|---|---|---|---|---|
| R-LANE01 — Diagnosis: per-cause failure breakdown | 01 | `docs/recall_swarm_state/lane-01-diagnosis.md` | **done — MERGED, commit `f92a9e5`** (coordinator commit) — analysis only; v1 numbers independently confirmed by Lane 09 (179/500 mapped oracle); pinned §2–§5 numbers UNVERIFIABLE-NOW (pinned file `11ffa32d…` gone from disk) | `git show --stat f92a9e5`; Lane 09 §1 |
| R-LANE02 — Paraphrase expansion: grow corpus, keep split clean | 02 | `scripts/build_synthetic_corpus.py`, `data/synthetic_v7_1/` | **done — MERGED, commit `de52ad4`** — corpus 5,000 → 8,000 (train 7,500 / validation 500, seed 7102); validation split FROZEN (sha `7640d067…`); leakage gate PASS (0 8-grams, max cosine 0.8269); new clusters hn_g/hn_h; Lane 05 kn_templates wired | `git show --stat de52ad4`; Lane 09 §2 (all counts re-verified) |
| R-LANE03 — Evidence anchors: harden regex anchors | 03 | `src/laya_v7_evidence.py` | **done — MERGED, commits `80e53d8`, `a0d58a0`, `58d950c`, `7839e86`, `c57919c`** — 5 rounds total; C4 anchor hardening (Kaanoon + audit paraphrase forms, in_scope OOS override, procedure issue) + C5 unit tests (17 new tests, full suite 66 OK); 16-Q 14/16 no regression; status file `lane-03-anchors.md` (151 lines) | `git show --stat 7839e86 / c57919c`; Lane 10 re-runs §2 |
| R-LANE04 — Classifier training prep: runnable training, RTX commands | 04 | `src/laya_v7_classifier.py`, `scripts/train_v71_classifier.py` | **done — MERGED, commits `6eb21d2`, `c596512`, `5498c91`** — PC-2 vocab pin, LoRA fix, RTX doc + status; all loader/count claims OLD-corpus-pinned (5,000) — 8,000 re-run still open (see §6) | `git log`; Lane 09 §4 |
| R-LANE05 — Kannada/Kanglish coverage | 05 | NEW files only: `scripts/kn_templates.py`, `src/laya_lang_normalizer.py`, `src/laya_lang_pack.py` | **done — MERGED, commits `a1f8c42`, `c19cecd`, `3d03399`** — 25 KN blocks (en 50 / kn 54 / kn_roman 71 variants); §4 AFTER numbers SUPERSEDED by Lane 02's 8,000 rebuild (not an error); P2.1 native-speaker audit still open | `git log`; Lane 09 §5 |
| R-LANE06 — Consultation brief (Gemini + ChatGPT) — PRIORITY, deliver first | 06 | `docs/recall_consultation_brief.md` | **done — MERGED, commit `f92a9e5`** (coordinator commit; brief corrected earlier by `0dbbad9`) — §3 corrected: 11 prompts not 9, cmax pooling exists, L417 custody block removed, anchor gating vars live in extractor.py not evidence.py | `git show --stat f92a9e5 / 0dbbad9`; Lane 09 §6 |
| R-LANE07 — Evaluation harness: held-out validation scoring | 07 | `tests/recall_eval.py` (new) | **done — MERGED, commits `aba4151`, `f9a4fdc`** — harness + `--suite kaanoon` (R6); baseline 173/500 on OLD split (superseded, see §3); self-test count claim "15" WRONG (12 on committed version, 21 current — self-test itself PASSES); sex-mapping bug found by Lane 09, fixed by coordinator `0dbbad9` | `git show --stat aba4151`; Lane 09 §7; `0dbbad9` diff |
| R-LANE08 — Stage 1 routes audit + fixes | 08 | `docs/recall_stage1_routes_audit.md`, `src/laya_v7_extractor.py`, `src/laya_v7_graph.py` (route fixes only) | **done — MERGED, commits `b9cd21c`, `4c464d6`, `69936e1`** — neural routes restit_p/dvcomp_p (prompts 9 → 11), post-order split facts, bnss-144-3/bnss-146; 16-Q 14/16 before and after; enumeration/probe claims UNVERIFIED (see §6) | `git log`; Lane 09 §8 |
| R-LANE09 — Independent verifier: blind-checks other lanes | 09 | `docs/recall_swarm_state/lane-09-verifier.md` | **done — MERGED, commit `8881a12`** — 623-line verification of lanes 01–08, 10, 11; found harness sex-mapping bug; corrected baselines 179/204; Kaanoon 12/28 measured; full verdicts in §9 | `git show --stat 8881a12`; `docs/recall_swarm_state/lane-09-verifier.md` |
| R-LANE10 — Docs/merge: tracker + merged view + push manifest | 10 | `docs/recall_status.md`, `docs/recall_swarm_state/merged.md`, `PUSH-MANIFEST-RECALL.md` | **done** — this file (update 6, FINAL) | Lane 10 |
| R-LANE11 — Kaanoon DO BOTH: held-out eval set + phrasing-patterns study | 11 | `data/kaanoon_eval/`, `docs/kaanoon_phrasing_patterns.md` | **done — MERGED, commit `410d65b`** — held-out eval 28 items + study sample 16 items + patterns doc (150 lines); verified in depth by Lane 09 (see §8 + §9) | `git show --stat 410d65b`; Lane 09 §10; Lane 10's own counts §8 |

**Swarm state: 11 of 11 lanes done. Swarm complete.** HEAD `f92a9e5` (26 commits on top of
recall baseline `1cb0bff`; recall delta 41 files).

### Coordinator commits recorded

| Commit | What it did |
|---|---|
| `0dbbad9` | Harness claimant_sex mapping fix (M/F/U → male/female/unknown; Lane 09 finding) + brief §3 correction (11 prompts, cmax exists, L417 block gone, anchors live in extractor.py) |
| `f92a9e5` | Shared state (`docs/recall_swarm_state.md`) + Lane 01 diagnosis + Lane 06 brief status committed (all lanes done; final frozen 261/500, Kaanoon 14/28) |

## 2. Test results actually run on this VM (Lane 10)

| Suite | Command | Result (exact pass line) |
|---|---|---|
| Graph v4 + frozen SHA (baseline, HEAD `1cb0bff`) | `python3 tests/test_graph_v4.py` | PASS: `GRAPH V4 + FROZEN SHA TEST PASS: 34 sections / 66 nodes / 99 edges, 0 dangling edges, 7/7 frozen hashes intact.` (exit 0) |
| Prose renderer v2 (baseline) | `python3 tests/test_prose_renderer_v2.py` | PASS: `PROSE VALIDATION PASS: 246 cases, Fp=0, quality_flags=0, 15/15 adversarial mutants caught, mean=0.0164ms, max=0.128ms` (exit 0) |
| Full unit suite (baseline) | `python3 -m unittest discover -s tests -p "test_*.py"` | `Ran 49 tests in 0.407s — OK` (exit 0) |
| Recall eval, FROZEN split, committed code (OFFICIAL, update 5) | `python3 tests/recall_eval.py --json-out /tmp/lane10_official_verify.json` (Lane 03 round-4 stashed) | **227/500 (45.4%)**, micro-P 0.8390 / micro-R 0.4328 / micro-F1 0.5710, TP/FP/FN 396/76/519, silent 223 — SUPERSEDED by final numbers (§3) |
| Recall eval `--suite kaanoon`, committed code (update 5) | `python3 tests/recall_eval.py --suite kaanoon` (same stash window) | **13/28 (46.4%)** — SUPERSEDED by final numbers (§3) |
| Recall eval, FROZEN split, FINAL (HEAD `f92a9e5`) | `python3 tests/recall_eval.py --json-out /tmp/lane10_final_verify.json` | **261/500 (52.2%)**, Wilson [0.4782, 0.5654], micro-P 0.8905 / micro-R 0.4623 / micro-F1 0.6086, TP/FP/FN 423/52/492, silent 212 — exact match to coordinator's final numbers (see §3) |
| Recall eval `--suite kaanoon`, FINAL (HEAD `f92a9e5`) | `python3 tests/recall_eval.py --suite kaanoon --json-out /tmp/lane10_final_kaanoon.json` | **14/28 (50.0%)**, Wilson [0.3263, 0.6737], micro-P 0.7500 / micro-R 0.6000 / micro-F1 0.6667, TP/FP/FN 27/9/18, silent 6 — exact match to coordinator's final numbers |
| Full unit suite, FINAL (HEAD `f92a9e5`) | `python3 -m unittest discover -s tests -p "test_*.py"` | `Ran 66 tests in 0.265s — OK` (exit 0) — includes Lane 03's 17 new C5 tests |
| 16-Q evidence-mode, FINAL (HEAD `f92a9e5`) | `python3 -m tests.v7_backtest --suite 16q --mode evidence --device cpu` | exact `14/16`, esc_bool `16/16`, esc_kinds_strict `10/16`, fp_prose 0, rating 7.6 — no regression |
| Graph v4 + frozen SHA, FINAL | `python3 tests/test_graph_v4.py` | PASS: 34 sections / 66 nodes / 99 edges, 0 dangling, 7/7 frozen hashes intact (exit 0) |
| Prose renderer v2, FINAL | `python3 tests/test_prose_renderer_v2.py` | PASS: 246 cases, Fp=0, quality_flags=0, 15/15 mutants, mean=0.0201ms, max=0.132ms (exit 0) |

Notes:
- No torch on this VM (`python3 -c "import torch"` → `ModuleNotFoundError`, traceback) — no neural
  run, training, or T4 run is possible here. Any RTX/T4 numbers must come from the user's RTX 5050
  machine or Colab.
- Guardrail check after every recall-lane change (per shared state): `python3 tests/test_graph_v4.py`
  and `python3 tests/test_prose_renderer_v2.py` must both PASS; revert if either fails. Both PASS
  at final HEAD.
- Correction to my own earlier record (Lane 09 §9.3, carried): Lane 07's status file is **165 lines**,
  not 150 as I wrote in update 4. The harness self-test count "15/15 PASS" is also wrong — 12 PASS
  lines on the committed version, 21 on the current version; the self-test itself PASSES (0 failures).

## 3. FINAL held-out validation exact numbers (official — replace update-5 numbers)

### FINAL — frozen split, HEAD `c57919c` (coordinator-measured; Lane 10 re-verified at HEAD `f92a9e5`)

**Frozen split: 261/500 (52.2%)** — validation sha256
`7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e`, n=500, manifest
`frozen_validation_sha256` + `frozen_validation_at` 2026-11-27T14:06:10.824537+00:00 (verified by
Lane 10: sha recomputed from disk matches manifest exactly; first 12 hex `7640d067c28a`).
Code state: HEAD `c57919c` (Lane 03 C5 tests), evidence mode, CPU. Lane 10's re-run at HEAD
`f92a9e5` (same code + coordinator commit `f92a9e5` on top, docs only) reproduced it exactly.

- Micro-P 0.8905 / micro-R 0.4623 / micro-F1 0.6086; TP/FP/FN 423/52/492; silent 212.
- Wilson 95% CI [0.4782, 0.5654].
- Per language: EN 209/235 (0.889), KN 30/153 (0.196), Kanglish 22/112 (0.196) — the Kannada/
  Kanglish gap is the dominant remaining weakness (EN is near-target; KN/Kanglish are ~0.20).
- **This REPLACES the update-5 official number 227/500 (45.4%)** — that was the pre-Lane-03-round-4
  number at committed code + fix; the +34 records are Lane 03's C4 anchor hardening.

### FINAL — Kaanoon real-phrasing eval, HEAD `c57919c`

**Kaanoon: 14/28 (50.0%)** — `data/kaanoon_eval/heldout.jsonl`, n=28. TP/FP/FN 27/9/18, silent 6;
Wilson [0.3263, 0.6737]; micro-P 0.7500 / micro-R 0.6000 / micro-F1 0.6667. On non-empty-expected
items: **10/21 = 47.6%**. Lane 10's re-run at HEAD `f92a9e5` reproduced it exactly.
**This REPLACES the update-5 official number 13/28 (46.4%).**
Labelled SEPARATELY from the synthetic validation number — never conflated, never presented
as a sealed number.

### FINAL — 16-Q regression set

**14/16 exact**, esc_bool 16/16, esc_kinds 10/16, fp_prose 0, rating 7.6 — re-run by Lane 10 at
final HEAD; no regression from any lane (same misses H6 pwdva-18, H14 hma-13 throughout).

### Progression table (all corrected, same frozen split — the only valid comparison series)

| Step | Frozen split exact | Code state / note |
|---|---|---|
| Harness as printed (pre-fix, frozen split) | 196/500 (39.2%) | Understated by the sex-mapping bug |
| Corrected (mapped re-score) | **204/500 (40.8%)** | Lane 09 corrected baseline; +8 records |
| Official, update 5 (committed code + fix `0dbbad9`) | **227/500 (45.4%)** | Lane 10 re-verified; pre-Lane-03-round-4 |
| PROVISIONAL, update 5 (round-4 uncommitted in tree) | 250/500 (50.0%) | Uncommitted anchors — provisional only |
| **FINAL, update 6 (HEAD `c57919c`)** | **261/500 (52.2%)** | Lane 03 C4+C5 committed; Lane 10 re-verified |

**Warning — do NOT compare across different files/code states:** 173/500 (old split, harness as
printed) vs 179/500 (old split, corrected) vs 196/204/227/261 (frozen split) are different
validation files AND different code. The valid progress read is the frozen-split series above:
204 → 227 → 261 (+57 records from the sex-mapping correction being applied and Lane 03's
anchor work). The old-split like-for-like code comparison is 179/500 (old code) vs 221/500
(current code on the old split, Lane 09 re-run) — +42 records from Lane 03 + Lane 08 changes.
- Target is ≥70% — the final frozen baseline is 52.2%, i.e. 17.8 points short. **Target NOT met.**
- These validation-split numbers are PROXIES for unseen-question recall (synthetic paraphrases
  from the same grammars as training), NOT the sealed number. The sealed Fresh-20 (7/20, 35%)
  and Kannada-8 (4/8, 50%) numbers are the user-facing sealed baselines; the sealed re-run happens
  ONLY on the RTX machine, never here — Lane 10 will never record a Fresh-20/Kannada-8 number
  from this VM.

### Brief §3 corrected (coordinator commit `0dbbad9`)

Lane 06's brief §3 had stale pre-10x claims (Lane 09 §6): 11 prompts not 9 (restit_p/dvcomp_p
added by Lane 08), cmax pooling exists (clause-max, not full-text-only), the L417 custody block
was removed by 10x Lane 01, and the anchor gating vars live in `src/laya_v7_extractor.py`
(lines ~388–459), not `src/laya_v7_evidence.py` (which holds `*_RE` regexes only). The brief is
now CORRECTED in commit `0dbbad9` and MERGED via `f92a9e5`.

## 4. Cross-lane contracts — status (final)

- R1 — Validation split is the ONLY progress number (500-record FROZEN `validation.jsonl`,
  sha `7640d067…`): **MEASURED — FINAL 261/500 = 52.2%**, harness fixed, Lane 10 reproduced
  it exactly (§3).
- R2 — Corpus schema (Lane 02 owns; Lane 04 codes against it): **DONE** — corpus 8,000
  (train 7,500 / validation 500, seed 7102); Lane 04's loader/count claims are OLD-corpus-pinned
  and need an 8,000 re-run (see §6).
- R3 — Lane 03 owns anchors in `laya_v7_evidence.py` ONLY; Lane 08 owns route/emission fixes in
  extractor/graph: **RESPECTED** — Lane 03's five commits touch only evidence.py (+ tests);
  Lane 08 touched only extractor.py + graph.py (Lane 09 verified via `git show --stat`).
- R4 — Lane 05 writes KN/Kanglish templates as NEW files; Lane 02 wires them in: **DONE** —
  Lane 02 wired `kn_templates.py` (`{'en': 50, 'kn': 54, 'kn_roman': 71}`).
- R5 — Lane 06's brief goes to the parent FIRST; no lane adopts model advice until the coordinator
  checks it against our own numbers: **BRIEF CORRECTED (`0dbbad9`) + MERGED (`f92a9e5`)** —
  model answers not yet received; no lane has adopted model advice.
- R6 — Kaanoon real-phrasing eval: evaluation only, Lane 07 scores it, no lane tunes against it;
  harness support `python3 tests/recall_eval.py --suite kaanoon` merged (`f9a4fdc`). FINAL
  Kaanoon baseline **14/28 (50.0%)**, separate from the synthetic number. Same sealed/test-bank
  guard applies. (Needs coordinator merge into shared state — shared state committed in `f92a9e5`.)
- R7 — Lane 02's Kaanoon reconciliation used ONLY the patterns file (`docs/kaanoon_phrasing_patterns.md`),
  never the held-out eval set (Lane 09 §2; Lane 02 states the heldout was never opened).

## 5. What still needs the RTX run (cannot be done on this VM)

| Need | Source |
|---|---|
| Classifier training (Lane 04's `scripts/train_v71_classifier.py`) + validation scoring at scale | shared state guardrails ("This VM has NO GPU/torch"); Lane 04 owns RTX commands |
| Sealed Fresh-20 / Kannada-8 re-run — the only true check of the ≥70% unseen target | shared state guardrails; sealed files must never be opened here |
| Any neural run, distillation, or T4 parity check | same |

## 6. Open follow-ups (carried — swarm closed, these are next steps, not lane work)

| Item | Owner / status |
|---|---|
| Schema-bump decision (28→36 facts) | **Parent** (needs coordinator + Lane 04 + Lane 07) |
| Lane 03 residuals: in_scope 3/222 (relayed-speech), landlord-evictor probe, mixed DV+OOS limitation | Lane 03 status file `lane-03-anchors.md` (C4: EN validation all 11 issues recall 1.00, all facts 1.00 except in_scope 3/222; full fact+issue FP sweep 0) |
| Lane 03's 2 earlier open defects (mutual-consent false-fire, child-only miss) | **FIXED in C4** — child-only branches incl. decimal ages + minor-speaker carve-out, school-fees pattern + money+minor rule, soft divorce/mutual negations (per commit `7839e86`); Lane 10's final harness re-run (261/500) is the end-to-end confirmation, not a per-defect re-test |
| P2.1 native Kannada audit | Human — native Kannada speaker/legal reviewer (open since 10x) |
| Sealed leakage check QUEUED (no sealed hash index exists); corpus cleared on readable refs only | Coordinator |
| RTX training + sealed re-run outstanding | RTX 5050 machine / Colab (see §5) |
| Asker-perspective GT convention tension on Kaanoon E10/E19-type items (pipeline predicts [bnss-144, pwdva-20] on E10 and [hma-13] on E19 against expected []) — keep the convention and accept the penalty, or annotate both asker and issue perspectives | **Coordinator decision** |
| Lane 08 enumeration/probe claims UNVERIFIED (grep/test/probe runs pending) | Lane 08 / verifier |
| Lane 04 old-corpus counts need 8,000 re-run (`--check-data-only` etc.); vacuous-1.0 `denied_recall` default + small-sample macro-F1 behaviour should be documented in the scorer | Lane 04 |
| Lane 11 on-disk leakage report STALE (C 18→20, D 0.6614→0.6425, both PASS) — re-run `check_disjoint.py` after the next corpus change and refresh the report | Lane 11 |
| Lane 01 pinned-file §2–§5 numbers UNVERIFIABLE-NOW (pinned file gone); record IDs are positional, not content-stable — cite corpus shas | Noted; no action |
| Lane 05 §4 AFTER numbers SUPERSEDED by Lane 02's rebuild — do not quote | Noted; no action |
| Lane 06 brief inherited inconsistency (Fresh-20 FN-by-section list sums to 27, total states 28; category tables cover only 18/20 Fresh-20 and 4/8 Kannada-8) — inherited from the 10x plan, not Lane 06's error | Noted; no action |

Carried from the 10x swarm (not recall-lane work): Lane 07 safety patch spec, Lane 05
wrapper-refactor spec, Lane 06 NLLB retirement, Lane 10 (10x) `compute_fb` H12 fix, PC-2 Lane 08
vocab re-alignment, PC-5 v4.1 rename decision. None of these is a recall-lane task unless the
coordinator assigns it.

## 7. Lane status board (FINAL — all 11 lanes done)

| Lane | Task | Status |
|---|---|---|
| 01 | Diagnosis | **DONE — MERGED `f92a9e5`** |
| 02 | Paraphrase expansion | **DONE — MERGED `de52ad4`** (corpus 8,000, frozen split) |
| 03 | Evidence anchors | **DONE — MERGED `80e53d8`, `a0d58a0`, `58d950c`, `7839e86`, `c57919c`** (17 new tests, 66 OK, 16-Q 14/16) |
| 04 | Classifier training prep | **DONE — MERGED `6eb21d2`, `c596512`, `5498c91`** (old-corpus-pinned) |
| 05 | Kannada/Kanglish | **DONE — MERGED `a1f8c42`, `c19cecd`, `3d03399`** (§4 AFTER superseded) |
| 06 | Consultation brief | **DONE — MERGED `f92a9e5`** (brief §3 corrected `0dbbad9`) |
| 07 | Evaluation harness | **DONE — MERGED `aba4151`, `f9a4fdc`** + fix `0dbbad9` |
| 08 | Stage 1 routes audit | **DONE — MERGED `b9cd21c`, `4c464d6`, `69936e1`** (code+16-Q verified; enumeration/probe claims unverified) |
| 09 | Independent verifier | **DONE — MERGED `8881a12`** |
| 10 | Docs/merge | **DONE** — this tracker (update 6, FINAL) |
| 11 | Kaanoon DO BOTH | **DONE — MERGED `410d65b`** (eval 28 + study 16 + patterns doc) |

## 8. External reference: kaanoon.com (phrasing-pattern reference + Lane 11 eval set)

- **What it is:** https://www.kaanoon.com/ — "Legal answers online from lawyers - Indian Kaanoon",
  a Q&A portal where real lawyers answer laypeople's legal questions. Verified by Lane 10 via
  page-text fetch 2026-11-27 ~19:40 IST (homepage title + user testimonials about lawyers
  answering; no live-browser visit). This is the site Nivedh mentioned on 2026-11-26 (voice call)
  for getting full clarity on the Laya decision graph. User instruction (voice call 2026-11-27
  ~19:23 IST, blanket permission): DO BOTH — fresh held-out eval set + phrasing-patterns study.
- **Permitted use:** Lanes 02, 03 and 08 may use it ONLY as a **phrasing-pattern reference** —
  for paraphrase templates (Lane 02), regex anchors (Lane 03), and the Stage 1 routes audit
  (Lane 08). Small number of public pages only; patterns summarized only — **no wholesale
  scraping or copying into the corpus** (licensing/IP), and it is **never cited as legal
  authority** (legal authority comes only from the verified registry / primary judgments).
- **Contribution log (phrasing-pattern reference):**

| Lane | Use | Contribution recorded |
|---|---|---|
| 02 (Paraphrase expansion) | Phrasing patterns for paraphrase templates | **Kaanoon-informed expansion** — corpus 5,000 → 8,000 used the patterns file only (R7); heldout never opened (Lane 09 §2) |
| 03 (Evidence anchors) | Phrasing patterns for regex anchors | C4 hardening used Kaanoon + audit paraphrase forms (commit `7839e86`); child-only, lockout/residence story forms, DV-comp harassment, Stridhan, JS paraphrase, procedure issue |
| 08 (Stage 1 routes audit) | Phrasing patterns for the routes audit | Kaanoon-derived phrasings cited are generic question phrasings ("court ordered maintenance but he is not paying", "amount is not enough, prices gone up, increase it") — NOT lawyer answers (Lane 09 §8) |

### Lane 11 — Kaanoon DO BOTH (DONE — MERGED `410d65b`)

| Item | Status / value |
|---|---|
| Eval set file `data/kaanoon_eval/heldout.jsonl` | **BUILT — 28 items**, all EN (28/28), source URL per item, annotated issues/facts + expected sections; 7 items with expected_sections == [] (E10, E11, E16, E19, E21, E25, E27); E14 Hinglish (lang 'en' with flagged note) |
| Study file `data/kaanoon_eval/study_sample.jsonl` | **BUILT — 16 items** |
| Study doc `docs/kaanoon_phrasing_patterns.md` | **BUILT — 150 lines**; verified: 0 shared 8-grams with eval, all 16 study IDs cited, 0 eval IDs cited, sampled fragments trace to study items only (Lane 09 §10) |
| Lane 11 status file | `docs/recall_swarm_state/lane-11-kaanoon.md` (committed in `410d65b`) |
| Sample size (held-out eval set) | **28 items** (target was ~25–35) |
| Per-category counts — eval | custody 5, maintenance 5, divorce 5, restitution 4, eviction 3, stridhan 2, joint_property 2, violence 2 (Lane 10 recount via Counter — matches Lane 11's claim exactly) |
| Per-category counts — study | maintenance 3, violence 3, stridhan 2, eviction 2, custody 2, divorce 1, joint_property 1, restitution 1, other (dowry) 1 (Lane 10 recount — matches Lane 11's claim) |
| Study-vs-eval split sizes | **study 16 / eval 28** (44 total specs in `build_heldout.py`); disjointness PASS — A eval vs train+val 0 shared 8-grams, B eval vs study 0 shared 8-grams/questions/ids, D max cosine 0.6425 < 0.90 (Lane 09 re-run) |
| Kaanoon baseline number | **FINAL 14/28 (50.0%)** at HEAD `c57919c` (Lane 10 re-run verified, §3); on non-empty-expected items 10/21 (47.6%). History: Lane 09 measured 12/28 (42.9%) on the pre-fix harness; update-5 official 13/28 (46.4%) at committed code + fix. Labelled SEPARATELY from the synthetic validation number; never conflated; no lane may tune against it (R6) |
| Changes in templates / anchors / routes from Lanes 02/03/08 | Lane 02: Kaanoon-informed 8,000 expansion (patterns file only). Lane 03: 5 anchor rounds incl. C4 Kaanoon forms. Lane 08: restit_p/dvcomp_p neural routes (prompts 9 → 11) + post-order split facts, citing generic Kaanoon question phrasings |
| Leakage report | `data/kaanoon_eval/leakage_report.json` verdict PASS — but **STALE** vs current train file (C 18→20, D 0.6614→0.6425, both PASS; Lane 09 re-run) — refresh after next corpus change |
| E04 note | First disjointness check FAILED check A (18 shared 8-grams from then-KAN-E04); item removed from eval, moved to study as KAN-S16; after the move A = 0 |

**Bounds (kept visible):** no wholesale copying of Kaanoon questions/answers into the training corpus;
lawyers' answers are **never cited as legal authority** (authority comes only from the verified
registry / primary judgments); the held-out set is evaluation only; the study is patterns summarized
only. No lawyer answer text is reproduced anywhere in the repo (Lane 09 check 3: heldout/study
records have NO answer field). All prior guardrails still apply: no sealed files opened, no frozen
files touched, no GPU/torch on this VM, no claim of ≥70% until a real run measures it.

## 9. Lane 09 verification — per-lane verdicts (commit `8881a12`)

Source: `docs/recall_swarm_state/lane-09-verifier.md` (623 lines; HEAD at final check `de52ad4`).
Method: re-ran each lane's cited commands, re-computed numbers from raw outputs, guardrail check.
No GPU/torch; sealed files never opened (numbers only from logged aggregates). Note: Lane 09's
check predates Lane 03's C4/C5 rounds — those were verified by Lane 10's own re-runs (§2: final
harness 261/500, 66 tests OK, 16-Q 14/16).

| Lane | Verdict |
|---|---|
| 01 Diagnosis | **VERIFIED** — v1 numbers + 16-Q + 0/500 Stage-2 cross-check + corpus-instability warning all verified; pinned §2–§5 numbers UNVERIFIABLE-NOW (pinned file `11ffa32d…` gone) |
| 02 Paraphrase expansion | **VERIFIED** — every re-runnable count (clusters, issues, facts, oracle positives, gate output, SHAs, freeze) matches; 2 explained hash deltas (freeze adoption) + 1 doc gap (§6 hashes predate §9) |
| 03 Evidence anchors | **VERIFIED code+suites** (rounds 1–3) — 3 commits touch only evidence.py; 16-Q 14/16 + 49/49 unit suite match; 3 of Lane 01's 5 headline defects FIXED end-to-end; **2 defects still open at that time** (mutual-consent false-fire, child-only miss); residence 27/40→6/30 numbers UNVERIFIABLE; **no status file at that time** — status file `lane-03-anchors.md` (151 lines) landed with C5 (`c57919c`); C4 claims the 2 defects fixed (see §6) |
| 04 Classifier training prep | **VERIFIED old-corpus-pinned** — PC-2, loader OK 4500/500, counts 155/4096/1664, smoke test n=200 all 1.0; caveats: 8,000 re-run needed, vacuous-1.0 denied_recall default |
| 05 Kannada/Kanglish | **VERIFIED except §4 AFTER superseded** — self-test, tables, smoke tests, leakage gate all match; §4 AFTER numbers superseded by Lane 02's 8,000 rebuild (not an error) |
| 06 Consultation brief | **VERIFIED numbers but §3 NEEDS CORRECTION** — sealed aggregates, corpus numbers, 16-Q, classifier config all verified; §3 stale/wrong on L417 block, pooling, anchor attribution — **FIXED by coordinator commit `0dbbad9`, merged via `f92a9e5`** |
| 07 Evaluation harness | **VERIFIED baseline exact but 2 mismatches** — baseline 173/500 reproduced exactly 3×; **sex-mapping bug** confirmed + quantified (old split corrected 179/500, frozen split corrected 204/500); **self-test count "15" WRONG** (12 committed / 21 current) — self-test itself PASSES |
| 08 Stage 1 routes audit | **VERIFIED code+16-Q, enumeration/probe claims UNVERIFIED** — prompts 9→11, post-order facts, graph additions, scope, 16-Q 14/16 before+after all verified; grep/test/probe claims still open |
| 10 Docs/merge (this tracker) | **VERIFIED-at-write-time, NOW STALE** (at update 5) — everything verified at write time was accurate; `merged.md` internally contradictory (stale "0 commits / NONE YET" lines); tracker listed Lanes 01/02/03 pending and Lane 11 NOT BUILT — **fixed in update 5; this update 6 is the FINAL refresh** |
| 11 Kaanoon DO BOTH | **VERIFIED in depth** — blind re-label expected-section agreement 4/9 (5 disagreements explained: 1 graph-rule miss on verifier's side, 4 asker-perspective convention differences); derivation `validate_expected` on all 28 items → **0 mismatches**; disjointness PASS; no lawyer answers reproduced; patterns doc mechanics verified; Kaanoon baseline 12/28 measured by verifier |

Headline findings: (1) harness sex-mapping bug — fixed by `0dbbad9`, corrected baselines in §3;
(2) validation split FROZEN (sha `7640d067…`) — all validation numbers must cite this sha;
(3) Lane 03 fixed 3 of Lane 01's 5 headline regex defects (rounds 1–3), 2 more in C4; (4) Lane 10
tracker stale — fixed by updates 5 and 6 (this file).

## 10. Gemini consultation — Hydrogen fallback, NOT Neon (filed 2026-11-27 ~20:12 IST)

Source: `workspace/goals/english-family-law-chatbot-retest/files/laya-graph/gemini-recall-consultation.md`
(coordinator-verified by reading it; Lane 10 read the same file and records from it).
**Status: proposed by Gemini (Hydrogen fallback), awaiting ChatGPT + parent decision — NOTHING
here is adopted yet. Do NOT finalise any adopted plan until ChatGPT's answer lands and both are
checked against our own numbers (second-opinion discipline).**

### CAVEAT FIRST — read before any verdict below

- **Neon was selected (Thinking High) but Gemini fell back to "Hydrogen High" — the answer is NOT
  from Neon, so a real Neon re-run is still owed** when Neon is available. The standing rule
  (consult Gemini Neon, Thinking High) is NOT satisfied by this consultation.
- Date: 2026-11-27 ~20:07–20:12 IST. Chat:
  https://gemini.google.com/app/18aadfecd490504c ("LAYA v7.1 Extraction Fixes and Recall Strategy"),
  signed in as Rocky Balbao (elvyn32@santarivn.store). Picker showed "currently Neon High" before
  sending, then "Pro is in high demand — Another model was used for this response", picker
  afterwards "currently Hydrogen High".
- Two sentences were truncated in the page's own text view (marked in the filed note).
- **Sign-in note:** nivedhbhat15@gmail.com was rejected by Google ("Wrong password"); signed in
  with the saved Elvyn login instead — **the nivedh Google password in the vault does not match
  that account (or has changed), unresolved.**
- The brief was pasted exactly as given; the model asked no clarifying question. Full response
  finished generating.

### Key verdicts to carry (Gemini's projections/recommendations, NOT measured numbers)

1. **REPLACE Stage 1 outright with the classifier** — regex only as post-classifier guards /
   overrides (explicit section citations, hard numeric/temporal parsers), never a veto — and
   **STOP tuning regex anchors**.
2. **8k pure-template corpus plateaus at 58–66% EN / 48–58% KN — short of 70%.** Crossing needs
   a multilingual backbone (**mmBERT-base or xlm-roberta-large, MIT** — English-only
   ModernBERT/DeBERTa called a **fatal flaw** for Kannada), **+3,000–4,000 LLM-diversified lay
   paraphrases** (allocation: 1,100 residence/lockout, 900 joint-property/Stridhan, 900
   custody/welfare, 700 divorce/ancillary, 400 dense multi-issue), and recall-biased per-head
   thresholds. With 12,000–13,000 total, Gemini projects **~72–78% EN / ~65–72% KN/Kanglish**.
   These are Gemini's projections, not measured numbers.
3. **Build a 250-item Blind Human-Register Stress Set as the pre-sealed go/no-go gate
   (≥72% exact, micro-R ≥0.90, micro-P ≥0.92)** — the 500-record synthetic val split must never
   be the sole gate. File proposed: `data/eval_blind_register_250.jsonl`.
4. **Fix before Run #1:** bf16 + grad checkpointing + max_seq_len 288 (36 sequences/step will OOM
   on 8 GB RTX 5050), grouped (not row-level) validation split, audit the 8 dead fact keys.
   (Further detail in the filed note: backbone switch, Asymmetric Loss, per-head thresholds via
   OOF + Empirical Bayes shrinkage, single-pass packed sequence + span pooling, veto calibration
   p_veto ≥0.75 with margin δ=0.25, Q2 augmentation ranking, Q4 failure modes incl. upstream
   fact fan-out collapse, Q6 go/no-go gates — all proposed, none adopted.)

### Status

- **ChatGPT's answer is still pending** — do NOT finalise any adopted plan until it lands and both
  are checked against our own numbers.
- Open: re-run this consultation on real Neon (Thinking High) when Neon is available.
- Open: resolve the nivedh Google password mismatch in the vault (unresolved).

## 11. ChatGPT consultation + both-model synthesis — ADOPTED as the working decision (filed 2026-11-27 ~20:13 IST)

Source: `workspace/goals/english-family-law-chatbot-retest/files/laya-graph/chatgpt-recall-consultation.md`
(coordinator-verified by reading it; Lane 10 read the same file and records from it).
**Status: ADOPTED as the working decision** — checked against our own numbers (see the synthesis
in the filed note). **Do NOT mark any of this as implemented** — it is the adopted working
decision; execution is the next phase (RTX training).

### Model status (both consultations visible together)

- **ChatGPT: GPT-6.2, thinking max — the REAL requested model** (unlike Gemini's Hydrogen
  fallback). Date: 2026-11-27 ~20:07–20:13 IST. Chat:
  https://chatgpt.com/c/6b0995f0-cd70-83ec-aa08-b3f0baa9944d ("Technical Consultation Summary").
  Response complete, "Worked for 2m 2s"; no sign-in needed; brief pasted exactly as given.
- **Gemini caveat (repeated here so both consultations' model status is visible together):**
  Neon was selected (Thinking High) but Gemini fell back to "Hydrogen High" — its answer is NOT
  from Neon, so a real Neon re-run is still owed. See §10.

### AGREED SYNTHESIS — adopted as the working decision (all 9 points)

1. **Replace Stage 1 with the classifier; regex never a recall gate** — regex survives only as
   post-classifier evidence (explicit citations, dates, amounts) + statutory consistency guards.
2. **Multilingual backbone mmBERT-base (MIT) primary; English-only ModernBERT/DeBERTa rejected
   as default.** (Gemini's alternative: xlm-roberta-large; ChatGPT's: mDeBERTa-v3-base.)
3. **Train the existing 8k FIRST with a nested learning curve (2k/4k/7.5k) before deciding on
   expansion** — ChatGPT's sequencing wins over Gemini's pre-commitment to +4k. Gemini says 8k
   plateaus 58–66% EN; ChatGPT says 70% plausible from 8k diverse at 60–75% — settle it by
   measurement, not opinion.
4. **Dead fact keys + graph contract first (P0).**
5. **bf16 + grad checkpointing + micro-batch 1 / grad-accum 8 on the RTX 5050** (both models
   independently computed 36 sequences/step will OOM).
6. **Pre-sealed gate: build ONE independent human-written holdout, 300 items (100/language),
   ≥80% exact per language** — ChatGPT's stricter gate, not Gemini's 250/≥72%.
7. **Per-head thresholds via OOF + shrinkage; no label smoothing.**
8. **NEW pre-training gates from ChatGPT:** run the four-configuration graph oracle (gold/gold,
   gold/pred, pred/gold, pred/pred) to verify the recall problem really lives in Stage 0/1;
   audit clause supervision (never assign question-level labels to every clause).
9. **Brief inconsistency to reconcile before the next evaluation report (found by ChatGPT):**
   the Fresh-20 category breakdown sums to 18 questions / 5 exact and itemised FNs sum to 27,
   not the reported 20 / 7 / 28. Coordinator-verified against
   `results/live-laya-v7-results.md`: headline aggregates ARE consistent (7/20, TP/FP/FN
   38/5/28; top_fn_sections list sums to 27). Two exact questions are unaccounted for in the
   breakdown. Action: reconcile the category breakdown against the sealed aggregates WITHOUT
   opening sealed text before the next evaluation report.

### Adopted allocation overlap

Residence/lockout + joint-property/Stridhan are the top two clusters in BOTH models' next-4,000
allocations (Gemini: 1,100 residence / 900 joint-property+Stridhan / 900 custody / 700 divorce /
400 dense multi-issue; ChatGPT: 1,000 residence / 850 Stridhan+joint / 750 custody / 650 divorce /
450 maintenance / 300 scope-negation). Adopt the union of the two allocations, weighted to
residence + joint-property first.

### Where they differ (not settled — needs experiment, not opinion)

- Can 8k alone reach 70%? Gemini: no (plateaus 58–66% EN, needs +3–4k LLM paraphrases).
  ChatGPT: yes, plausibly (5–8k diverse verified → 60–75%; 12–15k targeted diverse → 70–85%;
  "would not commit to 20,000 before measuring the first 8,000"). Resolution adopted: train the
  8k baseline first (with the learning curve), then decide on expansion from the measured curve.
- Evaluation gate size: Gemini 250 items / ≥72% overall; ChatGPT 300 items / ≥80% per language.
  Adopt ChatGPT's (stricter, per-language, statistically grounded in the Wilson bound — an
  observed 80/100 gives a ~71.1% Wilson lower bound vs ~60.4% for 70/100).

### Implementation status

**NOT IMPLEMENTED — adopted working decision only.** Next phase is execution (RTX training):
P0 dead keys + graph contract → P1 remove regex recall vetoes → P2 multilingual backbone →
P3 clause-supervision audit → P4 train 7,500 records (first measured baseline) → P5 calibrate →
P6 error mining + targeted examples → P7 independent human holdout (≥80% per language) →
P8 sealed re-run (≥70% per set) → P9 distil + CPU optimisation. (Priority order from the filed
ChatGPT note §7; execution has not started.)

## 12. Deep >70% plan — filed 2026-11-27 ~21:00 IST (plan, NOT a result)

- **Source file:** `workspace/goals/english-family-law-chatbot-retest/files/laya-graph/70-percent-plan.md` (166 lines). Verbatim copy in this repo: `docs/70-percent-plan.md` (sha256 `dca2be7f1adce88c4c82ee91a28b61273bf5bc31637a5864a789be774fb0ec66`, identical to the source; coordinator-copied, content unedited). Included in the recall push manifest.
- **Built only from verified sources:** the swarm's final numbers (261/500, 52.2%; Kaanoon 14/28), the Gemini consultation (Hydrogen fallback caveat included) and the ChatGPT consultation plus the both-model synthesis.
- **Structure:** §0 measured baselines, §1 adopted decision, §2 Phase A pre-training gates A1–A7 (dead keys, graph oracle, clause supervision audit, backbone swap + tokenizer audit, grouped split audit, VRAM smoke test, brief inconsistency reconciliation), §3 Phase B Training Run 1 on the RTX 5050 (nested 2k/4k/7.5k learning curve, mmBERT-base, bf16, micro-batch 1 / grad-accum 8, max_seq_len 288, ASL loss, label smoothing 0.0, OOF + Empirical Bayes thresholds), §4 Phase C error mining + ~4,750 targeted LLM-diversified records (allocation table by FN cluster), §5 Phase D 300-item independent human-written holdout (100/language, ≥80% per language pre-sealed gate), §6 Phase E sealed re-run (Fresh-20 ≥14/20, Kannada-8 ≥6/8, with adaptive-exposure disclosure), §7 Phase F distillation post-70%, §8 human gates, §9 risks/kill conditions, §10 conditional timeline, §11 stop list, §12 win criteria.
- **Exact RTX commands are NOT in the plan** — they live in `docs/recall_swarm_state/lane-04-classifier.md`, which the plan points to.
- **NOTHING in the plan claims ≥70%** — it is a path with gates, not a result. No training, holdout build, or sealed run has started under it.
