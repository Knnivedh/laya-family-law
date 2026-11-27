# Erratum — Ground Truth v2 (D1 Option A): HMA 27 removed from K0/H3/H10/H15

**Date:** 2026-11-27
**Frozen by:** Rater lane (independent of the tuning lanes)
**GT file:** `ground-truth-v2-hma27-A.json`
**GT file sha256:** `87818b1b659583bf06a25280a6b53dabedf65f29cab99058f02b8ed31c9ac97e`
**v1 source:** Cell 6 of `live-laya-colab-test-v5-precision.ipynb`
(Cell 6 source sha256: `bb6acfc5ef0a90c5a68b0b0be76a62e3c5c8ca5c55ceed7aabf0f6ae9bcbdad7`);
v1 GT also summarised in `backtest-laya-vs-llama8b.md` §3.
**Decision:** D1 **Option A**, decided by the user (Nivedh) 2026-11-27 ~09:46 IST —
remove HMA 27 from K0/H3/H10/H15 ground truth, **no replacement label**.
Option C (replace with a new `FCA 7(1) Expl. (c) / CPC 151` label) was rejected by
the user; **no FCA label is introduced anywhere in v2**. No Option C file was produced.

---

## 1. What changed — per-question diff (the only changes in v2)

v1 total: **57 sections**. v2 total: **53 sections**. Four removals, nothing else.
Every other question, section label, court, escalate expectation, fact annotation
and question wording is identical to v1, with the same frozen label strings.

| Q | v1 GT | v2 GT | Change |
|---|---|---|---|
| K0 | BNSS 144, PWDVA 20, GWA 1890, HMGA s.6, WELFARE, **HMA 27**, BNS 316, PWDVA 17, PWDVA 18, PWDVA 19 (10) | BNSS 144, PWDVA 20, GWA 1890, HMGA s.6, WELFARE, BNS 316, PWDVA 17, PWDVA 18, PWDVA 19 (9) | HMA 27 removed |
| H3 | HMA 27, BNS 316 (2) | BNS 316 (1) | HMA 27 removed |
| H10 | HMA 27, BNS 316, BNSS 144, PWDVA 20 (4) | BNS 316, BNSS 144, PWDVA 20 (3) | HMA 27 removed |
| H15 | BNS 316, HMA 27 (2) | BNS 316 (1) | HMA 27 removed |
| All other 12 questions (H1, H2, H4–H9, H11–H14) | — | — | **No change** |

**Courts unchanged** on all four affected questions (all stay
`[Family Court, Magistrate]`). That is correct, not an oversight: the civil
recovery route for Stridhan is still a Family Court route — under the Family
Courts Act s.7(1) Expl. (c) — and the Magistrate route (BNS 316 complaint) is
unchanged. **Escalate expectations unchanged** on all 16 questions.
**BNS 316 kept** on all four questions (criminal route, unaffected by the
proceeding question).

Verified by the rater from the v1 GT itself (notebook Cell 6, cross-checked
against `backtest-laya-vs-llama8b.md` §3 — the two agree exactly), not taken on
trust from the v6 report:

| Q | HMA 27 in v1 GT? | `proceeding_pending` | `divorce_asked` | `demand_made` | Any HMA petition stated / being filed? |
|---|---|---|---|---|---|
| K0 | Yes | **false** | false | true | No — asks the route; no petition mentioned |
| H3 | Yes | **false** | false | false | No — "never asked them to return it" |
| H10 | Yes | **false** | false | false | No — "have not asked for it back yet" |
| H15 | Yes | **false** | false | true (sale = refusal evident) | No — "sold my gold without asking me" |

H14 is the **only** question in the set with `proceeding_pending: true`, and it
does not carry HMA 27 in GT — it is the control that proves the distinction:
HMA 24 and HMA 26 correctly fire there and nowhere else. No other question's GT
contains HMA 27. The v6 report's count of four affected questions (K0, H3, H10,
H15) is confirmed; the earlier v4/plan count of three (omitting K0) was wrong.

---

## 2. Why — the corrected rule

HMA s.27 ("In any proceeding under this Act, the court may make such provisions
in the decree…") is ancillary. Corrected rule wording (v6 Lane 3 §1.4, adopted
under D1-A):

> HMA 27 fires only when a matrimonial proceeding under the HMA (ss. 9–13/13B)
> is pending, or is being filed together with the property claim, and the s.27
> application is made before that proceeding is decided. A freestanding s.27
> application with no HMA proceeding is not maintainable. A Family Court case
> under another Act (BNSS s.144, PWDVA, GWA 1890) is not an HMA proceeding for
> this purpose. "Being filed" means the user states they are filing, will file,
> or have instructed the filing of an HMA petition; wanting a divorce or wanting
> the property back, without more, does not count.

None of K0/H3/H10/H15 states a pending HMA proceeding or any intention to file
one, so HMA 27 cannot be in their GT. The graph already applies this exact
distinction to the parallel ancillary sections HMA 24 and HMA 26 (both `drop`
with no proceeding); HMA 27 was the only one never gated — an internal
contradiction, since the Stage 2 pipeline's own rule drops any section failing a
prerequisite check. The graph's "alternatively… pressed as part of the
family-court case for maintenance/custody/residence" limb is itself legally
wrong (a BNSS/PWDVA/GWA case is not an HMA proceeding) and is deleted with this
change, not kept.

---

## 3. Authority — *Astha Thakur* verification (read by the rater, 2026-11-27)

**Full citation:** *Astha Thakur v. Dhananjay Kanwar*, FAO (FC) No. 29 of 2022,
Himachal Pradesh High Court, Division Bench (Vivek Singh Thakur and Romesh
Verma, JJ.), decided **31 December 2025**, neutral citation **2025:HHC:46178**
(also cited as 2025 NCHHC 46178). Appeal against the order dated 12.10.2022 of
the Principal Judge, Family Court, Hamirpur (CMA No. 102 of 2017, in HMA
Petition No. 140 of 2016).

**What was read:** the Indian Kanoon text of the judgment (paras 2, 14, 18, 20,
21), the LiveLaw report (published 2026-01-06), and the LawFinder headnotes.
Sources:
- https://indiankanoon.org/docfragment/112564477/?formInput=section%2027%20of%20hindu%20marriage%20act
- https://www.livelaw.in/high-court/himachal-pradesh-high-court/himachal-pradesh-high-court-family-court-jurisdiction-divorce-decree-property-claims-516993

**Facts of the case (verified):** the wife obtained an ex parte divorce decree
under HMA s.13(1)(ia) on 31.01.2018 in HMA Petition No. 140 of 2016. **Her
s.27 application for return of stridhan, gifts and other articles was filed
during the pendency of that divorce petition** (CMA No. 102 of 2017); it was
not decided with the main petition and was dismissed afterwards by the Family
Court on the ground that, once the divorce decree had been passed without
property directions, no independent order could be passed. The High Court set
aside the dismissal and remitted the matter to the Family Court for decision on
the merits.

**Propositions it supports (verified from the judgment text):**

1. **s.27's "may" is discretionary** (para 14): "Court may make such provisions
   in the decree" as to property "which may belong jointly to both the husband
   and the wife". Failure to make a property provision in the decree does not
   exclude the Family Court's jurisdiction to entertain the property
   application afterwards.
2. **The Family Court retains jurisdiction under FCA s.7(1) Expl. (c) over
   property disputes between spouses even after a divorce decree** (paras 14,
   18): the Family Courts Act has overriding effect over inconsistent HMA
   provisions, and s.7 covers "a suit or proceeding between the parties to a
   marriage with respect to the property of the parties or of either of them".
3. **An application labelled s.27 only must still be adjudicated by the Family
   Court under its FCA s.7 jurisdiction**, to avoid multiplicity of litigation;
   the parties are not to be driven to a separate suit under FCA s.7(i) read
   with Expl. (c) (para 18).
4. **A post-decree property decree is treated as part of the divorce decree
   already granted** (para 20).
5. **No opinion was expressed on the merits** of either party's property claim
   (para 21).

**How it bears on D1-A:** it supports the correction in the precise sense that
matters here — the proper label for a Stridhan/property claim with no live
s.27 route is the **Family Court's FCA s.7(1) Expl. (c) jurisdiction, not
s.27 itself**. It does not rescue the v1 GT: the s.27 application in *Astha
Thakur* was filed inside a real, pending HMA proceeding, which is exactly what
K0/H3/H10/H15 lack.

**What it does NOT support — stated bluntly:**

- It does **not** decide a freestanding s.27 application where no HMA
  proceeding was ever filed. The LiveLaw summary's phrase "independent
  application" means independent of the *decree* (i.e. decidable after the
  decree), not independent of any proceeding. Anyone citing *Astha Thakur* for
  "s.27 needs no proceeding at all" is misreading it.
- It does **not** address whether a BNSS/PWDVA/GWA case counts as an HMA
  proceeding. That proposition rests on s.27's own words ("in any proceeding
  under this Act") and on *Balkrishna*, *Babulal* (Full Bench) and *Krishna
  Kumar Gupta* as recorded in v4 — **which this rater did not re-verify**.
- It is a **Division Bench of a single High Court** (Himachal Pradesh),
  decided 31.12.2025. It does not bind outside HP and is not Supreme Court
  authority. The v6 lane's caveat stands: no Supreme Court decision directly
  decides the freestanding-s.27 question.
- **Not all of the judgment was read in full.** The Indian Kanoon fetch
  returned paras 2, 14, 18, 20 and 21; paras 3–13, 15–17 and 19 were not read
  in full. The propositions above are verified from the paras actually read;
  nothing is claimed from the unread paras.

---

## 4. Consequence — gate §6.1 invalidation (read this before quoting any rating)

Per `laya-10-10-gate-definition.md` §6.1, **a GT change invalidates all prior
runs on that set — they must be re-run and re-filed**. This change therefore
invalidates, on the current 16:

- the v1 live run (5/16 exact, rating 3.3/10);
- the v3 live run (5/16 exact, gate-formula rating 5.0/10);
- the v4r live run (10/16 exact, micro-F1 0.905, gate-formula rating 7.3/10);
- the v5 prediction (16/16 exact, 9.8 raw → capped 9.0 — computed under the
  old 57-section GT; it **falls away** and must be re-predicted under v2).

No rating quoted from any of those runs survives this change. Under the
corrected GT, v4r re-scores **8/16 exact** before any system change is applied
(K0 and H10, both exact in v4r, become non-exact because the live system still
fires HMA 27 on both). That is the correction working, not a regression — but
it means the headline "10/16 → predicted 16/16" story is re-based, and the
user must be told so plainly.

**D2 must pair with D1 in the same logged change.** The notebook's Stage 2 gate
(HMA 27 dropped when no HMA proceeding is pending or being filed, R-HMA27-04
`escalate` → `drop`, "alternatively…" limb deleted, co-fire rule and BNS 316
exclusion amended per Lane 3 §1.4) must ship together with this GT file. Either
half alone makes the v5 prediction fall away: D1 without D2 gives 14/16 exact
(K0, H10 non-exact by HMA 27 false positive); D2 without D1 gives 14/16 exact
(K0, H10 non-exact by HMA 27 false negative). No run may be scored with the
gate on and the old GT, or vice versa.

**Sealed sets:** per v6 Lane 5 §7.1, the sealed fresh-20 and Kannada-8 sets also
contain HMA 27 in their GT. This erratum does **not** touch them (sealed sets
were not opened or modified by this lane). The same D1 question arises for
them and must be decided before any sealed run is scored — a sealed run scored
under a GT that still carries the known-wrong label would inherit the error.

---

## 5. Rater confirmations — D3 (H7) and D4 (H15)

Both are **confirmations, not GT changes**: no section, court or escalate
expectation changes for either question. The `gt_escalation_kinds` recorded in
v2 for H7 (`procedure`) and H15 (`recovery`) implement these confirmations
under the v6 Lane 2 typed-escalation design.

### D3 — H7 escalate expectation: KEEP True, re-grounded on a named fact kind (procedure)

H7 asks: "How do I get my daughter's birth certificate? The hospital did not
give us one." GT is `{Births and Deaths Act 1969}` only; court Registrar;
`escalate_expected: true`. I confirm **True**, on the following reasoning. The
question is fully answerable at the general-procedure level — the hospital
reports the birth under RBD Act s.8, the Registrar registers and issues the
certificate under s.12, and if already registered it is obtained by
application under s.17 — and none of that needs a lawyer. But it is **not**
fully answerable at the concrete-next-step level: the operative route turns
entirely on facts the question does not give, namely the child's date of birth
/ age, place of birth, and whether the birth was ever registered, because
s.13's delayed-registration tiers assign different authorities by delay
(≤30 days Registrar; 30 days–1 year District Registrar; >1 year a
Magistrate's order under s.13(3)). If the daughter is over one year old and
unregistered, the operative authority is a Magistrate, not the Registrar
alone — a material difference the system cannot know without asking. The
escalation is therefore a **named fact-ask to the user (DOB, delay,
registration status), then re-run** — recorded as kind `procedure` — and
expressly **not** a quantum escalation: the v4r True on H7 came from the
quantum boilerplate ("husband's income / school fees unknown"), which is
content-wrong on a birth-certificate question and must never be re-attached.
Flipping to False would assert the system can give the complete concrete next
step without the DOB, which is false. No GT change; no invalidation arises
from D3. Conditionality recorded: if a follow-up answer gives the DOB (e.g. a
newborn within the 30-day window), the escalation collapses to a routine
Registrar application.

### D4 — H15 escalate expectation: KEEP True, re-grounded on fact/proof kind (recovery)

H15 asks: "He sold my gold without asking me. The gold was given to me by my
parents at my wedding." GT is now `{BNS 316}` only (HMA 27 removed by D1-A);
court `[Family Court, Magistrate]`; `escalate_expected: true`. I confirm
**True**, on the following reasoning. The v5 framing — that H15 has no
escalation reason because `demand_made` is True, so no `demand` kind fires —
equates "escalation" with the three old typed kinds and misses the genuine
reasons, which are all fact/proof reasons: there is no proof of Stridhan
stated (no list, no receipts, no valuation), no sale details or value stated
(the gold is gone, so in-specie return is impossible and value recovery is the
question), and the criminal-route facts for a BNS 316 complaint are unstated.
The bot cannot value sold gold, cannot file a police complaint, and cannot
say the gold will be returned. The escalation is therefore a **named
fact/proof ask (proof, sale details/value, criminal-route facts)** — recorded
as kind `recovery` — and the old `demand` kind is no longer the reason.
Flipping to False would assert that a sold-gold Stridhan claim with no proof
or value stated needs no follow-up, which is false. No GT change; no
invalidation arises from D4. (D11 — confirming the `demand_made: true`
annotation on H15 as the inference "sale = refusal evident from conduct" —
is still outstanding at freeze time; it does not affect this confirmation,
since BNS 316 stays in GT via the demand-first fallback either way.)

---

## 6. What this file does NOT settle (outstanding, for the coordinator log)

- **D2** (HMA 27 corrected rule + Stage 2 gate, R-HMA27-04 → drop, co-fire
  rule and BNS 316 exclusion amended) — coordinator + notebook lane; must ship
  in the same logged change as this GT file.
- **D5** (H2/H4 escalate expectations + custody/residence kinds) — the
  `gt_escalation_kinds` for H2 (`custody`) and H4 (`residence`) in v2 are
  recorded per the v6 Lane 2 design; formal rater confirmation of D5 is still
  outstanding. The expectations themselves (True) are unchanged from v1.
- **D6** (H14 keeps HMA 13 — thinnest frozen call, relief-sought vs
  governing-section reading) and **D7** (H4 excludes PWDVA 20) — confirm-as-is
  recommended by Lane 3, still outstanding at freeze time.
- **D11** (H15 `demand_made: true` annotation as an inference) — still
  outstanding; no GT impact either way.
- **Recovery-text fix (coordinator, before any v6 run is scored):** the Lane 2
  `recovery` escalation text still says civil recovery is "under HMA s.27".
  Under D1-A that is wrong on K0 and H15. The text must be amended (civil
  recovery in the Family Court, without naming s.27) before any run scores
  those kinds — otherwise the removed label re-enters through prose.
  The same applies to the BNS 316 node exclusion text, which currently names
  HMA s.27 as the civil return route.
- **G2 amendment** (fresh gate 16 → 20) and the sealed-set HMA 27 question
  (§4 above) remain open and block any sealed run being scored.

---

## 7. Method note (how v2 was built, so it can be re-derived)

1. Read v1 GT from Cell 6 of `live-laya-colab-test-v5-precision.ipynb`
   (executed the cell source; 16 questions, 57 sections) and cross-checked
   every question, section set and court against `backtest-laya-vs-llama8b.md`
   §3 — exact agreement.
2. Verified from the GT + facts that exactly K0/H3/H10/H15 carry HMA 27, all
   with `proceeding_pending: false` and no filing intention in the question
   text (table in §1).
3. Built v2 programmatically: copied v1 verbatim, deleted only the `HMA 27`
   / `hma-27` element from those four questions, preserved v1 order and label
   strings, added `gt_escalation_kinds` (Lane 2 scoring set; `fact`
   informational only, never a scoring kind) and `gt_notes`. Re-verified from
   disk afterwards: total 53, only the four removals differ, no HMA 27 remains.
4. Read *Astha Thakur* via public web search + page fetch (Indian Kanoon
   fragment + LiveLaw); did **not** re-verify *Balkrishna* / *Babulal* /
   *Krishna Kumar Gupta* (v4's record stands, unverified by this rater).
5. No Colab run, no live model, no change to the sealed sets, no change to
   the v1 GT file or any notebook. No Option C file was produced.
