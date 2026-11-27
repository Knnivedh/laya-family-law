# v6 brutal-test notebook — Lane B build note

**Date:** 2026-11-27 (build finished ~10:55 IST, under the 10:51 IST "run now" instruction)
**Notebook:** `live-laya-colab-test-v6-brutal.ipynb`
**Notebook SHA-256:** `d6ee579534b5f2ac0b836f834954afe73fd5480d0da7a7a9fc5bec6e2461ff98`
**Builder:** `build_laya_v6_brutal.py` (SHA-256 `184657d96facf697f2aaee7db8cdff8e3dcb2c4b889a2295e7fddcc3c7e2cc7b`)
**Base:** `live-laya-colab-test-v5-precision.ipynb` (9 cells), builder pattern from `build_laya_v5_precision.py`.
**Verification done by this lane:** builder run twice — byte-identical output (same SHA-256 both runs); `nbformat.validate` PASS (one non-fatal `MissingIDFieldWarning` for missing cell ids, same shape as v5 base — fixed by pinning deterministic ids `cell-0`…`cell-23` in the builder after validation, which is what makes re-runs byte-identical); all code cells compile PASS (IPython `!pip` magic lines excluded, as in the builder's own check); Cell 6 exec PASS (16 questions, 53 sections); HMA25 + HMA27 shadow tests PASS; stub-agent D2/kinds test PASS; stub `score_batch` test PASS. **No live run was done by this lane (offline only).** The live Colab run is the coordinator's next step.

## What changed per cell (24 cells, indices 0–23)

| Cell | Change |
|---|---|
| 0 (md) | Retitled v6: D1-A settled, D2 gate, graph v3, brutal bank 230. |
| 1–4 | Byte-identical to v5 (setup, model load, graph-helpers, prompts). |
| 5 | Upload graph **v3**, verify SHA-256 `67bf2b04ca946f7c7fa3062068e01ce051fbce8f4d740c281afe6fff841c34a5`, assert counts **exactly (34 sections, 48 nodes, 79 edges)**. Counts-only assert — see "Pre-existing graph defects" below. |
| 5b (idx 6) | NEW: upload `brutal-bank-v1-frozen.json` via `files.upload()`, verify SHA-256 `934a2b2265ac137c96939e1fbeca3682a037010e42f972bfd459c2fcac4ec717` and 230 questions; stop with an error on mismatch. Never writes to the bank file. |
| 6 (idx 7) | 16-question GT replaced with corrected v2 GT (`ground-truth-v2-hma27-A.json`): **53 sections** (was 57; HMA 27 removed from K0/H3/H10/H15 per D1-A, no replacement). Added frozen fact `being_filed` per question (see derivation rule below). |
| 7 (idx 8) | Pipeline unchanged except: (a) **D2 drop-gate for HMA 27** — HMA 27 is dropped (not escalated) in Stage 2 when no HMA proceeding is pending or being filed, using `being_filed`; (b) **recovery escalation text** replaced with the parent-approved UNCONDITIONAL variant (see below); (c) stale "skeleton — fixes pending" header text fixed; (d) per-question Stage 1 + Stage 2 body refactored into ONE reusable function `run_one_question(t)` — re-indented only, no change to thresholds, prompts, scoring logic, or facts; dedent-equivalence verified in the builder. |
| 8 (idx 9) | Regression scoring + shared helpers (`SCORING_KINDS`, `COURT_NORMALIZE`, `SEALED_KIND_MAP`, `_wilson`, `bank_pairs`, `sealed_pairs`, `score_batch`). Keeps v5 diagnostics; adds hma-27 forbidden rule (D2-consequent, recorded); `LABEL_BY_ID`/`SECTION_COURT`/`SECTION_ISSUE` gain `hma-9` (Family Court, issue 'divorce') and `pwdva-22` (Magistrate, issue 'violence'); `esc_live` = {quantum, court, demand, custody, residence, recovery, procedure, safety}; per-row kinds fields + strict/fact-excluded kinds correctness; `escalates_on_empty_kept` guard (must be 0); gate-formula rating with full arithmetic; G14 per-component check. Output files renamed `live-laya-colab-results-v6-brutal-regression.json/.md`. |
| 9–18 (B1–B10) | NEW batch cells. B1–B9 run 25 bank questions each, B10 runs the last 5 (B-226…B-230), each through `run_one_question`, scored ONLY against the frozen bank GT. Each cell saves its per-batch JSON (exact, micro P/R/F1, TP/FP/FN, court correct, escalates correct incl. kinds, forbidden count, silent count, model errors, per-category exact) AND downloads it with `files.download()` immediately, then prints batch + cumulative summaries. Notebook states NO tuning happens between batches; code modifies no threshold, fact, or gate between batches. **Deviation flagged:** batches are sequential slices (B1 = B-001…B-025, …), NOT stratified as `brutal-test-200-plan.md` §4.2 requires — a crash loses whole categories. |
| 19 (idx 20) | NEW: sealed upload + verify (fresh-20 and Kannada-8 SHAs — see "Sealed-set verification"). |
| 20 (idx 21) | NEW: fresh-20 run + score (separate section). |
| 21 (idx 22) | NEW: Kannada-8 run + score (separate section). |
| 22 (idx 23) | Final cumulative cell: asserts 230 brutal records, re-scores only (no model calls), prints pass/fail vs plan §3.2, Wilson interval, brutal rating (capped 9.0, Fp NOT MEASURED), gate-row summary, G14 check print, saves + downloads `live-laya-colab-results-v6-brutal-final.json`. |

## `being_filed` derivation rule (frozen fact, Cell 6 + bank/sealed derivation)

`being_filed` is True **only if the user states a filing / will file / instructed filing** (e.g. "going to file", "I will file", "I have instructed filing"). **"I want a divorce" does NOT count.** All 16 regression questions: `being_filed` = False (H14 is proceeding-pending, not a fresh filing). For bank/sealed questions, facts are derived by the frozen text rules in `derive_facts_from_text()` + `complete_facts()` (Cell 7) — never per-question, never from GT; frozen annotations always win. Verified on probes: "going to file" → True; "I want a divorce" → False; "I do NOT want a divorce" → `divorce_asked` False; "case already going on" → `proceeding_pending` True; "never asked them to return it" → `demand_made` False; "asked … refused" → True; "sold my gold without asking" → `demand_made` None. **Demand derivation order:** FALSE check first ("never asked them to return it" contains "asked … return", which the TRUE pattern would otherwise catch).

## Recovery text (variant chosen: UNCONDITIONAL)

Verbatim, used in the `recovery` escalation:
> "Stridhan recovery: sold or withheld gold cannot be recovered or valued by the bot — escalate to a lawyer for valuation, a police complaint under BNS s.316 and civil recovery through the Family Court under FCA s.7(1) Expl. (c) / CPC s.151 (or under HMA s.27 where an HMA proceeding is pending or being filed)."
Source wording: `v6-lane2-escalates.md` line 98 (§1.2 `recovery` row) and line 367 (§3 `esc_typed.append` snippet) — old text "…civil recovery under HMA s.27." **Trigger kept as Lane 2's:** `kept ∩ {hma-27, bns-316} AND demand_made is True` (fires via bns-316 alone under D1-A, so K0/H15 still get recovery).

## Kind-derivation table (predicted kinds, from kept sections + facts)

| Kind | Derivation |
|---|---|
| quantum | maintenance sections kept |
| custody | kept ∩ {gwa-1890, hma-26} |
| residence | `'residence'` in fired (post-gate, NOT kept PWDVA 17/18/19 — H5 keeps PWDVA 18 via the violence-only branch) |
| recovery | stridhan kept + `demand_made` True |
| demand | stridhan fired + `demand_made` is not True (kept stridhan-only) |
| procedure | births-deaths kept (birth branch only) |
| safety | `pwdva-18` in kept (NOT Lane 2's violence-fact trigger — see evidence below) |
| court | `court_source == fallback-escalate` |

**Safety trigger evidence:** 31/32 bank safety uses carry `pwdva-18` in GT (only exception B-108, custody-only safety); only 13/32 state violence in words. On the 16 it fires only on K0/H4/H5/H6/H13, all already expected True.

**Underivable kinds — recorded as known scoring gaps, never silently mapped to True:**
- `fact` — 44 uses in the bank. 7 fact-only questions (B-111, B-112, B-114, B-120, B-122, B-126, B-228 — all hma-27 C6 questions) are guaranteed boolean + kinds misses.
- `procedure`, non-birth branches — 30 uses (14 non-empty non-birth + 16 empty-GT handoffs).
- `court` as forum-ask — 6 C11 questions (B-186, B-189, B-190, B-191, B-192, B-193 — all explicit "which court" asks).
- `demand` on B-010 (return-to-home + support, no stridhan GT) and B-135 (maintenance, "never asked for money before") — do NOT broaden demand to maintenance to fit these; that would be tuning to the bank.
- `safety` on B-108 (safety without pwdva-18 in GT) — the one safety gap.
- Typed-kinds scoring reports BOTH strict equality (incl. `fact`) and a fact-excluded variant; `fact` is excluded from the predicted scoring set.

**Sealed kinds mapping (`SEALED_KIND_MAP`):** quantum→quantum, safety→safety, written-demand-first→demand, registrar-procedure→procedure, ask_missing_fact→fact, proof→fact; human-lawyer, enforcement, ask-decision → None (unmapped, reported per question, never forced into a kind). Sealed kinds scoring is therefore diagnostic on the mapped subset only.

## Dual escalates scoring (layout)

Every batch summary, both sealed-set sections, and the final cell report BOTH: (a) old boolean escalates score (predicted escalate == GT escalate), and (b) typed-kinds score (predicted kind set == GT kind set, strict; plus the fact-excluded variant). The typed-escalation build itself (D5/D9) is a follow-up — escalates are reported exactly as measured.

## Sealed-set verification (read-only, verified by this lane)

| File | SHA-256 | Result |
|---|---|---|
| `sealed/sealed-fresh-20.json` (F1–F20) | `1d8b5dc376e711c3ac6ead4424bb2d8ce52b07552b9a533ad86e0616dbcf8837` | MATCHES freeze note |
| `sealed/sealed-kannada-8.json` (KN1–KN8) | `2f652af1123a22441cc4158ddf480ef0981aa923858bbcb9dc3622f5e5c25853` | MATCHES freeze note |

Builder also re-checks both SHAs at build time (INPUT FAIL on mismatch). Sealed files were NEVER edited. Sealed `gt_labels` are issue words (maintenance, custody, …), never used for scoring — score from `gt_sections` ids.

**ID normalisation — identity, no renaming needed.** Verified from the v5 live results JSON (`workspace/browser_downloads/sess-3450079326/live-laya-colab-results-v5-precision.json`): the pipeline already emits `hmga-1956-s6` and `welfare-principle` exactly as sealed GT does. The real normalisation is court names: `Judicial Magistrate First Class` → `Magistrate`, `Registrar of Births and Deaths` → `Registrar` (`COURT_NORMALIZE` in Cell 8).
**Court-convention difference (record, do not "fix"):** sealed maintenance-only questions expect Family Court (freeze note §12) while the 16-set expects Magistrate for the same relief; the pipeline follows the 16-set convention, so sealed court scores will show systematic misses on maintenance-only questions (F1, F2, KN1). Sealed court is a single lead forum (e.g. F3 lists only Family Court despite BNSS/PWDVA sections) vs the 16-set listing both courts — scored by lead-forum containment.

**F20 RULE:** F20 is out-of-scope (GT empty, court empty) BUT `gt_escalates=true` as a human-lawyer handoff; the F20-specific rule wins over the generic out-of-scope `escalates=False` rule. Score correct iff the system declines (empty kept, empty court); record `f20_rule_applied` per row.

**Pre-D1-A HMA 27 in sealed GT (score as frozen, do NOT edit):** F8, F9, F10, F16 (fresh-20) and KN3 (Kannada-8) carry `hma-27` with `proceeding_pending` False; the D2 gate drops it, so any hma-27 miss there is a GT-rule note (`hma27_gt_note_ids` in aggregates), not a plain system error. Also note sealed facts use `demand_made: False` where the 16-set uses None.

## G2 amendment text (prepared, NOT applied — gate file NOT rewritten)

**Dated amendment footer (for the parent to sign):**
> Amendment 2026-11-27 — G2 fresh held-out set amended 16 → 20 questions. The fresh-20 sealed set (`sealed-fresh-20.json`, frozen 2026-11-27) replaces the 16-question composition in gate §4. Until this amendment is signed, the fresh-20 score is a measured number only, NOT a gate pass.

**Composition table (verbatim from `sealed/sealed-sets-freeze-note.md`):**

| Requirement | Required | Delivered |
|---|---|---|
| Total | 20 | 20 |
| Maintenance (F1–F4) | 4 | 4 |
| Custody (F5–F7) | 3 | 3 |
| Stridhan (F8–F10) | 3 | 3 |
| Residence (F11–F12) | 2 | 2 |
| Violence/protection (F13–F14) | 2 | 2 |
| Divorce (F15–F16) | 2 | 2 |
| Birth certificate (F17–F18) | 2 | 2 |
| Out-of-scope/escalate (F19–F20) | 2 | 2 |
| Single-issue | ≥ 8 | 13 tagged (11 substantive + F19/F20 single-topic out-of-scope) |
| Multi-issue (≥3 issues) | ≥ 5 | 5 (F10, F14, F15, F16, F18) |
| — of which five-issue | 1 | 1 (F15) |
| Missing facts | ≥ 5 | 5 (F2 income unknown, F4 whereabouts unknown, F5 whereabouts unknown, F10 no proof, F17 no records) |
| No case filed anywhere | 5 | 5 (F1, F5, F7, F13, F17) |
| Case pending | 2 | 2 (F3, F15) |
| Decree already passed (HMA 25 keep-branch) | 1 | 1 (F4) |
| Divorce NOT asked (explicit trap) | ≥ 3, incl. 1 confused/undecided | 4 (F6 undecided, F7-not-tagged*, F12, F13, F18) |
| Negation ("I do NOT want…") | ≥ 2 | 3 (F7, F12, F13) |
| Judicial separation vs divorce | 1 | 1 (F18) |

Gate-doc updates the amendment implies (to be applied on signing, not done here): G2 row 16→20; §4 composition table replaced by the above; §4 step 6, §8 checklist, §3 tier row 10 updated accordingly.
**Accepted deviations:** salary-slips-missing and no-proceeding interim money are not verifiably present in the 20. Kannada-8 composition: KN1 maintenance, KN2 custody (child under 5), KN3 Stridhan (demand not yet made), KN4 residence, KN5 divorce-asked multi-issue, KN6 divorce-not-asked, KN7/KN8 per freeze note.

## Prose — Cell 9: SKIPPED, NOT MEASURED

Per the 10:51 IST scope cut: Cell 9 was NOT built and NOT attempted. Prose is **NOT MEASURED** in this round; the notebook reports Fp as NOT MEASURED (brutal rating capped at 9.0). Design exists (`v6-deep-dive-report.md` §5, `prose-renderer-design.md`, `v6-lane4-prose-latency.md` §2 corrected templates, §4: 4 bugs + 1 gap in the design doc) but building it cleanly was not possible in this scope: Lane 4's fixes need new Cell 6 facts (`child_fact`, `school_fees_fact`, `stridhan_sold`), the stridhan-sold wording needs legal sign-off, user-facing escalation lines for the four new kinds + safety are undefined in the design, and B1 facts for prose would need the same text derivation. Nothing is faked; the gap is reported honestly as missing.

## Latency / G14

Per-question latency recording kept from v5; G14 check print added in Cell 8 and the final cell (mean ≤15 s, max ≤30 s, full 16-run ≤240 s excl. load, load ≤60 s). **Expect FAIL on CPU** — v5 mean was 61.93 s (max 138.2 s). Report honestly; nothing was tuned to pass it. T4 option unverified; no T4 numbers claimed.

## Graph v3 counts + pre-existing defects

Graph v3 verified: **34 sections / 48 nodes / 79 edges** (+2/+2/+2 over v2 = `hma-9` + `pwdva-22` and their leaf nodes/edges), SHA-256 `67bf2b04ca946f7c7fa3062068e01ce051fbce8f4d740c281afe6fff841c34a5`. New sections: `hma-9` = HMA s.9 restitution of conjugal rights; `pwdva-22` = PWDVA s.22 compensation orders. No existing node changed; stage2 block differs (D2 + new sections). R-HMA27-04 `if_fail: drop`, corrected §1.4 wording, zero `alternatively` occurrences.
**Pre-existing v2 defects, carried into v3 byte-identical, out of scope, intentionally NOT fixed:** 3 edges point at non-nodes (`escalate_clarify`, `bns-316`, `escalate_demand_first`); `bnss-144` related_sections carries wrong id `hmga-6` (real id `hmga-1956-s6`, 1 occurrence). Cell 5 assert is counts + SHA only, so these do not block the run.

## Known structural gaps (not fixable in this build)

- **B-018 (`hma-9`) and B-019 (`pwdva-22`) are guaranteed misses** — graph v3 adds only stage-2 leaf nodes; no Stage 1 issue maps to them and `stage2()` has no route emitting them (emitting them needs a new issue prompt + stage2 route, a pipeline change beyond the no-logic-change constraint).
- **Residence GT split:** 5 questions carry PWDVA 17/19 without 18 (B-010, B-023, B-133, B-189, B-214) — the pipeline's full-set 17+18+19 rule adds a pwdva-18 FP if residence fires, so those are structurally non-exact; 15 questions carry pwdva-18 alone (violence-only branch handles those correctly).
- **Kannada fact-derivation limitation:** Kannada-script questions match no English pattern and fall back to defaults (proceeding False, demand None, violence False, residence False, money/gold False), so v5 gates veto almost everything — Kannada scores measure the English-text gates, not the model. Money need without money words reads `money_fact` False; gold as an object reads `gold_fact` True (gate does not veto; model score decides).
- **Bank kind distribution** (counted for the derivation design): kind vocabulary quantum, court, demand, custody, residence, recovery, procedure, fact, safety; category counts C1 30, C2 20, C3 20, C4 20, C5 20, C6 16, C7 16, C8 12, C9 16, C10 12, C11 12, C12 8, C13 16, C14 12. 9 bank questions carry `hma-27` (B-005, B-111, B-114, B-119, B-122, B-123, B-125, B-126, B-228); the bank has no `facts` dict per question.

## Pass bar (for the live run)

Plan §3.2: exact ≥200/230, micro-F1 ≥0.95, micro P/R ≥0.95, mean P/R ≥0.90, court ≥200/230, escalates (typed) ≥200/230, silent 0, Fb 0, Fp 0 if prose exists, model errors 0, no category <75% exact. Rating formula (gate §2): `10×[0.60·E + 0.15·Rm + 0.10·Pm + 0.075·C + 0.075·S] − 0.5·Fb − 1.0·Fp`, clamped [0,10], rounded 1 decimal; caps apply (prose not measured → ≤9.0; Fp≥1 → ≤5.0; Fb≥1 → ≤9.0). Brutal rating always quoted "(brutal bank, n = 230)".

## Things NOT verified by this lane (for the coordinator)

- Nothing about the live run itself (offline only; no Colab, no model calls, no browser).
- Graph v3 counts/SHA were supplied by Lane A and re-verified from the file at build time (builder INPUT FAILs on mismatch) — verified, not assumed.
- The live-run behaviour of `run_one_question` on the 230 bank questions is untested until Colab runs it; the refactor equivalence was verified only by the builder's dedent check + stub-agent tests.
