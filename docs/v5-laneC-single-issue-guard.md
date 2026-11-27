# v5 Lane C — Single-issue guard (in_scope)

**Lane:** C — single-issue guard / in_scope · **Round:** v5 PRECISION, round 2 of the overnight 10/10 run (v4r was round 1) · **Method:** offline analysis only, no Colab live run.
**Starting point (verified live, Colab 2026-11-27 ~00:19 IST):** v4r exact 10/16, micro P/R 0.826/1.000, micro-F1 0.905, TP/FP/FN 57/12/0. Recall 1.000, zero FN. All 12 FP are precision-only, on 6 questions (H1 2, H3 2, H6 3, H7 2, H14 1, H15 2).
**Sources:** `workspace/browser_downloads/sess-2184034649/browser-download-20261126T185447.300061282Z-0-live-laya-colab-results-v4r-residence-only.json` (`raw_live_runs`: `stage1_probs` = full-question scores, `stage1_clause_max`, `aux_max`, `stage1_final`, `fired_issues`, `fired_source`, `in_scope`); notebook `live-laya-colab-test-v4r-residence-only.ipynb` Cell 7 (thresholds, final = max(full, clause, aux), firing loop lines ~502–512, residence fact gate lines ~494–501, in_scope lines ~513–516); `laya-10-10-exact-plan.md` §2–§3; `empty5-fix-report.md`.
**Verdict in one line:** a safe guard exists. It kills all 6 FP sections on H3/H7/H15, touches no exact question, and predicts exact **13/16** (from 10/16) with recall still 1.000. It does **not** fix H1, H6, or H14. An in_scope gate must **not** be used as a firing gate — it cannot separate H7 from H13.

---

## 1. The guard rule (exact, implementable)

Apply in Cell 7 **after** the final scores are computed (`rec['stage1_final']`, notebook line ~471) and **after** the v4 residence fact gate (lines ~494–501), **before** the firing loop (lines ~502–512). It is a pure post-final, pre-firing filter. It changes no threshold, no aux prompt, no clause split, no Stage 2 rule.

### Constants

```python
GUARD_LIFT_BAR = 0.80        # lift a guarded issue must clear to fire
GUARD_FULL_CEILING = 0.01    # a guarded issue's full-question score must be <= this
THRESHOLDS = {               # unchanged v4r vector
    'maintenance': 0.10, 'custody': 0.20, 'stridhan': 0.50,
    'residence': 0.15, 'violence': 0.50,
    'divorce_asked': 0.45, 'divorce_pending': 0.12,
    'birth_certificate': 0.50, 'in_scope': 0.50,
}
```

### Definitions (all from already-recorded v4r fields — no new model calls)

- `full[i]` = `stage1_probs[i]` (full-question score). For residence use the **R0** score (`stage1_probs['residence']`); R1 never fires.
- `lift[i]` = `max(stage1_clause_max[i], aux_max[i])`, ignoring `None`. No aux prompts exist for stridhan / violence / birth_certificate / divorce-asked, so for those `lift[i] = stage1_clause_max[i]`. For divorce, `lift['divorce'] = max(asked clause/aux, pending clause/aux, pending full)` — i.e. the best lift behind either divorce signal.
- `dominant[i]` = `full[i] >= THRESHOLDS[i]`, with divorce judged on its **asked** signal only (`full['divorce'] >= 0.45`; the pending signal is a Stage-2-routed sub-signal, not a standalone issue score — see §4).
- The guard **arms** iff exactly **one** issue is dominant on the full question alone: `len([i for i in ISSUES if dominant[i]]) == 1`. Call that issue the dominant issue.
- A non-dominant issue `j` is **guarded** iff `full[j] <= 0.01`.

### Rule

```python
# Insert after residence fact gate, before the firing loop.
dominant = [name for name, _ in ISSUES
            if raw.get(name) is not None and raw[name] >= THRESHOLDS[name]]
            # divorce uses its asked threshold 0.45 via THRESHOLDS['divorce']
guard_armed = (len(dominant) == 1)
guard_blocked = []
for name, _ in ISSUES:
    if not guard_armed or name == dominant[0]:
        continue
    full_j = raw.get(name)                      # full-question score
    if full_j is None or full_j > GUARD_FULL_CEILING:
        continue
    lift_j = max([v for v in (clause_max.get(name),
                              rec['aux_max'].get(name)) if v is not None],
                 default=0.0)
    if name == 'divorce':
        lift_j = max([lift_j,
                      clause_max.get('divorce_pending') or 0.0,
                      raw.get('divorce_pending') or 0.0,
                      rec['aux_max'].get('divorce_pending') or 0.0])
    if lift_j < GUARD_LIFT_BAR:
        # Block: force final to 0.0 so the existing firing loop cannot fire it.
        # (Residence already forced to 0.0 by the fact gate when claim is False;
        #  the fact gate is the recorded reason there, not this guard.)
        final[name] = 0.0
        rec['stage1_final'][name] = 0.0
        guard_blocked.append((name, round(full_j, 4), round(lift_j, 4)))
        gated_out_a.append(
            f"single-issue guard: {name} blocked (dominant={dominant[0]}, "
            f"full={full_j:.4f}<=0.01, lift={lift_j:.4f}<0.80)")
rec['single_issue_guard'] = {
    'armed': guard_armed,
    'dominant': dominant[0] if guard_armed else None,
    'dominant_full': (round(raw[dominant[0]], 4) if guard_armed else None),
    'blocked': guard_blocked,
}
```

Then the existing firing loop runs unchanged on the (possibly forced) `final` scores. The dominant issue itself is **never** guarded — it fires on its full score alone. Issues with `full > 0.01` are never guarded, however low their lift. Issues are blocked only if **all three** conditions hold: guard armed (exactly one dominant issue) **and** `full <= 0.01` **and** `lift < 0.80`.

**Scope:** all 7 issues, not only maintenance/stridhan pairs. The mechanism (a ~zero full score rescued only by a weak clause/aux lift) is issue-general, and the per-question check (§5) shows the general scope costs nothing extra in-sample. Do **not** apply the 0.80 bar as a general aux/clause bar outside this guard — §3 shows genuine rescues below 0.80 that the guard's narrow scope deliberately leaves alone.

---

## 2. Evidence — the three target cases

v4r firing is `final = max(full, clause_max, aux_max)` against per-issue thresholds (maintenance 0.10). All three FP maintenance firings are pure weak-lift rescues of a ~zero full score:

| Q | True single issue (full) | FP issue | FP full | FP clause_max | FP aux_max | FP lift = max(clause, aux) | FP fired via (`fired_source`) | GT |
|---|---|---|---|---|---|---|---|---|
| H3 | stridhan **0.9332** | maintenance | **0.0001** | 0.0433 | **0.1218** | **0.1218** | aux — phrase *"he gives no money for me and my child"* scored 0.1218 on a gold question that never mentions money | [HMA 27, BNS 316] |
| H7 | birth_certificate **0.6624** | maintenance | **0.0** | **0.1971** | 0.0335 | **0.1971** | clause — *"The hospital did not give us one."* (0.1971; "did not give" matching a money-giving pattern) | [Births and Deaths Act 1969] |
| H15 | stridhan **0.9032** | maintenance | **0.0001** | 0.0298 | **0.1269** | **0.1269** | aux — same *"he gives no money for me and my child"* phrase, 0.1269 | [BNS 316, HMA 27] |

All three lifts (0.1218, 0.1971, 0.1269) are far below the 0.80 bar, and all three full scores are ≤ 0.01, and all three questions are single-dominant under §1 (H3: only stridhan ≥ its 0.50 threshold; H7: only birth_certificate ≥ 0.50; H15: only stridhan ≥ 0.50). So the guard blocks all three. Each block removes exactly 2 FP sections (BNSS 144 + PWDVA 20).

### Why the bar is 0.80 (not 0.30, not 0.50)

- The highest target lift is H7's **0.1971**. A bar of 0.30 would kill all three in-sample but with only **0.10** margin over H7 — one noisy clause away from failing on a fresh question. A bar of 0.50 kills all three with 0.30 margin.
- **0.80** kills all three with **0.60** margin over the highest target lift, and it sits just below the cluster of genuine high aux rescues that *do* rescue real issues on this set: H11 maintenance aux **0.9018**, K0 maintenance aux **0.8888**, H13 maintenance aux **0.8809**, H13 residence aux **0.8786**, H8 maintenance aux **0.8495**, H1 maintenance aux **0.802**. A genuine rescue on a ~zero full score, if one exists on fresh data, would have to look like those (≥ ~0.80) to be believed — a lift of 0.12–0.20 on a 0.0001 full score is noise, not evidence.
- Honest caveat: 0.80 is **not** a universal "genuine lift" threshold. Genuine rescues below 0.80 exist on this set — H14 custody aux **0.7895**, H10 maintenance aux **0.6772**, H4 residence aux **0.6474**, H1 stridhan clause **0.7545** (FP, §6). The bar is safe **only** because the guard's scope is narrowed to (single-dominant **and** full ≤ 0.01), where no genuine rescue in-sample sits below 0.80. That is why the scope conditions matter as much as the bar, and why the bar must be validated on the fresh F1–F20 set before locking (§7).

### Why the full-score ceiling is 0.01

- Highest FP full score among the three targets: **0.0001**. Lowest full score of any *fired true* issue in the 16: K0 maintenance **0.0773** (aux-rescued, §5). The ceiling 0.01 sits inside a wide empty band — no fired true issue has a full score between 0.001 and 0.0773 — 100× above the worst FP full (0.0001) and 7.7× below the lowest true fired full (0.0773). It is not a knife-edge.
- The next true full scores above the ceiling confirm the gap is structural, not lucky: H13 maintenance 0.1031, H5 custody 0.1098, H10 maintenance 0.1467, H14 custody 0.1321 — all ≥ 0.10, i.e. ≥ 10× the ceiling. No true issue in the 16 has a full score ≤ 0.01 at all (the lowest true full overall is K0 violence 0.0527, which does not fire and whose section PWDVA 18 is already covered via residence).

---

## 3. Why the dominance test is defined by per-issue thresholds (rejected first design)

**First design (rejected):** arm the guard whenever exactly one issue has `full >= 0.50`. That arms on 8 questions — K0, H3, H6, H7, H9, H10, H13, H15 — including the dangerous multi-issue cases K0 (stridhan 0.9064, second 0.265), H10 (stridhan 0.8929, maintenance 0.1467), H13 (violence 0.8892, residence 0.4212). Under that design the *only* thing protecting K0/H10/H13's true second issues is the ≤ 0.01 ceiling. It happens to hold in-sample (K0 maintenance 0.0773, H10 maintenance 0.1467, H13 maintenance 0.1031 / residence 0.4212 are all > 0.01), but the guard would be single-layer protection on exactly the questions where a mistake costs recall.

**Final design (adopted):** arm iff exactly one issue clears **its own** per-issue threshold on the full question alone (`full[i] >= THRESHOLDS[i]`). This correctly classifies the multi-issue questions as multi-issue *by the system's own thresholds*, because their second issues already clear their (low) thresholds on the full question:

| Q | Issues clearing their own threshold on full alone | Armed? |
|---|---|---|
| K0 | stridhan 0.9064 ≥ 0.50, custody 0.222 ≥ 0.20, residence 0.265 ≥ 0.15 (3) | No |
| H10 | stridhan 0.8929 ≥ 0.50, maintenance 0.1467 ≥ 0.10 (2) | No |
| H13 | violence 0.8892 ≥ 0.50, residence 0.4212 ≥ 0.15, maintenance 0.1031 ≥ 0.10 (3) | No |
| H6 | maintenance 0.898 ≥ 0.10, residence 0.2173 ≥ 0.15 (2) | No |
| H5 | maintenance 0.5366, violence 0.8343, divorce 0.9475 (3; residence 0.4882 also ≥ 0.15) | No |
| H2 | custody 0.852 ≥ 0.20, residence R0 0.8247 ≥ 0.15 (2; residence fact-gated anyway) | No |
| H3 / H7 / H15 | exactly one (stridhan / birth_certificate / stridhan) | **Yes** |
| H1 / H8 / H9 / H11 / H14 | exactly one (maintenance in each) | Yes, but nothing blocked (§5) |
| H4 / H12 | none (top fulls 0.1279 / 0.1218) | No |

So the dangerous cases (K0, H10, H13, H6) are disarmed **by construction**, and the ≤ 0.01 ceiling is a second layer, not the only layer. The two layers protect different things: dominance protects true second issues whose full score is low-but-not-~zero (0.0773–0.4212); the ceiling protects against a future single-dominant question whose true second issue genuinely sits at ~zero (it would then need lift ≥ 0.80, §2).

---

## 4. Divorce / residence handling inside the guard

- **Divorce:** judged for dominance on its **asked** signal only (`full['divorce'] >= 0.45`). The pending signal (`divorce_pending`, threshold 0.12) is a Stage-2-routed sub-signal, not a standalone issue score; counting it toward dominance would misclassify H14 (pending 0.9202) as two-dominant and H1 (pending 0.1354) as two-dominant, changing the armed list for no benefit — in-sample the firing outcome is identical either way (no blocked issue changes), so the simpler asked-only definition is locked. When divorce *is* the guarded (non-dominant) issue, both signals count toward its lift (§1 pseudocode). In-sample this never changes a firing: the only armed question with divorce full ≤ 0.01 is H7 (asked 0.0, pending 0.0, lift 0.1131 < 0.80 — blocked, but divorce final pending 0.0502 was already below its 0.12 threshold, so no firing change).
- **Residence:** the v4 fact gate runs **before** the guard and takes precedence. Where `residence_claim` is False, residence final is already 0.0 and the fact gate is the recorded reason. The guard's residence leg therefore only matters where the claim is True; in-sample no such case is guarded (K0/H4/H6/H13 residence fulls are 0.265/0.1267/0.2173/0.4212, all > 0.01, and none of those questions arms the guard).

---

## 5. Guardrail check — per-question table, all 16

Simulation: final guard (§1) applied to the v4r `raw_live_runs` numbers (full / clause_max / aux_max / fired_issues). "Blocked" lists only issues that were actually firing in v4r; issues that would also be blocked but were not firing anyway are noted in the last column. Section outcomes assume sub-choices for surviving issues are unchanged (their argmax clauses are unaffected by removing another issue).

| Q | v4r exact? | Dominant (full ≥ own thr) | Armed? | Fired before (v4r) | Blocked by guard (full, lift) | Fired after | Exact after? | Notes |
|---|---|---|---|---|---|---|---|---|
| K0 | ✓ | stridhan 0.9064, custody 0.222, residence 0.265 | No | maintenance, custody, stridhan, residence, divorce | — | unchanged | ✓ | **Key guardrail case.** True maintenance full 0.0773 (> 0.01, exempt) with aux 0.8888 — would clear the 0.80 bar anyway, but the guard never arms here, so it is protected twice over. |
| H1 | ✗ (2 FP) | maintenance 0.4795 | Yes | maintenance, stridhan, divorce | — | unchanged | ✗ (2 FP) | See §6. Stridhan full 0.4948 > 0.01, exempt. Birth full 0.0007, lift 0.0147 < 0.80 would be blocked but never fired. |
| H2 | ✓ | custody 0.852, residence 0.8247 | No | custody, divorce | — | unchanged | ✓ | Non-GT issues with full ≤ 0.01 (maintenance 0.0, stridhan 0.0, birth 0.0) have lifts ≤ 0.082 — none fired in v4r, none would fire. Residence already fact-gated. |
| H3 | ✗ (2 FP) | stridhan 0.9332 | **Yes** | maintenance, stridhan | **maintenance (0.0001, 0.1218)** | stridhan | **✓** | Target case. Kept → [HMA 27, BNS 316] = GT. |
| H4 | ✓ | none (top: violence 0.1279) | No | residence, divorce | — | unchanged | ✓ | **Key guardrail case.** Residence is single-issue-true but fires via aux 0.6474 (< 0.80). Guard does not arm (no issue clears its threshold on full alone), so H4 is untouched. A guard without the dominance test would kill H4. |
| H5 | ✓ | maintenance 0.5366, violence 0.8343, divorce 0.9475, residence 0.4882 | No | maintenance, custody, violence, divorce | — | unchanged | ✓ | **Key guardrail case.** True custody full 0.1098 (> 0.01, exempt) with aux lift only 0.2189 (< 0.80) — a guard without the dominance test *and* without the ≤ 0.01 ceiling would kill a true issue here. Guard never arms. |
| H6 | ✗ (3 FP) | maintenance 0.898, residence 0.2173 | No | maintenance, custody, residence, divorce | — | unchanged | ✗ (3 FP) | Custody FP survives: custody full 0.1602 > 0.01, so not guarded. Different mechanism (§7). Divorce firing is section-neutral (Stage 2 drops HMA 13, divorce not asked). |
| H7 | ✗ (2 FP) | birth_certificate 0.6624 | **Yes** | maintenance, birth_certificate | **maintenance (0.0, 0.1971)** | birth_certificate | **✓** | Target case. Kept → [Births and Deaths Act 1969] = GT. Court → [Registrar] correct (was [Magistrate, Registrar]). Also blocked-but-not-firing: residence (0.0001, 0.1307), stridhan (0.0, 0.2198), violence (0.0, 0.0), divorce (0.0, 0.1131). |
| H8 | ✓ | maintenance 0.1746 | Yes | maintenance | — | unchanged | ✓ | Dominant issue itself never guarded. Its aux 0.8495 ≥ 0.80 would pass the bar anyway. Birth full 0.0002, lift 0.0002 — not firing. |
| H9 | ✓ | maintenance 0.7931 | Yes | maintenance | — | unchanged | ✓ | Violence full 0.003, lift 0.003 — not firing, would be blocked. Stridhan full 0.2546 > 0.01, exempt, not firing. |
| H10 | ✓ | stridhan 0.8929, maintenance 0.1467 | No | maintenance, stridhan, divorce | — | unchanged | ✓ | **Key guardrail case.** True maintenance full 0.1467 (> 0.01, exempt) with aux 0.6772 (< 0.80) — a guard with a higher ceiling (e.g. ≤ 0.15) or no dominance test would kill it and break an exact question. Guard never arms. |
| H11 | ✓ | maintenance 0.1432 | Yes | maintenance, divorce | — | unchanged | ✓ | Divorce full 0.0965 > 0.01, exempt; its pending lift 0.3284 < 0.80 is irrelevant (no section effect — Stage 2 drops HMA 13). Birth full 0.0, lift 0.0 — not firing. |
| H12 | ✓ (empty) | none (top: custody 0.1218) | No | divorce | — | unchanged | ✓ (empty) | Guard never arms; nothing newly fires (a guard only blocks). Divorce firing stays section-neutral (Stage 2 drops HMA 13; kept stays []). in_scope 0.2606, see §7. |
| H13 | ✓ | violence 0.8892, residence 0.4212, maintenance 0.1031 | No | maintenance, residence, violence | — | unchanged | ✓ | **Key guardrail case.** True maintenance full 0.1031 and residence 0.4212, both > 0.01 and both with aux lifts ≥ 0.80 (0.8809 / 0.8786) — they would pass the bar even if the guard armed. It never arms. |
| H14 | ✗ (1 FP) | maintenance 0.2542 | Yes | maintenance, custody, divorce | — | unchanged | ✗ (1 FP) | True custody full 0.1321 (> 0.01, exempt) with aux 0.7895 (< 0.80) and true divorce full 0.1395 (> 0.01, exempt) — both survive only because of the ≤ 0.01 ceiling. The 1 FP (GWA 1890) is a Stage-2 route choice on a correctly-fired custody issue, not a firing error — outside this lane. |
| H15 | ✗ (2 FP) | stridhan 0.9032 | **Yes** | maintenance, stridhan | **maintenance (0.0001, 0.1269)** | stridhan | **✓** | Target case. Kept → [BNS 316, HMA 27] = GT. |

**Guardrail result: zero exact questions harmed.** All 10 v4r-exact questions are unchanged (K0, H2, H4, H5, H8, H9, H10, H11, H12, H13). The three non-exact targets become exact. H1, H6, H14 are unchanged (still non-exact, for reasons outside this guard — §6/§7).

### Predicted aggregate under the guard (offline, from v4r numbers)

| Metric | v4r | v5 + Lane C guard (predicted) |
|---|---|---|
| Exact | 10/16 | **13/16** (H3, H7, H15 fixed) |
| TP / FP / FN | 57 / 12 / 0 | **57 / 6 / 0** (no true issue blocked) |
| Micro P / R / F1 | 0.826 / 1.000 / 0.905 | **0.905 / 1.000 / 0.950** (57/63; mean P 0.9375, mean R 1.000) |
| Court correct | 13/16 | **14/16** (H7 fixed: kept {births-deaths-act-1969} → Registrar only; H1, H6 still wrong) |
| Escalates correct (Cell 8 patched scoring) | 14/16 | **12/16 — see side-effect below** |
| Remaining FP (6) | — | H1 stridhan 2 (BNS 316, HMA 27), H6 custody 3 (GWA 1890, HMGA s.6, WELFARE), H14 GWA 1890 1 |

**Escalates side-effect (must be read by the merger — not hidden):** H7 and H15 flip from escalates-correct to escalates-wrong under current Cell 8 scoring. In v4r their escalates=True came *solely* from the quantum boilerplate attached to the FP maintenance firing ("Quantum: husband's income / school fees unknown…"). Once maintenance is (correctly) removed, H7 has no typed escalation (birth-certificate only, kept non-empty, no court fallback) and H15 has none either (stridhan only, demand already made, so no demand escalation). H3 stays True via its demand escalation (demand_made=False). This is the plan §3.4 problem surfacing, not a section regression: the quantum text was content-wrong on a birth-certificate question and on a stridhan-sold question anyway. **Do not "fix" it by re-attaching the boilerplate.** The correct handling is a GT/scoring decision for the merger: H7's `escalate_expected=True` is already OPEN (fully answerable question, no named reason); H15 now joins it (same shape — fully answerable, no named reason). If the expectations for H7/H15 are resolved to False, escalates reads 14/16 again; if they stay True, it reads 12/16 and the guard still nets +3 exact / +1 court against −2 escalates. Either way the section score is the guard's deliverable; the escalate expectation is a separate open decision.

---

## 6. H1 verdict — explicitly NOT fixed by this guard; belongs to Lane A

H1: GT [BNSS 144, PWDVA 20] only. Maintenance is true (full 0.4795, aux 0.802, fires correctly). The FP is **stridhan**: full **0.4948** (just under its 0.50 threshold), clause_max **0.7545** (clause *"My husband has not given me any money for three months."*), final 0.7545 ≥ 0.50 → fires → BNS 316 + HMA 27 (2 FP). Court wrong ([Family Court, Magistrate] vs [Magistrate]) as a consequence.

The guard does **not** catch H1, for two independent reasons, either of which alone is sufficient:

1. **Ceiling leg fails:** stridhan full 0.4948 is 4,948× the 0.01 ceiling. The guard's whole premise is "full ≈ zero"; H1's stridhan full is a near-threshold score, the opposite pattern.
2. **Dominance does not save it either way:** H1 *does* arm the guard (only maintenance clears its threshold on full alone), but the ceiling leg exempts stridhan, so nothing is blocked.

**Could the guard be widened to catch H1? No — tested and rejected.** Widening the ceiling to ≤ 0.50 (so H1 stridhan, lift 0.7545 < 0.80, would be blocked) breaks a true issue under the *same* final guard: H14 custody, full 0.1321 ≤ 0.50, lift aux 0.7895 < 0.80, would be blocked on an armed question (H14 arms: only maintenance clears its threshold) — losing 3 GT sections (HMGA s.6, WELFARE, HMA 26) and breaking H14's true custody firing. H10 maintenance (full 0.1467, lift 0.6772 < 0.80) would also be caught by a ≤ 0.50 ceiling if H10 armed — it does not arm under the per-issue dominance test, but the H14 counterexample alone kills the widening. There is **no** ceiling value that catches H1 stridhan (0.4948) without also catching H14 custody (0.1321) or H10 maintenance (0.1467), because the FP full sits *above* both true fulls. H1 is a near-threshold stridhan problem (full 0.4948 vs threshold 0.50; clause lift 0.7545), not a ~zero-full weak-lift problem. **It belongs to Lane A** (stridhan threshold / clause-lift handling — e.g. a stridhan-specific clause bar, or keeping stridhan at 0.50 while requiring its clause lift to clear a higher bar when its full is below threshold). Lane C makes no proposal for it beyond this verdict. H1's court error also stays until its stridhan FP is fixed.

---

## 7. H7 in_scope analysis — an in_scope gate does NOT help; do not use one

### The numbers (from `raw_live_runs`)

in_scope full = `stage1_probs['in_scope']`; in_scope final = `max(full, clause_max)`; bool = final ≥ 0.50 (Cell 7 lines ~513–516). The in_scope question is *"Does this question concern a Hindu matrimonial / domestic-relationship family-law matter?"*

| Q | in_scope full | in_scope clause_max | in_scope final | in_scope bool | v4r exact? |
|---|---|---|---|---|---|
| H7 | **0.078** (lowest full in the set) | 0.113 | **0.113** | False | ✗ (target) |
| H13 | 0.0985 | 0.0985 | **0.0985** | False | ✓ |
| H12 | 0.145 | 0.2606 | 0.2606 | False | ✓ (empty) |
| H11 | 0.1502 | 0.1502 | 0.1502 | False | ✓ |
| H15 | 0.2351 | 0.1373 | 0.2351 | False | ✗ (target) |
| H8 | 0.2548 | 0.2548 | 0.2548 | False | ✓ |
| H9 | 0.4695 | 0.4695 | 0.4695 | False | ✓ |
| H4 | 0.5494 | 0.7646 | **0.7646** | True | ✓ |
| H6 | 0.6893 | 0.4948 | 0.6893 | True | ✗ |
| H1 | 0.6951 | 0.6567 | 0.6951 | True | ✗ |
| H10 | 0.702 | 0.5649 | 0.702 | True | ✓ |
| H3 | 0.7187 | 0.6915 | 0.7187 | True | ✗ (target) |
| H2 | 0.8175 | 0.8925 | 0.8925 | True | ✓ |
| H5 | 0.8252 | 0.7586 | 0.8252 | True | ✓ |
| K0 | 0.8472 | 0.8222 | 0.8472 | True | ✓ |
| H14 | 0.856 | 0.4197 | 0.856 | True | ✗ |

### Findings

1. **H7's full (0.078) is the lowest in the set, but only by 0.0205 over H13 (0.0985).** A gate on the *full* score with a cutoff in (0.078, 0.0985] — e.g. 0.09 — would separate H7 from H13 in-sample. That is a knife-edge on n=16, not a finding: one fresh question anywhere in that 0.02 band breaks it either way.
2. **On the final score (the value Cell 7 actually records and thresholds), no separation exists at all: H13's final 0.0985 is *below* H7's final 0.113.** Any cutoff on the final that blocks H7 also blocks H13 — a true multi-issue exact question (maintenance + residence + violence, all firing via aux ≥ 0.87) — which would go from exact to empty (5 FN). An in_scope gate on the final is therefore **rejected outright**.
3. **H4 is not the blocker — H13 is.** H4 (the single-issue residence case the task asked to protect) passes comfortably: full 0.5494, final 0.7646 — it clears the existing 0.50 bool threshold and any cutoff up to 0.54. If in_scope were used only as a *firing* gate it would not break H4. It would break H13 (and, as a general gate, H8/H9/H11/H15 — see 4).
4. **A general in_scope firing gate is catastrophic and must not be adopted.** in_scope bool is False on **5 of the 10 exact questions** (H8 0.2548, H9 0.4695, H11 0.1502, H13 0.0985, H15 0.2351). Gating firing on in_scope=True would empty or cripple all five. The in_scope prompt as worded ("Hindu matrimonial / domestic-relationship") systematically under-scores single-issue maintenance questions (H8/H9/H11) and the birth-certificate question (H7) — the low score is a prompt-coverage artefact (birth registration is not a matrimonial matter as worded), not a reliable single-issue signal. H7's 0.078 says "this is not a matrimonial question", which is arguably *correct* for a birth-certificate question — it carries no information about whether maintenance also fires.
5. **H12 (must stay empty):** in_scope full 0.145, final 0.2606, bool False. An in_scope gate **adds nothing** on H12 — a gate only blocks, it never fires, and H12's kept set is already empty (its fired divorce is section-neutral: Stage 2 drops HMA 13 because divorce was not asked). H12 stays empty with or without any in_scope gate, and with or without the Lane C guard (guard does not arm on H12: no issue clears its threshold on full alone).
6. **Recommendation:** keep in_scope exactly where it is — as an input to the court fallback only (Cell 7 `court_for`, kept-empty + in-scope → escalate; kept-empty + out-of-scope → `[]`). Do not promote it to a firing gate in v5, in either its full or its final form. If a future lane wants an out-of-scope signal, it needs a differently-worded prompt (one that covers birth registration and single-issue maintenance) and a fresh-set validation — not a threshold tuned on the 0.0205 H7/H13 gap.

### H7 escalate / court — status after the guard

- **Court:** fixed by the guard (kept {births-deaths-act-1969} → Registrar only, via the membership branch). No in_scope involvement.
- **Escalates:** the guard exposes the OPEN ambiguity rather than resolving it. H7 `escalate_expected=True` (Cell 6) has no named reason under typed scoring once the (content-wrong) quantum boilerplate leaves with the maintenance FP — see §5 side-effect. This lane does not resolve it; it is a coordinator decision (resolve the expectation, or name a reason such as "confirm hospital/registration procedure").

---

## 8. What the guard does NOT fix (residuals for other lanes)

- **H1 (2 FP, stridhan):** §6 — Lane A. Near-threshold, not ~zero-full.
- **H6 (3 FP, custody):** custody full 0.1602, clause 0.1712, aux 0.3669 (phrase *"I want my daughter to stay with me"*). Full is not ~zero and H6 does not arm the guard (maintenance + residence both clear their thresholds on full alone). Different mechanism — the custody aux phrase genuinely matches the question's wording ("to stay in the house with my daughter" is a residence claim, misread as custody). Lane A/B territory (custody prompt / aux-phrase scoping).
- **H14 (1 FP, GWA 1890):** custody fires correctly (full 0.1321, aux 0.7895); the FP is Stage 2 picking the GWA route instead of HMA 26 when a proceeding is pending. Firing is correct; routing is wrong. Lane for Stage 2 / custody-route gating.
- **H2/H4 escalates (Cell 8):** unchanged by this lane (H2 residence fact gate already in v4r; H4 escalates wrong under typed scoring for the reasons in the plan §3.4).

---

## 9. Implementation notes for the merger / notebook builder

1. Insert the §1 block after the residence fact gate, before the firing loop. No new model calls, no new prompts, no threshold changes. Cost: zero extra Laya calls; the guard is pure arithmetic on recorded scores.
2. Record per question: `rec['single_issue_guard']` (armed, dominant, dominant_full, blocked list) and one `gated_out` entry per blocked issue (wording in §1). Keep `fired_clause` / `fired_source` as computed (they record what *would* have fired) — only `final` / `stage1_final` is forced to 0.0 for blocked issues, mirroring the residence-gate convention.
3. **Do not** merge this guard with the residence fact gate's reason string — a future audit must be able to tell "blocked by residence_claim=False" from "blocked by single-issue guard".
4. The guard must run on the **R0** residence full score (the firing prompt), never R1.
5. Court/escalate consequences to carry into the v5 run report: court predicted 14/16; escalates predicted 12/16 under current Cell 8 scoring *unless* the H7/H15 expectations are resolved first (see §5). Do not let the escalates dip be misread as a guard failure — it is the removal of content-wrong boilerplate, and the section gain (+3 exact) is the guard's deliverable.
6. **Validation required before locking:** the 0.80 bar and the 0.01 ceiling are in-sample on n=16 (the 0.80 bar in particular has no true-positive calibrator inside guard scope — §2). Validate on the sealed fresh F1–F20 set: report (a) how many fresh single-issue questions arm the guard, (b) whether any fresh *true* second issue with full ≤ 0.01 and lift < 0.80 is blocked (that would be a recall loss and would force the bar down), (c) whether any fresh FP with full ≤ 0.01 and lift in [0.20, 0.80) survives (that would argue the bar up — it cannot go above the genuine-rescue cluster ~0.85 without new evidence). If (b) occurs even once, the guard as specified is unsafe as a default and should become a flag-and-escalate (block + record) rather than a silent block. Do not tune the bar on the fresh set — report the numbers and let the merger decide.

---

## 10. Summary for the merger

- **Guard:** arm iff exactly one issue clears its own per-issue threshold on the full question alone; then, for any other issue with full ≤ 0.01, require lift = max(clause_max, aux_max) ≥ **0.80** to fire, else block.
- **Bar:** 0.80 — 0.60 above the highest target lift (H7, 0.1971) and just below the genuine aux-rescue cluster (0.8495–0.9018). Ceiling 0.01 — 100× above the worst FP full (0.0001), 7.7× below the lowest true fired full (0.0773).
- **Kills:** 6 FP sections — H3 maintenance (0.0001 / 0.1218), H7 maintenance (0.0 / 0.1971), H15 maintenance (0.0001 / 0.1269). Predicted exact 10/16 → **13/16**, micro-F1 0.905 → **0.950**, TP/FP/FN 57/12/0 → **57/6/0**, recall stays 1.000, court 13/16 → 14/16.
- **Risks to exact questions:** none in-sample — all 10 v4r-exact questions verified unchanged, including the four dangerous ones (K0, H5, H10, H13) whose true second issues have low full scores (0.0773–0.4212) and, in H5/H10/H14, lifts below 0.80. They survive via the dominance test (guard never arms) and/or the ≤ 0.01 ceiling.
- **Not fixed:** H1 (belongs to Lane A — §6 proves no safe ceiling catches it), H6 custody FP, H14 GWA route FP.
- **in_scope gate:** rejected — H13's in_scope final (0.0985) is below H7's (0.113), so no final-score cutoff separates them; a full-score cutoff would rest on a 0.0205 gap; in_scope is False on 5 exact questions. Keep in_scope as court-fallback input only. H4 (0.5494 / 0.7646) was never the blocker; H12 stays empty either way.
- **Side-effect to carry:** escalates reads 12/16 (from 14/16) under current Cell 8 scoring because H7/H15 lose the quantum boilerplate that only existed via their FP maintenance firing — a scoring-expectation decision (H7 OPEN, H15 same shape), not a section regression. Do not re-attach the boilerplate.
