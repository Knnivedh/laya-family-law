# HMA 27 re-base — D1 Option A (remove HMA 27 from K0/H3/H10/H15 GT)

**Status: OFFLINE RE-SCORE ONLY. No Colab run, no live model call, no result file changed.**
**Decision:** D1 = Option A, decided by Nivedh 2026-11-27 ~09:46 IST (remove HMA 27 from
K0/H3/H10/H15 ground truth, no replacement; GT 57 → 53). D2 (paired HMA 27 gate) simulated
offline as specified below.
**Date of this re-base:** 2026-11-27. **Author:** re-base lane (subagent, offline).

## 0. Inputs (read only)

- v5 live run 3 JSON:
  `~/workspace/browser_downloads/sess-3450079326/browser-download-20261127T024408.189396223Z-0-live-laya-colab-results-v5-precision.json`
  (filed: exact 16/16, micro P/R 1.000/1.000, TP/FP/FN 57/0/0, court 16/16, escalates 12/16,
  rating 9.8 raw capped 9.0)
- v4r live run 2 JSON:
  `~/workspace/browser_downloads/sess-2184034649/browser-download-20261126T185447.300061282Z-0-live-laya-colab-results-v4r-residence-only.json`
  (filed: exact 10/16, micro P/R 0.826/1.000, micro-F1 0.905, TP/FP/FN 57/12/0, court 13/16,
  escalates 14/16, gate-formula rating 7.3)
- Gate definition `laya-10-10-gate-definition.md` §2 (frozen formula + caps), §6.1 (GT-change
  invalidation); v6 deep-dive `v6-deep-dive-report.md` §4 (D1-A, D2 pairing, v4r 8/16 expectation).
- Notebook source `live-laya-colab-test-v5-precision.ipynb` Cells 6–8 (Cell 6 facts/GT,
  Cell 7 court + typed-escalation rules, Cell 8 scoring) — used only to verify the
  re-derivation rules below, not re-run.

## 1. Method — and the validation that it is correct

All four re-scores were recomputed from the per-question `pred_labels` / `gt_labels` sets in
the filed JSONs (via `raw_live_runs[].kept_ids` / `gt_ids`), never from headline aggregates.

**Validation (must hold before any re-score is trusted):** the same code, run against the
**old GT with recorded predictions, reproduces both filed aggregates exactly** — v4r 10/16,
TP/FP/FN 57/12/0, mean P/R 0.833/1.000, court 13/16, escalates 14/16, rating 7.3; v5 16/16,
57/0/0, mean P/R 1.000/1.000, court 16/16, escalates 12/16, rating 9.8 raw capped 9.0.
It does. Two further rules were verified against the records before being applied to the
re-scores:

- **Court re-derivation.** `court_expected` is the court implied by the GT sections, so under
  corrected GT it must be re-derived, not left frozen. Re-derivation uses the notebook's own
  frozen section→court map (Cell 7 `court_for`: HMA 13/13B/24/25/26/27, GWA 1890, HMGA s.6,
  WELFARE → Family Court; BNSS 144, PWDVA 17/18/19/20, BNS 316 → Magistrate; Births and
  Deaths Act 1969 → Registrar). Under the **old** GT this map reproduces the recorded
  `court_expected` for **all 16 questions in both runs**, and reproduces recorded `court_live`
  from recorded kept sets for all 32 rows. Under corrected GT the only expected courts that
  change are H3, H10, H15 ([Family Court, Magistrate] → [Magistrate] — HMA 27 was their only
  Family Court section); K0 stays [Family Court, Magistrate] via GWA 1890.
- **Escalates re-derivation.** `escalates_live` is recomputed from the notebook's typed-kind
  rules (Cell 7–8): `demand` iff the stridhan issue fired and `demand_made is False`;
  `quantum` iff the maintenance issue fired or a maintenance section is kept
  (BNSS 144 / PWDVA 20 / HMA 24 / HMA 25); `court` only via the fallback when nothing is kept
  *and* the question is in scope; `esc_live = kinds ∩ {quantum, court, demand} ≠ ∅`. This
  reproduces recorded `escalates_live` for **all 32 rows** (16/16 per run). Note the demand
  kind depends on the stridhan issue firing + `demand_made`, **not** on HMA 27 being kept —
  so dropping HMA 27 under D2 does not remove H3/H10's demand escalation (BNS 316 stays kept,
  stridhan still fired). Escalate *expectations* are unchanged by D1 (D3/D4/D5 are separate
  decisions); H7's expectation stays OPEN as filed.

**Rating:** gate §2 frozen formula
`Rating = 10 × [0.60·E + 0.15·Rm + 0.10·Pm + 0.075·C + 0.075·S] − 0.5·Fb − 1.0·Fp`,
clamped [0, 10], rounded to 1 decimal, then §2 caps (lower wins). Fb = 0 in both runs
(HMA 27 is not a forbidden section; D1/D2 create no new forbidden fire). Fp = prose NOT
MEASURED in both runs (0 in the formula, but the §2 cap "prose not measured → ≤ 9.0"
applies, as do the fresh/Kannada/confirmation caps). Mean precision/recall use the §5 H12
convention (empty GT + empty pred = 1.0/1.0).

## 2. The corrected GT (built from the v1 GT in the JSONs)

Remove `hma-27` from K0, H3, H10, H15 only. Nothing else changes.

| Q | Old GT (n) | Corrected GT (n) | Removed |
|---|---|---|---|
| K0 | BNS 316, BNSS 144, GWA 1890, HMGA s.6, WELFARE, HMA 27, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 (10) | BNS 316, BNSS 144, GWA 1890, HMGA s.6, WELFARE, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 (9) | HMA 27 |
| H1 | BNSS 144, PWDVA 20 (2) | unchanged (2) | — |
| H2 | GWA 1890, HMGA s.6, WELFARE (3) | unchanged (3) | — |
| H3 | BNS 316, HMA 27 (2) | BNS 316 (1) | HMA 27 |
| H4 | PWDVA 17, PWDVA 18, PWDVA 19 (3) | unchanged (3) | — |
| H5 | BNSS 144, GWA 1890, HMA 13, HMGA s.6, PWDVA 18, PWDVA 20, WELFARE (7) | unchanged (7) | — |
| H6 | BNSS 144, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 (5) | unchanged (5) | — |
| H7 | Births and Deaths Act 1969 (1) | unchanged (1) | — |
| H8 | BNSS 144, PWDVA 20 (2) | unchanged (2) | — |
| H9 | BNSS 144, PWDVA 20 (2) | unchanged (2) | — |
| H10 | BNS 316, BNSS 144, HMA 27, PWDVA 20 (4) | BNS 316, BNSS 144, PWDVA 20 (3) | HMA 27 |
| H11 | BNSS 144, PWDVA 20 (2) | unchanged (2) | — |
| H12 | — (0) | unchanged (0) | — |
| H13 | BNSS 144, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 (5) | unchanged (5) | — |
| H14 | BNSS 144, HMA 13, HMA 24, HMA 26, HMGA s.6, PWDVA 20, WELFARE (7) | unchanged (7) | — |
| H15 | BNS 316, HMA 27 (2) | BNS 316 (1) | HMA 27 |
| **Total** | **57** | **53** | **4 × HMA 27** |

## 3. Verification: did each run actually fire HMA 27 on those four questions?

Checked from the recorded `kept_ids` in each JSON — **not assumed**.

- **v5 fired HMA 27 on exactly the four D1 questions** — K0, H3, H10, H15 — and on no other
  question. So under corrected GT each of the four becomes a 1-FP non-exact question in the
  naive re-score, and nothing else changes.
- **v4r fired HMA 27 on the four D1 questions PLUS H1.** H1's GT never contained HMA 27, so
  its HMA 27 fire was already a false positive under the old GT (H1 pred was
  {BNS 316, BNSS 144, HMA 27, PWDVA 20}). The D2 simulation therefore also drops HMA 27 from
  v4r H1 (see §4) — this is within the D2 rule as specified, not an extra assumption.

## 4. D2 simulation — proceeding status per question (no ambiguity)

D2 gate: drop HMA 27 from a run's predictions on any question where **no HMA proceeding is
pending or being filed**. Status taken from the recorded Cell 6 facts in the JSONs
(`proceeding_pending`, `divorce_asked`) plus the question text for "being filed" (v6 §4.1:
being filed = user states they are filing / will file an HMA petition; wanting divorce ≠
being filed).

| Q | `proceeding_pending` | `divorce_asked` | Question text on filing | D2 drops HMA 27? |
|---|---|---|---|---|
| K0 | False | False | no filing language | Yes (both runs fired it) |
| H1 | False | False | "no case filed anywhere" (explicit) | Yes (v4r only; v5 did not fire it) |
| H3 | False | False | "I have never asked them to return it" — no filing | Yes (both runs) |
| H10 | False | False | "I have not asked for it back yet" — no filing | Yes (both runs) |
| H15 | False | False | no filing language | Yes (both runs) |
| H5 | False | **True** | "I want a divorce" — wanting ≠ being filed | Moot — neither run fired HMA 27 |
| H14 | **True** | True | "My divorce case is already going on" | Moot — neither run fired HMA 27 |
| H2, H4, H6, H7, H8, H9, H11, H12, H13 | False | False | no filing language (H11: "I have not filed any case yet") | Moot — neither run fired HMA 27 |

**No question's proceeding status is ambiguous in the records.** Every question that fired
HMA 27 has `proceeding_pending = False` and no filing language, so D2 drops HMA 27 from all
of them. The only `proceeding_pending = True` question is H14, which never fired HMA 27.

## 5. Headline: all four re-scores (corrected 53-section GT)

| Re-score | Exact | Micro P / R / F1 | TP / FP / FN (of 53) | Mean P / Mean R | Court | Escalates | Rating (formula → capped) |
|---|---|---|---|---|---|---|---|
| **v4r naive** (preds unchanged) | **8/16** | 0.768 / 1.000 / 0.869 | 53 / 16 / 0 | 0.780 / 1.000 | 10/16 | 14/16 | **6.4** (6.41 raw) |
| **v4r D2-adjusted** | **10/16** | 0.828 / 1.000 / 0.906 | 53 / 11 / 0 | 0.823 / 1.000 | 14/16 | 14/16 | **7.4** (7.39 raw) |
| **v5 naive** (preds unchanged) | **12/16** | 0.930 / 1.000 / 0.964 | 53 / 4 / 0 | 0.916 / 1.000 | 13/16 | 12/16 | **8.1** (8.09 raw) |
| **v5 D2-adjusted** | **16/16** | 1.000 / 1.000 / 1.000 | 53 / 0 / 0 | 1.000 / 1.000 | 16/16 | 12/16 | **9.8 raw → capped 9.0** |

For reference, under the old 57-section GT the same code gives v4r 10/16, 57/12/0, rating 7.3
and v5 16/16, 57/0/0, rating 9.8 raw capped 9.0 — exactly the filed numbers (§1 validation).

**Reading:** D1 alone (naive) costs v5 four exact questions and v4r two; D2 recovers all of
them on sections. But D2 does **not** recover escalates: v5 D2-adjusted is still 12/16 on
escalates (H2, H4, H7, H15 wrong — the typed-kinds gap, D3/D4/D5 territory), and v4r D2 is
still 14/16 (H2, H4 wrong). Mean recall is 1.000 in all four re-scores (FN = 0 throughout —
both runs over-fire, never under-fire, on this set).

## 6. v4r naive — per-question table (pred vs corrected GT)

Exact questions: **H2, H4, H5, H8, H9, H11, H12, H13 (8/16)**.
Non-exact: K0 (HMA 27 FP), H1 (BNS 316 + HMA 27 FPs), H3 (BNSS 144 + HMA 27 + PWDVA 20 FPs),
H6 (GWA 1890 + HMGA s.6 + WELFARE FPs), H7 (BNSS 144 + PWDVA 20 FPs), H10 (HMA 27 FP),
H14 (GWA 1890 FP), H15 (BNSS 144 + HMA 27 + PWDVA 20 FPs).

| Q | Recorded pred (v4r) | Corrected GT | P | R | TP/FP/FN | Court live vs expected | Esc live vs exp |
|---|---|---|---|---|---|---|---|
| K0 | BNS 316, BNSS 144, GWA 1890, **HMA 27**, HMGA s.6, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20, WELFARE | BNS 316, BNSS 144, GWA 1890, HMGA s.6, WELFARE, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 | 0.900 | 1.000 | 9/1/0 | [FC, Mag] vs [FC, Mag] ✓ | T vs T ✓ |
| H1 | **BNS 316**, BNSS 144, **HMA 27**, PWDVA 20 | BNSS 144, PWDVA 20 | 0.500 | 1.000 | 2/2/0 | [FC, Mag] vs [Mag] ✗ | T vs T ✓ |
| H2 | GWA 1890, HMGA s.6, WELFARE | GWA 1890, HMGA s.6, WELFARE | 1.000 | 1.000 | 3/0/0 | [FC] vs [FC] ✓ | F vs T ✗ |
| H3 | BNS 316, **BNSS 144**, **HMA 27**, **PWDVA 20** | BNS 316 | 0.250 | 1.000 | 1/3/0 | [FC, Mag] vs [Mag] ✗ | T vs T ✓ |
| H4 | PWDVA 17, PWDVA 18, PWDVA 19 | PWDVA 17, PWDVA 18, PWDVA 19 | 1.000 | 1.000 | 3/0/0 | [Mag] vs [Mag] ✓ | F vs T ✗ |
| H5 | BNSS 144, GWA 1890, HMA 13, HMGA s.6, PWDVA 18, PWDVA 20, WELFARE | same | 1.000 | 1.000 | 7/0/0 | [FC, Mag] vs [FC, Mag] ✓ | T vs T ✓ |
| H6 | BNSS 144, **GWA 1890**, **HMGA s.6**, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20, **WELFARE** | BNSS 144, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 | 0.625 | 1.000 | 5/3/0 | [FC, Mag] vs [Mag] ✗ | T vs T ✓ |
| H7 | Births and Deaths Act 1969, **BNSS 144**, **PWDVA 20** | Births and Deaths Act 1969 | 0.333 | 1.000 | 1/2/0 | [Mag, Reg] vs [Reg] ✗ | T vs T ✓ |
| H8 | BNSS 144, PWDVA 20 | BNSS 144, PWDVA 20 | 1.000 | 1.000 | 2/0/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H9 | BNSS 144, PWDVA 20 | BNSS 144, PWDVA 20 | 1.000 | 1.000 | 2/0/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H10 | BNS 316, BNSS 144, **HMA 27**, PWDVA 20 | BNS 316, BNSS 144, PWDVA 20 | 0.750 | 1.000 | 3/1/0 | [FC, Mag] vs [Mag] ✗ | T vs T ✓ |
| H11 | BNSS 144, PWDVA 20 | BNSS 144, PWDVA 20 | 1.000 | 1.000 | 2/0/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H12 | — | — | 1.000 | 1.000 | 0/0/0 | [] vs [] ✓ | F vs F ✓ |
| H13 | BNSS 144, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 | same | 1.000 | 1.000 | 5/0/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H14 | BNSS 144, **GWA 1890**, HMA 13, HMA 24, HMA 26, HMGA s.6, PWDVA 20, WELFARE | BNSS 144, HMA 13, HMA 24, HMA 26, HMGA s.6, PWDVA 20, WELFARE | 0.875 | 1.000 | 7/1/0 | [FC, Mag] vs [FC, Mag] ✓ | T vs T ✓ |
| H15 | BNS 316, **BNSS 144**, **HMA 27**, **PWDVA 20** | BNS 316 | 0.250 | 1.000 | 1/3/0 | [FC, Mag] vs [Mag] ✗ | T vs T ✓ |

**Rating arithmetic (v4r naive):**
10 × [0.60×0.5000 + 0.15×1.0000 + 0.10×0.7802 + 0.075×0.6250 + 0.075×0.8750]
= 10 × [0.3000 + 0.1500 + 0.0780 + 0.0469 + 0.0656] = 10 × 0.6405 = 6.405 → **6.4**.
− 0.5×Fb(0) − 1.0×Fp(not measured, 0 in formula). Caps: ≤ 9.0 non-binding.
Mean precision check: (0.900+0.500+1+0.250+1+1+0.625+0.333+1+1+0.750+1+1+1+0.875+0.250)/16
= 12.4833/16 = 0.7802. Micro P = 53/(53+16) = 0.7681; micro R = 53/53 = 1.000;
micro-F1 = 2×0.7681×1.000/(1.7681) = 0.8689.

## 7. v4r D2-adjusted — per-question table (pred minus HMA 27 where §4 says drop)

D2 drops HMA 27 from K0, H1, H3, H10, H15 (all five v4r HMA 27 fires). No other pred changes.
Exact questions: **K0, H2, H4, H5, H8, H9, H10, H11, H12, H13 (10/16)**.
Non-exact: H1 (BNS 316 FP remains), H3 (BNSS 144 + PWDVA 20 FPs remain), H6, H7, H14 (unchanged
FPs), H15 (BNSS 144 + PWDVA 20 FPs remain). Court is repaired on H1, H3, H10, H15 (their
adjusted preds contain no Family Court section, matching corrected expected [Magistrate]);
H6, H7 stay court-wrong. Escalates unchanged at 14/16 (H2, H4 wrong).

| Q | D2-adjusted pred | Corrected GT | P | R | TP/FP/FN | Court live vs expected | Esc live vs exp |
|---|---|---|---|---|---|---|---|
| K0 | BNS 316, BNSS 144, GWA 1890, HMGA s.6, WELFARE, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 | same (9) | 1.000 | 1.000 | 9/0/0 | [FC, Mag] vs [FC, Mag] ✓ | T vs T ✓ |
| H1 | **BNS 316**, BNSS 144, PWDVA 20 | BNSS 144, PWDVA 20 | 0.667 | 1.000 | 2/1/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H2 | GWA 1890, HMGA s.6, WELFARE | same | 1.000 | 1.000 | 3/0/0 | [FC] vs [FC] ✓ | F vs T ✗ |
| H3 | BNS 316, **BNSS 144**, **PWDVA 20** | BNS 316 | 0.333 | 1.000 | 1/2/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H4 | PWDVA 17, PWDVA 18, PWDVA 19 | same | 1.000 | 1.000 | 3/0/0 | [Mag] vs [Mag] ✓ | F vs T ✗ |
| H5 | BNSS 144, GWA 1890, HMA 13, HMGA s.6, PWDVA 18, PWDVA 20, WELFARE | same | 1.000 | 1.000 | 7/0/0 | [FC, Mag] vs [FC, Mag] ✓ | T vs T ✓ |
| H6 | BNSS 144, **GWA 1890**, **HMGA s.6**, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20, **WELFARE** | BNSS 144, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 | 0.625 | 1.000 | 5/3/0 | [FC, Mag] vs [Mag] ✗ | T vs T ✓ |
| H7 | Births and Deaths Act 1969, **BNSS 144**, **PWDVA 20** | Births and Deaths Act 1969 | 0.333 | 1.000 | 1/2/0 | [Mag, Reg] vs [Reg] ✗ | T vs T ✓ |
| H8 | BNSS 144, PWDVA 20 | same | 1.000 | 1.000 | 2/0/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H9 | BNSS 144, PWDVA 20 | same | 1.000 | 1.000 | 2/0/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H10 | BNS 316, BNSS 144, PWDVA 20 | same | 1.000 | 1.000 | 3/0/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H11 | BNSS 144, PWDVA 20 | same | 1.000 | 1.000 | 2/0/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H12 | — | — | 1.000 | 1.000 | 0/0/0 | [] vs [] ✓ | F vs F ✓ |
| H13 | BNSS 144, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 | same | 1.000 | 1.000 | 5/0/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H14 | BNSS 144, **GWA 1890**, HMA 13, HMA 24, HMA 26, HMGA s.6, PWDVA 20, WELFARE | BNSS 144, HMA 13, HMA 24, HMA 26, HMGA s.6, PWDVA 20, WELFARE | 0.875 | 1.000 | 7/1/0 | [FC, Mag] vs [FC, Mag] ✓ | T vs T ✓ |
| H15 | BNS 316, **BNSS 144**, **PWDVA 20** | BNS 316 | 0.333 | 1.000 | 1/2/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |

**Rating arithmetic (v4r D2-adjusted):**
10 × [0.60×0.6250 + 0.15×1.0000 + 0.10×0.8229 + 0.075×0.8750 + 0.075×0.8750]
= 10 × [0.3750 + 0.1500 + 0.0823 + 0.0656 + 0.0656] = 10 × 0.7385 = 7.385 → **7.4**.
Mean precision check: (1+0.667+1+0.333+1+1+0.625+0.333+1+1+1+1+1+1+0.875+0.333)/16
= 13.1667/16 = 0.8229. Micro P = 53/(53+11) = 0.8281; micro-F1 = 0.9060.

## 8. v5 naive — per-question table (pred vs corrected GT)

Exact questions: **all except K0, H3, H10, H15 (12/16)**. The only FPs in the whole run are
the four HMA 27 fires — v5's other fixes hold under corrected GT.

| Q | Recorded pred (v5) | Corrected GT | P | R | TP/FP/FN | Court live vs expected | Esc live vs exp |
|---|---|---|---|---|---|---|---|
| K0 | BNS 316, BNSS 144, GWA 1890, **HMA 27**, HMGA s.6, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20, WELFARE | same minus HMA 27 (9) | 0.900 | 1.000 | 9/1/0 | [FC, Mag] vs [FC, Mag] ✓ | T vs T ✓ |
| H1 | BNSS 144, PWDVA 20 | BNSS 144, PWDVA 20 | 1.000 | 1.000 | 2/0/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H2 | GWA 1890, HMGA s.6, WELFARE | same | 1.000 | 1.000 | 3/0/0 | [FC] vs [FC] ✓ | F vs T ✗ |
| H3 | BNS 316, **HMA 27** | BNS 316 | 0.500 | 1.000 | 1/1/0 | [FC, Mag] vs [Mag] ✗ | T vs T ✓ |
| H4 | PWDVA 17, PWDVA 18, PWDVA 19 | same | 1.000 | 1.000 | 3/0/0 | [Mag] vs [Mag] ✓ | F vs T ✗ |
| H5 | BNSS 144, GWA 1890, HMA 13, HMGA s.6, PWDVA 18, PWDVA 20, WELFARE | same | 1.000 | 1.000 | 7/0/0 | [FC, Mag] vs [FC, Mag] ✓ | T vs T ✓ |
| H6 | BNSS 144, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 | same | 1.000 | 1.000 | 5/0/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H7 | Births and Deaths Act 1969 | same | 1.000 | 1.000 | 1/0/0 | [Reg] vs [Reg] ✓ | F vs T ✗ |
| H8 | BNSS 144, PWDVA 20 | same | 1.000 | 1.000 | 2/0/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H9 | BNSS 144, PWDVA 20 | same | 1.000 | 1.000 | 2/0/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H10 | BNS 316, BNSS 144, **HMA 27**, PWDVA 20 | BNS 316, BNSS 144, PWDVA 20 | 0.750 | 1.000 | 3/1/0 | [FC, Mag] vs [Mag] ✗ | T vs T ✓ |
| H11 | BNSS 144, PWDVA 20 | same | 1.000 | 1.000 | 2/0/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H12 | — | — | 1.000 | 1.000 | 0/0/0 | [] vs [] ✓ | F vs F ✓ |
| H13 | BNSS 144, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 | same | 1.000 | 1.000 | 5/0/0 | [Mag] vs [Mag] ✓ | T vs T ✓ |
| H14 | BNSS 144, HMA 13, HMA 24, HMA 26, HMGA s.6, PWDVA 20, WELFARE | same | 1.000 | 1.000 | 7/0/0 | [FC, Mag] vs [FC, Mag] ✓ | T vs T ✓ |
| H15 | BNS 316, **HMA 27** | BNS 316 | 0.500 | 1.000 | 1/1/0 | [FC, Mag] vs [Mag] ✗ | F vs T ✗ |

**Rating arithmetic (v5 naive):**
10 × [0.60×0.7500 + 0.15×1.0000 + 0.10×0.9156 + 0.075×0.8125 + 0.075×0.7500]
= 10 × [0.4500 + 0.1500 + 0.0916 + 0.0609 + 0.0563] = 10 × 0.8088 = 8.088 → **8.1**.
Mean precision check: (0.900+1+1+0.500+1+1+1+1+1+1+0.750+1+1+1+1+0.500)/16 = 14.65/16
= 0.9156. Micro P = 53/(53+4) = 0.9298; micro-F1 = 0.9636.

## 9. v5 D2-adjusted — per-question table (pred minus HMA 27 on K0/H3/H10/H15)

D2 drops HMA 27 from K0, H3, H10, H15. Every adjusted pred now equals the corrected GT.
**Exact 16/16; TP/FP/FN 53/0/0; mean P/R 1.000/1.000; court 16/16.**
Escalates stay 12/16 — H2, H4, H7, H15 wrong (unchanged; see §1: H3 keeps its `demand` kind
after the drop, H15 has no demand kind because `demand_made = True` and no maintenance, so
dropping HMA 27 cannot change either row).

| Q | D2-adjusted pred | Corrected GT | P | R | TP/FP/FN | Court | Esc live vs exp |
|---|---|---|---|---|---|---|---|
| K0 | BNS 316, BNSS 144, GWA 1890, HMGA s.6, WELFARE, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 | same | 1.000 | 1.000 | 9/0/0 | [FC, Mag] ✓ | T vs T ✓ |
| H1 | BNSS 144, PWDVA 20 | same | 1.000 | 1.000 | 2/0/0 | [Mag] ✓ | T vs T ✓ |
| H2 | GWA 1890, HMGA s.6, WELFARE | same | 1.000 | 1.000 | 3/0/0 | [FC] ✓ | F vs T ✗ |
| H3 | BNS 316 | same | 1.000 | 1.000 | 1/0/0 | [Mag] ✓ | T vs T ✓ |
| H4 | PWDVA 17, PWDVA 18, PWDVA 19 | same | 1.000 | 1.000 | 3/0/0 | [Mag] ✓ | F vs T ✗ |
| H5 | BNSS 144, GWA 1890, HMA 13, HMGA s.6, PWDVA 18, PWDVA 20, WELFARE | same | 1.000 | 1.000 | 7/0/0 | [FC, Mag] ✓ | T vs T ✓ |
| H6 | BNSS 144, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 | same | 1.000 | 1.000 | 5/0/0 | [Mag] ✓ | T vs T ✓ |
| H7 | Births and Deaths Act 1969 | same | 1.000 | 1.000 | 1/0/0 | [Reg] ✓ | F vs T ✗ |
| H8 | BNSS 144, PWDVA 20 | same | 1.000 | 1.000 | 2/0/0 | [Mag] ✓ | T vs T ✓ |
| H9 | BNSS 144, PWDVA 20 | same | 1.000 | 1.000 | 2/0/0 | [Mag] ✓ | T vs T ✓ |
| H10 | BNS 316, BNSS 144, PWDVA 20 | same | 1.000 | 1.000 | 3/0/0 | [Mag] ✓ | T vs T ✓ |
| H11 | BNSS 144, PWDVA 20 | same | 1.000 | 1.000 | 2/0/0 | [Mag] ✓ | T vs T ✓ |
| H12 | — | — | 1.000 | 1.000 | 0/0/0 | [] ✓ | F vs F ✓ |
| H13 | BNSS 144, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20 | same | 1.000 | 1.000 | 5/0/0 | [Mag] ✓ | T vs T ✓ |
| H14 | BNSS 144, HMA 13, HMA 24, HMA 26, HMGA s.6, PWDVA 20, WELFARE | same | 1.000 | 1.000 | 7/0/0 | [FC, Mag] ✓ | T vs T ✓ |
| H15 | BNS 316 | same | 1.000 | 1.000 | 1/0/0 | [Mag] ✓ | F vs T ✗ |

**Rating arithmetic (v5 D2-adjusted):**
10 × [0.60×1.0000 + 0.15×1.0000 + 0.10×1.0000 + 0.075×1.0000 + 0.075×0.7500]
= 10 × [0.6000 + 0.1500 + 0.1000 + 0.0750 + 0.0563] = 10 × 0.9813 = 9.813 → **9.8 raw**,
then §2 caps apply (prose not measured; fresh/Kannada/confirmation not passed) → **capped 9.0**.
Even this best re-score is not a gate pass: G9 (escalates 12/16, target 16/16) fails, G12
(prose) is unmeasured, G14 (latency) fails as filed, G15 (confirmation) not run.

## 10. Verdict on the v6 expectation — CONFIRMED, with one correction to v6 §4.2

**The v6 expectation is confirmed exactly:** under D1-A before the D2 gate is applied, v4r
re-scores **8/16 exact** — H2, H4, H5, H8, H9, H11, H12, H13 (naive, §6). The two questions
v4r loses relative to its filed 10/16 are K0 and H10, both by the HMA 27 false positive alone;
H1, H3, H15 were already non-exact and stay non-exact (their other FPs survive the GT change).

**Correction to v6 §4.2 (flagged, not in the assigned expectation):** §4.2 states that "if D1
is adopted without D2, corrected-GT exact would be 14/16 (K0, H10 non-exact by HMA 27 FP)".
That is wrong. All four D1 questions fired HMA 27 in v5 (§3), so D1-without-D2 makes **four**
questions non-exact, not two — **v5 naive is 12/16, not 14/16** (§8: K0, H3, H10, H15).
The same error affects the mirror claim ("if D2 without D1, old-GT exact would be 14/16"):
dropping HMA 27 from K0, H3, H10, H15 against the old GT creates four false negatives, so
that figure is also 12/16, not 14/16. H3 and H15 were missed in both §4.2 counts.

## 11. Gate §6.1 consequence

Under gate §6.1 ("a GT change invalidates all prior runs on that set — they must be re-run
and re-filed"), adopting D1-A invalidates the v3, v4r and v5 runs on the current 16: their
filed numbers (v3 5/16, v4r 10/16, v5 16/16) were all scored against the old 57-section
ground truth that contained the wrong HMA 27 labels, so none of them may be quoted as the
system's standing score under the corrected 53-section ground truth. Each must be re-run live
in Colab under the corrected GT — with the D2 gate shipped in the same logged change, per
v6 D2-A — and re-filed as a new sequential run number with the §2 rating recomputed. This
report is an offline estimate of what those re-runs should show (v4r ≈ 10/16 with D2,
v5 ≈ 16/16 on sections with D2 but still 12/16 on escalates): it re-scores recorded
predictions, it does not re-run the model, and it is not a substitute for the live re-runs —
a live re-run could differ (different Stage-1 scores once the gate changes what is kept, and
different court/escalation derivations), and only the live re-run's filed numbers count.

## 12. Caveats and limits of this re-base

1. **Court expected is re-derived, not frozen.** §1 validates the re-derivation (matches all
   16 recorded expectations under old GT), but if the rater instead freezes H3/H10/H15's
   expected court at [Family Court, Magistrate] despite the GT change, court counts change:
   v4r naive 10/16 → 13/16 (rating 6.4 → 6.5); v4r D2 14/16 → 11/16 (the D2-adjusted
   [Magistrate] preds on H3/H10/H15 would then mismatch the frozen expectation; rating
   7.4 → 7.2); v5 naive 13/16 → 16/16 (rating 8.1 → 8.2); v5 D2 16/16 → 13/16
   (rating 9.8 raw, still capped 9.0). Exact counts, TP/FP/FN and escalates are unaffected
   by this choice.
2. **D2 is a prediction-level simulation.** A real D2 gate drops HMA 27 inside Stage 2; the
   model could in principle re-fire other sections or change `fired` sets downstream. The
   simulation assumes only the HMA 27 label is removed and everything else (including
   `fired_issues`, hence escalation kinds) is unchanged — the only behaviour the records can
   support offline.
3. **Escalate expectations untouched.** D3/D4/D5 (typed kinds, H7/H15 expectations) are not
   part of this re-base; if the rater flips H7 to False, escalates counts change (v5 D2 12/16
   → 13/16) without touching any section score.
4. **No sealed-set impact assessed.** The sealed fresh-20/Kannada-8 sets also contain HMA 27
   in GT (v6 §7.1); whether any sealed question is affected is a separate rater task — this
   lane did not read sealed wording.
5. **Files untouched.** Both source JSONs were read only; no result file, notebook, or GT file
   was modified by this lane.
