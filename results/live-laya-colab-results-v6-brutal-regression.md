# Live Laya inference test — Colab run v6-brutal regression (Laya 421M + v3 graph)

## Aggregate (live, measured in Colab)

- **notebook_version**: v6-brutal (D1-A corrected GT 53 sections + D2 gate + Lane 2 typed kinds; v3 graph 34/48/79; v3 thresholds M 0.10 / C 0.20 / R 0.15 / D-asked 0.45 / D-pend 0.12)
- **system**: Laya 421M (classic ModernBERT checkpoint) + v2 two-stage graph, LIVE in Colab
- **loader**: {'loader_used': 'laya.load(local PIXMELT snapshot dir)', 'load_seconds': 7.6, 'errors_before_success': {}}
- **n_questions**: 16
- **exact_section_set_match**: 16/16
- **mean_precision**: 1.0
- **mean_recall**: 1.0
- **micro_precision**: 1.0
- **micro_recall**: 1.0
- **micro_tp_fp_fn**: [53, 0, 0]
- **fp_total**: 0
- **fp_by_section**: {}
- **fp_by_issue**: {}
- **empty5_exact**: 5/5
- **empty5_court_correct**: 5/5
- **empty5_escalates_correct**: 5/5
- **forbidden_before_recheck_total**: 0
- **forbidden_after_recheck_total**: 0
- **forbidden_proposed_before_gate_total**: 4
- **gated_out_total**: 72
- **gated_out_layerB_total**: 0
- **court_correct**: 13/16
- **court_from_kept_correct**: 13/16
- **escalates_correct**: 16/16
- **escalates_correct_any_typed_diagnostic**: 16/16
- **escalates_correct_bool_plain_diagnostic**: 16/16
- **escalates_kinds_correct**: 11/16
- **escalates_kinds_correct_fact_excluded**: 11/16
- **escalates_on_empty_kept**: 0
- **gate_formula_rating_raw**: 9.9
- **gate_formula_rating_capped_9.0**: 9.0
- **gate_formula_inputs**: {'E': 1.0, 'Rm': 1.0, 'Pm': 1.0, 'C': 0.812, 'S': 1.0, 'Fb': 0, 'Fp': 'NOT MEASURED'}
- **latency_mean_s**: 0.52
- **latency_max_s**: 1.51
- **latency_total_s**: 8.3
- **latency_load_s**: 7.6
- **g14_check**: {'mean_le_15': True, 'max_le_30': True, 'run_le_240': True, 'load_le_60': True, 'pass': True}
- **questions_with_model_error**: 0
- **h2_residence_fired**: False
- **h2_pwdva_17_18_19_kept**: []
- **h12_stays_empty**: True
- **residence_fired_r0_count_at_0.15**: 9
- **residence_fired_r1_count_at_0.15_diagnostic**: 11
- **residence_fired_count**: 4
- **residence_gated_count**: 12
- **prose_forbidden_mappings**: NOT MEASURED — Cell 9 prose renderer SKIPPED in v6 (see build note); no answer prose generated, Fp not measured, 9.0 cap applies
- **h7_h15_escalate_resolution**: RESOLVED (D3/D4, rater 2026-11-27): H7/H15 escalate_expected kept True; procedure (H7) and recovery (H15) kinds added (Lane 2). D5 rater confirmation of H2/H4 kinds still outstanding.
- **walk_ceiling_reference**: Graph-walk ceiling was 16/16 exact (deterministic walk, NOT live). Do not compare live numbers to it as if it were a baseline.
- **v1_baseline_reference**: v1 live: exact 5/16, mean P/R 0.656/0.492, micro P/R 0.875/0.368, TP/FP/FN 21/3/36, court 10/16, escalates 11/16, forbidden-before-recheck 2.
- **v3_baseline_reference**: v3 live: exact 5/16, mean P/R 0.673/0.866, micro P/R 0.671/0.895, TP/FP/FN 51/25/6, court 11/16, escalates 14/16, residence fired R1 11/16 vs R0 5/16.
- **v4r_baseline_reference**: v4r live: exact 10/16, mean P/R 0.833/1.000, micro P/R 0.826/1.000, TP/FP/FN 57/12/0, court 13/16, escalates 14/16, residence fired 4/16, gated 12/16.

## Per-question

| ID | Exact | Precision | Recall | Forbidden (before recheck) | Forbidden (proposed before gate) | Court | Escalates | Predicted |
|----|-------|-----------|--------|----------------------------|----------------------------------|-------|-----------|-----------|
| K0 | True | 1.0 | 1.0 | 0 | 1 | True | True | BNS 316, BNSS 144, GWA 1890, HMGA s.6, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20, WELFARE |
| H1 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, PWDVA 20 |
| H2 | True | 1.0 | 1.0 | 0 | 0 | True | True | GWA 1890, HMGA s.6, WELFARE |
| H3 | True | 1.0 | 1.0 | 0 | 1 | False | True | BNS 316 |
| H4 | True | 1.0 | 1.0 | 0 | 0 | True | True | PWDVA 17, PWDVA 18, PWDVA 19 |
| H5 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, GWA 1890, HMA 13, HMGA s.6, PWDVA 18, PWDVA 20, WELFARE |
| H6 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 |
| H7 | True | 1.0 | 1.0 | 0 | 0 | True | True | Births and Deaths Act 1969 |
| H8 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, PWDVA 20 |
| H9 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, PWDVA 20 |
| H10 | True | 1.0 | 1.0 | 0 | 1 | False | True | BNS 316, BNSS 144, PWDVA 20 |
| H11 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, PWDVA 20 |
| H12 | True | 1.0 | 1.0 | 0 | 0 | True | True | (none) |
| H13 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 |
| H14 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, HMA 13, HMA 24, HMA 26, HMGA s.6, PWDVA 20, WELFARE |
| H15 | True | 1.0 | 1.0 | 0 | 1 | False | True | BNS 316 |

## Empty-5 detail (H1/H4/H8/H11/H14)

| ID | Exact | Precision | Recall | TP | FP | FN | Court | Escalates | Fired issues |
|----|-------|-----------|--------|----|----|----|-------|-----------|--------------|
| H1 | True | 1.0 | 1.0 | 2 | 0 | 0 | True | True | maintenance, divorce |
| H4 | True | 1.0 | 1.0 | 3 | 0 | 0 | True | True | residence, divorce |
| H8 | True | 1.0 | 1.0 | 2 | 0 | 0 | True | True | maintenance |
| H11 | True | 1.0 | 1.0 | 2 | 0 | 0 | True | True | maintenance, divorce |
| H14 | True | 1.0 | 1.0 | 7 | 0 | 0 | True | True | maintenance, custody, divorce |

## Residence R0 vs R1 (v4: R0 fires, fact-gated; R1 diagnostic only)

| ID | R0 full | R1 full | R0 clause-max | R1 clause-max | Aux residence max | R0 final | Residence claim | Gated | Residence fired |
|----|---------|---------|---------------|---------------|-------------------|----------|-----------------|-------|---------------|

## FP by issue (v5: expect all zero)

- none — zero FPs on the 16.
| K0 | 0.2658 | 0.2774 | 0.7624 | 0.3184 | 0.8916 | 0.8916 | True | False | True |
| H1 | 0.0948 | 0.1582 | 0.0438 | 0.1119 | 0.0926 | 0.0948 | False | True | False |
| H2 | 0.8235 | 0.1694 | 0.8488 | 0.2501 | 0.3724 | 0.8488 | False | True | False |
| H3 | 0.056 | 0.1868 | 0.1718 | 0.1413 | 0.1272 | 0.1718 | False | True | False |
| H4 | 0.1272 | 0.8754 | 0.126 | 0.8715 | 0.6354 | 0.6354 | True | False | True |
| H5 | 0.4892 | 0.1309 | 0.3603 | 0.6983 | 0.2001 | 0.4892 | False | True | False |
| H6 | 0.207 | 0.6214 | 0.2642 | 0.7885 | 0.7373 | 0.7373 | True | False | True |
| H7 | 0.0001 | 0.0 | 0.1312 | 0.0955 | 0.0001 | 0.1312 | False | True | False |
| H8 | 0.0993 | 0.1334 | 0.0993 | 0.1334 | 0.1172 | 0.1172 | False | True | False |
| H9 | 0.0562 | 0.0614 | 0.0562 | 0.0614 | 0.069 | 0.069 | False | True | False |
| H10 | 0.1459 | 0.2673 | 0.1047 | 0.1475 | 0.1888 | 0.1888 | False | True | False |
| H11 | 0.0545 | 0.0005 | 0.0545 | 0.0005 | 0.0884 | 0.0884 | False | True | False |
| H12 | 0.045 | 0.1254 | 0.2164 | 0.3386 | 0.1318 | 0.2164 | False | True | False |
| H13 | 0.4308 | 0.18 | 0.4308 | 0.18 | 0.8797 | 0.8797 | True | False | True |
| H14 | 0.1206 | 0.5118 | 0.1458 | 0.749 | 0.1026 | 0.1458 | False | True | False |
| H15 | 0.0669 | 0.0685 | 0.0701 | 0.0821 | 0.0836 | 0.0836 | False | True | False |

H2 check: residence fired=False, PWDVA 17/18/19 kept=[].
H12 check: stays empty=True.

Escalates are scored BOTH as a boolean (v6 kind set) and as typed-kinds equality (strict + fact-excluded) — see Cell 8 header.
H7/H15 escalate expectations RESOLVED (D3/D4, rater 2026-11-27); procedure/recovery kinds added.
Prose forbidden mappings (Fp) NOT MEASURED in v6 (Cell 9 skipped); the 9.0 cap applies to any rating quoted from this run.
Fresh-20 (sealed) is a MEASURED NUMBER ONLY, not a gate pass, until the G2 20/20 amendment is signed.
Forbidden-after-recheck is 0 by construction when Stage 2 ran (Stage 2 drops those sections); quote forbidden-before-recheck / forbidden-proposed-before-gate as the live error counts.
Prose-level forbidden mappings (Rajnesh / Satish / tenancy label) are NOT MEASURED here.
