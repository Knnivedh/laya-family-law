# Lane 07 — P4 legal registry + citations + safety routing (V71-P4-1..P4-4 prep)

- Lane: 07. Scope: plan §4 (V71-P4-1 crosswalk, V71-P4-2 registry, V71-P4-3 safety
  decoupling design, V71-P4-4 ratification PREP only).
- Working copy only: `~/workspace/laya-v71-work`. Date: 2026-11-27.
- Status: **DONE (prep + code, no ratification, no graph edits)**. All three owned
  files exist; self-test 31/31; guardrail tests pass (below).
- Files owned by this lane (ONLY these were created/edited by Lane 07):
  - `legal/verified_authorities.json` (new)
  - `src/laya_legal_registry.py` (new)
  - `docs/ground-truth-v3-ratification-pack.md` (new, PREP ONLY)
  - `docs/10x_swarm_state/lane-07-p4.md` (this file)
- NOT touched by Lane 07: `graph/laya-crpc-bns-section-decision-tree-v4.json`
  (no hand edit — the 16-entry scrub is a builder patch spec, §4 below),
  `src/laya_v7_graph.py` (safety wiring is a patch SPEC in §5, not an edit —
  Lane 01 owns that file, contract C4), `ground-truth-v2-hma27-A.json`,
  brutal bank, sealed sets, any `results/*` file. No `git add/commit/push`
  (coordinator owns that).

## 1. Registry contents — `legal/verified_authorities.json`

Schema v1.0. 9 authorities: **1 verified_primary, 8 unverified**.
Top-level `status` field says so plainly: "PARTIAL — 1 of 9 case authorities
verified_primary; 8 unverified. P2.4/P2.5 are NOT closed by this file."
(The 8th unverified entry is Rashmi Kumar, added from the graph's precedent
fields — see below. The per-entry statuses are authoritative.)

### verified_primary (1)

| id | Case | Evidence for the promotion |
|---|---|---|
| `sukhdev-singh-v-sukhbir-kaur-2025` | Sukhdev Singh v. Sukhbir Kaur, SC, 3-Judge Bench (Oka, Amanullah, Masih JJ.), CA Nos. 2536 & 5726 of 2019, 12 Feb 2025, [2025] 2 SCR 1569 : 2025 INSC 197 : 2025 LiveLaw (SC) 195 | Plan §4.2 adopts the verification recorded in `docs/legal-decisions-v4.md` §Q3 (2026-11-26), corroborated there against the SCR text itself. Lane 07 did NOT re-fetch the SCR PDF in this pass; the `evidence_note` in the entry says so. Holding + limits recorded verbatim: spouse of a void (s.11) marriage may SEEK s.25 permanent alimony / s.24 interim maintenance; grant is discretionary; the decree requirement survives (no support for "HMA 25 with no decree"). `allowed_scopes`: `hma-25_nullity_decree`, `hma-24_nullity_pending`. `forbidden_scopes`: stridhan, custody, residence, general alimony quantum, hma-25-without-decree. |

### unverified (8) — each carries the EXACT verification step required

| id | Case | Why still unverified / exact step required |
|---|---|---|
| `balkrishna-...-1997` | Balkrishna Ramchandra Kadam v. Sangeeta Balkrishna Kadam, (1997) 7 SCC 500 / 1997 INSC 641, 4 Sep 1997 | Read full primary judgment (SCI PDF); confirm the "by including it in the decree" passage and the broad "at or about the time of marriage" holding; record the tension with Babulal's narrow exclusive-Stridhan reading. The v4-doc quotation alone is NOT verification. |
| `babulal-yadav-v-sonu-yadav-2023` | Babulal Yadav v. Sonu Yadav, Chh HC Full Bench, FA (MAT) 40/2022, 4 Jul 2023, 2023 SCC OnLine Chh 2815 | Read full primary judgment; confirm paras 17–18 (ancillary + before-decision timing), 20–21 (exclusive Stridhan outside s.27), 25–29 (CPC s.151 / FCA s.7(1) Expl. (c) route). Record its non-binding weight outside Chhattisgarh. |
| `krishna-kumar-gupta-v-priti-gupta-2025` | Krishna Kumar Gupta v. Priti Gupta, Allahabad HC FA 1116/2024, 31 May 2025 | Read the FULL primary judgment, not the LiveLaw/SCC OnLine news reports; confirm holding, set-aside order, s.25 contrast. |
| `pratibha-rani-v-suraj-kumar-1985` | Pratibha Rani v. Suraj Kumar, (1985) 2 SCC 370 | Read full primary judgment; confirm absolute ownership + custodian/trustee + criminal-breach-of-trust route. Graph itself records it as "lane-supplied, not retest-verified". |
| `rashmi-kumar-v-mahesh-kumar-bhada-1997` | Rashmi Kumar v. Mahesh Kumar Bhada, (1997) 2 SCC 397 | NOT named in plan §4.2, but present in graph v4 precedent fields for hma-27/bns-316 — registered here rather than silently left in the graph. Same "lane-supplied, not retest-verified" status; read full judgment, confirm what it adds beyond Pratibha Rani. |
| `satish-chander-ahuja-v-sneha-ahuja-2020` | Satish Chander Ahuja v. Sneha Ahuja (2020) | Read full primary judgment; confirm exact SCC citation (currently only "(2020)" in the graph) and the shared-household holding + residence-only scope limit. Currently "only checked via prose forbidden list" — that is not verification. |
| `rajnesh-v-neha-2020` | Rajnesh v. Neha, (2021) 2 SCC 324, decided 4 Nov 2020 | Read full primary judgment (SCI PDF already linked in `src/laya_family.py:26`); confirm citation metadata, quantum + affidavit directions, and that `src/laya_family.py:257-261` attaches it to maintenance only. The link's existence in code is not verification. |
| `astha-thakur-v-dhananjay-kanwar-2025` | Astha Thakur v. Dhananjay Kanwar, HP HC DB, FAO (FC) 29/2022, 31 Dec 2025, 2025:HHC:46178 | P2.5: read the FULL primary judgment — specifically unread paras 3–13, 15–17, 19. Erratum §3 records paras 2/14/18/20/21 as read (pendency filing, discretionary "may", FCA s.7(1) Expl. (c) jurisdiction surviving the decree) — those propositions are recorded in the entry's `partially_read` block, but the entry stays `unverified` until the unread paras are confirmed not to contradict them. Warning recorded: "independent application" means independent of the decree, not of any proceeding. |

**Verification rule enforced in the file:** `verified_primary` ONLY on
confirmation from primary judgment text. Secondary summaries, LiveLaw reports,
and `legal-decisions-v4.md` are evidence pointers, never verification.
**Prose gate rule in the file:** consumer prose may emit a precedent string
ONLY in an explicit verified-citation mode AND status == `verified_primary`
AND section in `kept_ids` AND use inside an `allowed_scope`. Default:
zero precedent strings (prose Forbidden Items 1 & 2).

## 2. Crosswalk summary — `src/laya_legal_registry.py`

Pure Python, no torch, no network. CPU self-test: **31/31 passed**
(`python3 src/laya_legal_registry.py`, exit 0).

- **Commencement boundary:** 1 July 2024 (`COMMENCEMENT_DATE`); BNSS via
  S.O. 848(E) verified in-repo at `src/laya_family_evidence.py:117-122`;
  exact Gazette notifications for BNS & BSA still to verify (plan §4.1) —
  recorded in `COMMENCEMENT_NOTE`, not silently assumed.
- **Verified pairs (plan §4.1):** CrPC s.125 ↔ BNSS s.144 (pre-Jul-2024
  orders stay CrPC s.125/127 under BNSS s.531; never emit bnss-144-3/146 on
  them); IPC s.406 ↔ BNS s.316(2) (flag IPC note if entrustment/FIR
  pre-dates 1 Jul 2024); IEA s.65B ↔ BSA s.63 (electronic-evidence
  certificates in doc checklists).
- **Excluded, never mapped:** IPC s.498A ↔ BNS s.85 — `unverified_excluded`
  (frozen 34-section graph, `docs/test-report-v2-layman.md:37`); human-lawyer
  criminal escalation only; never into `kept_ids`.
- **Provisional sub-routes (NOT verified):** CrPC s.125(3) ↔ BNSS s.144(3),
  CrPC s.127 ↔ BNSS s.146, both marked `provisional` with a BNSS-text
  verification step — the plan does not list them as verified pairs, so the
  module does not present them as verified.
- **`existing_order_statute` fact:** `derive_existing_order_statute(facts)`
  returns exactly one of `bnss_144 | crpc_125 | hma_24 | hma_25 | unknown`.
  Precedence: explicit valid value → `pre_bnss_order` True → `crpc_125` →
  `bnss_order` True → `bnss_144` → else `unknown`. A date alone NEVER decides
  the statute; `unknown` is never coerced to `bnss_144`.
- **Lookup API for the unified runtime (Lane 05):**
  `lookup_crosswalk(code)` (either side; excluded dict for 498A/85; None if
  unmapped), `is_pre_bnss(date)` (None when no date),
  `resolve_maintenance_section(facts, order_date=..., existing_order_statute=...)`
  (returns section/None + statute + rule; old-order enforcement/variation →
  section None + `s531_savings` rule; unknown statute → section None +
  `unknown_statute_ask`), `load_authorities()`,
  `check_citation_allowed(authority_id, section_id, scope)` (all-three
  conditions or denied with reason),
  `verified_citations_for_sections(kept_ids, scope)` (today returns at most
  Sukhdev Singh; empty list is the normal correct answer elsewhere).

## 3. Ratification-pack summary — `docs/ground-truth-v3-ratification-pack.md`

**PREPARED — PENDING independent-rater ratification. It does NOT create or
freeze ground-truth-v3 and does NOT modify ground-truth-v2** (SHA
`87818b1b…`). Deltas derived from v2 `gt_ids`/`gt_court`/`gt_escalation_kinds`
as read by Lane 07; no sealed file opened for the pack.

- **D-V4-1 (statutory_primary):** `kept_ids` = statutory only; `hmga-1956-s6`
  + `welfare-principle` → `applied_principles`. Exact rows: K0 9→7, H2 3→1,
  H5 7→5, H14 7→5 kept; v3 kept total **45** (was 53; 8 moved, not deleted).
  Courts unaffected.
- **D-V4-2(a):** H3/H10/H15 court `['Family Court','Magistrate']` →
  `['Magistrate']` (Option C-1, aligns with B-192; C-2 rejected as
  C11-masking). K0 court unchanged (gwa-1890 supplies Family Court).
- **D-V4-2(b):** add `'safety'` kind on K0/H4/H5/H6/H13 (all five carry
  pwdva-18 in v2 GT; consistent with Brutal 31/32 pwdva-18→safety). H6 safety
  is conditional on (d).
- **D-V4-2(c):** H12 — open either/or: Option 1 align to `procedure` handoff
  (like B-172/F20) vs Option 2 keep legacy empty/False with the
  `h12_stays_empty` compat assertion visible.
- **D-V4-2(d):** H6 pwdva-18 — legacy triple bundle (v2 GT, violence=False)
  vs decoupled graph (no violence/lockout → no pwdva-18). Option A keep
  (graph is the error to fix) vs Option B drop (v3 H6 → 4 sections; H6 safety
  falls away). H4 keeps pwdva-18 as the contrast control (lock change =
  dispossession backed by threat).
- **D-V4-2(e):** H14 hma-13 (D6) — Option A keep (governing-section, thinnest
  frozen call, v6 Lane 3 §3.1) vs Option B drop (relief-sought-only; v3 total
  −1; gate the notebook's pending-divorce hma-13 fire in the same change or
  H14 goes non-exact by FP).
- **D-V4-3:** confirm adjudicated lump-sum rule — hma-25 iff `decree` OR
  (`lump_sum_settlement` AND (`divorce_asked` OR `proceeding_pending_hma`));
  B-022/B-119/B-154 (+B-201) must not draw false `Fb`; strict pre-decree
  `Fb=0` on standard maintenance preserved; Sukhdev gives no support to
  "HMA 25 with no decree".
- **D-V4-4:** sealed sensitivity documentation only — F8/F9/F10/F16/KN3
  pre-D1-A hma-27; F1/F2/KN1 Bengaluru FCA s.7(2)(a) Family Court vs
  Magistrate. Recorded from plan §4.4 / v4-arch §5.2 / freeze-note §12 as
  cited; sealed-v2 commissioning put to the rater. No sealed text opened.
- **Projected totals:** D-V4-1 only 45; + (d)B 44; + (e)B 44; both 43.
- **Blockers listed in the pack (§0):** recovery-text fix ("under HMA s.27"
  must go before any run scores those kinds); D5/D7/D11 carried, undecided;
  sealed-set HMA 27 question must be decided before any sealed run is scored.
- **Adjudication template (§7):** rater name/role/date, per-item decision
  table with reasoning + GT effect, final kept total, signature block,
  coordinator instruction (create v3 as a NEW file, copy the signed record
  into its header, trigger Gate §6.1 re-run). Unsigned — authorises nothing.

## 4. Graph citation scrub — BUILDER PATCH SPEC (not an edit)

Per contract C4 / task instruction, Lane 07 did **not** hand-edit
`graph/laya-crpc-bns-section-decision-tree-v4.json`. The spec lives in
`legal/verified_authorities.json` under `graph_scrub_spec` (authority-id map,
replacement rule, exit check). Summary:

- **16 section entries to scrub:** bnss-144, hma-24, hma-25, pwdva-20, hma-26,
  gwa-1890, hmga-1956-s6, welfare-principle, hma-27, bns-316, pwdva-17,
  pwdva-18, pwdva-19, proc-filing-magistrate, doc-stridhan-list-proof,
  doc-residence-proof (plan §4.2 list).
- **Lane 07 grep verification (this pass):** case-name strings found in the
  `precedent` field for bnss-144, hma-24, hma-25, pwdva-20, hma-27, bns-316,
  pwdva-17, pwdva-19 (Rajnesh; Pratibha Rani + Rashmi Kumar; Satish Chander
  Ahuja); found only inside scope-limit notes for hma-26, gwa-1890,
  hmga-1956-s6, welfare-principle, pwdva-18 (e.g. "NEVER cite Satish Chander
  Ahuja for custody"); **no case-name string found in the `precedent` field**
  for proc-filing-magistrate, doc-stridhan-list-proof, doc-residence-proof.
- **Builder must also scrub** case names in `stage2/global_guardrails`
  (g-rajnesh), `stage2/rechecks_detail[*].checks[*].condition` /
  `drop_reason` / `guardrails`, `stage1/mappings_detail/mappings[7].ambiguity_rule`,
  `nodes[10]`/`nodes[15].question`, plus `precedent_never_to_cite`,
  `exclusions`, and `related_sections[].relationship` strings.
- **Replacement rule:** every embedded case-name string →
  `{"authority_id": "<id>", "use": "<scope>", "never_use_for": [...]}`;
  keep scope-limit text as a machine-readable list, not free prose.
- **Exit check:** after the scrub, grepping graph v4.1 for
  (Rajnesh|Satish Chander Ahuja|Pratibha Rani|Rashmi Kumar|Sukhdev|Balkrishna|
  Babulal|Krishna Kumar Gupta|Astha Thakur) must return 0 matches outside the
  registry file. **Caveat:** for the three no-hit entries the builder must
  confirm whether a case string exists elsewhere in the entry before declaring
  it clean — Lane 07 did not assume clean.
- **Applies to:** Lane 05's v4.1 build (`graph/laya-crpc-bns-section-decision-tree-v4.1.json`),
  not to frozen v4.

## 5. Safety decoupling design — PATCH SPEC for `src/laya_v7_graph.py` (Lane 01 applies; Lane 07 does not edit)

**Current state found (read-only, `src/laya_v7_graph.py`, 575 lines):**

- `_derive_escalations_v7()` (L231; `urgent_safety` param L235) already has a
  safety block at L268–269 with the comment "Safety is ALWAYS independent of
  statute eligibility and kept counts": fires if `"pwdva-18" in kept` OR
  `custody_risk` (L239, `child_safety_risk`) OR `urgent_safety`.
- BUT `urgent_safety` is computed at L362 as
  `proved_true(facts, "urgent_safety_risk") or violence` — and
  `urgent_safety_risk` is one of the 8 dead keys (never emitted by Stage 0/1,
  plan §1.1), so in practice the only live trigger is `violence`.
- `coercive_eviction_or_lockout` (L363) and `stay_in_house_under_eviction_pressure`
  (L364) do NOT feed the safety trigger — they feed only the pwdva-18
  disposition at L530–537, which is gated by `pwdva_eligible`
  (`(sex != "male") and dom_rel`, L520). Consequence: a male DV victim (B-148),
  a non-domestic assault/workplace case (B-181), or a coercive-lockout case
  with no violence gets NO safety escalation when pwdva-18 is gated out —
  even though the plan's decoupling rule says safety must fire independently
  of `claimant_sex`, `domestic_relationship`, `proceeding_pending_hma`,
  `demand_made`, and clarification holds.
- Safety text today is generic ("Safety risk indicated — escalate urgently…",
  L269); there is no helpline block and no severity grading anywhere in the
  graph file. Helpline rendering is prose-side (Lane 01/09 apply it from the
  structured head this spec returns).

**Precise patch spec (apply to `src/laya_v7_graph.py`; line numbers are this
working copy's):**

1. **New function `_derive_safety_head(facts) -> dict`, placed immediately
   before `_derive_escalations_v7()` (L231).** Pure function of `facts` only —
   it must NOT read `kept`, `sex`, `dom_rel`, `negated`, `pending_hma`,
   `being_filed`, `demand_made`, or any clarification/pending state.
   ```python
   def _derive_safety_head(facts):
       urgent = proved_true(facts, "urgent_safety_risk")
       violence = proved_true(facts, "violence")
       lockout = proved_true(facts, "coercive_eviction_or_lockout")
       stay_press = proved_true(facts, "stay_in_house_under_eviction_pressure")
       child_risk = proved_true(facts, "child_safety_risk")
       explicit_res_only = proved_true(facts, "explicit_residence_order_only")
       threat = violence or lockout or stay_press
       imminent = urgent or child_risk or (violence and (lockout or stay_press))
       # Over-fire guard: explicit-residence-only with NO violence/lockout/
       # pressure/child-risk/urgent fact must not fire safety (B-010/B-133/B-189).
       fire = (imminent or threat) and not (
           explicit_res_only and not (violence or lockout or stay_press
                                      or child_risk or urgent))
       severity = ("imminent_physical_or_child_danger" if imminent
                   else "threat_or_harassment" if threat else "none")
       if not fire:
           severity = "none"
       return {"fire": fire, "severity": severity,
               "triggers": {"urgent_safety_risk": urgent, "violence": violence,
                            "coercive_eviction_or_lockout": lockout,
                            "stay_in_house_under_eviction_pressure": stay_press,
                            "child_safety_risk": child_risk}}
   ```
   Severity vocabulary is exactly `none | threat_or_harassment |
   imminent_physical_or_child_danger` (plan §4.3). Rationale for the
   `imminent` clause: `urgent_safety_risk` or `child_safety_risk` alone is
   imminent; `violence` + lockout/pressure together is imminent (escalating
   physical + coercive pattern); violence/lockout/pressure alone is
   `threat_or_harassment`. No new fact keys are invented — all five inputs
   already exist in the codebase (L239/L362–L364); `urgent_safety_risk` stays
   in the spec so the head works the moment Lane 01 wires that dead key
   (P1-1), and `violence` keeps it live until then.
2. **Call site in `evaluate_stage2_v7()` (L317):** immediately after the
   existing L361–L365 block (`violence` / `urgent_safety` / `coercive_lockout`
   / `stay_eviction_press` / `explicit_res_only`), insert
   `safety_head = _derive_safety_head(facts)`. Do NOT move or re-gate the
   L361–L365 computations — pwdva-18 disposition (L530–537) keeps using them
   unchanged, so section routing is untouched by this patch.
3. **Replace the L268–269 safety block inside `_derive_escalations_v7()`:**
   delete the `if ("pwdva-18" in kept) or custody_risk or urgent_safety:`
   append (it double-counts once the head exists and it misses lockout-only
   cases) and replace it with a merge of the head passed in as a new parameter:
   change the signature at L231 to
   `_derive_escalations_v7(kept, facts, court_source, urgent_safety, safety_head=None)`
   and, where the old block was, insert
   `if safety_head and safety_head["fire"]: esc.append({"kind": "safety", "text": <helpline-aware text from the head's severity>})`.
   Keep the parameter `urgent_safety` for backward compatibility (callers at
   L400/L560 pass it); it becomes informational only for safety.
   **Both call sites must pass the head:** L400 (the `not in_scope` branch —
   safety MUST fire on out-of-scope/abuse queries too, e.g. B-148/B-181 with
   `kept == set()`) and L560 (normal return). The returned dict at both sites
   gains a top-level `"safety": safety_head` field so prose and the scorer can
   read severity without re-deriving it.
4. **Helpline block (prose-side, Lane 01/09 to render; this spec fixes the
   exact strings):** when `safety_head["fire"]` is True, the consumer response
   MUST open with this block, before any legal section, court, or procedural
   question — never gated behind "first clarify if an HMA case is pending":
   > "If you are in immediate danger, call 112 (Police / Emergency) now. Women
   > Helpline: 181. Childline: 1098. You can also contact the Protection
   > Officer or the nearest One Stop Centre for immediate protection and
   > support."
   Severity `imminent_physical_or_child_danger` uses the block verbatim with
   the "call 112 now" first sentence; `threat_or_harassment` uses the same
   block without "now" urgency rewording (same numbers, same order).
   The block is emitted from the structured `safety` field, not from prose
   free text, so `prose_forbidden_check()` can assert its presence/absence.
5. **Over-fire guard (tests to add with the patch — Lane 01):**
   `explicit_residence_order_only=True` with no violence/lockout/pressure/
   child-risk/urgent fact → `fire=False`, severity `none` (B-010, B-133, B-189
   controls; these must also NOT fire pwdva-18 — already handled at L530 via
   `protection_trigger ... and not explicit_res_only`).
   Positive controls that MUST fire regardless of sex/domestic/proceeding/
   demand: B-148 (male DV victim), B-181 (non-domestic assault), B-108
   (child abduction / alcoholic-parent risk), unclarified-scope abuse queries.
   C18 (plan §7.2) is the acceptance suite: 100% safety recall on those
   scenarios, 0 false safety triggers on benign residence-only queries.
6. **What this spec deliberately does NOT change:** pwdva-18 eligibility
   (`pwdva_eligible`, L520) and the pwdva-17/18/19 per-section split (L520–
   L537) are untouched — safety is orthogonal to, not a replacement for,
   section routing. `court_for_v7()` (L151) is untouched — safety never
   changes the forum. No new Stage 0/1 fact keys are introduced here; wiring
   `urgent_safety_risk` / `child_safety_risk` emission is Lane 01 (P1-1).

## 6. Guardrail compliance (verified by Lane 07)

- Frozen files untouched: `python3 tests/test_graph_v4.py` →
  "GRAPH V4 + FROZEN SHA TEST PASS: 34 sections / 66 nodes / 99 edges,
  0 dangling edges, 7/7 frozen hashes intact."
- `python3 tests/test_prose_renderer_v2.py` →
  "PROSE VALIDATION PASS: 246 cases, Fp=0, quality_flags=0, 15/15 adversarial
  mutants caught, mean=0.0166ms, max=0.132ms".
- Sealed sets: never opened (only plan/architecture/freeze-note aggregates
  cited in §3 D-V4-4). Brutal bank / GT v2 / filed results: never edited.
  `git status` for Lane 07's paths shows only the three new files above (+
  this status file); no other file was modified by this lane. (Note: `git
  status` also shows other lanes' in-flight files and two pre-existing
  modifications — `docs/10x_swarm_state.md`, `src/build_graph_v4.py` — which
  are NOT Lane 07's; left alone.)
- No GPU/torch used. No git write commands run.

## 7. Blockers / what needs a human or the RTX machine

- **Human — independent rater (blocking for v3):** every **RATER DECIDES**
  item in the ratification pack (§7 template): D-V4-1 confirmation, D-V4-2
  (a)–(e), D-V4-3, D-V4-4, plus carried D5/D7/D11 and the §0 recovery-text
  fix. Nothing in this lane's output authorises creating v3.
- **Human — primary-judgment verification (blocking for P2.4/P2.5 close):**
  all 8 unverified authorities need a reader of the full primary judgments
  (steps in §1). Lane 07 verified nothing from primary text in this pass
  except by adopting the plan's Sukhdev record.
- **Human — BNS/BSA Gazette check:** exact commencement Gazette notifications
  for BNS & BSA (plan §4.1); BNSS S.O. 848(E) is the only one verified in-repo.
- **Human — Lane 01 / coordinator:** apply the §5 safety patch spec to
  `src/laya_v7_graph.py` and the §4 scrub spec to graph v4.1; Lane 07 must not
  do either (contract C4 + task instruction).
- **RTX 5050 / Colab T4 (not this VM):** nothing in Lane 07's scope needs a
  neural run. The P4 exit criteria that DO need runs — C17 cross-walk tests
  (100% pass, 0 misrouted bnss-144-3/146) and C18 safety scenarios (100%
  recall, 0 false triggers) — can only be executed after Lane 01 applies the
  §5 patch and Lane 05 wires the registry into the unified runtime; record
  them as pending, not passed.
