# Live Laya inference test — Colab run v3-empty5 (Laya 421M + v2 graph)

## Aggregate (live, measured in Colab)

- **notebook_version**: v3-empty5 (clause-split + aux prompts + per-issue thresholds + R1 residence + HMA25 gate + court fallback + typed escalations)
- **system**: Laya 421M (classic ModernBERT checkpoint) + v2 two-stage graph, LIVE in Colab
- **loader**: {'loader_used': 'laya.load(local PIXMELT snapshot dir)', 'load_seconds': 28.9, 'errors_before_success': {}}
- **n_questions**: 16
- **exact_section_set_match**: 5/16
- **mean_precision**: 0.673
- **mean_recall**: 0.866
- **micro_precision**: 0.671
- **micro_recall**: 0.895
- **micro_tp_fp_fn**: [51, 25, 6]
- **empty5_exact**: 3/5
- **empty5_court_correct**: 4/5
- **empty5_escalates_correct**: 4/5
- **forbidden_before_recheck_total**: 0
- **forbidden_after_recheck_total**: 0
- **forbidden_proposed_before_gate_total**: 0
- **gated_out_total**: 13
- **gated_out_layerB_total**: 0
- **court_correct**: 11/16
- **court_from_kept_correct**: 11/16
- **escalates_correct**: 14/16
- **escalates_correct_any_typed_diagnostic**: 14/16
- **escalates_correct_bool_plain_diagnostic**: 14/16
- **questions_with_model_error**: 0
- **h2_residence_fired**: True
- **h2_pwdva_17_18_19_kept**: ['pwdva-17', 'pwdva-18', 'pwdva-19']
- **h12_stays_empty**: False
- **residence_fired_r0_count_at_0.15**: 5
- **residence_fired_r1_count**: 11
- **prose_forbidden_mappings**: NOT MEASURED — section classification only, no answer prose generated
- **h7_escalate_ambiguity**: OPEN — H7 escalate_expected=True kept as-is from Cell 6; under typed quantum/court scoring H7 reads escalates=False (no maintenance, kept non-empty, no court fallback). Resolve the expectation before re-scoring.
- **walk_ceiling_reference**: Graph-walk ceiling was 16/16 exact (deterministic walk, NOT live). Do not compare live numbers to it as if it were a baseline.
- **v1_baseline_reference**: v1 live: exact 5/16, mean P/R 0.656/0.492, micro P/R 0.875/0.368, TP/FP/FN 21/3/36, court 10/16, escalates 11/16, forbidden-before-recheck 2.

## Per-question

| ID | Exact | Precision | Recall | Forbidden (before recheck) | Forbidden (proposed before gate) | Court | Escalates | Predicted |
|----|-------|-----------|--------|----------------------------|----------------------------------|-------|-----------|-----------|
| K0 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNS 316, BNSS 144, GWA 1890, HMA 27, HMGA s.6, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20, WELFARE |
| H1 | False | 0.5 | 1.0 | 0 | 0 | False | True | BNS 316, BNSS 144, HMA 27, PWDVA 20 |
| H2 | False | 0.5 | 1.0 | 0 | 0 | False | False | GWA 1890, HMGA s.6, PWDVA 17, PWDVA 18, PWDVA 19, WELFARE |
| H3 | False | 0.333 | 1.0 | 0 | 0 | True | True | BNS 316, BNSS 144, HMA 27, PWDVA 17, PWDVA 19, PWDVA 20 |
| H4 | True | 1.0 | 1.0 | 0 | 0 | True | False | PWDVA 17, PWDVA 18, PWDVA 19 |
| H5 | False | 0.75 | 0.857 | 0 | 0 | True | True | BNSS 144, GWA 1890, HMA 13, HMGA s.6, PWDVA 17, PWDVA 19, PWDVA 20, WELFARE |
| H6 | False | 0.4 | 0.4 | 0 | 0 | False | True | BNSS 144, GWA 1890, HMGA s.6, PWDVA 20, WELFARE |
| H7 | False | 0.333 | 1.0 | 0 | 0 | False | True | Births and Deaths Act 1969, BNSS 144, PWDVA 20 |
| H8 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, PWDVA 20 |
| H9 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, PWDVA 20 |
| H10 | False | 0.571 | 1.0 | 0 | 0 | True | True | BNS 316, BNSS 144, HMA 27, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 |
| H11 | True | 1.0 | 1.0 | 0 | 0 | True | True | BNSS 144, PWDVA 20 |
| H12 | False | 0.0 | 0.0 | 0 | 0 | False | True | PWDVA 17, PWDVA 18, PWDVA 19 |
| H13 | False | 1.0 | 0.6 | 0 | 0 | True | True | BNSS 144, PWDVA 18, PWDVA 20 |
| H14 | False | 0.875 | 1.0 | 0 | 0 | True | True | BNSS 144, GWA 1890, HMA 13, HMA 24, HMA 26, HMGA s.6, PWDVA 20, WELFARE |
| H15 | False | 0.5 | 1.0 | 0 | 0 | True | True | BNS 316, BNSS 144, HMA 27, PWDVA 20 |

## Empty-5 detail (H1/H4/H8/H11/H14)

| ID | Exact | Precision | Recall | TP | FP | FN | Court | Escalates | Fired issues |
|----|-------|-----------|--------|----|----|----|-------|-----------|--------------|
| H1 | False | 0.5 | 1.0 | 2 | 2 | 0 | False | True | maintenance, stridhan, residence, divorce |
| H4 | True | 1.0 | 1.0 | 3 | 0 | 0 | True | False | residence, divorce |
| H8 | True | 1.0 | 1.0 | 2 | 0 | 0 | True | True | maintenance |
| H11 | True | 1.0 | 1.0 | 2 | 0 | 0 | True | True | maintenance, divorce |
| H14 | False | 0.875 | 1.0 | 7 | 1 | 0 | True | True | maintenance, custody, residence, divorce |

## Residence R0 vs R1

| ID | R0 full | R1 full | R0 clause-max | R1 clause-max | Fired R0 (0.15) | Fired R1 |
|----|---------|---------|---------------|---------------|-----------------|----------|
| K0 | 0.265 | 0.298 | None | 0.7674 | True | True |
| H1 | 0.0968 | 0.1643 | None | 0.0453 | False | True |
| H2 | 0.8247 | 0.1713 | None | 0.8464 | True | True |
| H3 | 0.057 | 0.1899 | None | 0.1727 | False | True |
| H4 | 0.1267 | 0.8789 | None | 0.1254 | False | True |
| H5 | 0.4882 | 0.1291 | None | 0.3523 | True | True |
| H6 | 0.2173 | 0.6272 | None | 0.282 | True | True |
| H7 | 0.0001 | 0.0 | None | 0.1307 | False | False |
| H8 | 0.1008 | 0.1344 | None | 0.1008 | False | False |
| H9 | 0.0608 | 0.0626 | None | 0.0608 | False | False |
| H10 | 0.1461 | 0.2719 | None | 0.1067 | False | True |
| H11 | 0.0555 | 0.0006 | None | 0.0555 | False | False |
| H12 | 0.0468 | 0.1244 | None | 0.2177 | False | True |
| H13 | 0.4212 | 0.1924 | None | 0.4212 | True | True |
| H14 | 0.1225 | 0.5167 | None | 0.155 | False | True |
| H15 | 0.067 | 0.0681 | None | 0.0712 | False | False |

H2 check: residence fired=True, PWDVA 17/18/19 kept=['pwdva-17', 'pwdva-18', 'pwdva-19'].
H12 check: stays empty=False.

Escalates are scored from the typed quantum/court flag, not from bool(escalations) — see Cell 8 header.
H7 escalate ambiguity is OPEN (see aggregate).
Forbidden-after-recheck is 0 by construction when Stage 2 ran (Stage 2 drops those sections); quote forbidden-before-recheck / forbidden-proposed-before-gate as the live error counts.
Prose-level forbidden mappings (Rajnesh / Satish / tenancy label) are NOT MEASURED here.
