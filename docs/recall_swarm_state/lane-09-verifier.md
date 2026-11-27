# Lane 09 — Independent Verifier (LAYA v7.1 recall swarm)

- **Lane:** 09 Verifier (read-only on every other lane's files; this file is the only file Lane 09 writes).
- **Method:** for each lane — (1) re-run the exact commands cited and compare output line-by-line;
  (2) re-compute numbers from raw outputs, not from summaries; (3) guardrail check (frozen files
  untouched, no sealed files opened, every number traces to a re-runnable command);
  (4) `python3 tests/test_graph_v4.py` + `python3 tests/test_prose_renderer_v2.py` after each merge.
- **HEAD at final check:** `de52ad4` (Lane 02 commit). Baseline HEAD at swarm start: `1cb0bff`.
- **Sealed discipline (Lane 09):** `test-bank/sealed/*.json` was never opened. Sealed numbers below
  come only from already-logged aggregates in `results/live-laya-v7-results.md`.
- **No GPU/torch on this VM** (verified: `python3 -c "import torch"` → ModuleNotFoundError).
- **Do NOT claim 70% until a real run measures it.**

## HEADLINE FINDINGS (read first)

1. **HARNESS BUG — sex-mapping (Lane 07, MAJOR, quantified twice).**
   `predict_sections_from_stage1` in `tests/recall_eval.py` passes record enums raw
   (`claimant_sex` "M"/"F"/"U") into `evaluate_stage2_v7`, but the graph compares against
   "male"/"female" while the real pipeline emits "male"/"female"/"unknown". Male-gating never
   fires in the harness's EXPECTED derivation. Effect on the OLD (swarm-start) split:
   173/500 claimed → **179/500 (35.8%) corrected** (+6 records, all male-claimant; silent
   263 → 257). Effect on the NEW frozen split: 196/500 as printed → **204/500 (40.8%)
   corrected** (+8 records; silent 242 → 234). Lane 01's independent mapped oracle confirms
   179/500 on the old split. Lane 11's `validate_expected` maps correctly — the harness must
   adopt the same mapping before any baseline is recorded as official.
2. **Validation split FROZEN** (Lane 02, §9 of its status file; coordinator freeze ~19:34 IST):
   `data/synthetic_v7_1/validation.jsonl` sha256
   `7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e`, 500 records,
   recorded in `manifest.json` as `frozen_validation_sha256` (+ `frozen_validation_at`
   2026-11-27T14:06:10.824537+00:00). The builder now refuses to overwrite it and regenerates
   train only. **All validation numbers from here on must cite this sha.** The old-split
   numbers (173/179) are historical only — the old file is gone from disk.
3. **Kaanoon (Lane 11) — VERIFIED in depth.** Blind re-label spot-check: expected-section
   agreement 4/9, with all 5 disagreements explained (1 graph-rule miss on my side, 4
   asker-perspective convention differences, all documented in Lane 11's notes). Derivation
   check: `validate_expected` on all 28 items → **0 mismatches** (GT mechanically consistent
   with the live graph). Disjointness: **PASS** (A=0, B=0, D<0.9); Lane 11's on-disk
   `leakage_report.json` is STALE vs the current train file (C=18→20, D 0.6614→0.6425) — both
   versions pass. No lawyer answers reproduced anywhere in the repo. Kaanoon baseline measured
   by ME (verifier) via Lane 07's harness: **12/28 (42.9%)**, Wilson [0.2651, 0.6093].
   Patterns doc verified: 0 shared 8-grams with eval, all 16 study IDs cited, 0 eval IDs cited,
   sampled fragments trace to study items only.
4. **Lane 03 fixed 3 of Lane 01's 5 headline regex defects** (decree, restitution, DV-comp —
   verified end-to-end on the extractor). **Still open:** `_MUTUAL_CONSENT_RE` false-fire on
   "will not agree to a mutual divorce" (mutual_consent still extracted supported) and
   `_CHILD_ONLY_CLAIM_RE` miss on "money only for the child's school fees".
5. **Lane 10's tracker is materially stale** (last update ~19:55 IST): it still lists Lanes
   01/02/03 as "pending — no status file landed" and Lane 11 as "NOT BUILT YET", while Lane 01
   and Lane 02 status files have landed and Lane 11 + Lane 02 + Lane 03 are committed/merged.
   `merged.md` is internally contradictory (stale "0 commits / NONE YET" lines alongside the
   updated summary). Accurate at write time; needs a refresh, not a correction of fact.

## §0 Guardrail status (whole swarm, final check at HEAD de52ad4)

- **Frozen files untouched:** `git diff --name-only` shows no frozen file modified; graph test
  reports **7/7 frozen hashes intact** on every run I did (baseline, after Lane 08, after
  Lane 03 ×3 commits, at final HEAD).
- **Required suites at final HEAD de52ad4:** graph PASS (34 sections / 66 nodes / 99 edges,
  0 dangling, 7/7 SHAs); prose PASS (246 cases, Fp=0, quality_flags=0, 15/15 mutants);
  full unit suite **Ran 49 tests — OK**.
- **16-Q evidence-mode:** 14/16, esc_bool 16/16, esc_kinds 10/16, fp_prose 0, rating 7.6 —
  re-run by me before AND after Lane 08 AND after Lane 03; identical every time, same misses
  H6 (pwdva-18) and H14 (hma-13). No regression from any lane.
- **No sealed files opened by any lane** (no lane cites sealed text; all sealed numbers trace
  to the logged aggregates). No faked numbers found anywhere: every measured number I checked
  traces to a re-runnable command, except where flagged UNVERIFIABLE below.
- **Scope:** no lane edited another lane's files except as noted (Lane 02's builder is its own;
  Lane 03 touched only `src/laya_v7_evidence.py`; Lane 08 touched only extractor.py + graph.py;
  Lane 05 wrote NEW files only). Lane 02's status file notes `src/laya_v7_evidence.py` shows as
  modified in the tree but that is Lane 03's work, left untouched by Lane 02 — confirmed by
  the commit contents (Lane 02's commit de52ad4 touches builder + data + its own status file only).

## §1 Lane 01 — Diagnosis (file `lane-01-diagnosis.md`, untracked, NOT committed)

- **Claim:** pinned validation (sha `11ffa32d…`) evidence-mode 179/500 (35.8%), micro
  P/R/F1 0.7810/0.3837/0.5146, TP/FP/FN 353/99/567, silent 235/411 (57.2%); Stage 2 is not
  the bottleneck (assess-kept == Stage-2-over-extracted-facts on 0/500 mismatches; true
  Stage 2 FN/FP = 0 after re-analysis); per-cause FN: paraphrase miss (kn/kn_roman) 488
  (86.1%), anchor miss (EN) 52, classifier gap 15, stage-2-rule-gap 4 (first pass, all
  reclassified as extraction artifacts); KN fact recall 0.0 on every fact; EN strong facts
  0.88–1.00, weak facts decree/dv-comp 0.0, child-only 0.05, demand 0.17, restitution 0.20;
  corpus moved under the lane (3 validation versions in ~15 min) — no lane should quote a
  validation number without its sha.
- **Re-run result:**
  - The pinned file (`11ffa32d…`) is GONE from disk (uncommitted intermediate, overwritten by
    Lane 02's rebuilds) — the pinned §2–§5 numbers **cannot be re-run as-is**. Flagged as
    UNVERIFIABLE-NOW, not as a Lane 01 error: the pin + warning (§0) is exactly the right
    response to the instability, and I observed the same instability myself.
  - **v1 (swarm-start file, from git) INDEPENDENTLY CONFIRMED:** my mapped re-scoring of the
    harness baseline gives exact 179/500, micro-R 0.3457, silent 257/417 — Lane 01's §6 v1
    row says 179/500 (35.8%), micro-R 0.346, silent 257/417. Exact match on all three.
    (This is also independent confirmation of the §HEADLINE-1 harness bug: same file, mapped
    oracle 179 vs unmapped harness 173.)
  - Re-ran Lane 01's own script `/tmp/lane01_diag.py` (copy with input path pointed at the
    git-HEAD validation file, output to `/tmp/lane09-diag-rows.json`) against the CURRENT
    code: exact **221/500 (44.2%)**, micro P/R/F1 0.8913/0.4188/0.5699, TP/FP/FN 418/51/580,
    silent 242, oracle-empty 83, assess-vs-Stage-2 mismatches **0/500**. The 179→221 delta is
    the Lane 03 + Lane 08 code changes since Lane 01 measured — i.e. current code on the old
    split scores 44.2% (mapped oracle). The 0/500 mismatch claim REPRODUCES on current code.
  - §4e regex defects tested directly against the regexes (current code, post-Lane 03):
    decree ×2, restitution ×2, demand, DV-comp all MATCH now (see §3 — Lane 03 fixed them);
    `_CHILD_ONLY_CLAIM_RE` still misses "I need money only for the child's school fees";
    `_MUTUAL_CONSENT_RE` still matches "will not agree to a mutual divorce" (see §3).
    The `injur\b` bug diagnosis is CONFIRMED by Lane 03's fix commit message ("injur/beat/pay
    never matched") and by the current pattern source (`injur\w*`).
  - §4e record-ID spot-check: IDs exist in the HEAD validation file but the TEXTS do not match
    Lane 01's quotes — because the quotes come from the pinned (v3) file, and record IDs are
    positional (same ID, different text across corpus versions). E.g. SYN-VA-0066 is a
    restitution text in the pinned file but a decree text ("Our divorce is already decided
    by the court") in the HEAD file. Consequence: record IDs are NOT content-stable across
    corpus versions — another reason the freeze (§HEADLINE-2) was needed.
  - 16-Q reproduction claim (14/16, esc_kinds 10/16, esc_bool 16/16, fp 0, rating 7.6):
    **matches my own re-runs exactly**.
- **Match/mismatch:** v1 numbers + 16-Q + 0/500 cross-check + corpus-instability warning all
  VERIFIED. Pinned-file §2–§5 numbers UNVERIFIABLE-NOW (file gone). §4e defect list: 6 of 7
  regex behaviours now FIXED by Lane 03 (see §3); the defects were real at measurement time.
- **Guardrail:** analysis only, no repo files edited (only its status file + /tmp scratch).
  Sealed discipline stated and respected (sealed numbers only from logged aggregates).

## §2 Lane 02 — Paraphrase expansion (commit `de52ad4`, status file committed)

- **Claim:** corpus 5,000 → 8,000 (train 7,500 / validation 500, seed 7102); langs EN 3,808 /
  KN 2,084 / kn_roman 2,108; validation langs EN 235 / KN 153 / kn_roman 112; per-cluster
  table (core 2000, combo 1900, hn_a 350, hn_b 450, hn_c 550, hn_d 450, hn_e 400, hn_f 900,
  neg 350, conflict 200, hn_g 250 NEW, hn_h 200 NEW); issue/fact counts (§1 tables);
  hma-26/27 oracle positives validation 9/13, train 140/162; Lane 05 kn_templates wired
  (`{'en': 50, 'kn': 54, 'kn_roman': 71}`); leakage gate PASS (corpus=8000, 0 8-grams,
  max cosine 0.8269); first gate run FAILED (7 shared 8-grams from 3 templates, reworded);
  rebuild deterministic (byte-identical); validation split FROZEN (§9, sha `7640d067…`,
  manifest records `frozen_validation_sha256` + timestamp, builder enforces it, `--new-split`
  only on coordinator order); schema-bump NOT done (28→36 facts needs coordinator + Lane 04
  + Lane 07); sealed check QUEUED (no sealed hash index exists); "committed by this lane".
- **Re-run result:**
  - Manifest counts: n_total 8000, n_train 7500, n_validation 500; langs EN 3808 / KN 2084 /
    kn_roman 2108 (sum 8000 ✓); clusters sum to 8000 ✓ — **all match**.
  - Per-cluster train/val split re-counted from the files: core 1865/135, combo 1792/108,
    hn_a 336/14, hn_b 420/30, hn_c 504/46, hn_d 424/26, hn_e 379/21, hn_f 853/47,
    neg 326/24, conflict 184/16, hn_g 232/18, hn_h 185/15 — **all match §1 exactly**.
  - Issues requested re-counted (11 issues) and facts supported re-counted (18 facts):
    **every number matches §1 exactly** (e.g. maintenance 3171, custody 1390, dv_compensation
    282, restitution 267; child_safety_risk 243, being_filed 223, decree 210, demand_made 421,
    child_maintenance_only 579, explicit_residence_order_only 105).
  - hma-26/27 oracle positives (my mapped oracle, `evaluate_stage2_v7` v3_bundled):
    validation 9/13, train 140/162 — **exact match**.
  - Leakage gate re-run by me on the new corpus: `corpus=8000 refs=408 overlap_8grams=0
    max_cosine=0.8269 (threshold 0.9) -> PASS`, exit 0, per-ref lines and top-3 cosine hits
    (0.8269 SYN-TR-4228/B-058; 0.7805 SYN-TR-0117/H14; 0.7762 SYN-TR-2366/B-142)
    **identical to Lane 02's §6 output, line for line**. On-disk `leakage_report.json`
    sha `44b9aa1c…` matches Lane 02's §6 hash. Train sha `0de7ddd7…` and validation sha
    `7640d067…` match §6 exactly.
  - Reworded templates present in the builder (lines 725 "remain under my care", 839 "first
    thing I should arrange", 911 "belongs with me") — the first-gate-failure fix is real.
    The first FAILED run itself is not re-runnable (templates already fixed) — plausible,
    consistent with the gate's collision mechanism; noted, not disputed.
  - Freeze: manifest on disk contains `frozen_validation_sha256 = 7640d067…` and
    `frozen_validation_at = 2026-11-27T14:06:10.824537+00:00` ✓; builder contains 7
    `frozen_validation` references + `--new-split` flag (lines 1997/2024/2030/2076) ✓.
    Validation sha on disk still `7640d067…` ✓ (unchanged since freeze).
  - Manifest sha `8d47ec57…` and builder sha `5dfaa09e…` do NOT match Lane 02's §6 hashes
    (`f052548f…`, `bce57abf…`) — EXPLAINED, not an error: §9's freeze adoption (after §6 was
    written) added the frozen fields to manifest.json and the enforcement code to the builder.
    The status file does not note that §6's hashes predate §9 — minor documentation gap.
  - "Committed by this lane": TRUE at HEAD `de52ad4` (commit includes builder + data +
    status file). Note the sequence: when I first read the status file the data files were
    still uncommitted in the tree; the commit landed afterwards. True now.
- **Match/mismatch:** VERIFIED on every re-runnable count (clusters, issues, facts, oracle
  positives, gate output, SHAs, freeze). Two explained hash deltas (freeze adoption) and one
  documentation gap (no note that §6 hashes predate §9).
- **Guardrail:** owns builder + data only; states Kaanoon heldout never opened (R6) — process
  claim, no evidence either way; §5 reconciliation used only the Lane 11 patterns file (R7),
  which is the allowed route. Sealed check honestly QUEUED, not claimed. No 70% claim made.

## §3 Lane 03 — Evidence anchors (commits `80e53d8`, `a0d58a0`, `58d950c`; NO status file landed)

- **Claim (commit messages only — no status file):** `80e53d8`: residence/lockout paraphrase
  anchors + nobody/has-not negation masks + explicit-residence order forms; "Residence recall
  on EN validation 27/40 miss -> 6/30 (corpus expanded 5k->8k by Lane 02 mid-task, so
  denominators shifted); explicit-residence 4/4 miss -> 0/4"; fixes FP where 'Nobody has
  hit/locked me out' fired violence + coercive lockout; removes stay-intent 'keep staying in
  the house' from lockout regex; 16-Q 14/16 unchanged; 49/49 unit tests pass.
  `a0d58a0`: fix DV-comp stem bug (injur/beat/pay never matched), Stridhan held-by/demand,
  decree forms. `58d950c`: divorce/restitution/custody/JS negation + conflict guards,
  violence stems, child-safety forms.
- **Re-run result:**
  - Diff review: `80e53d8` touches ONLY `src/laya_v7_evidence.py` (+35/−9) — scope respected
    (R3). The three commits together touch only evidence.py (verified via `git show --stat`).
  - 16-Q after all three commits: 14/16, same misses — **matches claim**. Unit suite:
    **Ran 49 tests — OK** — **matches claim**. Graph/prose PASS after the commits ✓.
  - Regex-behaviour tests (current code): `_DECREE_PASSED_RE` matches "The court gave the
    divorce decree last year" and "Our divorce is already decided (by the court)";
    `_RESTITUTION_RE` matches "I want him to come back home and live with me" and "I want
    my husband to return"; `_DEMAND_TRUE_RE` matches "I asked for it back and they refused
    to give it"; `_DV_COMP_RE` matches "I want compensation for my injuries" (pattern now
    `injur\w*` — the `injur\b` bug Lane 01 diagnosed is fixed). End-to-end extractor
    (`extract_v7_batch`, mode evidence): decree → supported, restitution_asked → supported,
    dv_injury_comp_asked → supported. **3 of Lane 01's 5 headline defects FIXED.**
  - **Still open (end-to-end extractor):** "My husband will not agree to a mutual divorce.
    Can I still get a divorce without his consent?" → `mutual_consent` still SUPPORTED
    (the `_MUTUAL_CONSENT_RE` match is not blocked by any negation mask; the hma-13→hma-13b
    flip Lane 01 §4a described still occurs). "I need money only for the child's school
    fees" → `child_maintenance_only` NOT supported (money_fact + school_fees_fact fire
    instead). Lane 03's `58d950c` "negation + conflict guards" did not fix the mutual-consent
    false-fire on this sentence.
  - Residence before/after numbers (27/40 miss → 6/30): **UNVERIFIABLE** — denominators
    shifted mid-task (corpus moved under Lane 03, as the commit message itself admits), no
    measurement script cited, no status file. The direction is consistent with my evidence:
    current code on the old split scores 221/500 (mapped) vs Lane 01's 179/500, and the
    residence anchors are visibly present in the diff — but the exact 27/40→6/30 cannot be
    re-derived. Flagged, not disputed.
- **Match/mismatch:** code changes + 16-Q + unit suite VERIFIED; 3/5 Lane 01 defects FIXED
  (verified end-to-end); 2 defects STILL OPEN; residence before/after numbers UNVERIFIABLE.
- **Guardrail:** evidence.py only; suites PASS; no status file — the lane's claims live only
  in commit messages, which is a process gap (coordinator: ask Lane 03 for a status file
  with the measurement scripts).

## §4 Lane 04 — Classifier training prep (commits `6eb21d2`, `c596512`, `5498c91`)

- **Claim:** PC-2 vocab pin (classifier FACTS == schema facts, ISSUES == schema issues); span
  schema; in_scope supported 4712 / denied 288 (5.8%); `stridhan_held_or_disposed` 0× in
  corpus; loader `--check-data-only` OK train=4500 val=500; denied-gate clause rows 155,
  span-masked clauses 4096, records with no spans 1664; `score_label_predictions` smoke test
  gold-vs-gold n=200 → issue/fact macro/micro F1 1.0, requested recall 1.0, in_scope accuracy
  1.0, denied recall 1.0 (n_denied 13); LoRA NameError fix; PIXMELT/laya build-time refusal;
  hyperparams (lr 2e-5, batch 4 × grad-accum 2, epochs 5, loss weights 0.35/0.35/0.15/0.10/0.05,
  tau_neg 0.5, ~2,800 steps); text lengths (mean 154.6 chars / 25.5 words, p95 262/47,
  p99 316/60, max 409/78; clauses mean 3.75, p95 6, max 8); exit bars (per-head F1 ≥0.95,
  requested recall ≥0.98, section-exact clearly above 173/500, silent well below 263) as
  TARGETS, not claims; RTX doc + status file (207 + 250 lines).
- **Re-run result:** PC-2 orderings verified exactly; loader `--check-data-only` → OK 4500/500
  exit 0 (on the OLD corpus — the loader counts changed with Lane 02's rebuild; Lane 04's
  numbers are pinned to the 5,000-record corpus and are now HISTORICAL, not wrong); report
  counts 155 / 4096 / 1664 verified; smoke test n=200 → all 1.0 verified; small-sample
  caveats found by me (n=5: fact macro F1 0.75 — absent classes score 0.0; `in_scope
  denied_recall` defaults to 1.0 when n_denied=0 — vacuous-1.0 on tiny samples); LoRA fix
  verified by code read (unverifiable on this VM — no torch/peft — Lane 04 states this
  honestly); PIXMELT refusal verified (build raises ValueError; `--backbone` still lists it
  in arg-parse, build-time refusal enforces); hyperparams verified in code; text/clause
  lengths verified exactly; "40 records hit the merge" vs my 48 records with exactly 8
  clauses — unclear, minor, not a firm contradiction (different quantities).
  Name collision resolved (renamed to `score_label_predictions`; docstring explains it);
  Lane 04 CONFIRMS Lane 07's shared signature in its status file §1.
- **Match/mismatch:** VERIFIED on all re-runnable claims (old-corpus-pinned). Two caveats to
  carry: (1) all loader/count claims are OLD-corpus numbers — Lane 04 must re-run
  `--check-data-only` against the 8,000-record corpus; (2) the vacuous-1.0 `denied_recall`
  default and small-sample macro-F1 behaviour should be documented in the scorer.
- **Guardrail:** owns classifier/train script/RTX doc/status only; graph/prose pass lines match
  my runs (timing variance only); no training run claimed (no torch here).

## §5 Lane 05 — Kannada/Kanglish (commits `a1f8c42`, `c19cecd`, `3d03399`)

- **Claim:** 25 KN blocks (`scripts/kn_templates.py`, 579 lines), self-test 25 blocks, variants
  en=50 kn=54 kn_roman=71 (175 total); blocks per issue/fact tables (§1); normalizer + lang
  pack self-tests PASS (kn fact_key_lexicon 12 keys, negation lexicon 5 keys, P2.1 still open);
  smoke tests (8 phrases → correct issue/fact); leakage gate on templates PASS (0 8-grams,
  max cosine 0.7762); rewording fix (old sentence 0×, new sentence 1×); §4 coverage finding
  (BEFORE in-memory run reproduced on-disk validation counts exactly; AFTER projection numbers).
- **Re-run result:** self-test PASS, 25 blocks / 50+54+71 variants — **exact match**; per-issue
  and per-fact block tables match the self-test output exactly; all 8 smoke-test phrases give
  the claimed issue/fact; leakage gate on the templates corpus (`/tmp/kn05_templates_corpus.jsonl`,
  215 lines) → `corpus=215 refs=408 overlap_8grams=0 max_cosine=0.7762 -> PASS`, exit 0 —
  **exact match to Lane 05's claimed output**; rewording verified (old 0×, new 1×).
  BEFORE counts in the kn_templates.py docstring verified exactly against the OLD validation
  file (issue requested kn+kn_roman: restitution 5, birth_certificate 7, dv_compensation 6,
  procedure 8, joint_property 13, stridhan 18, violence 17, divorce 22, custody 39, residence
  46, maintenance 134; thin facts as listed).
  §4 AFTER numbers: **SUPERSEDED, not fabrications.** My re-run of Lane 05's exact script
  `/tmp/measure_kn_coverage.py` FAILS at the assert: in-memory BEFORE gives kn 131 /
  kn_roman 135 vs on-disk kn 153 / kn_roman 119. Root cause: the builder's `N_TOTAL` was
  5000 when Lane 05 measured (verified via `git show c718f36`) but Lane 02 has since expanded
  it to 8000 and rebuilt the corpus. `generate(seed=7102)` is deterministic (verified 4 runs
  incl. PYTHONHASHSEED=0: val kn 131 / kn_roman 135, n_train 7500). The AFTER projection
  cannot be re-run as-is. The §4b dilution analysis and the coordinator decision it calls for
  (PLAN/N_TOTAL growth) remain relevant — and Lane 02's 8000-record rebuild is the answer to it.
- **Match/mismatch:** VERIFIED except §4 AFTER numbers, which are SUPERSEDED by Lane 02's
  rebuild (record as such, not as a Lane 05 error). Minor notes: status header "HEAD 1cb0bff"
  is the swarm-start baseline (stale by commit time but labelled as start); §8 "P2.1 must
  audit the KN prose templates, Lane 09" mislabels the lane (recall Lane 09 is the verifier;
  10x Lane 09 was Kannada prose); lang-pack comment cites "evidence.py:561" for the ಕೇಳಿಲ್ಲ
  stem — actual line is 600 (inherited stale plan citation); strong-words +39 / suffixes +9
  claimed in §2 were not independently tallied by me.
- **Guardrail:** NEW files only (R4 respected); Lane 02 wired them in; P2.1 native-speaker
  audit still open (stated in the status file itself).

## §6 Lane 06 — Consultation brief (files `docs/recall_consultation_brief.md`,
## `lane-06-brief.md`, uncommitted; doc only, no code, no tests)

- **Claim:** brief for Gemini (Neon, Thinking High) + ChatGPT (GPT-6.2, thinking max) carrying
  the sealed aggregates, corpus numbers, 16-Q numbers, classifier config, and the diagnosis
  (§3: L417 custody block, full-text-only pooling, anchor file attribution, hard negatives
  ~2,050, 8 dead fact keys, 421M PIXMELT/laya, latency target <0.5s/Q CPU).
- **Re-run result:** sealed aggregates verified vs `results/live-laya-v7-results.md` (Fresh-20
  7/20, Wilson [0.1812, 0.5671] → brief rounds [0.18, 0.57]; P/R/F1 0.8837/0.5758/0.6972;
  TP/FP/FN 38/5/28; silent 2; Kannada-8 4/8, Wilson [0.2152, 0.7848] → [0.22, 0.78];
  1.0/0.6957/0.8205; 16/0/7; silent 0; F1 arithmetic checks out). FP breakdown (pwdva-20 2,
  hma-13 2, bnss-144 1 = 5) and FN-by-section list and category-exact tables match
  `docs/10x_plane.md` lines 30–31 verbatim. Corpus numbers all verified (5000, 4500/500,
  seed 7102, EN 2316/KN 1333/Kanglish 1351, leakage 0 8-grams, max cosine 0.8182). 16-Q
  14/16 verified. Classifier claims verified in code (ModernBERT-large Apache-2.0,
  DeBERTa-v3-large MIT, heads [11,4]/[28,4], clause max-fusion). Train defaults verified
  (epochs 5, batch 4, grad-accum 2, lr 2e-5, max-seq-len 192, max-clauses 8).
  `LAYA_NOUL_PROMPTS` 9 entries verified by AST count. "8 dead fact keys" verified. "Zero
  neural probes" verified. Bank-tuned patterns verified. 421M PIXMELT/laya verified
  (extractor line 5). Latency target verified. Class imbalance (maintenance 2255 requested
  vs restitution 118) verified in manifest.
- **MISMATCHES in brief §3 (stale pre-10x claims, not errors at the time of the 10x plan):**
  1. "One rule (extractor line ~417) blocks the neural custody boost whenever residence_claim
     is true" — STALE. The L417 block was FIXED by 10x Lane 01; current code line 426 comment
     says so, and the custody boost condition (line ~436) has no residence_claim conjunct.
  2. "Pooling reads only the full-question encoding, ignoring per-sentence maxima" — WRONG for
     current code. `_run_laya_probes` computes clause-max pooling (`cmax_p`, `pooled[k] =
     cmax_p`); docstring says "clause-max semantic".
  3. Anchor file attribution: brief says anchors live in `src/laya_v7_evidence.py` (e.g.
     `has_strid_anchor`) — the `has_*_anchor` gating variables are in `src/laya_v7_extractor.py`
     lines ~388–459; evidence.py holds `*_RE` regexes only.
  4. "Hard negatives ~2,050" vs manifest actual 2,100 (hn_a 250 + hn_b 300 + hn_c 350 + hn_d
     300 + hn_e 300 + hn_f 600). Minor, explicitly approximate.
  5. INHERITED inconsistency (NOT Lane 06's error — faithfully copied from `docs/10x_plane.md`
     line 30 and `results/live-laya-v7-results.md` line 29): Fresh-20 FN-by-section list sums
     to 27 but total states 28 FN (one FN unlisted in every source). Category-exact tables
     cover only 18/20 Fresh-20 questions (5 exact of 7) and 4/8 Kannada-8 — partial coverage
     inherited from the plan.
  6. Kanglish example "Nanna ganda hana koduttilla" (§1): generic illustrative phrase, not
     presented as test text; provenance unverifiable, not flagged as sealed text.
- **Match/mismatch:** numbers VERIFIED; §3 needs a brief correction (items 1–3 are the
  substantive ones — the models would be briefed on code that no longer exists).
- **Guardrail:** doc only; no code/corpus touched; no sealed text cited (aggregates only).

## §7 Lane 07 — Evaluation harness (commits `aba4151`, `f9a4fdc`)

- **Claim:** `tests/recall_eval.py` (664 lines at landing, 681 after `--suite kaanoon`); sealed
  guard refuses sealed/test-bank paths (exit 2); expected via Stage 2 applied identically to
  labels and predictions; split size from manifest; Wilson CI from `tests/v7_backtest.py`;
  self-test "15 checks PASS"; baseline (OLD corpus, commit 2633a58) exact **173/500 = 34.6%**,
  Wilson [0.3056, 0.3887], micro P/R/F1 0.8498/0.3389/0.4846, TP/FP/FN 345/61/673, silent 263;
  per-language en 129/228 (0.566), kn 23/153 (0.150), kn_roman 21/119 (0.176); per-issue
  procedure 9/13 best, dv_compensation 0/12 and restitution 0/12 worst; per-cluster hn_f
  52/76 best, conflict 0/7, hn_b 2/34 worst; failure tags silent 263 / exact 173 /
  missing_only 27 / extra_only 20 / missing_and_extra 12 / empty_expected_nonempty_pred 5;
  top missing bnss-144 149, pwdva-20 95, pwdva-17/19 73 each, pwdva-18 44; top extra
  pwdva-20 25, welfare/gwa/hmga 8 each, bnss-144 6; wall 0.61s; R6 Kaanoon baseline pending
  Lane 11.
- **Re-run result:**
  - Baseline reproduced EXACTLY by me three times (two independent re-runs + Lane 10's own
    `/tmp/lane10_recall_eval_verify.json`, rows identical to baseline except wall time
    0.581s vs 0.608s). Independent recomputation from the baseline JSON rows: every aggregate
    recomputed exactly (exact, TP/FP/FN, silent, tags, per-language, per-cluster, Wilson CI
    via independent formula, micro P/R/F1); 0 internally inconsistent rows; 500 unique ids
    SYN-VA-0001..0500; failures file 327 rows = 500−173; split metadata n_manifest 500 =
    n_scored 500, seed 7102, 0 skipped lines; commit field 2633a58 ✓.
  - Third re-run (current tree, after Lane 08): still 173/500, all scored fields identical —
    Lane 08's changes did not move any validation prediction on the old split.
  - **HARNESS BUG (see §HEADLINE-1):** `predict_sections_from_stage1` passes raw M/F/U enums
    into `evaluate_stage2_v7`. Quantified on the OLD split: 10 records differ (all
    male-claimant); re-scoring baseline predicted sets against mapped expected gives
    **179/500 (35.8%)**, silent 263 → 257. Baseline understated by 6 records (+1.2pp).
    Lane 01's independent mapped oracle (179/500) confirms this from a different code path.
  - **"15 checks PASS" self-test claim — WRONG on both versions measured:** committed aba4151
    version runs 12 PASS lines (13 check() call sites, 12 executions: 8 single + guard loop
    ×3 + length-mismatch ×1); current version (with kaanoon checks) runs 21 PASS lines
    (24 call sites). "15" matches neither. Self-test itself PASSES (0 failures) on every run.
  - `--suite kaanoon` exit code verified as 3 with loud PENDING message when the file is
    absent; scores once it exists (see §10).
  - Status-file staleness (minor): "Lane 04 has not yet confirmed the shared signature" was
    already false when written (Lane 04's code confirmed it; see §4).
- **Match/mismatch:** baseline numbers VERIFIED exactly; self-test count claim WRONG (12 / 21,
  not 15); harness sex-mapping bug CONFIRMED and quantified (corrected old-split baseline
  179/500). The harness is the measurement instrument for the whole swarm — the mapping fix
  is the single most important follow-up.
- **Guardrail:** sealed guard verified working (3 refusal cases in self-test, exit 2).
  Harness reads only the validation split + manifest; never touches sealed files.

## §8 Lane 08 — Stage 1 routes audit (commits `b9cd21c`, `4c464d6`, `69936e1`)

- **Claim:** neural routes restit_p/dvcomp_p (`LAYA_NOUL_PROMPTS` 9 → 11, thresholds 0.55/0.45,
  explicitly UNCALIBRATED); post-order split facts (`arrears_recovery_asked`,
  `maintenance_variation_asked`, all modes); graph adds bnss-144-3/bnss-146 to
  MAGISTRATE_SECTIONS + forum authority + `maintenance:post-order-enforcement` Layer A branch
  + conditional (§1b) dispositions in `evaluate_stage2_v7` (deliberately conditional, NOT
  eligible — prose has no templates; kept ids unchanged by design); "2 statutory sections with
  no route before (bnss-144-3, bnss-146)"; "hma-9/pwdva-22 already had full evidence→Stage 2
  routes"; "16 proc/doc sections have no kept-emission route by design (zero references in
  src/ or tests/ outside graph JSON)"; "4 sections with no tests/test_v7_rules.py case (hma-26,
  births-deaths-act-1969, bnss-144-3, bnss-146)"; "test_v7_rules.py 10/10 OK; test_laya_family.py
  OK"; ad-hoc probes (arrears → bnss-144-3 in candidates, kept unchanged; variation ×3 →
  bnss-146 in candidates; Layer A drops exactly the non-asked sub-route); 16-Q 14/16 before
  and after; audit doc `docs/recall_stage1_routes_audit.md` (§5 notes the Kaanoon patterns
  doc had not landed when written; held-out eval set never opened or used, R6).
- **Re-run result:**
  - Code verified by diff read: prompts 9 → 11 with the stated thresholds and UNCALIBRATED
    comments ✓; `_post_order_split_facts()` emits both facts with the stated regexes ✓;
    graph additions (MAGISTRATE_SECTIONS, forum authority, Layer A branch, conditional
    dispositions) present ✓. Kaanoon-derived phrasings cited are generic question phrasings
    ("court ordered maintenance but he is not paying", "amount is not enough, prices gone
    up, increase it") — NOT lawyer answers ✓.
  - Scope respected: extractor.py + graph.py only; evidence.py untouched (R3) ✓.
  - 16-Q before/after 14/16, rating 7.6, same misses H6/H14, 0 FP: my independent re-runs
    give 14/16 both before (baseline) and after Lane 08 — **verified, no regression**.
    Required suites PASS after the changes (graph 7/7, prose 246/15/15) ✓.
  - **NOT yet verified (Lane 08's remaining claims):** the "2 sections with no route before"
    and "hma-9/pwdva-22 already had routes" claims; the "16 proc/doc sections, zero
    references" grep; the "4 sections with no test_v7_rules.py case" grep; the
    `test_v7_rules.py` 10/10 and `test_laya_family.py` runs; the ad-hoc bnss-144-3/bnss-146
    probes; full read of `docs/recall_stage1_routes_audit.md` §4/§5/§6. These need the
    grep/test/probe runs — they were still open when this file was written. (The full unit
    suite Ran 49 tests — OK, which includes test_v7_rules, was re-run by me at final HEAD,
    but the per-file 10/10 claim was not isolated.)
- **Match/mismatch:** code + 16-Q + scope VERIFIED. The audit's enumeration/probe claims are
  UNVERIFIED at write time — flagged here, not marked verified.
- **Guardrail:** no sealed text cited; Kaanoon heldout never opened (stated, consistent with
  the file landing after the audit was written).

## §9 Lane 10 — Docs/merge tracker (commits `81dbc5a`, `2633a58`, `c741579`, `f66ec89`)

- **Claim:** tracker `docs/recall_status.md`, merged view `docs/recall_swarm_state/merged.md`,
  `PUSH-MANIFEST-RECALL.md`; graph/prose pass lines; full unit suite 49 tests OK; corpus
  counts; 16-Q numbers; Lane 10's own re-run file `/tmp/lane10_recall_eval_verify.json`
  (rows identical to baseline); "docs/recall_swarm_state.md is UNTRACKED"; Kaanoon.com §8
  (title + testimonials); Lane 07 MERGED (aba4151), baseline 173/500 = 34.6%, "2 of 11 status
  files landed"; last updated ~19:55 IST (update 4).
- **Re-run result:**
  - Graph/prose/unit-suite lines match my runs (counts identical; prose timing varies run to
    run — timing-only variance) ✓. Corpus counts match ✓. 16-Q numbers match my re-runs ✓.
    Lane 10's `/tmp/lane10_recall_eval_verify.json` exists and its rows are identical to the
    baseline JSON ✓. Shared-state file UNTRACKED ✓. Kaanoon.com §8 verified by my own
    page-text fetch of https://www.kaanoon.com/ (2026-11-27): title "Legal answers online
    from lawyers - Indian Kaanoon" + user testimonials — matches ✓.
  - **MISMATCHES:**
    1. `merged.md` (update 4, ~19:55 IST) is internally contradictory: new summary lines say
       Lane 07 MERGED (aba4151), baseline 173/500, 2 of 11 status files landed — but stale
       lines remain in the same file: "Commits on top of recall baseline 1cb0bff: 0 (this file
       + docs/recall_status.md + PUSH-MANIFEST-RECALL.md are Lane 10's first commit, pending)"
       and "Current held-out validation exact number: NONE YET — Lane 07's harness does not
       exist yet". True commit count on top of 1cb0bff was 5+ by then (now 15+).
    2. Tracker repeats Lane 07's "self-test 15/15 PASS" — measured 12 on the committed
       version, 21 on the current version (see §7).
    3. Tracker says `lane-07-harness.md` is 150 lines — actual file is 165 lines.
    4. Minor timestamp inconsistency: tracker "Last updated ~19:30 IST" vs file mtime
       19:21:50 IST (first version). Cosmetic.
    5. Tracker §8 contribution log said Lane 08 "none yet — no status file landed" — accurate
       as worded at the time, now stale since Lane 08 merged (69936e1).
    6. **Tracker now materially stale (final check):** still lists Lane 01/02/03 as "pending —
       no status file landed" and Lane 11 as "NOT BUILT YET — neither file exists", while
       Lane 01 and Lane 02 status files have landed, Lane 02 is committed (de52ad4), Lane 03
       has 3 commits, and Lane 11 is committed (410d65b) with both files built. "1 of 11 lanes
       merged" is now wrong (07, 08, 04, 05, 11, 02, 03 all have commits; 8 status files
       landed: 01, 02, 04, 05, 06, 07, 08, 11).
- **Match/mismatch:** everything Lane 10 verified at write time was accurate; the file is now
  STALE and internally contradictory. Needs a refresh (update 5), not a fact correction.
- **Guardrail:** tracker files only; no code/corpus touched by Lane 10.

## §10 Lane 11 — Kaanoon eval set + study sample (commit `410d65b`)

Task checks from the coordinator (user voice call 2026-11-27 ~19:23 IST, blanket permission,
DO BOTH): (1) blind re-label spot-check of GT annotations; (2) study/eval split disjointness
+ no Kaanoon question text in the training corpus; (3) no Kaanoon lawyers' answers reproduced
anywhere in the repo.

- **Claim:** `data/kaanoon_eval/heldout.jsonl` 28 items + `data/kaanoon_eval/study_sample.jsonl`
  16 items + `data/kaanoon_eval/build_heldout.py` (450 lines) + `check_disjoint.py` +
  `leakage_report.json` + `README.md` + `docs/kaanoon_phrasing_patterns.md` + status file
  `lane-11-kaanoon.md`; eval categories custody 5, maintenance 5, divorce 5, stridhan 2,
  eviction 3, restitution 4, joint_property 2, violence 2; all en (28/28); 7 items with
  expected_sections == []; E14 Hinglish (lang 'en' with flagged note); study categories
  stridhan 2, eviction 2, maintenance 3, divorce 1, custody 2, joint_property 1, violence 3,
  restitution 1, other (dowry) 1; check_disjoint exit-0 PASS; E04 removed after first check
  FAILED check A (18 shared 8-grams, moved to study as KAN-S16); "9 public web searches + 5
  page-text fetches"; two answer-only pages (497240, 497670) excluded, not reconstructed;
  build exit 0; graph/prose PASS lines.
- **Check 1 — blind re-label spot-check (VERIFIED with analysis):**
  Sample: every 3rd item (E01, E04, E07, E10, E13, E16, E19, E22, E25, E28). Labels formed
  from the question texts only, before comparing. (E04 was removed from the file afterwards,
  so the scored sample is 9 items.)
  - My labels: E01 custody requested/divorce incidental, custody_claim+child_fact+
    proceeding_pending_hma supported, expected {gwa-1890, hmga-1956-s6, welfare-principle};
    E07 maintenance+divorce requested, expected {bnss-144, hma-13}; E10 maintenance requested,
    expected {bnss-144}; E13 divorce requested, expected {hma-13b, hma-25}; E16 no requested,
    judicial_separation_only supported, expected {}; E19 residence+maintenance+joint_property
    requested, expected {bnss-144, pwdva-17/18/19, hma-27}; E22 restitution requested/custody
    incidental, expected {hma-9, gwa-1890, hmga-1956-s6, welfare-principle}; E25 restitution
    requested, restitution_asked supported, expected {hma-9}; E28 violence requested, expected
    {pwdva-18}.
  - Agreement vs Lane 11: expected-section agreement **4/9** (E13, E16, E22, E28).
    Issues-requested agreement 5/9 counting E16 (both empty). Facts-supported agreement on
    nearly all facts I marked.
  - The 5 expected disagreements decompose as: **1 graph-rule miss on my side** (E01: Lane 11's
    hma-26, not my gwa-1890 — their note explains the pending HMA proceeding routes custody
    to hma-26; the mapped graph derivation confirms their version); **4 asker-perspective
    convention differences** (E07, E10, E19, E25: Lane 11 annotates from the asker's
    perspective — a male asker asking about maintenance he must pay, evicting his wife, or
    resisting a restitution complaint does not "request" that relief himself, so expected is
    reduced/empty; my labels assumed the underlying legal issue). All four are documented in
    Lane 11's annotation_notes and are consistent with the graph when sex is mapped correctly.
    E25 specifically: Lane 11 marks restitution_asked DENIED (wife resisting husband's
    complaint), expected []; I had marked it supported.
  - E04 (removed item): my blind label had agreed with Lane 11's original annotation (custody
    requested, expected {gwa-1890, hmga-1956-s6, welfare-principle}).
  - **Decisive derivation check:** importing Lane 11's own `validate_expected` from
    `build_heldout.py` and running it on the current 28-item file → **0 mismatches** — every
    expected_sections list matches live `evaluate_stage2_v7` (with the M/F/U →
    male/female/unknown mapping) exactly. My initial unmapped derivation showed 5 mismatches
    (E07, E10, E19, E20, E29) — that was MY error (same sex-mapping bug as the harness), not
    Lane 11's. **Verdict: Lane 11's GT is mechanically consistent with the live graph.**
  - No item I could not verify: all 9 sampled items were checkable from their texts + the
    graph. (The asker-perspective convention is a modelling choice, not a verification failure
    — but it IS a live tension: the pipeline predicts [bnss-144, pwdva-20] on E10 and [hma-13]
    on E19 against expected [], so asker-perspective GT will systematically count
    pipeline-correct-by-issue answers as wrong on those items. Coordinator call: keep the
    convention and accept the penalty, or annotate both asker and issue perspectives.)
- **Check 2 — disjointness + training-corpus leakage (VERIFIED, with staleness note):**
  Re-ran `python3 data/kaanoon_eval/check_disjoint.py` myself → **PASS, exit 0**: eval=28,
  study=16, train=7500, validation=500; A eval vs train+val shared 8-grams = 0; B eval vs
  study shared 8-grams = 0, shared questions = 0, shared ids = 0; D max cosine eval vs
  train+val = (0.6425, KAN-E03, SYN-TR-2993) < 0.90; D eval vs study = (0.6454, KAN-E27,
  KAN-S05). C study vs train+val (info only) = 20 shared 8-grams.
  - Discrepancy vs Lane 11's `leakage_report.json` (written 14:00:37): report says C = 18 and
    D eval-vs-train = (0.6614, KAN-E17, SYN-TR-7085); my re-run says C = 20 and D = (0.6425,
    KAN-E03, SYN-TR-2993). A, B, D-eval-vs-study match. Likely cause: Lane 02's train.jsonl
    changed between Lane 11's run and mine (corpus rebuild ongoing, uncommitted at the time).
    Both versions PASS all gates (A=0, D<0.9). **The on-disk leakage_report.json is STALE
    relative to the current train file — flag it; re-run check_disjoint.py after the next
    corpus change and refresh the report.**
  - E04 removal explained (README.md:81, lane-11-kaanoon.md:74): first check run FAILED check A
    (18 shared 8-grams, all from then-KAN-E04: generic 8-grams "i want to live separately
    from my husband" / "want to live separately from my husband with", shared with 9 train
    records). The item was removed from eval and moved to the study sample as KAN-S16 (hence
    check C = 18 in Lane 11's report, info only). After the move, A = 0. The build script's
    EVAL specs no longer contain KAN-E04 (grep: 0 hits; 44 `dict(id=` specs = 28 eval + 16
    study) ✓.
- **Check 3 — no lawyer answers reproduced (VERIFIED as far as checkable):**
  Heldout/study records have NO answer field (keys verified: heldout has annotation_notes,
  category, enums, expected_sections, facts, id, issues, lang, source_url, text; study has
  category, id, note, source_url, text). `grep -rni "answer" data/kaanoon_eval/` hits are only
  the docstring statement "lawyers' answers were never copied", an E06 note saying "the
  expected list is the graph-derived answer" (about expected sections, not a lawyer's answer),
  and a README line about answer-only pages excluded. No lawyer answer text found anywhere in
  the repo files I checked.
- **Other Lane 11 claims verified:** file list complete (all 7 files exist, including
  `docs/kaanoon_phrasing_patterns.md` which landed after my first check); per-category counts
  verified exactly (eval + study); 7 empty-expected items verified by count (E10, E11, E16,
  E19, E21, E25, E27); E14 Hinglish note verified; all 28 eval + 16 study items have a
  kaanoon.com source_url ✓; each eval record has all 11 issues + 28 facts + enums +
  expected_sections + annotation_notes + source_url + text + category + lang ✓.
  Patterns doc verified mechanically: 0 shared 8-grams between the doc text and the eval
  questions (claimed 0 ✓); all 16 study IDs S01–S16 cited, 0 eval IDs cited (KAN-E: none) ✓;
  sampled fragments trace to study items only ("I want to live separately from my husband
  with my 2.5 yrs old son." → KAN-S16; "I agreed to pay 14 lakh final settlement amount" →
  KAN-S07; "his husband is habitual drinker and beats her regularly" → KAN-S11; none in eval) ✓.
  Build exit-0 claim NOT independently re-run by me (running `build_heldout.py` would rewrite
  Lane 11's files — I used the imported `validate_expected` instead: 0 mismatches).
  "9 web searches + 5 page-text fetches" and the 497240/497670 exclusion — not independently
  verifiable by me. Test/graph/prose PASS lines match my runs (timing variance only).
  Lane 11 correctly did NOT run/score the Kaanoon eval itself (status file says so).
- **Kaanoon baseline (measured by ME, the verifier, via Lane 07's harness, commit 410d65b):**
  `python3 tests/recall_eval.py --suite kaanoon` → **12/28 (42.9%)**, Wilson 95% CI
  [0.2651, 0.6093], micro P/R/F1 0.6757/0.5556/0.6098, TP/FP/FN 25/12/20, silent 7
  (expected non-empty, predicted empty). Per-category: custody 3/5 (0.600), divorce 2/5
  (0.400), eviction 0/3 (0.000), joint_property 1/2 (0.500), maintenance 2/5 (0.400),
  restitution 1/4 (0.250), stridhan 1/2 (0.500), violence 2/2 (1.000). Failure tags:
  exact 12, missing_only 3, silent 7, extra_only 1, empty_expected_nonempty_pred 3,
  missing_and_extra 2. Top missing: welfare-principle/gwa-1890/hmga-1956-s6/hma-13/hma-9
  3 each, hma-25 2. Top extra: pwdva-20 3, bnss-144/pwdva-19/pwdva-17/pwdva-18 2 each.
  Header confirms "expected explicit 28 / derived 0", so the sex-mapping bug does NOT affect
  this number. Misses worth noting: E10 pred [bnss-144, pwdva-20] vs expected [] and E19
  pred [hma-13] vs expected [] — pipeline-vs-GT tension on the asker-perspective items
  (E10 note already flags it as a graph-behaviour finding). Lane 07 should record this as
  the official Kaanoon baseline in its status file (it was measured by the verifier, not
  by Lane 07). Wilson CI for 12/28 re-checked with the independent formula: [0.2651, 0.6093] ✓.
- **Match/mismatch:** VERIFIED in depth (blind spot-check + derivation 0 mismatches +
  disjointness PASS + no lawyer answers + patterns doc mechanics + baseline measured).
  Two flags: (1) on-disk leakage_report.json STALE (C/D numbers moved with the train file);
  (2) asker-perspective convention creates systematic pipeline-vs-GT tension on E10/E19-type
  items (coordinator decision, not a Lane 11 error).
- **Guardrail:** R6 respected (evaluation only; Lane 11 did not score it; no lane tuned
  against it — Lane 02's §5 reconciliation used only the patterns file, R7, and states the
  heldout was never opened). No sealed files involved. No lawyer answers copied.

## §11 Numbers table (all baselines, with pins — quote with the sha)

| Number | Value | Pin / source |
|---|---|---|
| 16-Q evidence-mode | 14/16, esc_bool 16/16, esc_kinds 10/16, fp 0, rating 7.6 | re-run by Lane 09 before/after Lane 08 and after Lane 03; identical |
| Sealed Fresh-20 | 7/20 (35%) | logged aggregate, `results/live-laya-v7-results.md` |
| Sealed Kannada-8 | 4/8 (50%) | logged aggregate |
| Synthetic validation, OLD corpus (5,000) | harness prints 173/500 (34.6%); **corrected 179/500 (35.8%)** | old validation file (git HEAD), harness baseline commit 2633a58; corrected via mapped oracle (Lane 09 + Lane 01 v1 agree) |
| Synthetic validation, OLD corpus, CURRENT code | **221/500 (44.2%)** mapped oracle | Lane 01 diag script re-run by Lane 09 on git-HEAD validation + current code (Lane 03 + Lane 08 changes) |
| Synthetic validation, NEW corpus (8,000), FROZEN split | harness prints 196/500 (39.2%); **corrected 204/500 (40.8%)** | validation sha `7640d067…`, manifest frozen; measured by Lane 09 at HEAD 58d950c; corrected via mapped re-score (+8 records) |
| Kaanoon real-phrasing eval | **12/28 (42.9%)**, Wilson [0.2651, 0.6093] | measured by Lane 09 via Lane 07 harness, commit 410d65b; expected explicit, sex-bug-free |
| Leakage gate, new corpus | PASS, 0 8-grams, max cosine 0.8269 | re-run by Lane 09, exit 0; matches Lane 02 §6 line for line |
| Kaanoon disjointness | PASS (A=0, B=0, D 0.6425/0.6454 < 0.9) | re-run by Lane 09; Lane 11's on-disk report stale (C 18→20, D 0.6614→0.6425) |
| Graph / prose / unit suite | PASS / PASS / 49 OK | final HEAD de52ad4 |

**Do NOT compare 173/500 with 196/500 or 204/500 as progress:** different validation files
AND different code. The only like-for-like code comparison on one file is Lane 01's 179/500
(old code, old split) vs my 221/500 re-run (current code, old split) — +42 records from the
Lane 03 + Lane 08 changes. The only official forward baseline is the frozen split:
196/500 as printed (204/500 corrected) at the current tree.

## §12 Open / unverifiable items (for the coordinator)

1. **Harness sex-mapping fix (Lane 07)** — the single most important follow-up. Map M/F/U →
   male/female/unknown in `predict_sections_from_stage1` before the next baseline is recorded.
   Corrected baselines: old split 179/500, frozen split 204/500.
2. **Lane 08 enumeration/probe claims** (§8) — still unverified (grep/test/probe runs pending).
3. **Lane 03 residence before/after numbers** (27/40 → 6/30) — unverifiable (denominators
   shifted, no script, no status file). Lane 03 has no status file at all — ask for one.
4. **Lane 01 pinned-file §2–§5 numbers** — unverifiable now (pinned file gone); v1 numbers
   confirmed independently. Record IDs are positional, not content-stable — cite corpus shas.
5. **Lane 05 §4 AFTER numbers** — superseded by Lane 02's rebuild; do not quote.
6. **Lane 04 loader/count claims** — pinned to the OLD 5,000-record corpus; re-run
   `--check-data-only` against the 8,000-record corpus.
7. **Lane 06 brief §3** — needs correction (L417 custody block, pooling, anchor attribution)
   before the models are briefed on it.
8. **Lane 10 tracker + merged.md** — needs update 5 (stale + internally contradictory).
9. **Lane 11 leakage_report.json** — stale vs current train file; re-run check_disjoint.py
   after the next corpus change.
10. **Asker-perspective convention (Kaanoon GT)** — coordinator decision: keep it (accepts
    systematic penalty on E10/E19-type items) or annotate both perspectives.
11. **Sealed leakage check** — still QUEUED (no sealed hash index exists); corpus is cleared
    on readable refs only. Sealed re-run stays RTX-only. No 70% claim is made anywhere in
    this file.
12. **Lane 03's two still-open defects** — mutual-consent false-fire ("will not agree to a
    mutual divorce") and child-only miss ("money only for the child's school fees") — verified
    end-to-end on the extractor at HEAD de52ad4.
