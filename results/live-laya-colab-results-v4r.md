# Live Laya inference test — Colab run v4r-residence-only (Laya 421M + v2 graph)

## Aggregate (live, measured in Colab)

- **notebook_version**: v4r-residence-only (R0 residence + residence_claim fact gate + residence full set 17/18/19; v3 thresholds M 0.10 / C 0.20 / R 0.15 / D-asked 0.45 / D-pend 0.12)
- **system**: Laya 421M (classic ModernBERT checkpoint) + v2 two-stage graph, LIVE in Colab
- **loader**: {'loader_used': 'laya.load(local PIXMELT snapshot dir)', 'load_seconds': 29.0, 'errors_before_success': {}}
- **n_questions**: 16
- **exact_section_set_match**: 10/16
- **mean_precision**: 0.833
- **mean_recall**: 1.0
- **micro_precision**: 0.826
- **micro_recall**: 1.0
- **micro_tp_fp_fn**: [57, 12, 0]
- **empty5_exact**: 3/5
- **empty5_court_correct**: 4/5
- **empty5_escalates_correct**: 4/5
- **forbidden_before_recheck_total**: 0
- **forbidden_after_recheck_total**: 0
- **forbidden_proposed_before_gate_total**: 0
- **gated_out_total**: 25
- **gated_out_layerB_total**: 0
- **court_correct**: 13/16
- **court_from_kept_correct**: 13/16
- **escalates_correct**: 14/16
- **escalates_correct_any_typed_diagnostic**: 14/16
- **escalates_correct_bool_plain_diagnostic**: 14/16
- **questions_with_model_error**: 0
- **h2_residence_fired**: False
- **h2_pwdva_17_18_19_kept**: []
- **h12_stays_empty**: True
- **residence_fired_r0_count_at_0.15**: 10
- **residence_fired_r1_count_at_0.15_diagnostic**: 11
- **residence_fired_count**: 4
- **residence_gated_count**: 12
- **prose_forbidden_mappings**: NOT MEASURED — section classification only, no answer prose generated
- **h7_escalate_ambiguity**: OPEN — H7 escalate_expected=True kept as-is from Cell 6; under typed quantum/court scoring H7 reads escalates=False (no maintenance, kept non-empty, no court fallback). Resolve the expectation before re-scoring.
- **walk_ceiling_reference**: Graph-walk ceiling was 16/16 exact (deterministic walk, NOT live). Do not compare live numbers to it as if it were a baseline.
- **v1_baseline_reference**: v1 live: exact 5/16, mean P/R 0.656/0.492, micro P/R 0.875/0.368, TP/FP/FN 21/3/36, court 10/16, escalates 11/16, forbidden-before-recheck 2.
- **v3_baseline_reference**: v3 live: exact 5/16, mean P/R 0.673/0.866, micro P/R 0.671/0.895, TP/FP/FN 51/25/6, court 11/16, escalates 14/16, residence fired R1 11/16 vs R0 5/16.

## Per-question

| ID | Exact | Precision | Recall | Forbidden (before recheck) | Forbidden (proposed before gate) | Court | Escalates | Predicted |
|----|-------|-----------|--------|----------------------------|----------------------------------|-------|-----------|-----------|
| K0 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNS 316, BNSS 144, GWA 1890, HMA 27, HMGA s.6, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20, WELFARE |
| H1 | False | 0.5 | 1.0 | 0 | 0 | False | True | BNS 316, BNSS 144, HMA 27, PWDVA 20 |
| H2 | True | 1.0 | 1.0 | 0 | 0 | True | False | GWA 1890, HMGA s.6, WELFARE |
| H3 | False | 0.5 | 1.0 | 0 | 0 | True | True | BNS 316, BNSS 144, HMA 27, PWDVA 20 |
| H4 | True | 1.0 | 1.0 | 0 | 0 | True | False | PWDVA 17, PWDVA 18, PWDVA 19 |
| H5 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, GWA 1890, HMA 13, HMGA s.6, PWDVA 18, PWDVA 20, WELFARE |
| H6 | False | 0.625 | 1.0 | 0 | 0 | False | True | BNSS 144, GWA 1890, HMGA s.6, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20, WELFARE |
| H7 | False | 0.333 | 1.0 | 0 | 0 | False | True | Births and Deaths Act 1969, BNSS 144, PWDVA 20 |
| H8 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, PWDVA 20 |
| H9 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, PWDVA 20 |
| H10 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNS 316, BNSS 144, HMA 27, PWDVA 20 |
| H11 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, PWDVA 20 |
| H12 | True | 1.0 | 1.0 | 0 | 0 | True | True | (none) |
| H13 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 |
| H14 | False | 0.875 | 1.0 | 0 | 0 | True | True | BNSS 144, GWA 1890, HMA 13, HMA 24, HMA 26, HMGA s.6, PWDVA 20, WELFARE |
| H15 | False | 0.5 | 1.0 | 0 | 0 | True | True | BNS 316, BNSS 144, HMA 27, PWDVA 20 |

## Empty-5 detail (H1/H4/H8/H11/H14)

| ID | Exact | Precision | Recall | TP | FP | FN | Court | Escalates | Fired issues |
|----|-------|-----------|--------|----|----|----|-------|-----------|--------------|
| H1 | False | 0.5 | 1.0 | 2 | 2 | 0 | False | True | maintenance, stridhan, divorce |
| H4 | True | 1.0 | 1.0 | 3 | 0 | 0 | True | False | residence, divorce |
| H8 | True | 1.0 | 1.0 | 2 | 0 | 0 | True | True | maintenance |
| H11 | True | 1.0 | 1.0 | 2 | 0 | 0 | True | True | maintenance, divorce |
| H14 | False | 0.875 | 1.0 | 7 | 1 | 0 | True | True | maintenance, custody, divorce |

## Residence R0 vs R1 (v4: R0 fires, fact-gated; R1 diagnostic only)

| ID | R0 full | R1 full | R0 clause-max | R1 clause-max | Aux residence max | R0 final | Residence claim | Gated | Residence fired |
|----|---------|---------|---------------|---------------|-------------------|----------|-----------------|-------|---------------|
| K0 | 0.265 | 0.298 | 0.7674 | 0.3158 | 0.8905 | 0.8905 | True | False | True |
| H1 | 0.0968 | 0.1643 | 0.0453 | 0.114 | 0.0947 | 0.0968 | False | True | False |
| H2 | 0.8247 | 0.1713 | 0.8464 | 0.2538 | 0.3813 | 0.8464 | False | True | False |
| H3 | 0.057 | 0.1899 | 0.1727 | 0.1392 | 0.1285 | 0.1727 | False | True | False |
| H4 | 0.1267 | 0.8789 | 0.1254 | 0.8791 | 0.6474 | 0.6474 | True | False | True |
| H5 | 0.4882 | 0.1291 | 0.3523 | 0.6972 | 0.2143 | 0.4882 | False | True | False |
| H6 | 0.2173 | 0.6272 | 0.282 | 0.7923 | 0.7318 | 0.7318 | True | False | True |
| H7 | 0.0001 | 0.0 | 0.1307 | 0.0958 | 0.0001 | 0.1307 | False | True | False |
| H8 | 0.1008 | 0.1344 | 0.1008 | 0.1344 | 0.1177 | 0.1177 | False | True | False |
| H9 | 0.0608 | 0.0626 | 0.0608 | 0.0626 | 0.0638 | 0.0638 | False | True | False |
| H10 | 0.1461 | 0.2719 | 0.1067 | 0.1506 | 0.1901 | 0.1901 | False | True | False |
| H11 | 0.0555 | 0.0006 | 0.0555 | 0.0006 | 0.0895 | 0.0895 | False | True | False |
| H12 | 0.0468 | 0.1244 | 0.2177 | 0.348 | 0.133 | 0.2177 | False | True | False |
| H13 | 0.4212 | 0.1924 | 0.4212 | 0.1924 | 0.8786 | 0.8786 | True | False | True |
| H14 | 0.1225 | 0.5167 | 0.155 | 0.756 | 0.1021 | 0.155 | False | True | False |
| H15 | 0.067 | 0.0681 | 0.0712 | 0.0831 | 0.0847 | 0.0847 | False | True | False |

H2 check: residence fired=False, PWDVA 17/18/19 kept=[].
H12 check: stays empty=True.

Escalates are scored from the typed quantum/court flag, not from bool(escalations) — see Cell 8 header.
H7 escalate ambiguity is OPEN (see aggregate).
Forbidden-after-recheck is 0 by construction when Stage 2 ran (Stage 2 drops those sections); quote forbidden-before-recheck / forbidden-proposed-before-gate as the live error counts.
Prose-level forbidden mappings (Rajnesh / Satish / tenancy label) are NOT MEASURED here.
