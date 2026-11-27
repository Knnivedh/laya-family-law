# Lane 5 — Website content / spec for the v2 Laya family-law decision graph

> **Lane:** 5 — Website content/spec (content only)
> **File:** `laya-graph/v2-lanes/lane5-website-content.md`
> **Status:** Content and structure only. **Do NOT build any artifact, web page, or app from this file in this lane** — the coordinator builds the web artifact.
> **Sources (do not edit):** `SHARED_BRIEF_V2.md`; v1 `laya-crpc-bns-section-decision-tree.json` (182 KB, valid JSON, 29 unique sections, 38 nodes, 66 edges, 0 dangling endpoints); v1 test report `laya-graph/test-report.md`.
> **Date:** 2026-11-26

## v2 two-stage design — confirmed understanding

**Stage 1 — Layman → article/section.** Pick ALL layman words and phrases in the user's question, fetch them into article-section format. Convert every layman expression into legal terms first, then map those legal terms to section(s) via Laya choice questions. The user asks in layman format; the graph does the translation — the user never has to know a section number.

**Stage 2 — Recheck inside the article section.** After Stage 1 picks sections, RECHECK each picked section against ALL its relations — prerequisites, exclusions / `not_for`, related sections, guardrails, court, and co-firing sections. Only after recheck is the answer final. A section that fails recheck (wrong issue, missing prerequisite, divorce not asked, etc.) must be **DROPPED with a reason**, not kept.

**Verified sections only.** Every section number on this site comes from the verified list in the shared brief. Anything else belongs in `unverified_excluded` and is not presented as fact.

---

# Suggested page structure

The coordinator should build the site in this order. Each heading below is one page section; the copy under it is the final website text.

1. **Hero** — what Laya is, in one screen, with the "NOT LLaMA" line and the promise: *ask in your own words, get the right sections.*
2. **What Laya is** — the model, in plain language.
3. **Why the old chatbot failed** — the 4/10 retest, with the exact mistakes named.
4. **How it works — the two-stage pipeline** — Stage 1, then Stage 2, as a diagram in words.
5. **The section graph** — the full map: every verified section, when it is used, and how the sections connect.
6. **Section cards** — one plain-language card per verified section (maintenance, custody, Stridhan, residence, procedure).
7. **Test-case walkthrough** — the 35-year-old Bengaluru woman's case, step by step through Stage 1, then Stage 2, to the final answer.
8. **Guardrails / wrong-mapping warnings** — prominent box, always visible, never buried.
9. **What it does NOT do** — the limits, stated plainly.
10. **Footer / sources and status** — what is verified, what is not, and where the numbers come from.

---

# 1. Hero

## Ask in your own words. Get the right law.

**Laya is a decision model, not a chatbot that makes things up.**

You do not need to know any section number. You say what is happening — in plain, everyday words — and Laya works out which articles and sections apply, checks each one again before answering, and tells you which court decides it.

> **Laya is NOT LLaMA.** Laya is the Convai Innovations **System One** decision model. It does not generate long free-text answers. It answers typed questions — choice, score, and `noul` — in a single forward pass, and picks the right section from a verified list.

**Three things this site shows you:**

1. **What Laya is** — and what it is not.
2. **Why the old chatbot got family law wrong** — the exact mistakes, so you can see what this graph fixes.
3. **How the new two-stage graph works** — layman words in, checked sections out — with a full worked example.

*This site explains the system. It is not legal advice. If confidence is low or a fact is missing, the system escalates to a human lawyer — it does not guess.*

---

# 2. What Laya is

## Laya, in plain language

**Laya is a decision model.** Most chatbots *generate* text — they write sentences, and a section number can slip in that was never checked. Laya works differently: it is given a typed question with a fixed set of answers, and it **chooses** — in one forward pass. That choice is the classification. No free-text generation is used for section selection.

- **Full name / maker:** Laya — Convai Innovations **System One** decision model.
- **NOT LLaMA.** Laya is not LLaMA, not a LLaMA variant, and not a general chat model wearing a different name. Saying so is a mistake the old system invited; this site corrects it up front.
- **Size and base:** **421M parameters, ModernBERT-large.**
- **Licence:** **Apache-2.0.**
- **How it answers:** typed **choice / score / `noul`** questions in **one forward pass**, instead of generating text. One Laya forward pass per decision node. A complex question runs the root choice once, then each selected lane's choice nodes in parallel — classification in a fraction of a second, not a generated answer.
- **What it decides here:** which Indian family-law sections apply to a layman's question — CrPC / BNSS and BNS, plus HMA, PWDVA, and the guardianship Acts where the retest proved them necessary.

## The model on this computer

- **Downloaded checkpoint (English):** **808 MB**, at `~/workspace/models/laya-english`
- **Main weights file:** `model.safetensors`, **804 MB**
- **How it got here:** the official repo weights failed with **403**, so the **PIXMELT snapshot** was used instead. Do not retry the official download — the checkpoint above is the one in use.
- **What the graph is:** the v1 decision tree is a separate file — `laya-crpc-bns-section-decision-tree.json` — with **29 unique sections, 38 nodes, and 66 edges, 0 dangling endpoints**. The v2 graph keeps that structure and adds the two-stage layman-proofing described on this page: a layman phrasebook (Stage 1) and a recheck rule for every section (Stage 2).

## What "System One" means for you

"System One" means fast, direct classification — the model picks, it does not chat. That is a strength for section selection (fast, checkable, no invented wording) and a limit for everything else (it cannot argue a case, weigh evidence, or decide an amount). Amounts, timelines, and judgement calls are escalated, never generated. See "What it does NOT do" below.

---

# 3. Why the old chatbot failed

## The fresh English retest, 2026-11-26: 4 out of 10

The old legal chatbot was retested in English on 2026-11-26 on one realistic case (see the walkthrough below). It scored:

- **Overall: 4/10**
- **Legal accuracy: 3/10**
- **English: 8/10** — the language was fine. The law was not.
- **Completeness: 3/10**
- **Reasoning: 2/10**

The words sounded right. The sections were wrong. That is the failure this graph is built to prevent: a fluent answer that cites the wrong law is worse than no answer, because it looks trustworthy.

## The exact mistakes

These are not paraphrases. Each one happened in the retest:

1. **Rajnesh v. Neha cited for Stridhan return.** Rajnesh v. Neha is a maintenance case — it governs how much maintenance is paid. It says nothing about returning Stridhan. The old chatbot used it as authority for getting gold and cash back.
2. **Satish Chander Ahuja cited for custody.** Satish Chander Ahuja is a shared-household / residence case. It says nothing about who gets custody of a child. The old chatbot cited it for custody.
3. **HMA ss. 13 / 13B listed, though no divorce was asked for.** The woman never asked for divorce. The old chatbot listed the divorce sections anyway — as if divorce were already on the table.
4. **Birth certificate wrongly said to be under the HMA.** A birth certificate is issued under the **Registration of Births and Deaths Act 1969**, not the Hindu Marriage Act.
5. **The wife's residence was called "tenancy rights".** It is not tenancy. It is the **right to reside in the shared household** under the Protection of Women from Domestic Violence Act (PWDVA). Calling it tenancy changes the legal basis entirely.
6. **The user was asked to pick the court.** The old chatbot asked *her* which court to go to (in the retest, Q6 asked the user to pick the court). A layman cannot be expected to know that. The graph must pick the court.
7. **Missing at the right time: BNSS s. 144 / CrPC s. 125 and PWDVA s. 20 for maintenance; HMA s. 26 / Guardians and Wards Act for custody; HMA s. 27 and IPC s. 406 / BNS s. 316 for Stridhan; PWDVA ss. 17–20 for residence.** The maintenance answer gave only HMA s. 24, with no s. 24 interim vs s. 25 permanent distinction and no maintenance amount. The core, immediate remedies were simply absent.
8. **Reasoning was template, not reasoning.** "Explainable Legal Reasoning" was only four bare titles. "Precedent Analysis" was generic template text. Raw JSON leaked seven times. The answer stopped at Turn 7 of 10.
9. **It never asked what it needed, and demanded what she did not have.** It never asked the husband's income, the school-fee amount, or where the husband actually lives now — and still demanded salary slips she said she does not have.

## The lesson

Section selection was the core issue; the reasoning fell apart because it was built on the wrong law. Fix the section first, check it again, and only then explain. That is the v2 pipeline.

---

# 4. How it works — the two-stage pipeline

## The pipeline, as a diagram in words

```
  YOUR WORDS (layman)
        │
        ▼
  ┌─────────────────────────────┐
  │  STAGE 1                    │
  │  Layman → legal terms →     │
  │  article / section          │
  │                             │
  │  • Pick ALL layman words    │
  │    and phrases              │
  │  • Convert each one into    │
  │    legal terms              │
  │  • Map legal terms to       │
  │    section(s) with Laya     │
  │    choice questions         │
  └─────────────────────────────┘
        │
        │  candidate sections
        ▼
  ┌─────────────────────────────┐
  │  STAGE 2                    │
  │  Recheck INSIDE each        │
  │  article / section          │
  │                             │
  │  • Prerequisites met?       │
  │  • Exclusions / not_for?    │
  │  • Related sections         │
  │    co-firing?               │
  │  • Guardrails passed?       │
  │  • Right court?             │
  │                             │
  │  PASS → keep the section    │
  │  FAIL → DROP it, with a     │
  │         reason, not kept    │
  └─────────────────────────────┘
        │
        ▼
  FINAL ANSWER
  checked section sets + court
  + the 3 missing facts to ask
  + documents checklist
  (amount escalated, never invented)
```

## Stage 1 — Layman → legal terms → article/section

**You ask in layman format. The graph does the translation.**

Stage 1 picks **ALL** layman words and phrases in the question — not just the first one — fetches them into article-section format, and converts every layman expression into legal terms before any section is chosen. Only then does Laya map the legal terms to section(s) through typed choice questions.

**The exact layman examples the graph is built to understand:**

- **"my husband is not giving me money"** — *money not given, no support* → maintenance: unable to maintain herself, husband neglecting / refusing to maintain.
- **"he took my gold"** — and in full, **"he took my gold and cash and won't return it"** — *her gold and cash, held by him / his family, not returned* → Stridhan: entrusted property withheld.
- **"they are throwing me out"** — and in full, **"they are throwing me out of the house"** — *eviction threat, being forced out of the home* → residence: right to reside in the shared household, protection from dispossession.
- **"who will get my daughter"** — *who the child lives with* → custody: who cares for the minor child, welfare of the child.
- **"I need money for my child"** — *child's upkeep, school costs* → maintenance for the minor child, and monetary relief for school fees.
- **"he beats me / threatens me"** — *violence, threats, intimidation* → protection: stop the violence and threats.

One question usually raises several issues at once. The root choice picks **ALL** that apply — maintenance, custody, Stridhan, residence, procedure — in one Laya forward pass. Divorce is **not** picked unless divorce was asked for.

## Stage 2 — Recheck inside each article/section

**Picking a section is not the answer. Checking it is.**

After Stage 1 picks sections, Stage 2 rechecks each picked section against **all** its relations before the answer is final:

- **Prerequisites** — are the conditions for this section actually met on these facts?
- **Exclusions / `not_for`** — is this section explicitly *not* for this issue?
- **Related sections** — do the sections that must fire together actually fire together?
- **Guardrails** — do the forbidden mappings (below) stay forbidden?
- **Court** — is this section's court the one the graph will name?

**Only after recheck is the answer final.** A section that fails recheck — wrong issue, missing prerequisite, divorce not asked — must be **dropped with a reason**, not kept to look complete.

**Worked recheck examples (these are the rules, not illustrations):**

- **BNSS s. 144 firing must recheck HMA s. 24 vs s. 25 and PWDVA s. 20.** Is there a pending HMA proceeding (s. 24, interim) or a decree (s. 25, permanent)? If neither, BNSS s. 144 is the live route and ss. 24/25 are named only as the conditional / future route. PWDVA s. 20 is checked alongside for monetary relief — and the amounts are set off, never double-counted.
- **Stridhan must recheck HMA s. 27 + BNS s. 316 together.** The civil return route (s. 27, Family Court) and the criminal breach-of-trust route (s. 316) are two routes for the same withheld property. One without the other is an incomplete answer; if either is dropped, the reason is recorded.
- **Custody must recheck welfare-of-the-child overriding the natural-guardian default.** For an 8-year-old, the father is the natural guardian in law — the mother's claim is not built by denying that, but by the welfare principle, which is paramount and overrides the default.
- **Residence must recheck PWDVA ss. 17 + 18 + 19 + 20 as a set.** The right to reside (s. 17), the protection order (s. 18), the residence order (s. 19), and monetary relief (s. 20) are checked together. Dropping one silently would leave the woman with a right she cannot enforce, or an order with no money behind it.

---

# 5. The section graph

## The full map — every verified section, and how they connect

There are **13 statutory sections and principles** in the verified set, plus **16 procedure items** (courts, filing, documents, timeline) — **29 unique sections in v1, 38 nodes, 66 edges, 0 dangling endpoints**. PWDVA s. 20 is one canonical section shared by the maintenance and residence lanes; it is counted once, not twice.

**The four section sets — the heart of the graph:**

| Issue | Section set (fires together) | In plain words |
|---|---|---|
| **Maintenance** | BNSS s. 144 + HMA s. 24 + HMA s. 25 + PWDVA s. 20 | Monthly support now, interim support during a case, permanent support after a decree, plus money for expenses |
| **Custody** | HMA s. 26 + Guardians and Wards Act 1890 + HMGA 1956 s. 6 + welfare-of-the-child principle | Who the child lives with, in a case or on its own, who the natural guardian is, and the child's welfare deciding it |
| **Stridhan** | HMA s. 27 + BNS s. 316 | Get her own gold and cash back (civil) + criminal breach of trust for withholding it |
| **Residence** | PWDVA s. 17 + s. 18 + s. 19 + s. 20 | Right to stay in the shared household, stop the threats, an enforceable stay order, plus money if she cannot stay |
| **Divorce** | *(empty in the test case)* | HMA ss. 13 / 13B fire **only** if divorce was asked. It was not. |

**How the sets connect to each other (co-firing):**

- **Maintenance ↔ Custody:** BNSS s. 144 child maintenance pairs with HMA s. 26 custody — who the daughter lives with decides who claims child maintenance for her. School fees sit in both: PWDVA s. 20 covers them as monetary relief, and they shape the maintenance amount.
- **Maintenance ↔ Residence:** Maintenance under BNSS s. 144 does not itself secure residence. PWDVA s. 17 is the residence remedy; PWDVA s. 20 covers rent or alternative accommodation if she is kept out. The money and the roof are claimed together so cutting off one does not defeat the other.
- **Custody ↔ Residence:** If the mother and daughter need to remain in the home, PWDVA ss. 17 and 19 secure the home for the custodial parent and child.
- **Stridhan ↔ Maintenance:** HMA s. 25 alimony is about ongoing support; HMA s. 27 is about return of property. Separate heads — do not merge them, and do not cite a maintenance case for a property return.
- **Everything ↔ Procedure:** Every set ends in the same procedure lane — the graph picks the court, asks the three missing facts, lists the documents, and stages filing → interim relief → evidence → final order → enforcement.

---

# 6. Section cards — every verified section, in plain language

*Each card gives: what it is, when it is used, what it gets you, and what it is NOT for. Section numbers are kept exactly to the verified list.*

## Maintenance

### BNSS s. 144 — Order for maintenance of wives, children and parents
*Old equivalent: CrPC s. 125.*

- **When it is used:** A wife, minor child, or parent who cannot maintain themselves asks a Magistrate for a monthly order against a person who has enough money but neglects or refuses to maintain them. Here: Hindu marriage subsisting since 2012, husband separated for 2 years, paying **no** maintenance at all, wife earning ₹40,000/month but unable to fully maintain herself and her 8-year-old daughter on it.
- **What it gets you:** Monthly maintenance for the wife **and separately** for the 8-year-old daughter (child maintenance is a second head under the same section); interim maintenance while the application is pending; costs.
- **Court:** Judicial Magistrate, Bengaluru — where the wife resides. The graph picks the court.
- **Not for:** permanent alimony after a divorce decree (that is HMA s. 25); interim support inside a pending HMA proceeding (that is HMA s. 24); Stridhan return (HMA s. 27 / BNS s. 316); residence (PWDVA ss. 17–19).
- **Precedent, correctly used:** **Rajnesh v. Neha** — maintenance **only**: the criteria for how much maintenance, and the affidavit of assets and liabilities. Never for Stridhan, custody, residence, or divorce.

### HMA s. 24 — Maintenance pendente lite (interim maintenance) and expenses of proceedings

- **When it is used:** **Interim** maintenance **during** a pending proceeding under the Hindu Marriage Act — restitution, judicial separation, divorce, or nullity — when the applicant has no independent income enough for support and the expenses of the case.
- **In the test case:** it applies **only if / when** an HMA proceeding is filed. No HMA case is pending, so it is conditional, not the live remedy. The retest error was citing *only* s. 24 and omitting BNSS s. 144.
- **What it gets you:** Monthly interim maintenance from the date of application until the proceeding ends, plus litigation expenses. Adjustable against the final s. 25 order.
- **Not for:** a standalone maintenance claim with no HMA case; permanent alimony (that is s. 25); Stridhan, custody, or residence.

### HMA s. 25 — Permanent alimony and maintenance

- **When it is used:** **Permanent** alimony ordered **at the time of passing an HMA decree, or any time after it**, on application by either spouse.
- **In the test case:** it does **not** apply yet — no divorce was asked for and no decree exists. It is named in the set so the user understands the permanent route exists at decree stage, and so the s. 24 (interim) vs s. 25 (permanent) distinction is explicit. Never cite s. 25 together with HMA ss. 13/13B unless divorce was actually asked for.
- **What it gets you:** Permanent alimony — a lump sum or a monthly payment for life or a fixed period, as the court directs. The court may vary it if circumstances change.
- **Not for:** maintenance while the marriage subsists with no decree in prospect (use BNSS s. 144 and PWDVA s. 20); interim support (that is s. 24); Stridhan, custody, or residence.

### PWDVA s. 20 — Monetary reliefs

- **When it is used:** A woman in a domestic relationship who has suffered domestic violence — including **economic abuse**, here two years of separation with no maintenance paid, plus eviction threats — and has incurred, or will incur, expenses or losses.
- **What it gets you:** Maintenance for the woman and the 8-year-old daughter, compensation for loss of earnings, medical expenses, **school fees**, loss or damage to property, and rent or alternative-accommodation costs where she has been kept out of the shared household. The Magistrate may also order a lump sum.
- **Court:** Judicial Magistrate under the PWDVA, Bengaluru. Shared with the residence lane — one canonical section, cross-linked, never duplicated or double-counted.
- **Not for:** a standalone maintenance code (the core claim remains BNSS s. 144 — cite together, never instead of it); Stridhan return; custody; a residence order by itself (that is ss. 17–19); divorce.

## Custody

### HMA s. 26 — Custody of children in matrimonial proceedings

- **When it is used:** A Hindu matrimonial proceeding is before the court **and** the parties have a minor child whose custody, maintenance, or education needs deciding. The court may pass interim or final custody orders at any stage.
- **What it gets you:** Interim or final custody; visitation / access for the non-custodial parent; directions on the child's maintenance and education during the proceedings. The order can be varied as circumstances change.
- **Not for:** custody where no HMA proceeding exists or is contemplated (use the Guardians and Wards Act 1890); appointing a guardian as a standalone matter; non-Hindu parties.
- **Guardrail:** **Satish Chander Ahuja is never a custody precedent.** It is residence only.

### Guardians and Wards Act 1890 — Guardianship and custody of minors (court-appointed guardian)

- **When it is used:** A minor child's custody or guardianship (of the person or of property) needs deciding by a court **and there is no HMA proceeding** in which custody can be decided under HMA s. 26 — for example, parents separated but no divorce/separation petition filed, or a guardian of the child's property must be appointed.
- **In the test case:** the fallback / parallel route — if no HMA proceeding is filed, the mother's custody claim for her 8-year-old daughter proceeds under this Act.
- **What it gets you:** Appointment or declaration of a guardian of the minor's person and/or property; a custody order for the fit person; visitation for the other parent; directions for the child's welfare, education, and property.
- **Not for:** the primary route when custody can be decided inside a pending HMA proceeding (use HMA s. 26 there); deciding who the natural guardian is in the abstract (that is HMGA s. 6); maintenance or residence.

### HMGA 1956 s. 6 — Natural guardians of a Hindu minor

- **When it is used:** The question is **who the natural guardian** of a Hindu minor is. For a legitimate child: the father first, then the mother. For a child **below five years**, custody is ordinarily with the mother. For an illegitimate child: the mother first, then the father.
- **In the test case:** the daughter is 8 — **above five** — so the father is the natural guardian in law. The mother's custody claim is therefore framed on the **welfare principle**, which overrides the default — not by denying the father's status.
- **What it gets you:** Recognition of natural-guardian status, and the framing of the custody claim. It does **not** by itself grant custody or appoint a guardian.
- **Not for:** granting custody by itself; appointing a guardian; non-Hindu minors; overriding the welfare of the child.

### Welfare-of-the-child principle — paramount consideration

- **When it is used:** In **every** custody or guardianship decision — under HMA s. 26, under the Guardians and Wards Act 1890, and in any consideration of natural guardianship under HMGA s. 6.
- **What it means:** Whenever a court decides who a minor child lives with, who cares for the child, visitation, or guardianship, the child's welfare — health, education, emotional well-being, stability, and wishes if old enough — is the **first and paramount consideration**. It overrides the parents' rights, the natural-guardian default order, and any other consideration.
- **In the test case:** the daughter's schooling in Bengaluru, stability, current living arrangement, and bond with each parent decide custody — not the father's natural-guardian status alone.

## Stridhan

### HMA s. 27 — Disposal of property: return of Stridhan / joint property in matrimonial proceedings

- **When it is used:** A Hindu wife's Stridhan — gold, jewellery, cash, gifts given to **her** at or around marriage by her parents, relatives, or in-laws, or acquired by her — is held by the husband or his family and has not been returned, in the context of a matrimonial proceeding.
- **In the test case:** ₹5 lakh gold + ₹2 lakh cash given as Stridhan, held by the husband's family, not returned after two years of separation.
- **What it gets you:** A direction for return of the Stridhan **in specie** (the gold itself) or, if it has been disposed of, its value — ₹7 lakh in total — plus a direction restraining disposal of the property pending return. This is return of the wife's **own property**, not maintenance and not alimony.
- **Court:** Family Court, Bengaluru.
- **Not for:** maintenance (HMA ss. 24/25, BNSS s. 144); custody; residence. **Never cite Rajnesh v. Neha for Stridhan.**
- **Open fact to confirm:** whether a demand for return was made. If no demand was made yet: demand first, then re-evaluate.

### BNS s. 316 — Criminal breach of trust (IPC s. 406 equivalent): Stridhan withheld

- **When it is used:** Stridhan was **entrusted** to the husband or his family — they received and held the wife's gold/cash as trustees — and, on demand, they dishonestly misappropriate it, convert it to their own use, or refuse to return it.
- **What it gets you:** Criminal prosecution for criminal breach of trust (imprisonment and fine as prescribed) and, in practice, pressure for return. **A conviction does not by itself order return** — the HMA s. 27 Family Court claim is needed for the return order. The two routes run together; neither replaces the other.
- **Warning to carry on the page:** filing an FIR / criminal complaint is a criminal step with its own consequences and should be taken on legal advice, alongside — not instead of — the civil claim.

## Residence

### PWDVA s. 17 — Right to reside in a shared household

- **When it is used:** The woman is threatened with eviction, dispossession, or exclusion from the household where she lives or has lived in a domestic relationship, or needs the legal basis to remain living there.
- **In the test case:** wife and 8-year-old daughter live in a house in the husband's name; eviction threatened; she seeks to stay. The right exists **whether or not** she has any title, ownership, or tenancy in the house, and whether or not the house is in the husband's name, joint-family property, or owned by in-laws.
- **What it gets you:** Recognition of the right to reside in the shared household. The respondent cannot evict, dispossess, or exclude her except in accordance with law. This is the legal foundation — the enforceable orders come under s. 19.
- **Not for:** tenancy. **Residence is NEVER "tenancy rights".**

### PWDVA s. 18 — Protection order

- **When it is used:** The respondent has committed, or threatens to commit, an act of domestic violence — including physical violence, threats, intimidation, harassment, or coercion — and an order is needed prohibiting it.
- **In the test case:** eviction threats against the wife (and the pressure this puts on her and her daughter) as domestic violence, plus any accompanying abuse, harassment, or intimidation by the husband or his family.
- **What it gets you:** An order prohibiting the respondent from committing domestic violence, aiding it, entering her workplace or other specified places, communicating with her in specified ways, or committing any other act specified in the order. Breach is punishable. It stops the threats; it does not settle residence, money, custody, or property.

### PWDVA s. 19 — Residence order

- **When it is used:** The s. 17 right to reside needs an **enforceable** order — restraining the respondent from dispossessing or disturbing her possession, restraining him or his relatives from entering the house, directing his removal, restraining him from selling or encumbering the house, or directing alternative accommodation / rent where she cannot live there.
- **In the test case:** the default direction is **restraint on dispossession** — she and her daughter stay in the house. Removal of the respondent and alternative accommodation are fact-dependent; do not assume them.
- **What it gets you:** A residence order making "she may stay" enforceable, and the fallback (alternative accommodation of the same level, or rent for it) if staying becomes impossible.

### PWDVA s. 20 — Monetary reliefs (residence face)

- **When it is used (residence face):** the woman has suffered economic loss because of domestic violence — including rent for alternative accommodation where she cannot live in the shared household — and needs money to meet those expenses and maintain herself and her child.
- **Cross-link:** defined once, in the maintenance cards above. The residence lane uses the same section for its money face; the maintenance lane owns the maintenance computation. Do not double-count the same maintenance under s. 20 and BNSS s. 144 / HMA ss. 24–25.

## Procedure — the graph picks the court

- **Family Court, Bengaluru** — HMA matters: maintenance ss. 24/25, custody s. 26, Stridhan s. 27.
- **Magistrate, Bengaluru** — BNSS s. 144 maintenance and PWDVA reliefs (ss. 17/18/19/20).
- **BNS s. 316** — criminal complaint route, parallel to HMA s. 27.
- **Divorce gate:** HMA ss. 13 / 13B fire **only** if divorce was expressly asked. Ambiguous → escalate to a human lawyer; do not infer a divorce request.
- **Documents checklist (collect as far as possible; never block filing on a document she does not have):** marriage proof (Hindu marriage, 2012); child's **birth certificate under the Registration of Births and Deaths Act 1969, NOT HMA**; husband's income **as she knows it — ask, never demand salary slips she said she does not have**; school-fee amount / receipts for the 8-year-old; husband's current address; Stridhan list with proof (₹5 lakh gold + ₹2 lakh cash); residence proof for the shared household and the facts of the eviction threats.
- **Staged timeline:** clarifying questions / documents → filing → notice / first hearing → interim relief → evidence → final order → enforcement. **Every duration is an ESTIMATE, not a statutory deadline. No fixed date is promised for any stage.**

---

# 7. Test-case walkthrough — the 35-year-old Bengaluru woman's case

*One case, end to end, so a visitor can see the whole system working. All facts are the 2026-11-26 retest facts.*

## The case

A **35-year-old Hindu woman, Bengaluru**. Hindu marriage **2012**. Husband separated **2 years**, paying **no maintenance**. She earns **₹40,000/month**. **8-year-old daughter.** **Stridhan: ₹5 lakh gold + ₹2 lakh cash**, held by the husband's family. **Eviction threats** from the house in the husband's name. She asks about **maintenance, custody, Stridhan return, residence, court, documents, and timeline**. She does **not** ask for divorce. She says she does **not** have her husband's salary slips.

## Step 1 — Stage 1: her words become legal terms

| She says (layman) | Legal terms | Issues picked |
|---|---|---|
| "my husband is not giving me money" | Wife unable to maintain herself; husband neglecting / refusing to maintain | Maintenance |
| "I need money for my child" | Minor child unable to maintain itself; school fees | Maintenance (child head) |
| "who will get my daughter" | Custody of a minor child; welfare of the child | Custody |
| "he took my gold" / "he took my gold and cash and won't return it" | Stridhan entrusted and withheld | Stridhan |
| "they are throwing me out" / "they are throwing me out of the house" | Threatened dispossession from the shared household | Residence |
| "he beats me / threatens me" (eviction threats) | Domestic violence — threats / intimidation | Residence — protection |

**Root choice (one Laya forward pass):** picks **ALL** of maintenance, custody, Stridhan, residence, procedure. **Divorce is not picked** — it was not asked for. No free-text generation is used for section selection.

## Step 2 — Stage 1 (continued): each lane picks its sections

- **Maintenance lane** → BNSS s. 144 + HMA s. 24 + HMA s. 25 + PWDVA s. 20.
- **Custody lane** → HMA s. 26 + Guardians and Wards Act 1890 + HMGA 1956 s. 6 + welfare-of-the-child principle.
- **Stridhan lane** → HMA s. 27 + BNS s. 316.
- **Residence lane** → PWDVA s. 17 + s. 18 + s. 19 + s. 20.
- **Procedure lane** → court selection, clarifying questions, documents checklist.

## Step 3 — Stage 2: recheck each section before the answer is final

- **Maintenance recheck:** BNSS s. 144 passes — marriage subsists, two years of zero payment, wife cannot fully maintain herself and her daughter on ₹40,000/month. HMA s. 24 is checked and kept **conditional** — it needs a pending HMA proceeding, and none is filed; BNSS s. 144 is the live route. HMA s. 25 is kept as the **future** permanent route at decree stage, with no divorce sections cited. PWDVA s. 20 passes on economic abuse (maintenance withheld) plus eviction threats; amounts are set off against BNSS s. 144, never double-counted.
- **Custody recheck:** HMA s. 26 passes as the in-proceeding route; the Guardians and Wards Act 1890 passes as the standalone fallback if no HMA proceeding is filed. HMGA s. 6 passes — and its recheck is the point: the father **is** the natural guardian for an 8-year-old above five, so the claim rests on the **welfare principle**, which overrides that default. Satish Chander Ahuja is checked and **dropped for custody with a reason** — it is residence only.
- **Stridhan recheck:** HMA s. 27 and BNS s. 316 pass **together** — civil return and criminal breach of trust for the same ₹7 lakh. Rajnesh v. Neha is checked and **dropped for Stridhan with a reason** — it is maintenance only. One open fact is flagged, not guessed: whether a demand for return was made (fallback: demand first, then re-evaluate).
- **Residence recheck:** PWDVA ss. 17 + 18 + 19 + 20 pass **as a set**. Default s. 19 direction: restraint on dispossession — she stays in the house. Removal / alternative accommodation is **not** assumed; it is fact-dependent. Residence is checked against the "tenancy rights" label and the label is **dropped** — it is the right to reside in the shared household.
- **Procedure / divorce-gate recheck:** HMA ss. 13 / 13B are checked and **dropped with a reason** — no divorce was asked for, so the divorce set is **empty**. The birth-certificate route is checked and corrected to the **Registration of Births and Deaths Act 1969**, not HMA.

## Step 4 — The final answer

**Final section sets:**

- **Maintenance:** BNSS s. 144 + HMA s. 24 (conditional) + HMA s. 25 (future / decree-stage) + PWDVA s. 20
- **Custody:** HMA s. 26 + Guardians and Wards Act 1890 + HMGA 1956 s. 6 + welfare-of-the-child principle
- **Stridhan:** HMA s. 27 + BNS s. 316 — ₹5 lakh gold + ₹2 lakh cash, return in specie or ₹7 lakh value
- **Residence:** PWDVA s. 17 + s. 18 + s. 19 + s. 20
- **Divorce:** *(empty — not asked for)*

**The court the graph picks (never asked of the user):**

- **Family Court, Bengaluru** — HMA matters (maintenance ss. 24/25, custody s. 26, Stridhan s. 27)
- **Magistrate, Bengaluru** — BNSS s. 144 maintenance and PWDVA reliefs (ss. 17/18/19/20)
- **Criminal complaint route, parallel** — BNS s. 316

**The three missing facts the graph asks (and nothing else is demanded):**

1. The husband's income — as she knows it; **never demand salary slips she said she does not have**
2. The school-fee amount for the 8-year-old daughter
3. Where the husband actually lives now (for notice and jurisdiction)

**Maintenance amount:** **escalated, not invented.** Section selection is high-confidence on these facts; the amount is low-confidence until the husband's income is known. No figure is stated.

**What the old chatbot gave on this same case, for contrast:** only HMA s. 24 for maintenance, Rajnesh v. Neha for Stridhan, Ahuja for custody, HMA ss. 13/13B with no divorce asked, birth certificate under HMA, residence as "tenancy rights", and the user asked to pick the court. Overall 4/10; legal accuracy 3/10.

---

# 8. Guardrails / wrong-mapping warnings

> **⚠ READ THIS FIRST — WRONG MAPPINGS THE SYSTEM MUST NEVER MAKE**
>
> These are hard guardrails. Stage 2 enforces them on every answer. If a section or case fails one of these checks, it is **dropped with a reason** — it is never kept to make the answer look complete.
>
> - **Rajnesh v. Neha = maintenance ONLY.** Never cite it for Stridhan, custody, residence, or divorce. It governs *how much* maintenance — not whether gold is returned.
> - **Satish Chander Ahuja = shared household / residence ONLY.** Never cite it for custody. It says nothing about who gets the child.
> - **Residence is NOT "tenancy rights".** It is the **right to reside in the shared household** (PWDVA s. 17). The wrong label changes the legal basis.
> - **Never ask the user to pick the court.** The graph picks **Family Court, Bengaluru** (HMA) / **Magistrate** (BNSS s. 144, PWDVA). A layman is never asked to choose a forum.
> - **Never demand salary slips she said she does not have.** Ask the husband's income, the school-fee amount, and where the husband lives now. Income is tested by court-directed disclosure from the husband — never by demanding documents from the wife.
> - **HMA ss. 13 / 13B ONLY if divorce was asked.** No divorce asked → the divorce set is empty. Never infer a divorce request. Ambiguous → escalate.
> - **Birth certificate = Registration of Births and Deaths Act 1969. NOT the Hindu Marriage Act.**
> - **Maintenance quantum: escalate, never invent an amount.** No figure is stated without the husband's income. No double-counting: the same maintenance is never counted under both PWDVA s. 20 and BNSS s. 144 / HMA ss. 24–25 — amounts are set off against each other.
> - **Stridhan is two routes together.** HMA s. 27 (civil return) + BNS s. 316 (criminal breach of trust). A conviction alone does not order return; a civil claim alone drops the criminal lever. If one is dropped, say why.
> - **Custody is decided by welfare, not by status alone.** The father's natural-guardian status (HMGA s. 6, child above five) is acknowledged — and the welfare-of-the-child principle, which is paramount, decides.
> - **Low confidence or a missing material fact → escalate to a human lawyer / LLM review. Do not guess a section, an amount, a court, or a timeline.**

*Design note for the coordinator: render this box prominently on every page view — above the section cards and beside the walkthrough — not as a footnote. It is the clearest proof the system learned from the 4/10 retest.*

---

# 9. What it does NOT do

Be plain about the limits. A system that states its limits is more trustworthy than one that hides them.

- **No invented sections.** Only the verified list is used: BNSS s. 144; HMA ss. 24, 25, 26, 27; PWDVA ss. 17, 18, 19, 20; Guardians and Wards Act 1890; HMGA 1956 s. 6; the welfare-of-the-child principle; BNS s. 316; HMA ss. 13/13B only if divorce is asked; Registration of Births and Deaths Act 1969 for birth certificates. Any BNS section other than s. 316, any CrPC / BNSS section other than s. 144, HMA ss. 13/13B as a default citation, and any maintenance amount are **unverified — do not use as fact**.
- **No invented maintenance amounts.** The amount is escalated until the husband's income is known. No figure, no percentage, no "typical" amount is stated.
- **No live legal advice claim.** This site explains a classification system and a worked example. It is not a lawyer, not a filing, and not a substitute for one. Filing an FIR under BNS s. 316 is a criminal step to take on legal advice.
- **No promised timelines.** Every duration in the staged timeline is an **estimate**, not a statutory deadline. No fixed date is promised for any stage.
- **No guessing on missing facts.** Was a demand for Stridhan return made? Is a matrimonial proceeding already pending (which gates HMA ss. 24/27)? Which s. 19 direction does she prefer? Where does the husband live? If a material fact is unknown, the system asks once, then escalates — it does not fill the gap with an assumption.
- **No "never fails" claim.** The v1 test report is honest about what passed and what is still open. The v2 lanes must report an honest pass rate and every failure with a fix. This site must carry that same honesty: the old system scored 4/10, and the new system is built to be checked, not believed.
- **No precedent beyond what was verified.** Lane 3's Stridhan precedents (Pratibha Rani v. Suraj Kumar, 1985; Rashmi Kumar v. Mahesh Kumar Bhada, 1997) are the correct issue but were **not retest-verified** — check them against the judgment text before citing them in a live answer. They are not presented as verified on this site.

---

# 10. Footer / sources and status

- **Model:** Laya — Convai Innovations System One decision model, 421M ModernBERT-large, Apache-2.0. **NOT LLaMA.** Typed choice / score / `noul` questions, one forward pass, no free-text generation for section selection.
- **Checkpoint:** 808 MB English checkpoint at `~/workspace/models/laya-english` (`model.safetensors`, 804 MB). Official repo weights failed 403; PIXMELT snapshot used.
- **Graph v1:** `laya-crpc-bns-section-decision-tree.json` — 29 unique sections (13 statutory / principle + 16 procedure), 38 nodes, 66 edges, 0 dangling endpoints. Valid JSON.
- **Evidence:** Fresh English retest, 2026-11-26 — overall 4/10, legal accuracy 3/10, completeness 3/10, reasoning 2/10. Test report: `laya-graph/test-report.md`.
- **Verified sections only.** Full list in §5–§6 above and in `SHARED_BRIEF_V2.md`. Anything else is in `unverified_excluded`.
- **Status:** v2 content (this file) — Stage 1 phrasebook, Stage 2 recheck rules, adversarial tests, and this website content are the v2 lanes. The coordinator owns the merged v2 file and builds the web artifact from this content.

---

## Content checklist for the coordinator (build spec)

- [ ] Hero carries "Laya is NOT LLaMA" and the one-line promise.
- [ ] "What Laya is" states: Convai Innovations System One, 421M ModernBERT-large, Apache-2.0, choice / score / `noul`, one forward pass, 808 MB checkpoint at `~/workspace/models/laya-english`, `model.safetensors` 804 MB, official weights failed 403, PIXMELT snapshot used.
- [ ] "Why the old chatbot failed" states 4/10 overall and 3/10 legal accuracy, and names all nine mistakes in §3.
- [ ] Pipeline section renders Stage 1 → Stage 2 as a diagram, with the six exact layman examples: "my husband is not giving me money", "he took my gold" / "he took my gold and cash and won't return it", "they are throwing me out" / "they are throwing me out of the house", "who will get my daughter", "I need money for my child", "he beats me / threatens me".
- [ ] Section graph shows the four sets (maintenance BNSS 144 + HMA 24/25 + PWDVA 20; custody HMA 26 + GWA 1890 + HMGA s. 6 + welfare principle; Stridhan HMA 27 + BNS 316; residence PWDVA 17 + 18 + 19 + 20) and the empty divorce set.
- [ ] Every section card uses only verified section numbers; no new BNS / CrPC section is introduced.
- [ ] Walkthrough covers the test case step by step (Stage 1 → Stage 2 → final sets → court picked by the graph → three missing facts → amount escalated).
- [ ] Guardrails box is prominent on the page, with all eleven warnings in §8.
- [ ] "What it does NOT do" states: no invented sections, no invented amounts, no live legal advice claim, no promised timelines, no guessing, no "never fails" claim.
- [ ] No artifact, web page, or app is built from this lane file — the coordinator builds the web artifact.
