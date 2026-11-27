# Legal decisions — v4 (research only, 2026-11-26)

**Purpose:** resolve three open decisions blocking the Laya 10/10 push (overnight
2026-11-26). Research and recommendation only. **No ground-truth, graph, or
notebook file was modified.**

**Context read (only):** `laya-10-10-gate-definition.md` §5 (frozen definitions,
prose forbidden list) and the HMA 27 / H7 rows of `laya-10-10-exact-plan.md`
§3.2–§3.4. Live results JSONs and tuning reports were **not** read.

**Method:** primary sources first — statute text (India Code / Indian Kanoon
consolidated text), Supreme Court and High Court judgments, then reputable
legal reporting. Short quotes only. All URLs below are the exact URLs returned
by the searches / page reads used on 2026-11-26.

**Status note:** this is legal research for a test-system design decision, not
legal advice for any real person.

---

## Q1 — HMA s.27 (Stridhan / disposal of property): does it need a matrimonial proceeding?

### Verdict (one line)

**The v2 graph prerequisite is CORRECT in law and the GT is WRONG: HMA s.27 is
ancillary — it can only be pressed inside a matrimonial proceeding under the
HMA that is pending or being filed together with the claim, never as a
freestanding application with no HMA proceeding — so HMA 27 should not be in
the GT for H3/H10/H15 as those questions are worded (no proceeding pending or
being filed).**

### Evidence

**1. Statute text — HMA s.27.** Hindu Marriage Act 1955, s.27, "Disposal of
property":

> "In any proceeding under this Act, the court may make such provisions in the
> decree as it deems just and proper with respect to any property presented, at
> or about the time of marriage, which may belong jointly to both the husband
> and the wife."

Two qualifying phrases do all the work: *"in any proceeding under this Act"*
and *"in the decree"*. The section confers no freestanding cause of action; it
is a power exercisable inside a proceeding, at decree stage.

**2. Supreme Court — *Balkrishna Ramchandra Kadam v. Sangeeta Balkrishna
Kadam*, (1997) 7 SCC 500 / 1997 INSC 641, decided 4 Sept 1997.** The Court,
construing s.27:

> "On a plain reading of the section, it becomes obvious that the Matrimonial
> Court trying any proceedings under the Hindu Marriage Act, 1955, has the
> jurisdiction to make such provision in the decree as it deems just and proper
> with respect to any property presented 'at or about the time of marriage'
> which may belong jointly to both the husband and the wife. This section
> provides an alternate remedy to the wife so that she can recover the property
> which is covered by the section, by including it in the decree in the
> matrimonial proceedings, without having to take recourse to the filing of a
> separate Civil Suit and avoid further litigation."

Note the mechanism the Supreme Court describes: recovery *"by including it in
the decree in the matrimonial proceedings"* — i.e. inside a proceeding, not
instead of one. The Court also held the s.27 property need not be given only
at the wedding itself ("before or after marriage also, so long as it is
relatable to the marriage") — a broad reading of *"at or about the time of
marriage"*, but still a reading *inside* a proceeding.

**3. Chhattisgarh High Court (Full Bench) — *Babulal Yadav v. Sonu Yadav*,
FA (MAT) No. 40 of 2022, decided 4 July 2023 (2023 SCC OnLine Chh 2815).**
This is the most on-point authority: a three-judge bench convened precisely
because two Division Benches conflicted on this question
(*Devika Joshi* (2016) — independent s.27 suit maintainable — vs *Babita @
Gyatri v. Modprasad* (2017, AIR 2018 Chh 40) — not maintainable). Its
principles (para 18):

> "(ii) It must be a matrimonial proceeding pending under the Act and an
> application for disposal of the property under Section 27 of the Act must be
> made before the decision of the said matrimonial proceeding."
> "The entire section is qualified by words 'in any proceeding under this Act'
> and further 'may make such provision in the decree'. These two qualified
> phrases … make the provision 'ancillary'. In other words, there must be
> primary proceeding under the Act of 1955 in which the relief as available
> under Section 27 can be sought … the relief … can be sought 'in addition to'
> and 'along with' the substantive and main relief as is sought in the main
> proceeding initiated under the provisions of the Act of 1955."

And on Stridhan specifically (paras 20–21, 26–29):

> "Any property which is given separately to husband or the wife as stridhan
> cannot be held to be jointly belonging to both of them and in turn, Section
> 27 … would not be applicable for restitution of stridhan. Stridhan is the
> property of the wife in her individual capacity and the husband is merely the
> trustee of that property."
> "It is held that substantive and independent application under Section 151 of
> the CPC for return of stridhan would be maintainable before the Family Court
> under Explanation (c) to sub-section (1) of Section 7 of the [Family Courts]
> Act of 1984."
> "the judgment rendered in Smt. Devika Joshi (supra) to the extent that wife
> is entitled to recover stridhan by filing appropriate proceeding before the
> Family Court is the correct law, but, further, the finding that it would be
> maintainable under Section 27 of the Act of 1955 cannot be said to be laying
> down the correct law."

The Full Bench also held (para 29) that an application already filed under
s.27 claiming Stridhan "has to be read and treated as application under
Section 151 of the CPC" — the wrong label does not defeat the Family Court's
jurisdiction under Family Courts Act s.7(1) Expl. (c), but it does not make
the claim a s.27 claim either.

**4. *Babita @ Gyatri v. Modprasad @ Pintu*, Chhattisgarh HC, FAM No. 148 of
2016, decided 12 Sept 2017** — the question framed was exactly ours:

> "whether an independent proceeding for return of Streedhan under Section 27
> of the Hindu Marriage Act, 1955 … is maintainable when no other matrimonial
> proceeding between the parties has ever been decided or pending."

Held: no —

> "When any matrimonial proceeding under the Act is not decided between the
> parties, the provision does not clothe the Court with jurisdiction to
> entertain an independent application under Section 27 of the Act without
> there being any further proceeding under the Act as contemplated in Section 9
> to 13 and 13-A and 13-B of the Act, 1955."

(*Babita* itself was later overruled by *Babulal* only on the narrow point
that no independent remedy exists at all — *Babulal* preserves *Babita*'s core
holding that a first-time standalone s.27 application is not maintainable,
while adding the CPC s.151 / Family Courts Act s.7(1) Expl. (c) route.)

**5. Allahabad High Court — *Krishna Kumar Gupta v. Priti Gupta*, First
Appeal No. 1116 of 2024, reported 31 May 2025** (most recent authority found).
Following *Babita* and *Balkrishna*:

> "return of 'stree dhan' has to be an issue, to be determined at trial in a
> proceeding under the Act and not independently on application made under
> section 27."
> "Section 27 empowers the Court passing decree to include provisions in it
> with respect to any property presented, at or about the time of marriage,
> which may belong jointly to the parties."

The Family Court's freestanding s.27 order (₹10,54,364 in lieu of Stridhan,
made outside the divorce decree) was set aside. The Court also confirmed the
contrast with s.25: *"section 25 allows for a spouse to, subsequent to decree
for dissolution of marriage, apply for direction on maintenance"* — s.25
expressly allows a post-decree application; s.27 contains no such language.

### The "alternatively pressed as part of the family-court case" reading

This reading is **valid, and it is the only reading under which HMA 27
legitimately appears**. It is already inside the v2 prereq's "pending **or
being filed**" limb:

- If the user files a matrimonial petition under the HMA (ss. 9–13/13B —
  restitution, judicial separation, nullity, divorce) **together with** the
  property claim, the s.27 relief is pressed *in addition to and along with*
  the main relief in that proceeding (*Babulal* para 17). The proceeding need
  not have been pending for months; being filed with the claim suffices.
- The s.27 application must be made **before that proceeding is decided**
  (*Babulal* principle (ii)). A s.27 application first made *after* the decree,
  where the decree made no property direction, was set aside in *Krishna Kumar
  Gupta*. (A *subsequent* s.27 application after a previously instituted
  proceeding has been decided was treated as maintainable in *Manish Nema v.
  Sandhya Nema*, AIR 2009 MP 108, as summarised in *Babita/Babulal* — but only
  where a matrimonial proceeding had in fact been instituted; it does not help
  a case where no proceeding was ever filed.)
- What is **not** valid is treating s.27 as the label for a standalone
  Stridhan-recovery claim with no HMA proceeding at all. The standalone route
  exists — it is just not s.27: an independent suit/application in the Family
  Court under **Family Courts Act 1984, s.7(1) Explanation (c)** ("a suit or
  proceeding between the parties to a marriage with respect to the property of
  the parties or of either of them"), procedurally as a **CPC s.151**
  application (*Babulal* paras 25–29), plus the criminal route already in the
  GT (**BNS s.316**, criminal breach of trust — *Pratibha Rani v. Suraj Kumar*
  (1985) 2 SCC 370, wife is absolute owner of Stridhan, husband a custodian).

### Second-order scope point (not needed for the verdict, but material)

Even *with* a pending proceeding, s.27 on its text covers only property
*"which may belong jointly to both the husband and the wife"*. *Babulal*
(paras 20–21) holds exclusive Stridhan — e.g. gold given by the wife's own
parents at her wedding, as in H15 — outside s.27. *Balkrishna* took a broader
view of the property covered (the wife's jewellery given by her father was
held within s.27). This is a genuine tension between a Supreme Court
authority and a High Court Full Bench; it is **not** relied on for the verdict
above (the proceeding point alone decides it), but it is a further reason to
prefer the Family Courts Act s.7(1) Expl. (c) label for exclusive-Stridhan
claims rather than stretching s.27.

### Recommendation (do not edit files — coordinator / independent rater to act)

1. **Keep the v2 graph prerequisite; do not delete or weaken it.** Reword it
   slightly for precision: *"HMA 27 fires only when a matrimonial proceeding
   under the HMA is pending or is being filed together with the property claim,
   and the s.27 application is made before that proceeding is decided. A
   freestanding s.27 application with no HMA proceeding is not maintainable."*
   The current "pending or being filed" wording is already substantively
   right; the rewording only adds the before-decision timing point.
2. **GT is wrong on H3/H10/H15 as worded: remove HMA 27 from those three GT
   sets.** This is a GT correction, so per gate-definition §6 rule 1 it must go
   to an **independent rater (not the tuning lane)**, and it **invalidates all
   prior runs on the current 16** (they must be re-run and re-filed under the
   corrected GT). The 3 "exact matches" that gating would break were measuring
   a wrong label — losing them is the correction working, not a regression.
3. **Replace HMA 27 in those GT sets with the correct standalone route**,
   which needs a label the current set does not have: *Family Court —
   Family Courts Act s.7(1) Expl. (c) / CPC s.151 suit for return of Stridhan*.
   Keep **BNS 316** (already in GT for H3/H10/H15) as the criminal route.
   If the label set cannot gain a new label mid-gate, the honest fallback is
   to drop HMA 27 from those GT sets without replacement and record the
   missing-label gap — do **not** keep a known-wrong label to preserve the
   exact-match count.
4. **Gate HMA 27 on the prerequisite in Stage 2** (the "do NOT gate until
   settled" hold in plan §3.2 can now be lifted) — but apply the gate **in the
   same logged change as the GT correction**, so no run is scored with the gate
   on and the old GT, or vice versa.
5. **Prose rule (for the prose gate, §5):** any answer prose that cites s.27
   for a standalone Stridhan claim with no proceeding is a forbidden mapping
   of the same kind as gate §5 items 3/6/7 (wrong section for the facts). The
   correct prose formulation is: *"Ask for the property inside a matrimonial
   case under the HMA (s.27), or file a separate property suit in the Family
   Court (Family Courts Act s.7(1) Expl. (c)); if the property was entrusted
   and refused, BNS s.316 is the criminal route."*

### What remains uncertain

- **Contrary recent authority:** Himachal Pradesh HC, *Astha Thakur v.
  Dhananjay Kanwar*, FAO (FC) No. 29 of 2022, reported as decided 31 Dec 2025,
  held a Family Court retains jurisdiction over Stridhan/property claims even
  after a divorce decree and that an independent s.27 application is
  maintainable, reasoning from the Family Courts Act's overriding effect. This
  conflicts with *Krishna Kumar Gupta* (Allahabad, 2025) and *Babulal*. It is a
  single High Court decision, it does not bind outside HP, and it was only
  read here as a LiveLaw summary (full judgment not read). It does not displace
  the s.27-text reading, but it shows the point is litigated, not unanimous.
  If the coordinator wants certainty, the HP full judgment should be read
  before the GT change is frozen.
- **Scope tension** (*Balkrishna* broad vs *Babulal* narrow on exclusive
  Stridhan within s.27) — see above; unresolved, and a reason the FCA route
  is the safer label for H15-type facts.
- **No Supreme Court decision directly decides** the freestanding-s.27
  question; the chain is SC *Balkrishna* (ancillary, in-the-decree) +
  High Court Full Bench / Division Bench authority. That is strong, but not
  SC-direct.

### Sources — Q1

- Hindu Marriage Act 1955, s.27 (India Code official text, PDF):
  https://indiacode.gov.in/server/api/core/bitstreams/444124ee-b6d2-4649-8fc0-9eb48376484b/content
- Same text, with India Code attribution:
  https://voxjuris.org/act/hindu-marriage-act-1955/section-27-disposal-of-property
- *Balkrishna Ramchandra Kadam v. Sangeeta Balkrishna Kadam*, SC, 4 Sept 1997
  (1997 INSC 641): https://api.sci.gov.in/jonew/judis/13804.pdf
  and https://voxjuris.org/judgment/1997-insc-641/balkrishna-ramchandra-kadam-v-sangeeta-balkrishna-kadam
- *Babita @ Gyatri v. Modprasad*, Chhattisgarh HC, 12 Sept 2017 (FAM 148/2016):
  https://indian-high-court-judgments.s3.ap-south-1.amazonaws.com/data/pdf/year=2017/court=22_18/bench=cghccisdb/CGHC010227462016_1_2017-09-12.pdf
- *Babulal Yadav v. Sonu Yadav*, Chhattisgarh HC Full Bench, 4 July 2023
  (FA (MAT) 40/2022; 2023 SCC OnLine Chh 2815):
  https://www.courtkutchehry.com/judgements/1169390/babulal-yadav-vs-sonu-yadav/
- *Devika Joshi v. Deepak Joshi*, Chhattisgarh HC, 22 July 2016 (FAM 61/2016;
  the "independent s.27 suit maintainable" line, overruled in part by
  *Babulal*):
  https://taxguru.in/wp-content/uploads/2017/03/Smt.-Devika-Joshi-wo-Vs-Shri-Deepak-Joshi-So-Chhattisgarh-High-Court.pdf
- *Krishna Kumar Gupta v. Priti Gupta*, Allahabad HC, First Appeal 1116/2024,
  reported 31 May 2025:
  https://www.livelaw.in/amp/high-court/allahabad-high-court/streedha-section-27-hindu-marriage-act-proceedings-not-separate-293934
  and https://www.scconline.com/blog/post/2025/06/03/stridhan-recovery-must-be-under-hindu-marriage-act-allahabad-hc/
- Contrary authority (summary only, full judgment not read): *Astha Thakur v.
  Dhananjay Kanwar*, HP HC, FAO (FC) 29/2022, reported 31 Dec 2025:
  https://www.livelaw.in/high-court/himachal-pradesh-high-court/himachal-pradesh-high-court-family-court-jurisdiction-divorce-decree-property-claims-516993

---

## Q2 — H7 birth certificate: fully answerable, or is escalation genuinely needed?

Question as asked: *"How do I get my daughter's birth certificate? The
hospital did not give us one."* GT: only Registration of Births and Deaths
Act 1969; court: Registrar. Cell 6 sets `escalate_expected: true`.

### Verdict (one line)

**Escalate_expected = True is CORRECT, but only on a named fact-ask reason —
the question gives no date of birth / age, place, or registration status, so
the concrete route (Registrar alone vs District Registrar's permission vs a
Magistrate's order under s.13) cannot be determined — and it is NOT a
quantum/income escalation; the quantum boilerplate must never be attached to
H7.**

### Evidence

**1. The hospital does not issue the certificate; the Registrar does.**
Registration of Births and Deaths Act 1969, s.8(1)(b): for births in a
hospital, *"the medical officer in charge or any person authorised by him"*
must give the information to the Registrar. S.12:

> "The Registrar shall, as soon as the registration of a birth or death has
> been completed, but not later than seven days, give, free of charge,
> electronically or otherwise under his signature, to the person who gives
> information under section 8 or section 9, a certificate extracted from the
> register relating to such birth or death…"

So the first correction in any answer is: the hospital was never the issuer —
it reports; the Registrar (for the local area where the birth took place,
s.7) registers and issues. If the birth *was* registered, the parent obtains
the certificate by search/application under s.17. The question as asked does
not say whether the birth was registered at all.

**2. The procedure — and the forum — turn entirely on delay, which the
question does not state.** S.13, "Delayed registration of births and deaths"
(consolidated text as amended by the 2023 Amendment, in force 1 Oct 2023):

> "(1) Any birth of which information is given to the Registrar after the
> expiry of the period specified therefore, but within thirty days of its
> occurrence, shall be registered on payment of such late fee as may be
> prescribed.
> (2) Any birth or death of which delayed information is given to the Registrar
> after thirty days but within one year of its occurrence, shall be registered
> only with the written permission of the District Registrar or such other
> authority, on payment of such fee and on production of self-attested document
> in such form and manner as may be prescribed.
> (3) Any birth or death of which delayed information is given to the Registrar
> after one year of its occurrence, shall be registered only on an order made by
> a District Magistrate or Sub-Divisional Magistrate or by an Executive
> Magistrate authorised by the District Magistrate, having jurisdiction over the
> area where the birth or death has taken place, after verifying the correctness
> of the birth or death and on payment of such fee as may be prescribed."

Normal reporting period is 21 days (ss. 8–9, state Rules). So three different
answers attach to three different facts the user did not give:

| Delay | Route |
|---|---|
| ≤ 30 days | Registrar, late fee — s.13(1) |
| 30 days – 1 year | District Registrar's written permission + self-attested document — s.13(2) |
| > 1 year | Order of District Magistrate / SDM / authorised Executive Magistrate — s.13(3) |

If the daughter is over one year old and unregistered, the "court" is in
substance a Magistrate, not the Registrar alone — a material difference the
system cannot know without asking. That is a genuine escalation reason, not a
scoring technicality.

**3. The general route *is* answerable.** Act (Registration of Births and
Deaths Act 1969, not HMA — gate §5 prose item 6), authority (Registrar of the
area of birth), the hospital's s.8 duty, the s.12 free certificate, and the
s.13 tiers can all be stated without any further fact. So the question is not
unanswerable, and it needs no lawyer referral and no maintenance-quantum
escalation. The escalation is a **fact-ask to the user, then re-run** (the
v2 pipeline step-8 pattern in plan §3.4): ask the missing facts, then give the
one applicable tier.

### Recommendation (do not edit files)

1. **Keep `escalate_expected: true` for H7** — this resolves the plan §3.4
   ambiguity in favour of the "True on a named reason" branch (the branch
   under which escalates can reach 16/16). Do **not** flip it to False: False
   would assert the system can give the complete concrete next step, which it
   cannot without the date of birth.
2. **Name the reason as a typed escalation** (`kind: fact`, not `quantum` /
   `court`): *"Ask: daughter's date of birth / age, place of birth, and
   whether the birth was ever registered; then apply the s.13 tier — if over
   one year and unregistered, a Magistrate's order under s.13(3) is needed."*
   Cell 8 should score H7's escalation from this fact flag, not from the
   quantum flag (which must be False for H7).
3. **Prose rule:** H7 prose must give the tiered s.13 procedure (all three
   windows) plus the ask, and must state the hospital reports under s.8 while
   the Registrar issues under s.12. It must never carry the "husband's income /
   school fees unknown" boilerplate.
4. **Court stays Registrar** for the classification (the Registrar is the
   authority in every tier, including as the recipient of a Magistrate's order
   under s.13(3)); do not change `court_expected` to Magistrate on these
   facts.

### What remains uncertain

- **Daughter's age is the whole uncertainty.** If she is a newborn (within
  21/30 days), the answer is routine and no escalation beyond "confirm the
  hospital reported it / apply to the Registrar" would be needed. The True
  verdict is conditional on the fact being missing *in the question as asked*;
  a follow-up answer giving the DOB would collapse the escalation.
- **State Rules vary.** Forms, fees, the exact local office (municipality /
  panchayat / corporation) and the online portal (e.g. CRS) come from the
  applicable State Registration of Births and Deaths Rules, which the question
  does not identify (no state/place given). The answer must flag "as per your
  State Rules" rather than invent a form or fee.
- **Pre-amendment sources differ.** Older explainers cite s.13(2) as
  "prescribed authority + affidavit before a notary" and s.13(3) as "Magistrate
  of the first class / Presidency Magistrate". The current consolidated text
  (2023 Amendment) says District Registrar + self-attested document, and
  District Magistrate / SDM / authorised Executive Magistrate. Prose must use
  the current wording.

### Sources — Q2

- Registration of Births and Deaths Act 1969, ss. 7, 8, 12, 13, 17
  (consolidated text, as amended 2023):
  https://indiankanoon.org/doc/1636244/
- S.13 text (pre-amendment wording shown for comparison):
  https://Indiankanoon.org/doc/874632/
- Delayed-registration explainer (four windows, 2023 Amendment):
  https://www.legalrepublic.in/everyday-law/birth-certificate-late-registration/

---

## Q3 — Verify: "Sukhdev Singh v Sukhbir Kaur (Feb 2025)" on HMA s.25 permanent alimony

### Verdict (one line)

**VERIFIED — the judgment exists: Supreme Court of India, *Sukhdev Singh v.
Sukhbir Kaur*, Civil Appeal Nos. 2536 & 5726 of 2019, decided 12 February
2025, three-judge bench (Oka, Amanullah & Masih JJ.), [2025] 2 SCR 1569 :
2025 INSC 197 : 2025 LiveLaw (SC) 195 — it holds a spouse of a marriage
declared void under HMA s.11 IS entitled to seek permanent alimony under
s.25 (and interim maintenance under s.24 during s.11 proceedings), as a
discretionary relief.**

### Evidence

**Identity.** Supreme Court Reports headnote (2025 INSC 197):

> "Whether a spouse of a marriage declared as void under s.11 of the Hindu
> Marriage Act, 1955, is entitled to claim permanent alimony and maintenance
> under u/s.25 of the Act; whether in a petition filed seeking a declaration
> under s.11 … a spouse is entitled to seek maintenance pendente lite under
> u/s.24 of the Act."

Case details (corroborated by LiveLaw, LawFoyer, Telegraph, and the SCR PDF):
Civil Appeal No. 2536 of 2019 (with 5726 of 2019); judgment 12 February 2025;
bench Abhay S. Oka, Ahsanuddin Amanullah, Augustine George Masih JJ.; author
Oka J.; a reference by a two-judge bench order of 22 Aug 2024 because of
conflicting views.

**Holding on s.25.** LiveLaw headnote (2025 LiveLaw (SC) 195):

> "Hindu Marriage Act, 1955; Sections 11, 24 and 25 – Held, permanent alimony
> and interim maintenance can be granted under Sections 25 and 24 of the Hindu
> Marriage Act, 1955, respectively, even when a marriage is declared void
> under Section 11. The ruling resolved conflicting Supreme Court decisions,
> clarifying that the term 'any decree' in Section 25 includes decrees
> declaring a marriage void. (Para 18, 28)"

SCR headnote:

> "s.25 confers power on matrimonial court to grant permanent alimony 'at the
> time of passing any decree or at any time subsequent thereto' – 'Decree' in
> s.25 is to be understood with reference to s.23 HMA, which deals with decrees
> granting relief u/ss.9 to 13 HMA … s.25(1) makes no distinction between
> decree of divorce and decree declaring marriage as nullity, thus decree of
> nullity u/s.11 cannot be excluded from purview of s.25(1)."

The Court affirmed *Chand Dhawan v. Jawaharlal Dhawan* and *Rameshchandra
Daga v. Rameshwari Daga*, and disapproved the Bombay Full Bench view in
*Bhausaheb @ Sandhu v. Leelabai* and conflicting High Court / two-judge views.
It distinguished s.125 CrPC / s.18 HAMA authorities (*Yamunabai Adhav*,
*Savitaben Bhatiya*) as different remedial fields, and censured pejorative
descriptions ("illegitimate wife", "faithful mistress") in the Bombay Full
Bench judgment as violating Art. 21 dignity.

**Limits that must travel with the citation:**

- **Entitlement to *seek*, not entitlement to *receive*.** The relief is
  discretionary: *"Whether such a relief of permanent alimony can be granted
  or not always depends on the facts of each case and the conduct of the
  parties"* (Telegraph report of Oka J.; SCR headnote: "discretionary –
  Whether relief … depends on facts of each case and conduct of parties").
  Do not cite it as "s.25 always grants alimony in void marriages".
- **It was a reference, answered on law.** The reference was answered and
  *"the matters were directed to be placed before an appropriate Bench for
  decision on merits"* — the three-judge bench settled the question of law; it
  did not decide the parties' final alimony on the merits.
- **It does NOT remove the decree requirement for s.25.** It widens *which*
  decrees count ("any decree" includes a s.11 nullity decree); s.25 still
  operates *"at the time of passing any decree or at any time subsequent
  thereto"*. It therefore gives **no support** to the forbidden
  "HMA 25 with no decree" fires (H5/H9 in the retest) — those remain forbidden.
- **S.24 holding (for completeness):** interim maintenance *pendente lite*
  may be granted during s.11 proceedings if s.24 conditions are met, even
  where a prima facie view of nullity exists.

### Recommendation (do not edit files)

1. **Citation is safe to use, with the narrow proposition above.** Suggested
   citable form: *Sukhdev Singh v. Sukhbir Kaur*, (2025) 2 SCR 1569 : 2025
   INSC 197 (SC, 3-Judge Bench, 12 Feb 2025) — *"a spouse of a marriage
   declared void under HMA s.11 is entitled to seek permanent alimony under
   s.25 ('any decree' includes a nullity decree); grant is discretionary and
   depends on facts and conduct."*
2. **Scope-limit it in any precedent allow-list:** usable only for the
   void-marriage → s.25/s.24 question. Never cite it for Stridhan, custody,
   residence, general alimony quantum, or s.25-without-a-decree (that last use
   would be a prose forbidden mapping of the gate §5 kind — a precedent cited
   for the wrong issue).
3. Remove its "UNVERIFIED" flag; no further verification needed.

### What remains uncertain

- Nothing material about existence, date, court, or holding — all four are
  corroborated by the SCR text itself. The only open item is the eventual
  merits outcome for the parties after remittal, which is irrelevant to Laya's
  use of the case.

### Sources — Q3

- Supreme Court Reports text (2025 INSC 197), full judgment PDF:
  https://indian-supreme-court-judgments.s3.ap-south-1.amazonaws.com/data/pdf/year=2025/english/2025_2_1569_1587_EN.pdf
- LiveLaw full judgment PDF, 2025 LiveLaw (SC) 195:
  https://livelaw-nludelhi.refread.com/pdf_upload/2025-livelaw-sc-195-sukhdev-singh-v-sukhbir-kaur-12-feb-2025-623293.pdf
- Case summary / headnote:
  https://lawfoyer.in/sukhdev-singh-v-sukhbir-kaur-2025-2-s-c-r-1569-2025-insc-197/
- News report of the holding:
  https://www.telegraphindia.com/india/supreme-court-rules-spouses-can-seek-alimony-even-if-marriage-is-declared-void/cid/2083207

---

## Cross-cutting note for the coordinator

Q1 and Q2 both point the same way: **the system's labels must carry their
preconditions, not just their names.** HMA 27 without a proceeding, and a
birth-certificate answer without the s.13 delay tier, are both cases where the
section label is right in the abstract and wrong for the facts as stated. The
recommended fixes (GT correction for HMA 27 via an independent rater; typed
fact-escalation for H7) are the two concrete unblockers; neither requires any
change to the frozen rating formula or gate definitions.
