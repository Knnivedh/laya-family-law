# Lane 05 — Kannada / Kanglish paraphrase coverage — Status

Lane: 05 · Swarm: recall (unseen-question recall → ≥70% exact) · Date: 2026-11-27
Working copy ONLY: `~/workspace/laya-v71-work` (HEAD 1cb0bff, 10x swarm merged).
No other lane's files edited. No sealed test-bank file opened. No GPU/torch
used. Commits by this lane only (see §7).

## 0. Target context

User target (2026-11-27 ~19:19 IST): unseen law-related questions ≥70% exact.
Current measured: Sealed Fresh-20 7/20 (35%), Sealed Kannada-8 4/8 (50%) —
Kannada is half the gap. This lane attacks the KN/Kanglish paraphrase
coverage of the synthetic corpus only. It does NOT claim any 70% number:
the sealed re-run happens only on the RTX 5050 machine.

## 1. Templates added — `scripts/kn_templates.py` (NEW file, Lane 02 wires in)

25 blocks, all `kn_`-prefixed ids (can never collide with the builder's ids),
each with EN + KN-script + Kanglish (`ro`) variants and `[[key:phrase]]`
span markup in the builder's `B()` shape. Wiring for Lane 02 is one call:
`wire_into_builder(build_synthetic_corpus)` — registers the blocks and
extends `CORE_SINGLE` / `HN_BLOCKS` / `COMBOS` (see `WIRING` / `KN_COMBOS`
in the file). This lane never edited `scripts/build_synthetic_corpus.py`
and never wrote `data/synthetic_v7_1/`.

Variant counts: **EN 50, KN 54, kn_roman 71** (175 total).

Blocks per issue (requested):

| Issue | Blocks | | Issue | Blocks |
|---|---|---|---|---|
| maintenance | 6 | | divorce | 2 |
| stridhan | 4 | | dv_compensation | 1 |
| residence | 3 | | joint_property | 1 |
| violence | 3 | | restitution | 1 |
| custody | 2 | | birth_certificate | 1 |
| | | | procedure | 1 |

Denied intents also covered: divorce denied (2 blocks), maintenance denied
(1 block). Blocks per fact (supported): money_fact 6, child_fact 6,
minor_child 6, stridhan_claim 4, demand_made 3, residence_claim 3,
violence 3, custody_claim 2, divorce_asked 2, coercive_eviction_or_lockout 2,
being_filed 1, birth_cert_asked 1, child_maintenance_only 1,
child_safety_risk 1, dv_injury_comp_asked 1, existing_order_enforcement 1,
interim_asked 1, joint_property_claim 1, judicial_separation_only 1,
lump_sum_settlement 1, mutual_consent 1, proceeding_pending_hma 1,
restitution_asked 1, school_fees_fact 1, stridhan_sold_or_mortgaged 1.

Coverage axes (all fresh from statutory concepts, never from test banks):
- Colloquial / spoken forms: ದುಡ್ಡು ಕೊಡಲ್ಲ, ಮನೆಯಿಂದ ಆಚೆ ಹಾಕಿದ್ದಾರೆ,
  ಬಂಗಾರ ಇಟ್ಕೊಂಡಿದ್ದಾರೆ, ಹೊಡೆಯುತ್ತಾನೆ, ಮನೆ ಬಿಟ್ಟು ಹೋಗುವುದಿಲ್ಲ.
- Roman spelling variants: jeevanamsha / jeevanamsa / jeevanaamsha /
  jivanaamsha, vichhedana / vichchhedana, paalane / palane, stridhan /
  streedhan, maintanance.
- Code-mixed forms: "maintenance beku", "divorce beku", "custody beku",
  "residence beku", "stridhan vapas beku", "lump sum beku",
  "interim maintenance beku", "birth certificate beku".
- Demand-negation forms: ಕೇಳಿಲ್ಲ / ಕೇಳಿಯೇ ಇಲ್ಲ / ಎಂದೂ ಕೇಳಿಲ್ಲ /
  keliye illa / yavattu kelilla / kelalilla (demand_made denied) and
  ಕೇಳಿದ್ದೇನೆ / kelidde / bedike ittiddene (demand_made supported).

## 2. Normalizer changes — `src/laya_lang_normalizer.py`

- Strong Kanglish words: +39 entries for the template vocabulary
  (jeevanamsha/jeevanamsa/jeevanaamsha/jivanaamsha, vichhedana/
  vichchhedana, paalane/palane, bangara, chinna, parihara, janti, ottu,
  baki, teerpu, hakku, bedike, pramanapatra, janana, nyayanga, berpadike,
  madhyantara, shala, shulka, surakshitavagilla, rakshane, bembala,
  apaya, hodeyu, hodita, bedarike, maguvina, gandana, hendatiya,
  kelidde, keliddene, kelalilla, maridare, adavittare, adavittiddare,
  horahakidare, horahakidaru). Zero-FP exemptions untouched; plain
  English ("I want maintenance from my husband", "My husband sold my
  gold…") still detects as `en` — asserted in the self-test.
- Suffixes: +9 endings attested in the templates — uttiddaru, iddare,
  iddaru, kondiddare, kondidaru, abahude, bekendu, iddene, agide.
- `kannada_fact_hints()`: demand-false gains ಕೇಳಿಯೇ ಇಲ್ಲ / ಎಂದೂ ಕೇಳಿಲ್ಲ
  and roman keliye illa / yavattu kelilla / endu kelilla; demand-true
  gains roman bedike ittiddene; violence gains ಹೊಡೆದರು /
  ಹೊಡೆಯುತ್ತಿದ್ದಾರೆ / ಹೊಡೀತಾರೆ / ಬೆದರಿಕೆ ಹಾಕುತ್ತಾನೆ and roman hodeyu /
  hodeyuttare / hodeyuttiddare / hodidaru / bedarike / bedarisuttare;
  eviction gains ಮನೆಯಿಂದ ಹೊರ ಹಾಕಿದರು / ಮನೆ ಬಿಟ್ಟು ಹೋಗುವಂತೆ and roman
  horahakidare / horahakidaru / ache hakidare / ache hakidaru /
  beega hakidaru.
- NEW `kannada_issue_hints(text)` (exported in `__all__`): maps
  Kannada-script, Kanglish spelling-variant and code-mixed surface forms
  to the same corpus issue/fact keys as the formal forms (e.g.
  "jeevanamsa" → maintenance/money_fact, "paalane" → custody/
  custody_claim, "streedhan vapas beku" → stridhan/stridhan_claim,
  "janti asti" → joint_property/joint_property_claim, "janana
  pramanapatra" → birth_certificate/birth_cert_asked, "parihara" →
  dv_compensation/dv_injury_comp_asked, "marali banni" → restitution/
  restitution_asked). Verification-only: a match corroborates a Stage 0/1
  prediction; absence is never a denial; a match never sets a fact alone.

## 3. LanguagePack changes — `src/laya_lang_pack.py`

- New dataclass field `fact_key_lexicon: dict[str, str]` (12 keys) on
  `LanguagePack`, mirroring the normalizer's issue-hint patterns; filled
  for the `kn` pack.
- `KANNADA_PACK.negation_demand_lexicon`: demand_made gains ಕೇಳಿಯೇ ಇಲ್ಲ /
  ಎಂದೂ ಕೇಳಿಲ್ಲ + roman keliye illa / yavattu kelilla / endu kelilla;
  violence_denied gains roman hodedilla / hodilla; residence_denied gains
  roman mane beda / maneyalli iralu beda; new stridhan_claim (safe in own
  possession) and custody_claim (not wanted) denial patterns, KN + roman.
- `template_catalog` gains `"kn_templates": "scripts/kn_templates.py
  (Lane 05 — 25 blocks, DRAFT pending P2.1)"`; `benchmark_manifest`
  records the Lane 05 before-numbers. `native_audit_signoff` stays "" —
  P2.1 still open, `ready_for_production` still False.
- New `python3 -m src.laya_lang_pack` self-test: lexicon keys are valid
  corpus fact keys, all patterns compile, and the normalizer/pack
  cross-check agrees on probe forms.

## 4. KN validation coverage — before / after (COUNTS ONLY)

Method: `data/synthetic_v7_1/validation.jsonl` (500 records), counts only,
never text. BEFORE = on-disk validation file. AFTER = in-memory projection:
the builder's `generate(seed=7102)` re-run with `wire_into_builder()`
applied — exactly the call Lane 02 makes — same seed, same PLAN totals
(5,000). Script kept at `/tmp/measure_kn_coverage.py` (not a repo file).
The BEFORE in-memory run reproduced the on-disk validation counts
exactly (cross-check IDENTICAL).

### 4a. Validation-split counts per issue (requested, kn + kn_roman), seed 7102

| Issue | Before | After | Δ |
|---|---|---|---|
| maintenance | 134 | 102 | −32 |
| custody | 39 | 36 | −3 |
| residence | 46 | 38 | −8 |
| divorce | 22 | 17 | −5 |
| stridhan | 18 | 25 | +7 |
| joint_property | 13 | 10 | −3 |
| violence | 17 | 29 | +12 |
| dv_compensation | 6 | 9 | +3 |
| restitution | 5 | 6 | +1 |
| birth_certificate | 7 | 8 | +1 |
| procedure | 8 | 7 | −1 |

KN-family validation n: 272 → 261 (kn 153→125, kn_roman 119→136 — the
lang draw itself shifts under the re-shuffle).

Thin facts supported (kn + kn_roman), seed 7102: child_safety_risk 2→5
(+3), demand_made 14→22 (+8), dv_injury_comp_asked 6→9 (+3),
mutual_consent 6→7 (+1), restitution_asked 5→6 (+1), birth_cert_asked
7→8 (+1); interim_asked 5→5 (0), judicial_separation_only 6→6 (0);
being_filed 4→1 (−3), lump_sum_settlement 6→4 (−2),
stridhan_sold_or_mortgaged 6→3 (−3), existing_order_enforcement 16→12
(−4).

### 4b. Why the raw counts move both ways — and what actually improved

The corpus is fixed at N=5,000 with fixed PLAN bucket counts, so adding
blocks to a pool DILUTES per-block sampling instead of adding records:
the gain is surface-form diversity, not raw per-issue counts. The
validation split (n=500, KN-family ~265) is also too small for stable
per-issue counts — a 3-seed variance check (seeds 7102/7103/7104,
before wiring) shows restitution 5/10/7, joint_property 13/21/16,
dv_compensation 6/10/7, so ±5–10 swings are sampling noise. After
wiring, the only seed-consistent raw-count gains are stridhan
(18/20/15 → 25/28/28) and mostly violence (17/19/22 → 29/26/18).

The robust, deterministic measure is distinct KN/kn_roman template
variants available per issue (each block template variant counted once):

| Issue | Before | After | Δ |
|---|---|---|---|
| maintenance | 80 | 111 | +31 |
| stridhan | 12 | 32 | +20 |
| residence | 20 | 34 | +14 |
| violence | 16 | 30 | +14 |
| custody | 16 | 27 | +11 |
| divorce | 12 | 22 | +10 |
| joint_property | 12 | 17 | +5 |
| restitution | 8 | 13 | +5 |
| birth_certificate | 4 | 9 | +5 |
| procedure | 8 | 13 | +5 |
| dv_compensation | 4 | 8 | +4 |
| TOTAL | 192 | 316 | +124 (+65%) |

Every thin issue gains variants; the thinnest more than double
(stridhan 12→32, birth_certificate 4→9, dv_compensation 4→8). Forms
that had ZERO coverage before — jeevanamsa, "maintenance beku",
paalane/palane, "stridhan vapas beku", keliye illa, horahakidare —
now exist as templates AND as normalizer/pack mappings.

Implication for Lane 02 / coordinator: if raw per-issue validation
counts (not just diversity) must rise for the thin issues, the PLAN
bucket counts or N_TOTAL have to grow with the new blocks — wiring
alone cannot do it at fixed N=5,000. That is a coordinator decision,
not a Lane 05 change.

## 5. Leakage gate (readable refs)

Rendered all 215 distinct template texts (all langs, 6 slot draws per
template) to `/tmp/kn05_templates_corpus.jsonl` and ran
`scripts/check_ngram_leakage.py` on them:

- First run FAILED: 5 shared 8-grams with 16-Q ground truth, all from
  one EN sentence in `kn_stridhan_colloq` ("My wedding gold is with my
  husband's family and they will not return it") — near-identical to a
  16-Q question. Fixed by rewording to "My in-laws hold on to the gold
  from my wedding and refuse to hand it over."
- Re-run PASS, exact output: `corpus=215 refs=408 overlap_8grams=0
  max_cosine=0.7762 (threshold 0.9) -> PASS` (16-Q max cosine 0.7303,
  Brutal-230 0.7762, maintenance fixtures ≤0.6761), exit 0.
- Sealed check: NOT run — no sealed hash index is available to lanes;
  Lane 02 must re-run the full gate (incl. the sealed hash index via the
  coordinator) after wiring. No sealed text was opened by this lane.

## 6. Verification log (this lane, 2026-11-27)

```
python3 scripts/kn_templates.py
kn_templates self-test PASS: 25 blocks, variants en=50 kn=54 kn_roman=71

python3 -m src.laya_lang_normalizer
laya_lang_normalizer self-test: all checks passed

python3 -m src.laya_lang_pack
laya_lang_pack self-test PASS: kn fact_key_lexicon 12 keys, negation lexicon 5 keys, P2.1 still open

python3 tests/test_graph_v4.py
GRAPH V4 + FROZEN SHA TEST PASS: 34 sections / 66 nodes / 99 edges, 0 dangling edges, 7/7 frozen hashes intact.

python3 tests/test_prose_renderer_v2.py
PROSE VALIDATION PASS: 246 cases, Fp=0, quality_flags=0, 15/15 adversarial mutants caught, mean=0.0183ms, max=0.334ms

python3 scripts/check_ngram_leakage.py --corpus /tmp/kn05_templates_corpus.jsonl
corpus=215 refs=408 overlap_8grams=0 max_cosine=0.7762 (threshold 0.9) -> PASS (exit 0)
```

Builder `validate()` also passes on the in-memory wired generation
(`generate(seed=7102)` after `wire_into_builder`), so the blocks are
schema-valid and produce no span-offset or duplicate-text errors.

## 7. Commits (this lane only)

- `R-LANE05: add 25 KN/Kanglish paraphrase template blocks (scripts/kn_templates.py)` — new file only.
- `R-LANE05: extend lang normalizer + KN LanguagePack for new KN/Kanglish forms` — `src/laya_lang_normalizer.py`, `src/laya_lang_pack.py` only.
- `R-LANE05: lane 05 status — templates, normalizer, KN validation coverage` — this file.

No other files staged or committed by this lane (other lanes' modified
files in the working tree were left untouched).

## 8. What is still unverified / open

- **P2.1 native Kannada speaker sign-off — OPEN.** All 25 blocks' KN
  wording and all new normalizer/pack KN forms are DRAFT, written from
  the builder's existing KN vocabulary and the plan §3.2 colloquial axes,
  not by a native speaker. P2.1 must audit `scripts/kn_templates.py`
  (and the KN prose templates, Lane 09) before any training run treats
  the KN split as gold. `KANNADA_PACK.native_audit_signoff` is still "".
- **Lane 02 wiring not yet done.** The corpus on disk is unchanged;
  the "after" numbers in §4 are an in-memory projection of the exact
  wiring call. After Lane 02 wires + rebuilds, it must re-run the
  leakage gate (incl. sealed hash index) and the validation counts will
  differ slightly from §4 (same seed, but the rebuilt corpus is the real
  one).
- **Sealed Kannada-8 re-run — NOT done here** (RTX 5050 only, blind,
  aggregate only). Nothing in this lane measures or claims the 70%
  target; the templates raise paraphrase diversity, which is a
  precondition, not a measured recall gain.
- **Raw-count dilution (§4b):** at fixed N=5,000, thin-issue raw counts
  do not reliably rise from wiring alone; a PLAN/N_TOTAL decision is
  needed if the coordinator wants raw-count growth too.
- **Normalizer hint functions are verification-only** and untested
  against any live extractor run: `kannada_issue_hints()` /
  `kannada_fact_hints()` corroborate Stage 0/1 predictions; no lane has
  wired them into `laya_v7_extractor.py` / `laya_v7_evidence.py` yet
  (those files belong to Lanes 01/03/08).
