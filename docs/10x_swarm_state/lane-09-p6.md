# Lane 09 — P6 Kannada prose + readability + human audit packets

Status: DONE (code + tests + exporter, all run on this CPU-only VM).
Date: 2026-11-27. Working copy only: `~/workspace/laya-v71-work`.
No other lane's files touched. No git add/commit/push (coordinator owns that).
No sealed question text opened, quoted, or copied at any point.

## Modules built (Lane 09 files only)

| File | What it is |
|---|---|
| `src/laya_prose_kn.py` | Deterministic Kannada templates module (V71-P6-1) + Kannada parity verifier + P6-2 design spec + KN checklist/forum/readability helpers |
| `tests/test_prose_kn_mutants.py` | 7 unittest tests: 20-section coverage + 25 Kannada adversarial mutants + self-test wrapper |
| `scripts/export_human_audit.py` | Blind G12 + P2.1 audit packet exporter (V71-P6-3) |

## Template coverage (V71-P6-1)

- **20/20 sections**: bnss-144, bnss-144-3, bnss-146, pwdva-20, hma-24, hma-25,
  gwa-1890, hmga-1956-s6, welfare-principle, hma-26, hma-27, bns-316, pwdva-17,
  pwdva-18, pwdva-19, pwdva-22, hma-13, hma-13b, hma-9, births-deaths-act-1969.
- **9/9 escalation kinds** (quantum, court, demand, recovery, custody, residence,
  safety, procedure, fact) + safety emergency helplines (112 / 181 / 1098) +
  Protection Officer / One Stop Centre note.
- INTRO_LINE_KN, CLOSING_LINE_KN, OUT_OF_SCOPE_LINE_KN, INVALID_RECORD_HANDOFF_KN.
- Safety banner (`SAFETY_BANNER_KN`) is the FIRST paragraph whenever "safety" is
  in escalation_kinds, independent of kept_ids / claimant_sex / proceeding.
- `render_prose_kn(rec, facts, include_draft_banner=True, include_forum_note=False,
  include_checklist=False)`; `render_prose_localized(rec, facts, target_lang="auto")`
  routes `lang in {"kn","kn_roman"}` (or `target_lang="kn"`) to the KN renderer and
  otherwise lazily delegates to English `laya_prose_v2.render_prose`.
- **DRAFT marking (non-negotiable)**: every template entry carries
  `DRAFT — NEEDS P2.1 native Kannada speaker verification`; every render prepends
  `DRAFT_NOTICE_KN` (default on) and returns `"draft": True, "p2_1_verified": False`.
  No Kannada wording in this lane is verified. The banner may be removed ONLY
  after a signed P2.1 report is filed.
- **0 question marks** anywhere in rendered prose (Forbidden #5). No invented
  rupee amounts. No salary-slip / pay-slip wording anywhere — not even in a
  "missing" clause (the literal strings are checker traps; see below).
- `prose_forbidden_check_kn(prose, kept_ids, dropped_ids, facts)` — Kannada parity
  of the 9 frozen items + Additions A–E: traps for "ಬಾಡಿಗೆ ಹಕ್ಕು"/"ಟೆನೆನ್ಸಿ" (#4),
  "ಸಂಬಳದ ಚೀಟಿ"/"ಪೇ ಸ್ಲಿಪ್" + income-proof demands (#9), invented rupee numbers
  (₹/ರೂ./ರೂಪಾಯಿ/ಸಾವಿರ/ಲಕ್ಷ/ಕೋಟಿ + monthly context, #8), "?" / court-choice
  phrasing (#5), HMA + "ಜನನ ಪ್ರಮಾಣಪತ್ರ" (#6), Kannada statutory-pattern parity
  against kept_ids (#7, incl. 144(3)-before-144 and 13B-before-13 ordering).

## Self-test results actually run here (CPU only, no torch, no GPU)

```
python -m src.laya_prose_kn
KANNADA PROSE SELF-TEST PASS: 20/20 sections, 9/9 kinds, 28 renders,
Fp=0, quality_flags=0, question_marks=0, mean=0.0459ms, max=0.105ms

python -m unittest tests.test_prose_kn_mutants -v
Ran 7 tests — OK (20-section clean-render, dispatcher, checklist,
25 mutants, >=15-mutant count, module self-test)
```

Mutants: **25** (plan requires >= 15), covering items 1, 2, 3 (13 + 13B), 4
(Kannada + Latin "ಟೆನೆನ್ಸಿ"), 5 ("?" + "ನ್ಯಾಯಾಲಯವನ್ನು ಆಯ್ಕೆ ಮಾಡಿ"), 6
(HMA-linked + missing-1969-Act), 7 (dropped + not-kept), 8 (₹, ರೂ., monthly
ರೂಪಾಯಿ, ಲಕ್ಷ), 9 ("ಸಂಬಳದ ಚೀಟಿ", "ಪೇ ಸ್ಲಿಪ್", income-proof demand), flags
A, B (child + school-fees), C (HMA-27 leak), E (male claimant).

Guardrails re-run after my changes (both must pass — they do):

```
python tests/test_graph_v4.py
GRAPH V4 + FROZEN SHA TEST PASS: 34 sections / 66 nodes / 99 edges,
0 dangling edges, 7/7 frozen hashes intact.

python tests/test_prose_renderer_v2.py
PROSE VALIDATION PASS: 246 cases, Fp=0, quality_flags=0,
15/15 adversarial mutants caught, mean=0.0164ms, max=0.129ms

python -m unittest discover -s tests -p "test_*.py"
Ran 49 tests — OK
```

Bugs found and fixed inside Lane 09's own files during self-test:
1. Item-8 amount patterns used `[\d,]+`, which matches a bare comma — so
   "ಬೇಕಾದರೂ," (ends in "ರೂ" + comma) false-fired item 8. Fixed to
   `[\d][\d,]*` (require at least one digit) in all five KN amount patterns.
2. School-fees clause grammar ("ಶಾಲಾ ಶುಲ್ಕ" → "ಶಾಲಾ ಶುಲ್ಕಗಳನ್ನು" /
   "ಶಾಲಾ ಶುಲ್ಕಗಳು" to agree with the surrounding case).
3. One mutant carried a misspelled "ಪ್ರಮಾಣಪತ್ರ" (wrong codepoint order);
   fixed to the module's spelling and the test now passes.

Observation for Lane 01 (NOT my file, NOT edited — flag only): the English
`laya_prose_v2.py` item-8 patterns have the same `[\d,]+` bare-comma class
(`₹\s?[\d,]+`, `Rs\.?\s?[\d,]+`, `\b[\d,]+\s*(?:per month|...)`). A template
ending in "Rs" + comma, or "₹" + comma, could false-fire the same way. Lane 01
may want the same `[\d][\d,]*` fix when it does its P6-1 partial.

## P6-2 readability / checklist (design + KN implementation)

- Full design spec lives in the `P6-2 DESIGN` section of the
  `src/laya_prose_kn.py` module docstring (safety banner first, FCA s.7(2)(a)
  forum note, per-section checklist, readability rules: avg sentence <= 22
  words, zero Latin/legalese jargon, plain step ordering What applies ->
  Which court -> Next steps & documents -> Missing facts -> Disclaimer).
- Implemented in this lane: `document_checklist_kn(kept_ids, facts)`
  (per-section items; school-fee records only when `school_fees_fact` is
  True; closing line "Give whatever records you have. If a record is missing,
  say that it is missing." — salary slips are NEVER named),
  `forum_guidance_kn(kept_ids)` (Bengaluru/metro FCA s.7(2)(a) note, opt-in,
  only when bnss-144 is kept), `readability_check_kn(prose)` (avg/max
  sentence words, "?" flag, pass/fail vs the <= 22-word bar).
- The self-test asserts readability `passes` on every rendered combination.

## PATCH SPEC for Lane 01 — English P6-2 checklist + KN dispatch (Lane 01 applies)

Lane 09 does not edit `src/laya_prose_v2.py`. Lane 01 (or a follow-up) applies:

1. **EN action_plan / document_checklist** in `laya_prose_v2.py` (same
   template-lock + `prose_forbidden_check` Fp=0 discipline as this lane's KN
   version): add `document_checklist_en(kept_ids, facts)` mirroring
   `document_checklist_kn` item-for-item (marriage proof; income information
   the user already knows; school-fee records only if `school_fees_fact`;
   existing order + unpaid-instalment list for bnss-144-3; existing order +
   change-of-circumstances proof for bnss-146; child birth/school records for
   custody; Stridhan list/photos/written-demand copy for hma-27/bns-316;
   shared-household proof for pwdva-17/19; medical/police/message records for
   pwdva-18/22; hospital record or other birth proof for births-deaths-act-1969),
   plus the closing line "Provide whatever records you have. If a record is
   missing, say that it is missing." **Never name salary slips / pay slips in
   rendered prose** — the item-9 checker is a literal string match, so even a
   "if salary slips are missing" clause trips it. Wire it behind an
   `include_checklist=False` opt-in parameter on `render_prose`, like the KN
   renderer.
2. **Safety banner (EN)**: when "safety" is in escalation_kinds, put the
   emergency-numbers banner (112 / 181 / 1098 + Protection Officer / One Stop
   Centre) as the FIRST paragraph — same rule as the KN renderer.
3. **Forum note (EN)**: when bnss-144 is kept, optional note — "Where a Family
   Court is established, BNSS s.144 claims are filed in the Family Court under
   FCA s.7(2)(a); otherwise before a Judicial Magistrate First Class" — as
   `forum_guidance_en(kept_ids)`, opt-in, never a question.
4. **KN dispatch**: add `render_prose(rec, facts, target_lang="auto" | "en" | "kn")`
   to `laya_prose_v2.py` that routes `rec["lang"] in {"kn","kn_roman"}` (or
   `target_lang="kn"`) to `laya_prose_kn.render_prose_kn` and otherwise renders
   English. Reference implementation already exists as
   `laya_prose_kn.render_prose_localized` — Lane 01 can call it or inline the
   same 6 lines. Keep the KN draft banner ON until P2.1 sign-off is filed.
5. **EN item-8 fix (optional, same class as Lane 09 fix #1)**: change
   `[\d,]+` to `[\d][\d,]*` in the five EN amount patterns so a bare comma
   after "₹"/"Rs" cannot false-fire item 8.
6. **Docs**: update `src/README.md:15` (currently "English/Kannada" — the
   renderer is English-only until this dispatch lands) only after (4) lands.

## Human audit packets (V71-P6-3) — exporter built + tested

`scripts/export_human_audit.py` — pure Python, CPU-only.

What it does: builds blinded G12 + P2.1 packets from **aggregate statistics +
already-rendered prose outputs only**. It strips gt_ids, kept_ids, court,
escalation kinds, classifier scores, forbidden-check results, model names,
latency fields; replaces real IDs with blind IDs (G12-001… / P21-001…,
deterministic seed); flags every 4th item for double-rating (25%) with
third-reader adjudication; writes the blind→real mapping ONLY to a
`*-PRIVATE-mapping.json` file OUTSIDE the packet dir.

Sealed handling (critical): the exporter NEVER reads `test-bank/sealed/*.json`.
Any input path under `test-bank/` or containing a `sealed` component is
REFUSED; any input item carrying a `question` field, or `gt_ids`/`kept_ids`/
scores/forbidden-check fields, is REFUSED. Sealed Fresh-20 / Kannada-8 items
enter only as IDs from the aggregate-stats file and are emitted as ID-only
placeholders — the rater fills question + rendered prose from the sealed
store itself. No sealed text is ever fabricated, printed, or copied.

Exact commands (run from the repo root, on the RTX 5050 machine where the
rendered outputs were produced):

```
# 1. Produce the inputs (NOT done by this lane — needs a live run):
#    results/laya-v71-rendered-prose.json : {"items": [{id, suite, category?,
#      lang, prose}]} — prose only, no question text, no gt_ids/kept_ids/scores.
#    results/laya-v71-aggregate-stats.json : {"suites": {"16-Q": {"n": 16},
#      "Brutal-230": {"n": 230}, "Fresh-20": {"n": 20, "ids": [...]},
#      "Kannada-8": {"n": 8, "ids": [...]}}} — counts + IDs only.
python scripts/export_human_audit.py \
    --rendered-outputs results/laya-v71-rendered-prose.json \
    --aggregate-stats results/laya-v71-aggregate-stats.json \
    --out-dir docs/human-audit/g12-p21-packet-v1 \
    --brutal-sample 30 --seed 20261127
# Share ONLY docs/human-audit/g12-p21-packet-v1/ with the raters.
# Keep docs/human-audit/g12-p21-packet-v1-PRIVATE-mapping.json sealed
# with the coordinator until ratings are returned.
```

Demo run actually executed here (fake DEMO ids + prose rendered by our own
EN/KN renderers in /tmp — no real data, no sealed files):

```
AUDIT PACKETS EXPORTED: 82 G12 items (21 double-rated), 16 P2.1 items
(4 double-rated) -> /tmp/lane09-demo/packet
Sealed placeholders: Fresh-20 20 placeholders, Kannada-8 8 placeholders
```

Verified on the demo: packet item keys are blind-only, all rating fields
blank, no real IDs in packet files, sealed placeholders carry no prose,
all 4 packet files byte-identical on re-run with the same seed (only the
manifest's `mapping_location` differs, as expected). Guard tests: a
`test-bank/sealed/...` input path is refused; an input item carrying a
`question` field is refused; a mapping path inside the packet dir is refused
(includes a fixed string-prefix bug where `packet-PRIVATE-...` counted as
inside `packet/`).

## P2.1 / G12 handoff (what needs humans)

- **P2.1 (native Kannada legal reviewer)**: sign off (a) fluency + statute
  accuracy of the Kannada renders, (b) ALL templates in
  `src/laya_prose_kn.py` (currently DRAFT), (c) Kanglish test items. Use the
  `p21-packet.md/.json` from the exporter. Any discovered GT error goes in a
  separate kn-v2 sensitivity file — frozen SHAs are never mutated. Only after
  the signed P2.1 report is filed in `docs/` may the draft banner be removed.
- **G12 (2 independent legally literate raters)**: score `g12-packet.md/.json`
  (16-Q + Fresh-20 + Kannada-8 + stratified Brutal sample) against Forbidden
  Items 1–9 (+ Lane 4 P10–P11) and completeness (a)–(d); 25% double-rating +
  adjudication. A signed G12 report with Fp = 0 lifts the <= 9.0 prose cap.
- **Not done by this lane (needs live runs / humans)**: producing the real
  `results/laya-v71-rendered-prose.json` + aggregate stats (needs RTX 5050
  runs); the actual G12/P2.1 ratings; Lane 01 applying the patch spec above;
  `tests/test_prose_renderer_v2.py` gaining the >= 60 new EN/KN scenarios
  (the KN half is covered by `tests/test_prose_kn_mutants.py`; the EN half
  belongs with Lane 01's P6-2 implementation).

## Blockers

- None inside Lane 09's scope. Open dependencies (not blockers for this
  lane): Lane 01's P6-1 partial + P6-2 patch application; live rendered-prose
  outputs for a real packet export; human raters for G12/P2.1.
