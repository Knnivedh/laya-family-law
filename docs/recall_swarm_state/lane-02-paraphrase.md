# Lane 02 — Paraphrase Expansion (recall swarm, V71-P1-2 follow-up) — Status

- **Lane:** 02 Paraphrase expansion
- **Status:** DONE — corpus grown, gate passing, tests passing, committed by this lane.
- **Working copy:** `~/workspace/laya-v71-work`, HEAD `1cb0bff` at start.
- **Files owned and touched (only these):** `scripts/build_synthetic_corpus.py`,
  `data/synthetic_v7_1/` (`train.jsonl`, `validation.jsonl`, `manifest.json`,
  `schema.json`, `leakage_report.json`), plus this status file
  `docs/recall_swarm_state/lane-02-paraphrase.md`.
- **Files NOT touched:** every other lane's files. In particular
  `scripts/kn_templates.py` is Lane 05's file (this lane only *imports* it —
  see §3); `src/laya_v7_evidence.py` shows as modified in the tree but that
  is Lane 03's work, left untouched and uncommitted by this lane.
- **Sealed discipline:** `test-bank/sealed/*.json` was never opened. The
  held-out Kaanoon eval set `data/kaanoon_eval/heldout.jsonl` (Lane 11) was
  never opened, read, or used for templates, training, or tuning (contract
  R6). Templates come only from statutory grammar + the Lane 11 study-sample
  patterns file (contract R7). No test-bank, ground-truth, or fixture
  question text was read, copied, or paraphrased by the builder.

## 1. What changed — new totals

| | Before (10x Lane 02) | After (this lane) |
|---|---|---|
| Total records | 5,000 | **8,000** |
| Train / validation | 4,500 / 500 | **7,500 / 500** (seed 7102, unchanged) |
| Languages | EN 2,316 / KN 1,333 / kn_roman 1,351 | **EN 3,808 / KN 2,084 / kn_roman 2,108** |
| Validation langs | EN 228 / KN 153 / kn_roman 119 | **EN 235 / KN 153 / kn_roman 112** |
| Merge warnings | none | **none** |

Per-cluster counts (total, train / validation) — measured on the final
frozen files:

| Cluster | Before | After | Train | Validation |
|---|---|---|---|---|
| core (single) | 1,400 | **2,000** | 1,865 | 135 |
| combo | 1,300 | **1,900** | 1,792 | 108 |
| hn_a custody-vs-residence | 250 | **350** | 336 | 14 |
| hn_b residence/dv-comp | 300 | **450** | 420 | 30 |
| hn_c divorce/pending/JS/restitution | 350 | **550** | 504 | 46 |
| hn_d stridhan/joint-property | 300 | **450** | 424 | 26 |
| hn_e maintenance variants | 300 | **400** | 379 | 21 |
| hn_f hypothetical/quoted/past/OOS | 600 | **900** | 853 | 47 |
| neg (explicit denials) | 150 | **350** | 326 | 24 |
| conflict | 50 | **200** | 184 | 16 |
| hn_g incidental-mention traps (NEW) | 0 | **250** | 232 | 18 |
| hn_h modality traps (NEW) | 0 | **200** | 185 | 15 |

Issues requested (before → after): maintenance 2,255→**3,171**,
custody 792→**1,390**, residence 831→**869**, divorce 385→**596**,
stridhan 365→**748**, joint_property 296→**442**, violence 408→**624**,
dv_compensation 134→**282**, restitution 118→**267**,
birth_certificate 135→**333**, procedure 135→**319**.
Issues denied (new coverage): residence 0→**22**, joint_property 0→**23**,
dv_compensation 0→**24**, restitution 0→**29** (maintenance 86→111,
custody 33→32, divorce 197→427, stridhan 62→57).

Facts supported (before → after, thinnest first): child_safety_risk 50→**243**,
being_filed 66→**223**, judicial_separation_only 73→**133**,
mutual_consent 104→**180**, stridhan_sold_or_mortgaged 100→**131**,
interim_asked 128→**151**, lump_sum_settlement 142→**219**,
decree 183→**210**, dv_injury_comp_asked 134→**282**,
restitution_asked 118→**267**, birth_cert_asked 135→**333**,
demand_made 309→**421**, joint_property_claim 296→**482**,
proceeding_pending_hma 304→**370**, existing_order_enforcement 295→**330**,
explicit_residence_order_only 141→**105** (see note below),
child_maintenance_only 358→**579**, school_fees_fact 358→**640**.
Facts conflicting (new, was divorce_asked only 50): divorce_asked **44**,
money_fact **42**, custody_claim **89**, residence_claim **30**,
stridhan_claim **31** (total 236, was 50).
Enums: sex F 4,191→**6,735** / M 255→**361** / U 554→**904**; role spouse
4,362→**6,951** / parent 84→**107** / child 95→**85** / other 459→**857**;
modality present 4,640→**7,133** / past 188→**378** / future 66→**223** /
hypothetical 58→**141** / quoted 48→**125**.

Note on `explicit_residence_order_only` (141→105) and role `child`
(95→85): both fell in absolute terms while the corpus grew 60% — adding
blocks to a pool dilutes per-block sampling (same effect Lane 05 measured
at fixed N). Both were lifted part-way back by the balance pass (§2):
explicit-only was 89 before the extra `residence_explicit_only` combo;
child role was 62 before the `maint_child_self` combo. They remain the
two thinnest supported counts to watch; no further action taken here
because the thin-cluster target in the task brief was met for the five
named clusters.

## 2. What was added (blocks)

**New blocks in `scripts/build_synthetic_corpus.py` (all EN + KN + kn_roman,
2 templates each unless noted; `[[key:phrase]]` span markup, `{slot}`
placeholders from the builder's `SLOTS`):**

- Thin clusters — `birth_cert_late`, `birth_cert_correction`,
  `birth_cert_lost`; `procedure_documents`, `procedure_fees`,
  `procedure_timeline` (+3rd template: time-limit ask);
  `dv_comp_medical`, `dv_comp_mental`, `dv_comp_lost_wages`;
  `restitution_wife_left` (+3rd template: left without telling anyone,
  away a year), `restitution_desertion`; `js_only_living_apart`,
  `being_filed_custody`, `being_filed_maintenance`, `mutual_refused`,
  `mutual_agreed_terms`; `child_risk_alcoholic`,
  `child_risk_abduction`, `child_risk_neglect`;
  `multi_ask_maint_stridhan`, `multi_ask_custody_maint` (numbered
  multi-question asks); `stridhan_after_decree` (post-decree recovery).
- Conflict (was 1 block, now 5) — `conflict_custody`,
  `conflict_maintenance`, `conflict_residence`, `conflict_stridhan`
  (new `conflicting` facts for custody_claim, money_fact,
  residence_claim, stridhan_claim).
- Near-miss denials (neg, was 5 blocks, now 12) — `neg_residence`,
  `neg_stridhan`, `neg_joint`, `neg_dvcomp`, `neg_restitution`,
  `neg_soft_divorce`, `neg_soft_js` (soft denial: "not agreeing",
  "divorce is not essential").
- hn_g incidental-mention traps (NEW cluster) — `bg_violence_past`,
  `bg_stridhan_mention`, `bg_residence_mention`, `bg_joint_property`,
  `bg_birth_cert`: the issue is mentioned as background and labelled
  `incidental`, never `requested`.
- hn_h modality traps (NEW cluster) — `hypo_custody`, `hypo_stridhan`,
  `quoted_maintenance`, `quoted_residence`, `past_violence_stopped`
  (past violence, current ask is maintenance only),
  `past_threats` (past threat never acted on, current ask is divorce).
- OOS domains (12→16) — `oos_workplace`, `oos_shop_sale`,
  `oos_hospital_bill`, `oos_dowry_punishment`.
- 3rd templates added to existing blocks (Kaanoon-informed, §5):
  `maint_arrears` ("he paid for three months, then stopped"),
  `stridhan_held` (list + photos evidence), `custody_mother` ("Is there
  any legal way for me to get custody of my baby?"), `violence_beats`
  (habitual drinker + hospital), `violence_threats` (threat as a
  condition on asking for money).
- Framing: EN prefix +"Please suggest what I should do. ",
  EN suffix +" Please guide me on what to do next."
- Combos: 28→57 entries, incl. hma-27 positives
  (`joint_property` + `divorce_pending` / `being_filed_maintenance`),
  hma-26 positives (`divorce_pending` + `custody_mother`,
  `joint_property_hma_pending` + `custody_mother`), and balance combos
  for joint_property / proceeding_pending / decree / interim /
  explicit-only / child-role / parent-role.

**PLAN (was 5,000, now 8,000):** single 2,000 / combo 1,900 / hn_a 350 /
hn_b 450 / hn_c 550 / hn_d 450 / hn_e 400 / hn_f 900 / neg 350 /
conflict 200 / hn_g 250 / hn_h 200. Validation stays 500 (R1: the
validation split is the only progress number).

## 3. Lane 05 wiring (contract R4)

`main()` in the builder now tries `import kn_templates` (Lane 05's file,
25 blocks) and calls `kn_templates.validate()` +
`wire_into_builder(sys.modules[__name__])` before `generate()`; if the
file is absent it prints a note and builds without it. Wiring confirmed
in every build log: `wired Lane 05 kn_templates: {'en': 50, 'kn': 54,
'kn_roman': 71}`. The builder's own `kn_templates.py` file was never
edited by this lane. (Lane 05's §4b dilution note is why the PLAN/N_TOTAL
growth in §2 matters: wiring alone at fixed N=5,000 could not raise thin
raw counts; at N=8,000 it does — e.g. KN-family validation counts and
stridhan/violence diversity both rise.)

## 4. Lane 01 diagnosis — what it changed

`docs/recall_swarm_state/lane-01-diagnosis.md` landed mid-task (after the
first build). Its Lane-02 items and this lane's response:

- **Zero-recall EN facts (decree / restitution / dv-comp / demand /
  explicit-only / JS-only / child-safety, §4e):** the new blocks add
  surface forms for exactly these — "divorce was decided by the court"
  (`divorce_decree_done` already had it; `stridhan_after_decree` adds
  decree+stridhan), "come back home and live with me"
  (`restitution_*`), "compensation for my injuries and medical costs"
  (`dv_comp_*`), "asked for it back" (`stridhan_held` 3rd template,
  `stridhan_display`), "I only want an order that I can live in our
  shared house" (`residence_explicit_only`, unchanged), "maintenance
  only for my daughter" (`maint_child_only`, `maint_partial_fees`,
  `bg_violence_past`), "beats our son" (`child_risk_*`). These are
  corpus-side fixes; the regex fixes themselves belong to Lane 03.
- **hma-26 (0 oracle positives in old validation) / hma-27 (only 10):**
  measured on the NEW split with `evaluate_stage2_v7`
  (custody_vocab="v3_bundled", same oracle construction as Lane 01):
  validation hma-26 **9**, hma-27 **13**; train hma-26 **140**, hma-27
  **162**. hma-26 is fixed; hma-27 validation is still thin (13/500) —
  the D2 gate needs pending/being-filed alongside joint_property, and
  the validation slice is small; train has 162.
- **Schema gaps (NOT done — coordinator decision, see §7):** Lane 01
  asks for `interim_only_asked` plus the 7 missing dead-8 facts in the
  schema. This lane did NOT expand the schema 28→36 facts: Lane 04's
  classifier (`src/laya_v7_classifier.py:105`, fact head `[28, 4]`),
  the train script, and Lane 07's harness all hardcode/import the
  28-fact list, so a unilateral schema change mid-swarm would drift
  from the code that trains on it (contract R2: coordinator
  reconciles). The 8 facts and the blocks that would populate them are
  listed in §7 for a schema-bump decision.

## 5. Kaanoon — what it contributed (R6/R7)

**Direct read by this lane (before Lane 11's file landed):** 2 web
searches + 1 public page fetch (`kaanoon.com/22593/maintenance-from-husband`,
text fetch only, no browser work). Patterns observed then and used:
dated narrative openers, numbered multi-question asks, arrears/execution
framing ("he paid for three months, then stopped"), "how do I file this
myself" procedure asks, post-decree stridhan recovery, husband-side
questions. No Kaanoon question or answer text was copied into the corpus.

**Lane 11 patterns file (`docs/kaanoon_phrasing_patterns.md`, study
sample KAN-S01–S16 only) landed after the first build; reconciliation
pass applied — pattern → template mapping:**

| Pattern (Lane 11) | Template change |
|---|---|
| Narrative first, question last ("Kindly advice how to proceed") | NEW `narr_maint_separated`, `narr_custody_separate` (story sentences + closing ask) |
| "Live separately with the child" custody framing | `narr_custody_separate` template 1 |
| School-fees itemisation (bus/dress/books, partial payment) | NEW `maint_partial_fees` |
| Enforcement fear as jail / confiscation (husband asker) | NEW `maint_enforcement_fear` (hn_e, male enums, maintenance `incidental`) |
| Settlement-first divorce framing ("end the litigations", mediator terms) | NEW `divorce_settlement_terms` |
| Stridhan argued from wedding display / photos / video | NEW `stridhan_display` (hn_d) |
| "Asked to leave / not taken back" lockout story | NEW `residence_asked_to_leave` (hn_b) |
| Restitution as disappearance + separation duration | 3rd template on `restitution_wife_left` |
| Violence with frequency/habit words + injury as proof | 3rd template on `violence_beats` (habitual drinker, hospital) |
| Threats quoted as conditions ("not dare to ask for a single rupee") | 3rd template on `violence_threats` |
| Joint property as yes/no rights question + documents in joint name | NEW `joint_property_rights` |
| Time-limit question | 3rd template on `procedure_timeline` |
| Third-party asker: son for mother, mother-in-law | NEW `third_party_son` (hn_f) |
| Soft negation ("not agreeing for the divorce", "divorce is not essential") | NEW `neg_soft_divorce`, `neg_soft_js` |
| Dowry punishment question (no Laya section) | NEW OOS `oos_dowry_punishment` |
| Numbered sub-questions; third-party askers; fear of child taken away | Already covered (`multi_ask_*`, `third_party`/`quoted_*`, `child_risk_abduction`) — no change |
| Unedited lay misspellings | NOT added (Lane 05 already covers spelling variants; more misspelt templates would teach wrong spellings) |
| Owner-side "let her out" eviction ask; "stopped going to court"; mother's-gold-vs-father | NOT added — no Laya section / no schema fact / would mislabel `stridhan_claim` |

**Held-out eval set:** `data/kaanoon_eval/heldout.jsonl` exists (Lane 11)
but was never opened by this lane — evaluation only, Lane 07 scores it.

## 6. Leakage gate — exact output (final run)

Command: `python3 scripts/check_ngram_leakage.py --out data/synthetic_v7_1/leakage_report.json`

```
corpus=8000 refs=408 overlap_8grams=0 max_cosine=0.8269 (threshold 0.9) -> PASS
  ground-truth/ground-truth-v2-hma27-A.json: overlap=0 max_cosine=0.7805 synthetic_ids=[]
  test-bank/brutal-bank-v1-frozen.json: overlap=0 max_cosine=0.8269 synthetic_ids=[]
  tests/fixtures/laya_maintenance_development.json: overlap=0 max_cosine=0.6776 synthetic_ids=[]
  tests/fixtures/laya_maintenance_verification.json: overlap=0 max_cosine=0.6249 synthetic_ids=[]
  tests/fixtures/laya_maintenance_challenge.json: overlap=0 max_cosine=0.6922 synthetic_ids=[]
  tests/fixtures/laya_maintenance_final_check.json: overlap=0 max_cosine=0.7217 synthetic_ids=[]
  top cosine hits: [{'cosine': 0.8269, 'synthetic_id': 'SYN-TR-4228', 'ref_file': 'test-bank/brutal-bank-v1-frozen.json', 'ref_id': 'B-058'}, {'cosine': 0.7805, 'synthetic_id': 'SYN-TR-0117', 'ref_file': 'ground-truth/ground-truth-v2-hma27-A.json', 'ref_id': 'H14'}, {'cosine': 0.7762, 'synthetic_id': 'SYN-TR-2366', 'ref_file': 'test-bank/brutal-bank-v1-frozen.json', 'ref_id': 'B-142'}]
```

Gate exit code 0. **First run of the expanded corpus FAILED** (7 shared
8-grams: 3 vs 16-Q, 4 vs Brutal-230, max cosine 0.8182) from three new EN
templates — `conflict_custody` template 2 ("One moment I want my
{child_word} to live with me…"), `being_filed_custody` template 2
("…custody petition for my {child_word}. What should I do first?"),
`child_risk_alcoholic` template 2 ("…and I want my {child_word} to stay
with me"). All three were reworded ("belongs with me / then I wonder
whether…", "What is the first thing I should arrange?",
"…to remain under my care") and the gate re-run passes. The colliding
8-grams were identified from the gate's synthetic record ids plus a
scratch comparison script (`/tmp/lane02_find_overlap.py`, not a repo
file); no reference text was printed or copied. Sealed check: QUEUED as
before — no `sealed-hash-index.json` exists; trusted command (coordinator
/ rater only) is unchanged from the 10x lane status file. Corpus must not
be called fully leakage-cleared until that returns 0.

**Rebuild note: CHANGED, not byte-identical to the 5,000-record corpus**
(expected — N_TOTAL 5,000→8,000, 60+ new blocks, new PLAN, Lane 05
wiring). Rebuild determinism verified: re-running the final builder
produces byte-identical files (train + validation + manifest +
leakage_report hashes match across consecutive runs; see hashes below).

Final SHA-256:

```
0de7ddd73e5cd371f4d866fc980881757ba9ec30d209ac2524cba94e26a48156  data/synthetic_v7_1/train.jsonl
7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e  data/synthetic_v7_1/validation.jsonl
f052548f4c2c9d50f319f395abbd03c5cc649d010339a54410fdc72211483f7a  data/synthetic_v7_1/manifest.json
44b9aa1cd7f0255e1f608f2f025beb799f2740045953042ab653e14e00bd800c  data/synthetic_v7_1/leakage_report.json
bce57abf37f4a2b47c4bbd434ef79585c8426731a15cfe9adaed5f2c134c5123  scripts/build_synthetic_corpus.py
```

## 7. Verification log (commands + exact outputs)

```
python3 scripts/build_synthetic_corpus.py
wired Lane 05 kn_templates: {'en': 50, 'kn': 54, 'kn_roman': 71}
wrote 7500 train + 500 validation -> data/synthetic_v7_1 (seed=7102)
languages: {'kn_roman': 2108, 'en': 3808, 'kn': 2084}
clusters: {'hn_h': 200, 'combo': 1900, 'hn_c': 550, 'hn_d': 450, 'hn_e': 400, 'core': 2000, 'hn_f': 900, 'hn_g': 250, 'hn_a': 350, 'hn_b': 450, 'neg': 350, 'conflict': 200}
merge warnings: none

python3 scripts/check_ngram_leakage.py --out data/synthetic_v7_1/leakage_report.json
-> PASS (exact output in §6), exit 0

python3 tests/test_graph_v4.py
GRAPH V4 + FROZEN SHA TEST PASS: 34 sections / 66 nodes / 99 edges, 0 dangling edges, 7/7 frozen hashes intact.

python3 tests/test_prose_renderer_v2.py
PROSE VALIDATION PASS: 246 cases, Fp=0, quality_flags=0, 15/15 adversarial mutants caught, mean=0.0189ms, max=0.132ms
```

No GPU/torch used anywhere; no neural runs; no training run (Lane 04 +
RTX 5050 are downstream). No 70% claim is made here — the corpus is a
precondition; measurement is Lane 07's harness on the validation split
and, for sealed sets, the RTX re-run only.

## 8. Still unverified / open (for the coordinator)

- **Sealed leakage check QUEUED** — no sealed hash index exists; see §6.
  Corpus is cleared on readable refs only.
- **P2.1 native Kannada audit — OPEN.** All new KN/Kanglish templates
  (mine and Lane 05's) are plain everyday Kannada written for this corpus,
  not native-speaker-audited. P2.1 must audit before any training run
  treats the KN split as gold.
- **Schema-bump decision (Lane 01 §8, NOT done here):** add 8 facts to the
  corpus schema — `interim_only_asked` (pending-HMA interim-only → hma-24
  alone; without it the 9-FN oracle artifact recurs on every validation
  run), plus the 7 dead-8 keys `money_fact_child_or_parallel`,
  `stay_in_house_under_eviction_pressure`,
  `stridhan_held_by_inlaws_refused`, `stridhan_safe_in_own_possession`,
  `stridhan_abandoned_or_undisputed`, `urgent_safety_risk`,
  `hypothetical_or_joint_prop_fact_only`. Blocks that would populate
  them already exist in nascent form: `maint_interim_pending` (interim
  only), `stridhan_held` / `stridhan_safe` (held-by-inlaws-refused /
  safe-in-own-possession), `lockout` / `residence_thrown_out` (stay under
  eviction pressure), `violence_child_risk` / `child_risk_*` (urgent
  safety). Doing this needs Lane 04 to move the fact head `[28, 4]` →
  `[36, 4]` and Lane 07 to update the harness — coordinator call, not a
  Lane 02 unilateral change.
- **hma-27 validation still thin (13/500)** despite train 162 — see §4.
  If the coordinator wants validation-side hma-27 power, the split (not
  just the corpus) needs stratification.
- **No training run was done here** (no GPU/torch on this VM) — training
  (Lane 04 code + RTX 5050 run) is downstream; the corpus + gate are the
  deliverable.
- **Kaanoon held-out eval set untouched** by this lane (R6); Lane 07
  scores it. Lane 11's patterns file was applied (§5); if Lane 11
  revises it, a follow-up template pass may be needed.

## 9. SPLIT FREEZE (coordinator action, 2026-11-27 ~19:34 IST)

`data/synthetic_v7_1/validation.jsonl` is **FROZEN** exactly as it was at
the freeze point — it was regenerated 4 times during the swarm and must
not be regenerated again. Frozen file:

- sha256 `7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e`
  (500 records; verified unchanged by the freeze-adoption build below)
- `manifest.json` now records `frozen_validation_sha256` (same hash),
  `frozen_validation_at: 2026-11-27T14:06:10.824537+00:00` (19:36 IST),
  and `frozen_validation_note` ("Frozen 2026-11-27 (recall swarm,
  coordinator freeze): validation.jsonl is the frozen split; all
  validation-split numbers are measured against this exact file; further
  expansion goes to train.jsonl only."). All validation-split numbers
  from here on are measured against this exact file.

Enforcement (built into `scripts/build_synthetic_corpus.py`, `main()`):
a rebuild keeps the existing `validation.jsonl` byte-for-byte and
regenerates `train.jsonl` only. If the builder is unchanged since the
freeze, the regenerated train is byte-identical too (verified: the
freeze-adoption run left BOTH `train.jsonl`
`0de7ddd73e5cd371f4d866fc980881757ba9ec30d209ac2524cba94e26a48156` and
`validation.jsonl` `7640d067…` byte-identical to the pre-freeze run).
If the builder changes later, train regenerates excluding every frozen
validation `(lang, text)` so no train record can duplicate the frozen
split; if a recorded frozen hash ever mismatches the file, the builder
refuses to run. `--new-split` regenerates the validation file only when
the coordinator explicitly orders a new split version (new versioned
splits should live as e.g. `validation-v2.jsonl` with their own manifest
entry, not by overwriting the frozen file).

Final leakage-gate run against the frozen split (command:
`python3 scripts/check_ngram_leakage.py --out
data/synthetic_v7_1/leakage_report.json`, exit 0):

```
corpus=8000 refs=408 overlap_8grams=0 max_cosine=0.8269 (threshold 0.9) -> PASS
  ground-truth/ground-truth-v2-hma27-A.json: overlap=0 max_cosine=0.7805 synthetic_ids=[]
  test-bank/brutal-bank-v1-frozen.json: overlap=0 max_cosine=0.8269 synthetic_ids=[]
  tests/fixtures/laya_maintenance_development.json: overlap=0 max_cosine=0.6776 synthetic_ids=[]
  tests/fixtures/laya_maintenance_verification.json: overlap=0 max_cosine=0.6249 synthetic_ids=[]
  tests/fixtures/laya_maintenance_challenge.json: overlap=0 max_cosine=0.6922 synthetic_ids=[]
  tests/fixtures/laya_maintenance_final_check.json: overlap=0 max_cosine=0.7217 synthetic_ids=[]
  top cosine hits: [{'cosine': 0.8269, 'synthetic_id': 'SYN-TR-4228', 'ref_file': 'test-bank/brutal-bank-v1-frozen.json', 'ref_id': 'B-058'}, {'cosine': 0.7805, 'synthetic_id': 'SYN-TR-0117', 'ref_file': 'ground-truth/ground-truth-v2-hma27-A.json', 'ref_id': 'H14'}, {'cosine': 0.7762, 'synthetic_id': 'SYN-TR-2366', 'ref_file': 'test-bank/brutal-bank-v1-frozen.json', 'ref_id': 'B-142'}]
```

Sealed check remains QUEUED (no sealed hash index exists) — see §6.
