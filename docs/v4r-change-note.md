# v4r — residence-only variant (derived from v4 by the coordinator)

## Why v4r exists
The v4 notebook (as specified: residence fix + Lane A PRIMARY thresholds M 0.05 / C 0.13)
was built and validated, but its own change log §5 flags a problem, which the coordinator
verified against the v3 live JSON `stage1_final` values:
- Maintenance at 0.05 newly fires on H2 (0.0820), H4 (0.0844), H12 (0.0824) — all
  non-maintenance questions.
- Custody at 0.13 newly fires on H7 (0.1372), H10 (0.1713), H12 (0.1397) — all
  non-custody questions.
- Predicted v4-as-specified: exact 6/16, micro-F1 0.809, rating ~6.4/10.
- Predicted residence-only (v3 thresholds kept): exact 10/16, micro-F1 0.905, rating ~7.7/10.
Both are PREDICTIONS computed offline from v3 saved scores (newly-fired issues' sub-choice
outcomes were never run live), not results. The live run decides.

## What v4r is
`live-laya-colab-test-v4r-residence-only.ipynb` — byte-identical logic to v4 except:
- THRESHOLDS reverted to v3 values: maintenance 0.10, custody 0.20, residence 0.15,
  stridhan 0.50, violence 0.50, divorce-asked 0.45, divorce-pending 0.12,
  birth_certificate 0.50, in_scope 0.50.
- Version strings / output filenames renamed v4 → v4r
  (`live-laya-colab-results-v4r-residence-only.json/.md`).
- Residence fix UNCHANGED: R0 firing prompt, `residence_claim` fact gate, residence
  full-set PWDVA 17+18+19, HMA 25 gate, court fallback, typed escalations, esc_live patch.
Verified: code-only diff vs v4 is exactly the 4 threshold values + version/filename strings.
nbformat.validate PASS, Cells 7–8 compile PASS.
sha256: `7d67bd53033bb96b0c5a1f99b4c637975fdbdc91911a49c4c3ccd64432e382f5`

## Run order recommendation (for the parent agent)
1. Run **v4r first** (clean single-fix iteration, predicted 10/16). One Colab run, ~16 min.
2. Run **v4** (with PRIMARY thresholds) only if v4r passes and the threshold vector still
   needs testing — its prediction says it will regress, so treat it as a falsification test,
   not the main line.
3. Whichever runs, file both JSON+MD results and log exact/micro-F1/court/escalates.
   If v4r does NOT improve exact and F1 together vs v3 (5/16, 0.767), revert the residence
   fix per the loop rule and consult the models' next proposal.

## Predicted v4r outcome (offline, from v3 scores — NOT a result)
Exact 10/16 (new exact: H2, H5, H10, H12, H13; H6 fixed on FN but custody FPs remain),
TP/FP/FN ~57/12/0, micro-P/R ~0.826/1.000, micro-F1 ~0.905, court ~13/16,
escalates ~15/16, rating ~7.7/10. Remaining after v4r: H1/H3/H7/H15 (Stridhan/maintenance
over-fire), H6 (custody FP), H14 (GWA FP), H4 escalates. Those are v6/v7 work.
