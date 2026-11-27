# v5 planning note — after the residence fix (PLAN ONLY, no notebook built)

Build v5 only after the v4r and v4.1 live runs land. Remaining after
residence: H1/H3/H7/H15 Stridhan/maintenance over-fire (8 FPs), H6 custody
FPs (3), H14 GWA FP (1), H4 escalates. Both models agree the next fix is
the financial-claim boundary; they differ on mechanism — Gemini: one
4-option choice; ChatGPT: per-issue evidence gates. Build ONE in v5, keep
the other as the v6 fallback.

## 1. Financial-claim boundary — Gemini's 4-option choice (v5 primary)

Replace the independent maintenance and Stridhan `noul` prompts with ONE
4-option Laya choice classifier:

- `maintenance_only` — asks for periodic money/support, states no Stridhan claim.
- `stridhan_only` — asks for return of the wife's gold/cash/property held by the husband's side, no periodic money asked.
- `both` — asks for both. Must preserve K0 and H10 as `both`.
- `neither` — asks for neither (e.g. birth certificate, residence-only, custody-only).

**Wording flag:** the four labels are as Gemini gave them; the definitions
above are draft reconstructions from the ground truth, NOT a verbatim quote
of Gemini's full answer — verify exact option wording against it before
building. Mapping: `maintenance_only` → maintenance fires, Stridhan does
not; `stridhan_only` → reverse; `both` → both fire; `neither` → neither
fires. Other issues keep existing prompts. The choice cutoff replaces the
old 0.10/0.50 noul cutoffs; set it from a dry run on v3 saved scores if
possible, else from the live run. Mechanism per Gemini: out-of-distribution
`noul` prompts collapse toward "no"; choice prompts move signal into a
separable 0.35–0.85 range — test live, do not assume.

**Projection (Gemini, PROJECTION — not a result):** resolves H1, H3, H7,
H15 (8 of 12 remaining FPs) → exact 10 → 14/16, micro-F1 0.905 → 0.966
(TP 57 / FP 4 / FN 0), leaving H6 custody (3 FP), H14 HMA-26 routing
(1 FP), H4 escalation.

## 2. Financial-claim boundary — ChatGPT's evidence gates (v6 fallback)

If the 4-option choice underperforms live, use per-issue evidence-grounded
verification (ChatGPT §5): an issue fires only on a stated grounding fact —
maintenance needs a money-not-given / periodic-money fact; Stridhan needs
a gold-or-property-held fact; custody needs a who-gets-the-child fact. A
bare prompt score with no grounding fact must not fire the issue. Same
evidence-first principle as v4.1's residence rule, extended to money.

## 3. H14 — proceeding-aware custody routing (v5 or v6, one change)

H14 GT routes custody through HMA 26 (divorce proceeding pending;
`divorce_pending` final 0.9202 in v3), but v3 also kept standalone GWA
1890. Fix: in Stage 2, when `proceeding_pending` is True, drop standalone
GWA 1890 from the custody route (keep HMA 26 + HMA 24 + HMGA s.6 +
WELFARE). Do NOT touch the no-proceeding route (H2: GWA 1890 + HMGA s.6 +
WELFARE is correct there).

## 4. H6 — clause-split fix (v6)

H6: "I just want money every month from my husband and to stay in the
house with my daughter." Custody's 3 FPs remain: "stay in the house with
my daughter" was read as a custody claim. Root cause: the splitter splits
on "and"/"but" only when followed by I|he|they|my husband|my son|my
daughter — "and to stay…" never splits. Fix options: (a) extend the split
trigger to infinitives "to stay / to live" after "and"; (b) add a residence
aux prompt for verbatim "stay in the house"; (c) custody requires a
who-gets-the-child claim — "stay in the house with my daughter" is a
residence claim, not custody. Pick one in the v6 brief; do not bundle
with v5.

## 5. Residence generalisation — Gemini's 2-option choice gate (v5/v6)

Replace frozen boolean `residence_claim` (hand-annotated per question;
fails silently on indirect lockout idioms — "in-laws kept my house keys",
"he put my clothes outside the door") with a single Laya 2-option choice
gate, applied only when R1 ≥ 0.35: (A) spouse locked out / threatened
eviction / claiming right to reside in the shared matrimonial household vs
(B) child custody / taking-away, ancestral property title / partition, or
violence / gold claim without eviction. Until built, any claim that the
residence fix generalises is capped.

## Sequencing

v5: 4-option financial-claim choice (§1). If live exact < 14/16 or F1
falls, revert and build §2 instead. v6: whichever of §3 / §4 remains, one
per run — never bundle. Residence gate upgrade (§5) after the money
issues, before the sealed fresh-20 run: the sealed set will contain unseen
lockout phrasings, and a frozen annotation cannot be written for unseen
questions without leaking the test set into the annotation.
