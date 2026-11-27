# Lane 02 — V71-P1-2 Synthetic Corpus + Leakage Gate — STATUS: DONE

Owner: Lane 02. Files owned (only these touched):
- `scripts/build_synthetic_corpus.py` (new)
- `scripts/check_ngram_leakage.py` (new)
- `data/synthetic_v7_1/` (new): `train.jsonl`, `validation.jsonl`,
  `manifest.json`, `schema.json`, `leakage_report.json`

No other files edited. No git add/commit/push (coordinator owns that).
No sealed file opened at any point; no sealed text printed, quoted or copied.

## What was built

Deterministic, seeded (seed `7102`), stdlib-only, CPU-safe template builder.
Corpus is generated purely from statutory grammars, paraphrase templates and
hard-negative perturbations — never from test banks. No test-bank, GT or
fixture question text was read, copied or paraphrased by the builder.

- **Size: 5,000 examples — train 4,500 / validation 500** (random shuffle
  with the same seed, then first 500 = validation; every cluster and
  language is present in validation).
- **Languages:** EN 2,316 (46.3%), KN 1,333 (26.7%), Kanglish/kn_roman
  1,351 (27.0%). Validation: EN 228 / KN 153 / kn_roman 119.
- **Clusters:** core single-issue 1,400; multi-issue combos 1,300;
  hn_a custody-vs-residence 250; hn_b pwdva-17/19 vs 18-lockout vs violence
  300; hn_c divorce/pending/being-filed/JS/restitution/decree 350; hn_d
  stridhan-safe/sold vs joint-property 300; hn_e male-self / father-child-only
  / elder-parent / bnss-144-3 arrears / bnss-146 variation 300; hn_f
  hypotheticals / third-party / quoted / pre-BNSS CrPC-125 / past / 12 OOS
  domains 600 (of which OOS ≈ 288, in_scope denied); negation primaries 150;
  conflicting (divorce_asked) 50.
- **Issues requested (of 5,000):** maintenance 2,255; custody 792;
  residence 831; divorce 385; stridhan 365; joint_property 296; violence
  408; dv_compensation 134; restitution 118; birth_certificate 135;
  procedure 135. Issues denied: divorce 197, maintenance 86, stridhan 62,
  custody 33 (explicit negations only).
- **Facts supported:** every one of the 28 facts has ≥ 49 supported
  examples (min: child_safety_risk 50; max: money_fact 2,255).
  Facts denied is populated only where the corpus has an explicit-negation
  template (14 of 28 facts; e.g. divorce_asked 197, custody_claim 191,
  residence_claim 180, in_scope 288); absent facts are `unknown` by design.
  Only `conflicting` fact in the corpus is divorce_asked (50, the conflict
  block). Merge warnings during generation: none.
- **Enums:** sex F 4,191 / M 255 / U 554; role spouse 4,362 / other 459 /
  parent 84 / child 95; modality present 4,640 / past 188 / future 66 /
  hypothetical 58 / quoted 48.
- **Determinism verified:** rebuild produces byte-identical files
  (train sha256 `8777bddd…`, validation sha256 `f07c2d36…`).
- **Self-checks in the builder:** every record carries all 11 issues + all
  28 facts with legal values; every span offset slices back to its span
  text; no duplicate (lang, text); every block sets `in_scope`
  (hard error otherwise).

## Leakage-gate results — actually measured here

Command: `python3 scripts/check_ngram_leakage.py --out data/synthetic_v7_1/leakage_report.json`
(full report in `data/synthetic_v7_1/leakage_report.json`)

| Reference (408 questions) | Word 8-gram overlap | Max TF-cosine |
|---|---|---|
| 16-Q `ground-truth/ground-truth-v2-hma27-A.json` | **0** | 0.7805 |
| Brutal-230 `test-bank/brutal-bank-v1-frozen.json` | **0** | 0.8182 |
| maintenance dev (48) | **0** | 0.6669 |
| maintenance verification (46) | **0** | 0.6490 |
| maintenance challenge (34) | **0** | 0.6836 |
| maintenance final_check (34) | **0** | 0.7559 |
| **Total** | **0** | **0.8182 (< 0.90)** |

**Verdict: PASS on all readable references.** First run failed (44
8-grams, max cosine 0.9317); fixed by (a) correcting the gate tokenizer —
Python `\w` shreds Kannada words at combining marks, so the gate now splits
on whitespace/punctuation, keeping Kannada words whole — and (b) rewording
the colliding templates (maint_wife, custody/coloc "stay/live with me",
violence threat, stridhan-held, OOS employment, neg-custody, framing suffix,
forum add-on). Final run: 0 / 0.8182.

**Sealed check: QUEUED, not run.** No `sealed-hash-index.json` exists and
this lane did not create one (building it requires reading sealed files).
Blind-hash mode is implemented and tested for the missing-index path
(exit code 2, prints the trusted command, opens nothing). Exact trusted run
for the coordinator / rater:
```
python3 scripts/check_ngram_leakage.py --build-hash-index test-bank/sealed/sealed-fresh-20.json test-bank/sealed/sealed-kannada-8.json --hash-index-out data/synthetic_v7_1/sealed-hash-index.json && python3 scripts/check_ngram_leakage.py --sealed-index data/synthetic_v7_1/sealed-hash-index.json
```
`--build-hash-index` writes SHA-256 hashes only and never prints sealed text.

## Schema notes for Lane 03 (classifier)

Record: `{id, lang, text, issues: {11: intent}, facts: {28: state},
enums: {claimant_sex, claimant_role, modality_time}, spans: [...],
meta: {cluster, blocks, split}}` — see `data/synthetic_v7_1/schema.json`.
`meta` is extra bookkeeping; Lane 03 may ignore it.

- **Issues (11):** maintenance, custody, residence, divorce, stridhan,
  joint_property, violence, dv_compensation, restitution,
  birth_certificate, procedure. Intent: requested | incidental | denied |
  uncertain. OOS records use `uncertain` for every issue; the signal is
  `facts.in_scope = "denied"`.
- **Facts (28):** divorce_asked, mutual_consent, judicial_separation_only,
  restitution_asked, proceeding_pending_hma, being_filed, decree,
  money_fact, lump_sum_settlement, existing_order_enforcement,
  interim_asked, custody_claim, child_fact, minor_child,
  child_maintenance_only, school_fees_fact, child_safety_risk,
  residence_claim, coercive_eviction_or_lockout,
  explicit_residence_order_only, violence, dv_injury_comp_asked,
  stridhan_claim, stridhan_sold_or_mortgaged, demand_made,
  joint_property_claim, birth_cert_asked, in_scope.
  State: supported | denied | unknown | conflicting.
- **Mappings / caveats (also in the builder docstring):**
  - `interim_asked` == evidence `interim_only_asked`; `interim_asked`
    supported always co-occurs with `proceeding_pending_hma` supported.
  - Stridhan "safe in my own possession" is encoded as `stridhan_claim`
    `denied`, not a separate fact.
  - `urgent_safety_risk` (graph dead key) is NOT a corpus fact; derive as
    `violence` supported OR `child_safety_risk` supported.
  - `domestic_relationship`, `forum_question_asked`,
    `procedure_how_to_asked`, `first_demand_never_made`,
    `no_dispute_empty` are NOT corpus facts; procedure issue + `in_scope` +
    role/sex enums carry that signal.
  - `claimant_sex`: F | M | U. `claimant_role`: spouse | parent | child |
    other — `other` also covers genuinely unstated role; `child` only when
    the claimant speaks as the child (95 examples).
  - `modality_time`: present | past | future | hypothetical | quoted.
  - `denied` is a minority class for facts (explicit negations only);
    most absent facts are `unknown`, not `denied`.
  - Spans: `{key, kind ("fact"|"issue"), text, start, end}` — char offsets
    verified against the text. Framing prefixes/suffixes and the forum
    add-on carry no spans.
- **Known thin spots:** modality hypothetical 58 / quoted 48 / future 66;
  `child_safety_risk` supported only 50; `being_filed` supported only 66;
  role parent 84 / child 95; sex M 255. If Lane 03 needs more of any of
  these, the fix is new blocks in the builder + a re-run, not hand edits
  to the JSONL.

## Guardrails — verified after my changes

- `python3 tests/test_graph_v4.py` — PASS (34 sections / 66 nodes / 99
  edges, 0 dangling, 7/7 frozen hashes intact).
- `python3 tests/test_prose_renderer_v2.py` — PASS (246 cases, Fp=0,
  quality_flags=0, 15/15 mutants).
- Frozen SHAs unchanged: GT v2 `87818b1b…`, brutal bank `934a2b22…`.
- `git status` shows only my files (`data/`,
  `scripts/build_synthetic_corpus.py`,
  `scripts/check_ngram_leakage.py`); the `M src/...` entries are other
  lanes' concurrent work, untouched by this lane.
- No GPU/torch used anywhere; no neural runs.

## Blockers / what needs RTX / human

- **Sealed leakage check is QUEUED** (see trusted command above) — needs
  a trusted operator to build the blind hash index and re-run the gate.
  Corpus must not be called fully leakage-cleared until that returns 0.
- **Kannada templates have had no native-speaker audit (P2.1).** They are
  plain everyday Kannada written for this corpus; P2.1 should audit the KN
  and Kanglish templates (and the KN sample sentences in this file's
  builder) before any training run treats the KN split as gold.
- **No training run was done here** (no GPU/torch on this VM) — training
  (Lane 03 code + RTX 5050 run) is downstream; the corpus + gate are the
  deliverable.
