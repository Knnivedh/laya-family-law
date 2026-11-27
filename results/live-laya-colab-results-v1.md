# Live Laya inference test — Colab run (Laya 421M + v2 graph)

## Aggregate (live, measured in Colab)

- **system**: Laya 421M (classic ModernBERT checkpoint) + v2 two-stage graph, LIVE in Colab
- **loader**: {'loader_used': 'laya.load(local PIXMELT snapshot dir)', 'load_seconds': 25.8, 'errors_before_success': {}}
- **n_questions**: 16
- **exact_section_set_match**: 5/16
- **mean_precision**: 0.656
- **mean_recall**: 0.492
- **micro_precision**: 0.875
- **micro_recall**: 0.368
- **micro_tp_fp_fn**: [21, 3, 36]
- **forbidden_before_recheck_total**: 2
- **forbidden_after_recheck_total**: 0
- **court_correct**: 10/16
- **escalates_correct**: 11/16
- **questions_with_model_error**: 0
- **prose_forbidden_mappings**: NOT MEASURED — section classification only, no answer prose generated
- **walk_ceiling_reference**: Graph-walk ceiling was 16/16 exact (deterministic walk, NOT live). Do not compare live numbers to it as if it were a baseline.

## Per-question

| ID | Exact | Precision | Recall | Forbidden (before recheck) | Court | Escalates | Predicted |
|----|-------|-----------|--------|----------------------------|-------|-----------|-----------|
| K0 | False | 1.0 | 0.2 | 0 | True | True | BNS 316, HMA 27 |
| H1 | False | 0.0 | 0.0 | 0 | False | False | (none) |
| H2 | False | 0.5 | 1.0 | 0 | False | True | GWA 1890, HMGA s.6, PWDVA 17, PWDVA 18, PWDVA 19, WELFARE |
| H3 | True | 1.0 | 1.0 | 0 | True | True | BNS 316, HMA 27 |
| H4 | False | 0.0 | 0.0 | 0 | False | False | (none) |
| H5 | False | 1.0 | 0.571 | 1 | True | True | BNSS 144, HMA 13, PWDVA 18, PWDVA 20 |
| H6 | False | 1.0 | 0.4 | 0 | True | True | BNSS 144, PWDVA 20 |
| H7 | True | 1.0 | 1.0 | 0 | True | True | Births and Deaths Act 1969 |
| H8 | False | 0.0 | 0.0 | 0 | False | False | (none) |
| H9 | True | 1.0 | 1.0 | 1 | True | True | BNSS 144, PWDVA 20 |
| H10 | False | 1.0 | 0.5 | 0 | True | True | BNS 316, HMA 27 |
| H11 | False | 0.0 | 0.0 | 0 | False | False | (none) |
| H12 | True | 1.0 | 1.0 | 0 | True | True | (none) |
| H13 | False | 1.0 | 0.2 | 0 | True | True | PWDVA 18 |
| H14 | False | 0.0 | 0.0 | 0 | False | False | (none) |
| H15 | True | 1.0 | 1.0 | 0 | True | True | BNS 316, HMA 27 |

Forbidden-after-recheck is 0 by construction when Stage 2 ran (Stage 2 drops those sections); quote forbidden-before-recheck as the live error count.
Prose-level forbidden mappings (Rajnesh / Satish / tenancy label) are NOT MEASURED here.
