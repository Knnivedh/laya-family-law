# Overnight coordinator log — Laya 10/10 push (2026-11-26 night → 27 Nov morning)

Owner: overnight coordinator subagent. User Nivedh asleep; blanket permission granted until
tomorrow morning — no approvals asked. Parent agent must execute the BROWSER steps
(Colab runs + Gemini/ChatGPT consultations); this subagent cannot operate a live browser.

## Starting state (measured, frozen)

- v3 live Colab 2026-11-26 23:38 IST: exact **5/16** (K0,H4,H8,H9,H11), mean P/R 0.673/0.866,
  micro P/R 0.671/0.895, micro-F1 0.767, TP/FP/FN **51/25/6** of 57 GT, court 11/16,
  escalates 14/16, forbidden-before-gate 0, model errors 0/16, rating **5.9/10** (frozen formula).
  Notebook: https://colab.research.google.com/drive/1vXB7ckTFKhscsHH1zbVdKV13ovGpnntr
- v1 was exact 5/16, F1 0.518, TP/FP/FN 21/3/36. v3 fixed recall (FN 36→6) and broke
  precision (FP 3→25).
- Frozen gate: `laya-10-10-gate-definition.md` (16/16 current + fresh + Kannada 8/8 + prose 0 +
  confirmation re-run). NOTE: gate file says fresh **16**; the overnight task says fresh **20**.
  The sealed set being built is 20 (stricter); record the discrepancy, do not silently edit the gate.
- Prose renderer does not exist → cap 9.0 until built + measured. Latency v3: Cell 7 897.6 s,
  35–123 s/question — a quality failure vs the "fraction of a second" aspiration.

## v3 per-question diagnosis (from the live JSON — the ONLY basis for fixes)

| ID | Exact | TP/FP/FN | FP | FN | Root cause |
|----|-------|----------|----|----|------------|
| K0 | Y | 10/0/0 | — | — | clean |
| H1 | N | 2/2/0 | BNS 316, HMA 27 | — | Stridhan clause-max 0.7545 on "My husband has not given me any money for three months" (money-not-given misread as Stridhan-held); court wrong (extra Family Court) |
| H2 | N | 3/3/0 | PWDVA 17/18/19 | — | Residence R1 clause-max 0.8464 on "take him away" (custody-only Q); court + escalates wrong |
| H3 | N | 2/4/0 | BNSS 144, PWDVA 20, PWDVA 17, PWDVA 19 | — | Maintenance + residence over-fired on pure Stridhan Q (v1 was exact here — v3 REGRESSED H3) |
| H4 | Y | 3/0/0 | — | — | exact sections, but escalates wrong (expected True, live False — residence-only kept, no typed escalation fires) |
| H5 | N | 6/2/1 | PWDVA 17, PWDVA 19 | PWDVA 18 | Residence fired though GT has only PWDVA 18 (via violence); sub-choice split the residence set |
| H6 | N | 2/3/3 | GWA 1890, HMGA s.6, WELFARE | PWDVA 17/18/19 | Custody fired INSTEAD of residence ("stay in the house with my daughter" read as custody); clause-split never split "and to stay in the house" |
| H7 | N | 1/2/0 | BNSS 144, PWDVA 20 | — | Maintenance over-fired on birth-certificate Q; court wrong |
| H8 | Y | 2/0/0 | — | — | clean |
| H9 | Y | 2/0/0 | — | — | clean |
| H10 | N | 4/3/0 | PWDVA 17/18/19 | — | Residence fired on pure gold/Stridhan Q |
| H11 | Y | 2/0/0 | — | — | clean |
| H12 | N | 0/3/0 | PWDVA 17/18/19 | — | Residence fired on out-of-scope ancestral-house Q; GT empty, must stay empty; court wrong |
| H13 | N | 3/0/2 | — | PWDVA 17, PWDVA 19 | Residence fired but sub-choice kept only PWDVA 18 (partial set) |
| H14 | N | 7/1/0 | GWA 1890 | — | Custody sub-choice picked standalone GWA though a divorce proceeding is pending (should be HMA 26 route) |
| H15 | N | 2/2/0 | BNSS 144, PWDVA 20 | — | Maintenance over-fired on "He sold my gold without asking me" |

FP total 25: residence 3×5 questions (H2,H5,H10,H12 = 11 + H3 2 = 13 residence FPs),
maintenance 2×4 questions (H1? no — H1's are Stridhan; maintenance FPs: H3 2, H7 2, H15 2 = 6),
Stridhan 2 (H1), custody 3 (H6) + 1 (H14) = 4. FN total 6: residence partial-set 1 (H5) + 2 (H13),
residence missed 3 (H6). Court wrong: H1,H2,H6,H7,H12. Escalates wrong: H2,H4.

## Iteration plan (one focused fix per run — never bundle)

- **v4 — residence precision + Lane A PRIMARY thresholds** (M 0.05 / C 0.13; R1→R0; residence
  fact gate `residence_claim`; residence full-set 17/18/19). BUILD IN PROGRESS (child lane).
  Predicted (NOT a result): fixes H2/H10/H12 residence FPs (9), H13 FN 17/19 (2), H6 FN 17/18/19 (3),
  H5 FP 17/19 (2) → exact 9/16, TP 56, FP 16, FN 1, micro-F1 ~0.87, rating ~6.9/10. Verify live.
- **v5 — H12 out-of-scope gate + in_scope production gate** (8th `noul` question; empty kept +
  in-scope → ESCALATE + top-2 payload, never `[]`; out-of-scope stays empty).
- **v6 — Stridhan/maintenance cross-fire + custody route**: Stridhan fact gate (gold/property-held
  mention required — kills H1 FP); maintenance must not fire on gold-sale / birth-cert clauses;
  custody sub-choice must honour proceeding_pending (H14 GWA→HMA 26); violence→PWDVA 18 mapping (H5 FN).
- **v7 — H6 custody-vs-residence confusion + clause-split rule fix** (split on "and to stay…";
  custody requires a who-gets-the-child claim, residence a stay-in-house claim).
- **v8 — latency + prose renderer** (template prose, Cell 9, prose forbidden self-check; call-count cuts).
- **v9 — final consolidation** (best verified fixes only, re-run, then sealed + confirmation runs).

RULE per run: if exact AND micro-F1 do not improve together, REVERT that fix and try the models'
next proposal. File every run JSON+MD, failures included. Never change GT to fit the model.
Never tune on the sealed fresh-20 / Kannada-8 (they are written blind; run once after 16/16).

## Open decisions — LEGAL LANE DELIVERED 2026-11-26 ~23:51 IST

File: `legal-decisions-v4.md`. Verdicts (research only, no files changed):
1. **HMA 27: graph prereq CORRECT, GT WRONG** — s.27 is ancillary ("in any proceeding under
   this Act… in the decree"), cannot be a freestanding Stridhan application with no HMA
   proceeding. Recommendation: remove HMA 27 from H3/H10/H15, replace with Family Court suit
   route (Family Courts Act s.7(1) Expl. (c) / CPC s.151, per *Babulal Yadav* FB, 4 July 2023),
   keep BNS 316. ⚠️ GATE IMPACT: changing GT invalidates all prior runs (gate §6 rule 1 —
   GT change needs an independent rater and re-runs). DO NOT apply silently; parent/coordinator
   decision required. Caveat: contrary HP HC decision (*Astha Thakur*, 31 Dec 2025, summary
   only) conflicts — read in full before freezing any GT change.
2. **H7 escalate_expected=True is CORRECT**, but only on a named fact-ask reason (no DOB/age,
   place, registration status → s.13 tier undetermined), never as quantum/income escalation.
3. **Sukhdev Singh v Sukhbir Kaur VERIFIED** — SC, 12 Feb 2025, 3-judge bench, Civil Appeal
   Nos. 2536 & 5726 of 2019, 2025 INSC 197: spouse of void marriage may SEEK s.25 alimony
   ("any decree" includes nullity decree). Does NOT remove s.25's decree requirement — no
   support for "HMA 25 with no decree" fires.

## Sealed sets — DELIVERED + VERIFIED 2026-11-26 ~23:52 IST

Files under `laya-graph/sealed/`: `sealed-fresh-20.json` (F1–F20),
`sealed-kannada-8.json` (KN1–KN8), `sealed-sets-freeze-note.md`.
SHA-256 verified by coordinator: fresh-20 `1d8b5dc376e711c3ac6ead4424bb2d8ce52b07552b9a533ad86e0616dbcf8837`,
Kannada-8 `2f652af1123a22441cc4158ddf480ef0981aa923858bbcb9dc3622f5e5c25853` — match the writer's report.
Blindness held (only `backtest-laya-vs-llama8b.md` read). No-overlap check: zero shared 8-grams
vs the current 16. Composition meets the required table (4/3/3/2/2/2/2/2; 5 multi-issue incl.
1 five-issue F15; decree-passed HMA-25-keep F4; mutual-consent 13B F16; judicial-separation F18).
⚠️ FLAG: F20 (dowry/second marriage) — GT/court empty but escalates True (human-lawyer);
conflicts with the generic "OOS escalates False" rule. Writer followed the F20-specific
instruction and flagged it; scorer must apply the human-lawyer rule, not mark it a failure.
⚠️ FLAG: F4 GT = HMA 25 + BNSS 144 only (PWDVA 20 excluded post-decree, HMA 13 excluded) —
judgement call documented in the freeze note.
DO NOT run the system against these sets until 16/16 on the current set. DO NOT tune on them.

## Prose renderer + latency — DELIVERED 2026-11-26 ~23:53 IST

Files: `prose-renderer-design.md` (Cell 9 spec: deterministic template assembler keyed only
by kept_ids — dropped sections can never appear, zero precedents, zero amounts, zero
"salary slips"/"tenancy rights"; pure-regex self-checker for all 9 forbidden items; Fp metric
+ §2 rating computation) and `latency-analysis.md`. No notebook/builder/graph/results modified.
KEY FINDINGS:
- v3 Cell 7 = **682 `noul` keys per 16-question run** (full pass 160, clause-split 330,
  aux 192; ~1.32 s/key on Colab CPU). K0 highest (72 keys); single-clause questions waste a
  duplicate clause pass (32 keys where the clause IS the full question).
- **v3 FAILS gate row G14** (mean 56.1 s / max 123 s / run 897.6 s vs 15 / 30 / 240 s).
  v1 PASSED G14 (11.77 s mean). The empty-5 recall fix cost ~4.8× latency. Zero-risk trims
  recover only ~25–35% — G14 cannot be restored on CPU by trimming; realistic v8 target is
  a recorded T4 GPU runtime (mean ~8–12 s/question) or report CPU as a G14 failure.
- "Fraction of a second" aspiration is NOT achievable with per-prompt CPU calls — needs a
  single-forward-pass multi-label rebuild, out of scope for v8. Say so honestly in the final report.
- Dead waste: `stage2()` never reads custody/stridhan sub-choice answers (pure-waste predict
  calls — delete them or make Stage 2 read them). H12's first clause is mangled by the splitter
  ("I are fighting…"). Cell 8 does not compute the §2 rating (Cell 9 design closes this).
- One required v8 edit: Cell 7's `fact` escalation text must drop the phrase "salary slips".

## v4 notebook — DELIVERED + VERIFIED, plus v4r variant (2026-11-26 ~23:55 IST)

Files: `build_laya_v4_residence.py`, `live-laya-colab-test-v4-residence.ipynb`
(sha256 `af1d6a5d4749bd1e72389885081cadcc13171ea0e28e16977776f69a56e1a45b`),
`v4-change-log.md`. Validated: nbformat PASS, Cells 7–8 compile PASS, Cells 0–5 identical
to v3, Cell 6 diff exactly +7 header / +16 residence_claim lines, R0 prompt verbatim vs v1,
esc_live patch asserted present. Also fixed in v4 Cell 8: v3's residence table read a
non-existent key (R0 clause-max column always None).
⚠️ FLAG (verified by coordinator from v3 `stage1_final`): the PRIMARY thresholds are
predicted to COST ~4 exact — M 0.05 newly fires maintenance on H2 (0.0820), H4 (0.0844),
H12 (0.0824); C 0.13 newly fires custody on H7 (0.1372), H10 (0.1713), H12 (0.1397).
Predicted v4-as-specified: exact 6/16, F1 0.809, ~6.4/10. Residence-only counterfactual:
exact 10/16, F1 0.905, ~7.7/10. H5's PWDVA 18 IS predicted fixed in v4/v4r (violence→18
path is blocked in v3 only when residence fires — `if 'violence' in fired and 'residence'
not in fired` — and the gate unblocks it), contrary to the original remain-list.
Coordinator built **v4r** (`live-laya-colab-test-v4r-residence-only.ipynb`,
sha256 `7d67bd53033bb96b0c5a1f99b4c637975fdbdc91911a49c4c3ccd64432e382f5`,
note `v4r-change-note.md`): identical logic to v4 except thresholds reverted to v3 values
— code-only diff is exactly the 4 threshold values + version/filename strings, validated.
RECOMMENDED RUN ORDER: v4r first (clean single fix, predicted 10/16), v4 second only as a
falsification test of the threshold vector. Both predictions are offline estimates, not results.
Minor: builder comment mislabels H2's R0 as 0.8464 (that is the R1 clause-max; R0 full is
0.8247) — comment only, no behaviour.

## Lanes status — ALL 4 DONE
1. v4 notebook engineer — DONE (+ coordinator-built v4r variant).
2. Blind sealed-set writer — DONE (fresh-20 + Kannada-8 frozen, checksums verified).
3. Legal researcher — DONE (HMA 27 / H7 / Sukhdev Singh verdicts).
4. Prose renderer + latency analyst — DONE (Cell 9 design + latency analysis; v3 FAILS G14).

## Browser steps needed from the PARENT agent (this subagent cannot do these)

1. **Consult BOTH models per iteration** using `v4-consultation-pack.md` (next file): Gemini
   (Neon, Thinking High) + ChatGPT (GPT-6.2, thinking max). Paste the exact failure numbers.
   Verify their proposals against our own numbers before adopting.
2. **Run each notebook version live in Colab** (user's login nivedhbhat15; upload the versioned
   .ipynb to Drive, run all cells, download results JSON+MD to
   `workspace/browser_downloads/` AND `.../laya-graph/`, file with versioned names).
3. After 16/16 on the current set: run sealed fresh-20 + Kannada-8 ONCE, then confirmation
   re-run with zero code changes. Report sealed numbers separately.
4. Deliver the final honest rating in this side chat by morning with the frozen formula.

## Run log (append per live run)

| Run | Version | Date/time IST | Change | Exact | Micro-F1 | Court | Escalates | TP/FP/FN | Rating | Notes |
|-----|---------|---------------|--------|-------|----------|-------|-----------|----------|--------|-------|
| 0 | v1 | 2026-11-26 22:28 | baseline | 5/16 | 0.518 | 10/16 | 11/16 | 21/3/36 | 3.3 | |
| 1 | v3 | 2026-11-26 23:38 | clause-split+aux+per-issue thr+R1 | 5/16 | 0.767 | 11/16 | 14/16 | 51/25/6 | 5.9 | recall fixed, precision broke |
| 2 | v4 | — | residence precision + PRIMARY thr | — | — | — | — | — | — | pending build + live run |
