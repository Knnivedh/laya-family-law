# v6 Lane 4 — Prose renderer design + latency diagnosis

**Lane:** 4 (prose renderer design + latency) of the v6 deep-dive.
**Status:** DESIGN ONLY. No notebook, builder, graph, ground truth, or results
file was modified. All counts below were derived by reading the v5 notebook
Cell 7 (`live-laya-colab-test-v5-precision.ipynb`) and the filed v4r live JSON
— no browser, no Colab, no model call.
**Inputs read:**
- `laya-10-10-gate-definition.md` (§5 forbidden list, §1 G12/G14, §2 caps)
- `prose-renderer-design.md` (existing v8 design — built on and corrected here, §4)
- `latency-analysis.md` (v3 Cell 7 analysis — verified/corrected here, §6.1)
- `v5-precision-report.md` (predicted v5 kept sets = GT sets, 16/16)
- `~/workspace/browser_downloads/sess-2184034649/browser-download-20261126T185447.300061282Z-0-live-laya-colab-results-v4r-residence-only.json`
  (v4r live run, 2026-11-27 ~00:19 IST)

## 0. Verdicts up front

1. **Prose renderer: template-based assembler, NOT free generation.** Reasons in
   §1.1. Free generation cannot be made to score Fp = 0 by construction; it can
   only be checked after the fact, and a single slip caps the run at ≤ 5.0.
2. **The existing `prose-renderer-design.md` is sound in structure but has
   three real bugs and one gap** (§4): its maintenance template asserts a child
   and school fees on questions with no child (H8/H9/H11); its residence
   paragraph asserts a residence right when only a protection order
   (`pwdva-18`) is kept (H5); its divorce paragraph is in the wrong tense when
   a proceeding is already pending (H14); and it has no answer for the
   no-escalation questions (H2/H4, and H7/H15 under v5). All four are fixed in
   §2–§3 below. The existing §8 self-checker is adopted verbatim, with two
   additions (§5.1).
3. **Latency: v4r Cell 7 took 921.6 s (mean 57.6 s, max 133.32 s, min 36.31 s)** —
   worse than the 897.6 s quoted in `latency-analysis.md`, because that figure
   was the **v3** run, not v4r (§6.1). The cause is sheer inference count:
   **105 `agent.predict` calls / 728 inferences per 16-question run**
   (682 `noul` keys + 46 `choice` keys), at a measured **~1.27 s per
   inference** on Colab CPU. Nothing else is wrong; there is no single slow
   call to fix.
4. **All verified score-preserving trims together cut the run to ~584 s
   (mean ~36.5 s, max ~61 s) on CPU — still a G14 failure by 2.4×.**
   G14 (mean ≤ 15 s, max ≤ 30 s, run ≤ 240 s) is **not achievable on Colab CPU
   with this architecture**, even with every verified trim. The only route that
   keeps the recall mechanism intact is a **recorded GPU runtime** (T4):
   trimmed, ~92–184 s/run at the planning figure of 0.2–0.4 s/inference
   (§6.5). That figure is an unverified planning estimate and must be measured.
5. **"Fraction of a second" classification is not achievable with this model
   on CPU, and not achievable with this architecture at all.** The cheapest
   observed question (H9: 4 calls, 33 inferences) took 36.31 s; the lowest
   observed per-inference cost is 1.10 s and the lowest per-call cost 7.3 s.
   Sub-second needs a single-forward-pass multi-label head + GPU/quantised
   serving + a different call path — a model rebuild, out of scope for v6,
   with real recall risk (§6.6).
6. **Prose generation lives in a new Cell 9, after Cell 8** (§7). It needs zero
   model calls (~milliseconds/question), so it cannot affect latency or any
   classification metric. It can also be **rehearsed offline** against the
   filed v4r/v5 JSONs before any live run, since its only inputs are already in
   `RESULTS`.

---

## 1. Prose renderer — recommendation

### 1.1 Template-based assembler (recommended) vs free generation

| | Template assembler (recommended) | Free generation (rejected) |
|---|---|---|
| Forbidden mappings | Prevented **by construction**: a mapping can only appear if a fixed template string contains it, and the fixed strings are audited once (§3) | Prevented only by post-hoc checking; every run is a fresh lottery over 9 mappings, each slip caps the run at ≤ 5.0 |
| Inputs | `kept_ids`, `dropped`, `court_live`, `court_source`, `escalations_typed`, `facts` — never the question text, never a model | Would need the question text + kept sections as a prompt — the exact surface where the 2026-11-26 retest errors came from (wrong precedent, wrong Act, invented amounts) |
| Latency | 0 model calls, milliseconds/question | ≥ 1 generation call/question on CPU (~10 s+ each at current per-call cost) — would by itself break G14 |
| Determinism / audit | Same inputs → same prose, byte for byte; a rater can audit the template file once and trust every run | Different prose every run; the rater must re-audit every answer, every run |
| Failure mode | If classification is wrong, prose is a fluent statement of the wrong law (bounded by classification quality — stated honestly, §1.3) | Same failure, plus invented law on top of wrong law |
| Cost of a bug | One template fix, re-verify once | Unbounded; no template to fix |

**Decision: deterministic template assembler.** One template per issue, with
conditional clauses keyed to kept section ids and to Cell 6 facts. Slots are
filled **only** from kept sections + facts + the kept court — never from
fired-but-dropped issues, never from candidates, never from the question text.
The renderer takes **no question-text input at all**: this alone prevents any
amount in the question ("forty thousand", "five lakh" in K0) from leaking into
prose, and prevents any paraphrase of the question from inventing law.

### 1.2 Renderer inputs (exact)

| Input | Source | Notes |
|---|---|---|
| `kept_ids` | Cell 7 `RESULTS[i]` | **Only** section input. Dropped sections are never passed. |
| `dropped` (ids) | Cell 7 `RESULTS[i]` | Checker input only (item 7), never rendered. |
| `court_live`, `court_source` | Cell 7 `RESULTS[i]` | Court line (§2.5). `fallback-escalate` → no court line. |
| `escalations_typed` (kinds only) | Cell 7 `RESULTS[i]` | Kinds only; the Cell 7 verbatim texts are internal wording and must never reach the user (existing design §6 — adopted). |
| `facts` | Cell 6 `TEST_SET[i]` | `divorce_asked`, `proceeding_pending`, `demand_made`, `violence`, `residence_claim`, `money_fact`, `gold_fact`, **plus three new annotation-only fields (§1.4)**. |
| `in_scope` | Cell 7 `RESULTS[i]` | Out-of-scope branch (§2.7). |

### 1.3 What the renderer does NOT do (honest limits — carried from existing design §10)

- It does not fix classification. Wrong `kept_ids` → fluent, well-formed
  prose stating the wrong law. Prose quality is bounded by classification
  quality; the self-check (§5.1 / existing design §8) catches forbidden *mappings*, not
  wrong-but-allowed sections.
- It does no cross-issue synthesis. Multi-issue answers are the issue
  paragraphs joined in fixed order. Synthesis is where a generator invents law.
- It answers one question per classification. No multi-turn prose.
- The self-check is string matching, not legal judgement. Its job is to catch
  builder mistakes in fixed strings, not to judge free text — because there is
  no free text.

### 1.4 New Cell 6 fact fields required (annotation-only — GT untouched)

The existing design's templates state facts the Cell 6 facts cannot support
(§4, bugs 1–2). Three boolean fields are added to Cell 6, in the same
frozen-annotation style as `money_fact`/`gold_fact` (v5 Fix 1). They are
annotations of the question text, not GT changes; they cannot change any
classification score (nothing in Cell 7 reads them except the renderer, which
lives in Cell 9). Values for the current 16, read from the Cell 6 question
texts:

| Field | Meaning | True on (current 16) |
|---|---|---|
| `child_fact` | The question mentions a child of the user (son/daughter/child) | K0, H1, H2, H5, H6, H7, H10, H13, H14 |
| `school_fees_fact` | The question mentions school fees | H13, H14 |
| `stridhan_sold` | The question states the Stridhan was sold (not merely held) | H15 only |

All other questions: False on all three. (H7's child is real — "my daughter's
birth certificate" — but no maintenance paragraph renders for H7, so
`child_fact` is inert there; it is recorded for completeness, not used.)
**Fresh/Kannada sets:** the same three fields must be annotated by the
independent rater who freezes those sets' GT — never by the tuning lane, never
inferred from model output.

---

## 2. Templates (exact text — the v6 builder copies these verbatim)

### 2.1 Assembly order (fixed, deterministic)

1. Intro line (§2.2) — only if `kept_ids` non-empty and `in_scope` true.
2. Issue paragraphs (§2.3–§2.4), in fixed order: maintenance, custody,
   Stridhan, residence, divorce, birth certificate. A paragraph renders only
   if at least one of its section ids is in `kept_ids`, subject to the
   paragraph's own base-sentence condition (§2.3).
3. Court line (§2.5) — from `court_live` / `court_source`.
4. Escalation lines (§2.6) — one per typed escalation kind present.
5. Closing line (§2.2) — on every in-scope answer.
6. Out-of-scope paragraph (§2.7) instead of 1–5 when `kept_ids` is empty and
   `in_scope` is false.
7. Kept empty but in scope: no issue paragraphs, no court line; escalation
   line (court kind) + closing line only.

Paragraphs joined with a blank line. No other text is ever added. No template
contains a question mark, a precedent/case name, a currency figure, the phrase
"salary slips" / "pay slips", or the phrase "tenancy rights" / "tenant rights".

### 2.2 Intro and closing lines (unchanged from existing design §2 — adopted verbatim)

**Intro (in-scope, non-empty kept):**

> Based on what you have said, the following applies to your question. This is
> general information, not legal advice, and a lawyer or the court will look
> at your full facts before deciding anything.

**Closing (every in-scope answer):**

> This answer is general information based only on the sections identified
> for your question. It is not legal advice for your full situation.

### 2.3 Issue paragraphs (full template text)

Conditional clauses are included only when their section id is in `kept_ids`
and their fact condition holds. Section ids that are not legal citations
(e.g. `welfare-principle`) render as plain sentences, never as a cited section.

#### 2.3.1 Maintenance — `bnss-144`, `pwdva-20`, `hma-24`, `hma-25`

Base paragraph (renders if `bnss-144` or `pwdva-20` is kept):

> You can ask for monthly maintenance for yourself[IF `child_fact`: and for
> your child].
> [IF `bnss-144` kept:] The law allows a wife to claim maintenance from her
> husband under Section 144 of the Bharatiya Nagarik Suraksha Sanhita, 2023.
> [IF `pwdva-20` kept:] You can also claim monetary relief under Section 20
> of the Protection of Women from Domestic Violence Act, 2005.

Conditional additions, appended to the same paragraph:

> [IF `hma-24` kept:] Because your case under the Hindu Marriage Act, 1955 is
> already going on, you can also ask the Family Court for interim maintenance
> while that case is pending, under Section 24 of the Hindu Marriage Act, 1955.
> [IF `hma-25` kept:] After a decree is passed, permanent alimony can be asked
> for under Section 25 of the Hindu Marriage Act, 1955.

Quantum sentence, always appended to the maintenance paragraph (the
user-facing form of the quantum escalation — the amount is escalated, never
stated):

> The monthly amount cannot be fixed from the information given. It will
> depend on your husband's income and your needs[IF `school_fees_fact`: and
> your child's school fees], and it will be decided by the court. No amount
> is stated here because the amount is not decided by this system.

**Why the `child_fact` / `school_fees_fact` conditionals exist:** the existing
design's unconditional "for yourself and for your child" and "your child's
school fees" state false facts on H8, H9 and H11, none of which mentions a
child. See §4 bug 1.

#### 2.3.2 Custody — `gwa-1890`, `hmga-1956-s6`, `welfare-principle`, `hma-26`

> The question of who your child stays with will be decided keeping the
> welfare of the child first.
> [IF `gwa-1890` kept:] The Guardians and Wards Act, 1890 is the law that
> applies to guardianship.
> [IF `hmga-1956-s6` kept:] Section 6 of the Hindu Minority and Guardianship
> Act, 1956 is also relevant to guardianship of a Hindu child.
> [IF `hma-26` kept:] Because your case under the Hindu Marriage Act, 1955 is
> already going on, the Family Court can also pass orders about the child
> under Section 26 of the Hindu Marriage Act, 1955 while that case is pending.

#### 2.3.3 Stridhan — `hma-27`, `bns-316`

> The gold, cash, and gifts given to you at your marriage belong to you.
> [IF `stridhan_sold` is False:] You can ask for them back under Section 27
> of the Hindu Marriage Act, 1955.
> [IF `stridhan_sold` is True:] You can ask for their value back under
> Section 27 of the Hindu Marriage Act, 1955, because they have been sold.
> [IF `bns-316` kept:] Keeping back a wife's property can also be an offence
> under Section 316 of the Bharatiya Nyaya Sanhita, 2023.

**Review flag on the sold variant:** "ask for their value back" is the
practical remedy for sold Stridhan; it is proposed wording, not a verified
legal proposition. The coordinator should have it confirmed before the v6 live
run; if it is not confirmed, the fallback is the held-variant sentence for all
cases (which is merely imprecise on H15, not forbidden). Either way this is a
template decision, not a live-run decision.

#### 2.3.4 Residence — `pwdva-17`, `pwdva-18`, `pwdva-19`

> [IF `pwdva-17` or `pwdva-19` kept:] You have the right to stay in the shared
> household.
> [IF `pwdva-17` kept:] Under Section 17 of the Protection of Women from
> Domestic Violence Act, 2005, you have the right to reside in the shared
> household.
> [IF `pwdva-19` kept:] Under Section 19 of the Protection of Women from
> Domestic Violence Act, 2005, the court can pass a residence order about the
> shared household.
> [IF `pwdva-18` kept:] Under Section 18 of the Protection of Women from
> Domestic Violence Act, 2005, the court can pass a protection order stopping
> violence, threats, and harassment at home.

**Why the base sentence is conditional:** the existing design renders "You
have the right to stay in the shared household" whenever any of the three
sections is kept. H5 keeps `pwdva-18` only (protection order, no residence
section) — the old template would assert a residence right the kept sections
do not support. That is not one of the 9 frozen forbidden mappings, but it is
the same class of error (prose asserting law beyond the kept sections), and it
is adjacent to item 7. See §4 bug 2. Note: `pwdva-20` kept via a residence
route is a maintenance section; it renders in the maintenance paragraph
(§2.3.1), not here.

#### 2.3.5 Divorce — `hma-13` only

Included only if `hma-13` is in `kept_ids`:

> [IF `proceeding_pending` is False:] You have asked for a divorce. A divorce
> can be sought under Section 13 of the Hindu Marriage Act, 1955, and the
> Family Court will decide it on the facts and evidence in your case.
> [IF `proceeding_pending` is True:] Your divorce case is already going on.
> It will be decided under Section 13 of the Hindu Marriage Act, 1955, and
> the Family Court will decide it on the facts and evidence in your case.

**There is no template for `hma-13b`.** If `hma-13b` is in `kept_ids` (no
current test question should produce this), the renderer emits no divorce
paragraph and instead appends the escalation line from §2.6 (kind `court`,
human-review wording). A mutual-consent provision must never be explained
from a template that assumes a contested divorce.

#### 2.3.6 Birth certificate — `births-deaths-act-1969`

> You can get your child's birth certificate from the Registrar of Births and
> Deaths. Birth registration is done under the Registration of Births and
> Deaths Act, 1969. If the hospital did not give a certificate, you can apply
> to the Registrar with the hospital record or other proof of birth.

The Hindu Marriage Act is never mentioned in this paragraph. The Act named
here is the only Act the paragraph is allowed to name.

### 2.4 Section-id → paragraph map (the renderer's only dispatch table)

| Kept section id | Paragraph |
|---|---|
| `bnss-144`, `pwdva-20`, `hma-24`, `hma-25` | §2.3.1 maintenance |
| `gwa-1890`, `hmga-1956-s6`, `welfare-principle`, `hma-26` | §2.3.2 custody |
| `hma-27`, `bns-316` | §2.3.3 Stridhan |
| `pwdva-17`, `pwdva-18`, `pwdva-19` | §2.3.4 residence |
| `hma-13` | §2.3.5 divorce |
| `births-deaths-act-1969` | §2.3.6 birth certificate |
| `hma-13b`, or any section id not in this table | **no paragraph** — escalation line instead (fail-safe) |

Unknown section ids must never render a paragraph. If a future Stage 2
change keeps a new section id, the builder must add its template first; until
then the system escalates instead of inventing prose.

### 2.5 Court line

Built from Cell 7's `court_live` (list) and `court_source`. It is a statement,
never a question. Court names map to fixed fragments (`Family Court` → "the
Family Court"; `Magistrate` → "the Magistrate"; `Registrar` → "the Registrar
of Births and Deaths").

- One court: `You would approach the Family Court.`
- Two courts: `You would approach the Family Court and the Magistrate.`
  (Three courts: commas + final `and`.)
- `court_source == 'fallback-escalate'`, or `kept_ids` empty but in scope:
  **no court line at all**; the court-kind escalation line (§2.6) is used
  instead. The system never names a court it did not derive from kept
  sections, and never asks the user to choose.
- Out of scope: no court line at all (§2.7).

### 2.6 Escalation lines (renderer-owned, keyed by typed kind)

These are **not** the verbatim `escalations_typed` texts from Cell 7 — those
are internal system wording and must never reach the user. One line per kind
present, in the order quantum, court, demand, fact. Duplicates collapse to one.

| Kind | User-facing line |
|---|---|
| `quantum` | The monthly amount is not fixed here. It will be decided after your husband's income and your needs[IF `school_fees_fact`: and your child's school fees] are known. |
| `court` | The court cannot be named from the information given. This question needs to be looked at by a human adviser, who will say which court applies. |
| `demand` | Before going to court, make a written demand for the return of your property and keep a copy of it. |
| `fact` | Some facts are still needed: your husband's income, in an estimate or a range[IF `school_fees_fact`:, the school-fee amount][IF `residence_claim`:, and where your husband lives now]. Give whatever records you have. If a record is missing, say that it is missing. |

Notes:
- The `fact` line's school-fee and whereabouts clauses are conditional
  (§4 bug 1 — the existing design lists both unconditionally).
- The `fact` line never says "salary slips". **Required Cell 7 edit
  (carried from existing design §6):** the `fact`-kind escalation text in
  `stage2()` currently contains the phrase "never demand salary slips". The
  renderer never reuses that string, but the phrase must not survive anywhere
  in user-facing paths; the v6 builder must reword it to "Ask husband's
  income (estimate/range), school-fee amount, where husband lives now; never
  demand income proof you do not have". The self-check (existing design §8, item 9) flags
  any occurrence, so a missed rewording is caught.
- **No-escalation gap (open, §8):** under v5 predicted kept sets, H2 and H4
  have no typed escalation kind at all, and H7/H15 lose theirs (v5-precision
  §6). Their prose therefore ends after the court line + closing, with no
  "what next" sentence. This is honest but thin. A generic next-steps line is
  proposed in §8 as a coordinator decision — it is **not** adopted here,
  because adding user-facing text is a content decision, not a lane decision.

### 2.7 Out-of-scope prose (H12 shape)

When `kept_ids` is empty and `in_scope` is false:

> This question is outside the family-law matters this system covers. It does
> not say anything about your rights in this matter. A human adviser will need
> to look at it.

No intro, no issue paragraph, no court line, no closing line, no section
citation. `escalates` stays False, as in v3/v4r.

---

## 3. Worked renderings (v5 predicted kept sets — NOT live results)

Kept sets, courts and escalation kinds below are the **v5 predicted** values
from `v5-precision-report.md` §5 (predicted 16/16 exact). They are shown so the
templates can be read as finished answers; they are not measurements. If the
live v5/v6 run keeps a different set, the same templates render from whatever
is kept.

### 3.1 Maintenance-only — H1 (child, no school fees), H8, H9, H11 (no child)

**H1** — kept `{bnss-144, pwdva-20}`, court `[Magistrate]`, kinds
`{quantum, fact}`, `child_fact=True`, `school_fees_fact=False`:

> Based on what you have said, the following applies to your question. This is general information, not legal advice, and a lawyer or the court will look at your full facts before deciding anything.
>
> You can ask for monthly maintenance for yourself and for your child. The law allows a wife to claim maintenance from her husband under Section 144 of the Bharatiya Nagarik Suraksha Sanhita, 2023. You can also claim monetary relief under Section 20 of the Protection of Women from Domestic Violence Act, 2005. The monthly amount cannot be fixed from the information given. It will depend on your husband's income and your needs, and it will be decided by the court. No amount is stated here because the amount is not decided by this system.
>
> You would approach the Magistrate.
>
> The monthly amount is not fixed here. It will be decided after your husband's income and your needs are known.
>
> Some facts are still needed: your husband's income, in an estimate or a range. Give whatever records you have. If a record is missing, say that it is missing.
>
> This answer is general information based only on the sections identified for your question. It is not legal advice for your full situation.

**H8** — kept `{bnss-144, pwdva-20}`, court `[Magistrate]`, kinds
`{quantum, fact}`, `child_fact=False` (no child mentioned; salary slips
missing, income unknown). Same skeleton as H1 **minus** "and for your child"
and minus the school-fee clause. The words "salary slips" appear nowhere:
the fact line says only "Give whatever records you have. If a record is
missing, say that it is missing." — this is the item-9 test case, and it passes
by construction.

**H9** — kept `{bnss-144, pwdva-20}`, court `[Magistrate]`, kinds
`{quantum, fact}`, `child_fact=False`. Same as H8. The question asks "How much
money can I get every month" — the answer states no amount and escalates the
quantum instead (item 8 passes by construction).

**H11** — kept `{bnss-144, pwdva-20}`, court `[Magistrate]`, kinds
`{quantum, fact}`, `child_fact=False`, `proceeding_pending=False`. Same as
H8/H9. Note: no `hma-24` clause renders (no proceeding pending), so no interim
maintenance sentence appears — correct, because H11 states no case has been
filed.

### 3.2 Stridhan-only — H3 (demand not made) and H15 (sold)

**H3** — kept `{hma-27, bns-316}`, court `[Family Court, Magistrate]`, kinds
`{demand}`, `stridhan_sold=False`:

> Based on what you have said, the following applies to your question. This is general information, not legal advice, and a lawyer or the court will look at your full facts before deciding anything.
>
> The gold, cash, and gifts given to you at your marriage belong to you. You can ask for them back under Section 27 of the Hindu Marriage Act, 1955. Keeping back a wife's property can also be an offence under Section 316 of the Bharatiya Nyaya Sanhita, 2023.
>
> You would approach the Family Court and the Magistrate.
>
> Before going to court, make a written demand for the return of your property and keep a copy of it.
>
> This answer is general information based only on the sections identified for your question. It is not legal advice for your full situation.

No precedent is cited anywhere (items 1–2 pass by construction — there is no
precedent allow-list at all; the renderer has no mechanism to cite a case).

**H15** — kept `{bns-316, hma-27}`, court `[Family Court, Magistrate]`,
`demand_made=True`, `stridhan_sold=True`. Same as H3 except the Stridhan
paragraph's second sentence becomes "You can ask for their value back under
Section 27 of the Hindu Marriage Act, 1955, because they have been sold."
and **no** demand line renders (demand already made). Under v5 this question
reads escalates False vs expected True — the open H15 expectation decision
(§8); the prose does not paper over it.

### 3.3 Custody-only — H2

Kept `{gwa-1890, hmga-1956-s6, welfare-principle}`, court `[Family Court]`,
no escalation kinds:

> Based on what you have said, the following applies to your question. This is general information, not legal advice, and a lawyer or the court will look at your full facts before deciding anything.
>
> The question of who your child stays with will be decided keeping the welfare of the child first. The Guardians and Wards Act, 1890 is the law that applies to guardianship. Section 6 of the Hindu Minority and Guardianship Act, 1956 is also relevant to guardianship of a Hindu child.
>
> You would approach the Family Court.
>
> This answer is general information based only on the sections identified for your question. It is not legal advice for your full situation.

Note the missing escalation section — the no-escalation gap (§2.6, §8). The
answer is correct and complete on the sections, but gives no next step.

### 3.4 Residence-only — H4

Kept `{pwdva-17, pwdva-18, pwdva-19}`, court `[Magistrate]`, no escalation kinds:

> Based on what you have said, the following applies to your question. This is general information, not legal advice, and a lawyer or the court will look at your full facts before deciding anything.
>
> You have the right to stay in the shared household. Under Section 17 of the Protection of Women from Domestic Violence Act, 2005, you have the right to reside in the shared household. Under Section 19 of the Protection of Women from Domestic Violence Act, 2005, the court can pass a residence order about the shared household. Under Section 18 of the Protection of Women from Domestic Violence Act, 2005, the court can pass a protection order stopping violence, threats, and harassment at home.
>
> You would approach the Magistrate.
>
> This answer is general information based only on the sections identified for your question. It is not legal advice for your full situation.

The words "tenancy rights" appear nowhere (item 4 passes by construction —
the string does not exist in any template). Same no-escalation gap as H2.

### 3.5 Birth-certificate-only — H7

Kept `{births-deaths-act-1969}`, court `[Registrar]`, no escalation kinds (v5):

> Based on what you have said, the following applies to your question. This is general information, not legal advice, and a lawyer or the court will look at your full facts before deciding anything.
>
> You can get your child's birth certificate from the Registrar of Births and Deaths. Birth registration is done under the Registration of Births and Deaths Act, 1969. If the hospital did not give a certificate, you can apply to the Registrar with the hospital record or other proof of birth.
>
> You would approach the Registrar of Births and Deaths.
>
> This answer is general information based only on the sections identified for your question. It is not legal advice for your full situation.

The Hindu Marriage Act is not mentioned anywhere in this answer (item 6
passes by construction). Note: in v4r H7 wrongly kept maintenance sections;
under v4r kept sets this template would have rendered a maintenance paragraph
too — correctly reflecting the (wrong) classification, which is the honest
behaviour: prose follows kept sections, it does not second-guess them.

### 3.6 Multi-issue — K0 (maintenance + custody + Stridhan + residence)

Kept `{bnss-144, pwdva-20, gwa-1890, hmga-1956-s6, welfare-principle, hma-27,
bns-316, pwdva-17, pwdva-18, pwdva-19}`, court `[Family Court, Magistrate]`,
kinds `{quantum, fact}`, `child_fact=True`, `school_fees_fact=False`,
`divorce_asked=False` (no divorce paragraph — correct: K0 does not ask for
divorce). Rendered in fixed order: intro → maintenance (with child clause,
without school-fee clause) → custody → Stridhan (held variant) → residence
(all three clauses; base sentence renders because `pwdva-17`/`pwdva-19` are
kept) → court line ("You would approach the Family Court and the
Magistrate.") → quantum line → fact line → closing. Ten sections, four
paragraphs, zero precedents, zero amounts, zero questions asked. The amounts
in K0's question text ("forty thousand", "five lakh", "two lakh") cannot
appear, because the renderer never receives the question text.

**H5 and H14 (divorce variants, for completeness):** H5 renders maintenance +
custody + residence (only the `pwdva-18` clause — base sentence correctly
absent) + divorce (asked variant, `proceeding_pending=False`). H14 renders
maintenance (with the `hma-24` interim clause) + custody (with the `hma-26`
clause, **without** the GWA sentence — v5 Fix 4 drops `gwa-1890` from H14's
kept set) + divorce (pending variant). H13 renders maintenance (school-fee
clause present, `school_fees_fact=True`) + residence (all three clauses).

---

## 4. Corrections to `prose-renderer-design.md` (existing v8 design)

Adopted as the base; the following are corrections, not restatements. The
builder should apply these on top of that document.

| # | Bug / gap in existing design | Evidence | Fix in this document |
|---|---|---|---|
| 1 | Maintenance template asserts a child and school fees unconditionally ("for yourself and for your child"; "your child's school fees"; fact line lists "the school-fee amount" and "where your husband lives now" for every question) | H8, H9, H11 mention no child; only H13/H14 mention school fees | `child_fact` + `school_fees_fact` conditionals (§1.4, §2.3.1, §2.6); fact line's whereabouts clause keyed to `residence_claim` |
| 2 | Residence paragraph's base sentence ("You have the right to stay in the shared household") renders whenever any of `pwdva-17/18/19` is kept | H5 keeps `pwdva-18` only — protection order, no residence right | Base sentence only if `pwdva-17` or `pwdva-19` kept (§2.3.4) |
| 3 | Divorce paragraph ("A divorce can be sought") is in the wrong tense when the case is already pending | H14: `proceeding_pending=True`, `divorce_asked=True` | Pending variant (§2.3.5), keyed to existing `proceeding_pending` fact — no new field needed |
| 4 | Stridhan template ("You can ask for them back") assumes the property is held, not sold | H15: gold sold | Sold variant (§2.3.3), keyed to new `stridhan_sold` fact; flagged for legal confirmation (§2.3.3) |
| 5 | Gap: no answer for questions with no typed escalation kind | v4r: H2, H4 have `escalations_typed=[]`; v5 predicted: H7, H15 also have none | Not fixed unilaterally — proposed generic line is a coordinator decision (§8) |
| 6 | (Minor) Checker item-9 second pattern flags obligation verbs + "income proof"; the §2.6 `fact` line says "Give whatever records you have" — passes, but only just | Re-checked against §2.6 wording | Keep the checker verbatim; add the `fact`-line wording to the checker's regression set (every template string must pass the §5.1 checks before a run ships) |

Everything else in the existing design is adopted unchanged: the
kept-only input rule, the no-precedent / no-amount / no-question-mark
invariants, the `hma-13b` fail-safe, the court-line rules, the out-of-scope
paragraph, and the §8 self-checker code (with the two additions in §5.1).

---

## 5. Forbidden-mapping prevention table (by construction)

For each of the 9 frozen mappings (gate §5): what prevents it in the
renderer itself (not in a post-hoc check), what the self-checker catches if
the builder breaks it, and what would have to go wrong for it to appear.

| # | Forbidden mapping | Prevented BY CONSTRUCTION because… | Self-checker tripwire (existing design §8 + §5.1) | It could only appear if… |
|---|---|---|---|---|
| 1 | Rajnesh v. Neha cited for Stridhan (or any precedent for the wrong issue) | The renderer has **no precedent mechanism at all**: no case-name slot, no citation table, no allow-list — the strings "Rajnesh", "Neha", "v." do not occur in any template | Any `[A-Z][a-z]+ v. [A-Z][a-z]+`, "Rajnesh", "AIR", "SCC" match → hit | A builder adds a precedent string to a template (caught by the checker + by template audit) |
| 2 | Satish Chander Ahuja cited for custody (or any precedent for the wrong issue) | Same as #1 — one mechanism covers both items; there is no per-issue citation to get wrong | Same patterns as #1 (item recorded as 1, rater re-attributes to 2 if the citation is the Satish one) | Same as #1 |
| 3 | HMA ss. 13/13B in prose when divorce was not asked (13B needs mutual consent) | "Section 13" occurs only in the divorce paragraph (§2.3.5), which renders only if `hma-13 ∈ kept_ids`; `hma-13` can only be kept when Stage 2's divorce gate opened it; there is **no 13B template at all** — `hma-13b` kept → escalation line, never a paragraph | `Section 13B?` in prose without `divorce_asked` or without `hma-13`/`hma-13b` kept → hit; `13B` without `hma-13b` kept → hit | Stage 2 keeps `hma-13` on a divorce-not-asked question (a classification error, visible in exact-match first — prose would faithfully reflect it) |
| 4 | Residence called "tenancy rights" (or any wrong legal label) | The strings "tenancy rights" / "tenant rights" do not occur anywhere in the template set; the residence paragraph names only the PWDVA sections | Regex `tenancy rights?\|tenant rights?` → hit | A builder writes the phrase into a template (caught by checker + audit) |
| 5 | User asked to pick the court instead of the system naming it | No template contains a `?` character; the court line (§2.5) is a statement built only from `court_live`; when the court is underivable, the court-kind escalation line names a human adviser instead of asking | Any `?` in prose → hit; pick-a-court phrasings → hit | A builder adds a question to a template (caught by the `?` check) |
| 6 | Birth certificate placed under HMA (or any wrong Act) | The birth-certificate paragraph (§2.3.6) names exactly one Act — the Registration of Births and Deaths Act, 1969 — and never mentions HMA; it renders only if `births-deaths-act-1969 ∈ kept_ids` | "birth certificate" within 80 chars of "Hindu Marriage Act" (either order) → hit; 1969 Act missing when the section is kept → hit | A builder edits the paragraph to name HMA (caught by checker + audit) |
| 7 | Any section in prose that Stage 2 dropped for the stated facts | The renderer's **only** section input is `kept_ids`; dropped ids are never passed to it, so a dropped section has no path into prose | Every section pattern cited in prose is extracted and set-compared against `kept_ids` and `dropped` → any cited-but-not-kept id is a hit | A template hard-codes a section instead of conditioning on `kept_ids` (caught by the cited-vs-kept check) |
| 8 | A maintenance amount stated as a number instead of escalated | No template contains a currency figure, a digit with a per-month unit, or an amount word; the quantum sentence and quantum escalation line both say the amount is not fixed here; the renderer receives no question text, so question amounts ("forty thousand", "five lakh") cannot leak in | `₹`/`Rs`/`rupees` + digits, digits + per-month, amount words ("forty thousand", "five lakh") → hit. Bare years (1969, 1890, 1956) and bare section numbers are deliberately **not** flagged | A builder writes a figure into a template (caught); or a future slot interpolates a number (forbidden by design — no numeric slots exist) |
| 9 | Salary slips demanded when the user said they do not have them | The strings "salary slips" / "pay slips" / "payslips" do not occur in any template; the fact line says "Give whatever records you have. If a record is missing, say that it is missing." — no document is demanded, and no obligation verb is paired with income proof | `salary slips?\|pay slips?\|payslips?` → hit; obligation verb + income-proof pairing → hit | A builder writes the phrase into a template, or Cell 7's `fact` escalation text leaks into prose (renderer uses kinds only, so it cannot — but the Cell 7 rewording in §2.6 is still required so the phrase survives nowhere in user-facing paths) |

**Expected Fp on every run: 0, by construction.** If a live run ever reports
Fp ≥ 1, that is a renderer/template bug, not a tuning signal: fix the template
or the dispatch table, do not tune thresholds to fix it. A single Fp ≥ 1 caps
the run at ≤ 5.0 under the frozen formula.

### 5.1 Two additions to the self-checker (beyond existing design §8)

The existing §8 checker is adopted verbatim, plus these two pure-string
checks (prose + `kept_ids` + `facts` only, no model). They exist to catch the
§4 bugs 1–2 if a future template edit reintroduces them; neither maps to a
frozen Fp item, so a hit here is recorded as `prose_quality_flag` (not Fp)
and blocks the run from shipping until fixed — it is a builder tripwire, not
a gate metric.

```python
# Addition A — residence-right sentence without a residence section (catches §4 bug 2).
if 'right to stay in the shared household' in prose and not (kept & {'pwdva-17', 'pwdva-19'}):
    flags.append({'check': 'residence-base-without-section',
                  'detail': 'residence-right sentence present but neither pwdva-17 nor pwdva-19 kept'})
# Addition B — child / school-fee sentence without the fact (catches §4 bug 1).
if not facts.get('child_fact') and re.search(r'\byour child\b', prose):
    flags.append({'check': 'child-without-fact',
                  'detail': '"your child" in prose but child_fact is False'})
if not facts.get('school_fees_fact') and re.search(r'school fee', prose):
    flags.append({'check': 'school-fees-without-fact',
                  'detail': '"school fees" in prose but school_fees_fact is False'})
```

Both must pass on every template string before a run ships (builder
regression set, §8.3 step 5), and on every live-rendered answer in Cell 9.

---

## 6. Prose scoring — independent-rater protocol (G12)

The gate (§5) requires prose to be "generated and scored by an independent
rater against this list". The notebook self-check (existing design §8 + §5.1) is an automated
tripwire; it does not replace the rater. Both must agree at 0; if they
disagree, **the rater is right and the checker gains a pattern**.

### 6.1 Who rates

- **Rater:** one person who is **not** the tuning lane and **not** the prose
  author (Lane 4). Ideally the same rater who froze the set's GT (they already
  hold the facts), or a second rater briefed from the gate §5 list only.
- **Kannada set:** the rater must be Kannada-fluent; a non-fluent rater may
  not score Kannada prose.
- **Blinding:** the rater scores from (question text, generated prose,
  `kept_ids`, `facts`, GT ids) **without** seeing the self-checker's output.
  The checker result is revealed only at reconciliation, so the rater cannot
  be anchored by it.
- **Second rater (sample):** all questions with Fp > 0 (by either the rater or
  the checker) **plus a 25% random sample** of the remaining questions are
  double-rated by a second independent rater. Inter-rater agreement is
  reported (agree/disagree per question). A disagreement is resolved by
  discussion with the gate §5 list as the arbiter; the agreed verdict is
  recorded, with the disagreement noted.

### 6.2 What counts as a hit

- A hit is **one forbidden mapping in one question**: the rater quotes the
  exact offending sentence/span from the prose, names the item number (1–9),
  and writes one line saying why it matches the gate definition.
- **Fp (the gate metric)** = number of questions with ≥ 1 hit. Total
  instances across the run are also recorded (a question with two hits counts
  Fp = 1, instances = 2).
- **Borderline rule:** if a sentence is arguably wrong law but matches no
  item 1–9, it is **not** an Fp hit. It is recorded separately as a
  `prose_quality_note` (free text) for the coordinator — it must not be
  shoehorned into an item to inflate or deflate Fp. The 9-item list is frozen.
- **Wrong-but-allowed sections are not Fp.** If prose correctly renders a
  wrongly-kept section (e.g. v4r H7's maintenance paragraph), that is a
  classification error, already punished by exact match / precision — it is
  not double-counted as prose-forbidden. The rater must not use Fp to punish
  classification.
- **Out-of-scope prose (H12 shape)** is scored the same way: any section
  citation, court name, or amount in it is a hit under items 7/5/8 as
  applicable (the template makes this impossible by construction, but the
  rater still checks).

### 6.3 Per-question record format (what the notebook must emit + what the rater adds)

Notebook-emitted fields per question (Cell 9, §7.2):

| Field | Type | Content |
|---|---|---|
| `prose` | str | Full rendered answer (empty string only if `in_scope` is false and no out-of-scope paragraph rendered — never empty otherwise) |
| `prose_citations` | list[str] | Section ids extracted from `prose` by the §5.1 checker (empty for H12) |
| `prose_court_named` | list[str] | Court names appearing in `prose` (from `court_live`; empty if no court line) |
| `prose_amounts_stated` | list[str] | Matches of the item-8 patterns in `prose` (expected `[]` always) |
| `prose_forbidden_hits` | list[{item, detail}] | Self-checker hits (existing design §8 + §5.1 additions) |
| `prose_forbidden` | 0/1 | 1 if `prose_forbidden_hits` non-empty |
| `prose_render_ms` | float | Renderer wall time (expected < 5 ms) |
| `prose_template_version` | str | Template-set version string, e.g. `v6-lane4-2026-11-27` |
| `prose_facts_used` | dict | The fact values the conditionals read (`child_fact`, `school_fees_fact`, `stridhan_sold`, `proceeding_pending`, `divorce_asked`, `demand_made`) — so a rater can verify each conditional fired correctly |

Rater-added fields per question (filed with the run, in the rater record JSON):

| Field | Type | Content |
|---|---|---|
| `rater_id` | str | Rater identifier (not a name if the rater prefers an id) |
| `rater_date` | str | Date scored (IST) |
| `rater_fp` | 0/1 | Rater's verdict: 1 if ≥ 1 hit |
| `rater_hits` | list[{item, quote, reason}] | One entry per hit, quoting the exact offending span |
| `rater_prose_quality_notes` | list[str] | Borderline / wrong-but-allowed observations (not Fp) |
| `second_rater_id` / `second_rater_fp` | str / 0/1 | Only for double-rated questions |
| `reconciled_fp` | 0/1 | Final verdict after reconciliation (this is the Fp that enters the rating) |

Aggregate fields per run: `Fp` (sum of `reconciled_fp`), `Fp_rater`
(sum of `rater_fp`), `Fp_checker` (sum of `prose_forbidden`),
`prose_forbidden_total_instances`, `rater_checker_agreement` (questions where
rater and checker agree / 16), §2 rating (formula + caps, computed in Cell 9).

### 6.4 When prose is scored

- After every live run, before the rating is published. Prose scoring is part
  of the run record (gate §4 step 10), not an afterthought.
- **Offline rehearsal:** Cell 9's renderer + checker can be run offline
  against any filed results JSON (v4r, v5) with no model call. The rater
  protocol can be rehearsed on the v4r prose the same way. Rehearsal does not
  count as a live measurement for the gate — but it must happen before the
  live v6 run, so the live run is not the first time prose is ever generated.

---

## 7. Latency

### 7.1 Verification / corrections to `latency-analysis.md`

The prior analysis was done on the **v3** run. Checked against the filed
**v4r** JSON, three corrections and two confirmations:

| Prior claim | Check against v4r JSON | Verdict |
|---|---|---|
| Cell 7 took 897.6 s, mean 56.1 s, max 123 s (v3) | v4r JSON `latency_s`: **total 921.6 s, mean 57.6 s, max 133.32 s (K0), min 36.31 s** | **Corrected.** Latency got slightly worse from v3 to v4r (+24 s), not better. All v4r figures in this document supersede the v3 figures. |
| 682 `noul` keys/run; per-key ≈ 1.32 s | v4r clause counts reproduce 682 exactly (33 clauses total, C = 1–5 per question); 921.6 / 682 = **1.35 s per `noul` key**; 921.6 / 728 total inferences = **1.27 s per inference** | Confirmed, with the v4r unit cost. |
| §4.3 skip-aux-if-fired saves ~64–96 keys/run | Offline simulation on v4r JSON (recompute firing with aux restricted to issues not firing pre-aux): **106 of 192 aux keys skippable, firing unchanged on all 16** (see §7.3) | **Corrected upward.** The estimate was conservative; verified saving is 106 keys. Caveat: the simulation compares pre-gate firing (see §7.3 note). |
| §4.4 restrict `in_scope`/`divorce_pending` to full question saves 66 keys; "adopt only if no change on all 16" | Verified: `clause_max > raw` for `in_scope` on H2/H4/H7/H12 and for `divorce_pending` on K0/H1/H3/H4/H7 — but **no boolean changes on any question** at thresholds 0.50 / 0.12 (H4 pending full 0.1216 vs threshold 0.12 is a knife-edge margin, but it is the full score itself, not created by this change) | **Verified adoptable on the 16**, with the fresh-set risk noted in §7.3. |
| §4.1 (skip clause pass when C == 1) saves 40 keys; §4.2 (drop R0) saves 49 keys; §4.6 (dead sub-choices) saves ~10–25 inferences | C == 1 on H8/H9/H11/H13 (40 keys) — confirmed. R0: 16 full + 33 clause = 49 keys — confirmed. Dead sub-choice keys counted exactly from v4r JSON: custody 5 + stridhan 10 = **15 keys** (10 predict calls) — confirmed, at the low end of the estimate. | Confirmed. |
| Regression / per-call vs per-key decomposition | Least-squares on v4r: latency ≈ −27.5 + 3.37·calls + 1.48·keys, max residual 14.0 s; calls-only fit max residual 20.6 s; keys-only fit max residual 14.1 s. Identical-count questions differ by 5 s (H8 41.26 s vs H9 36.31 s, both 4 calls / 33 inferences). | **Neither calls-only nor keys-only explains latency well.** Per-question wall time is noisy (body length, Colab CPU variance). All estimates below use the measured 1.27 s/inference as a planning unit with ±15% uncertainty; do not quote a per-call figure as precise. |

### 7.2 Exact `predict()` count — v5 notebook Cell 7 (read-only)

Cell 7 has **one** `agent.predict` call site (`_ask`), invoked from four
places per question. v5 adds **zero** model calls over v4r (both notebooks have
the same 4 call sites; v5's changes are deterministic vetoes after scoring).

| Call site | Payload keys | Calls / question | Keys / run (16 q) |
|---|---|---|---|
| Full-question pass | 10 `noul` (7 ISSUES + R1 + `divorce_pending` + `in_scope`) | 1 | 160 |
| Clause-split passes | 10 `noul` per clause | C (clauses; mean 2.06, range 1–5) | 330 (33 clauses) |
| Aux prompts | 12 `noul` (maintenance 6, residence 3, custody 2, `divorce_pending` 1) | 1 | 192 |
| Sub-choices | 1–2 `choice` per fired issue, one call per fired issue | F (fired issues; v4r mean 2.5, range 1–5) | 46 `choice` keys in 40 calls (v4r) |
| **Total** | | **2 + C + F predict calls** | **682 `noul` + 46 `choice` = 728 inferences in 105 calls** |

Per-question extremes (v4r): K0 — 12 calls, 79 inferences, 133.32 s.
Cheapest: H9 — 4 calls, 33 inferences, 36.31 s. No question is below 32
`noul` keys: the full pass (10) + aux (12) + one clause pass (10) is the
floor of this architecture.

### 7.3 Why Cell 7 takes ~15 min

There is no slow call, no retry loop, and no single bottleneck to fix. The
arithmetic closes exactly: **728 inferences × ~1.27 s ≈ 922 s**. The cost
driver is the *number* of sequential CPU inferences, and every inference is
a full 421M-model forward pass through the `agent.predict` path. The three
passes re-score the same question three times (full → every clause → aux),
and nothing is shared or cached between them. Clause passes are the largest
group (330/682 `noul` keys, ~48%), but they are also the recall mechanism
that fixed the empty-5 failure — they cannot simply be deleted.

**Offline verifications performed for this lane (from the v4r JSON, no live run):**

- **§4.3 (skip aux for already-fired issues): VERIFIED.** Recomputing firing
  with aux restricted to issues not firing from `max(full, clause_max)`
  changes **no issue's firing on any of the 16**. Skippable aux keys: 106/192
  (K0 12, H14 12, H5/H6 10 each, H13 9, H1/H10/H11 7 each, H2/H7/H8/H9 6 each,
  H12 4, H3 3, H4 1, H15 0). Note the simulation compares **pre-gate**
  firing: the JSON's `fired_issues` is post-gate (residence fact gate,
  divorce pending signal), so the simulation was run as restricted-vs-
  unrestricted pre-gate firing, not against the JSON's fired list — the two
  agree on the comparison that matters (restricted == unrestricted on all 16).
  H5's custody (fires only via aux, final 0.2189) is automatically protected:
  custody does not fire pre-aux on H5, so its 2 aux keys are still scored.
  H15 skips 0 aux keys: its maintenance fires only via aux. **Interaction
  with v5 Fix 3 (single-issue guard):** the guard's lift uses aux values of
  candidate issues — candidates by definition do not fire pre-aux, so their
  aux is always scored. No interaction. **Cost:** `aux_max` / `aux_scores`
  become partial (only non-fired issues have aux values) and `fired_source`
  can no longer read `'aux'` for an already-fired issue. Both are diagnostics.
  **Must be re-verified on the v5 live JSON** before it ships in v6 (v5 vetoes
  do not change pre-aux firing, but the check is cheap and the gate's
  one-change rule wants it).
- **§4.4 (restrict `in_scope` / `divorce_pending` to full + aux): VERIFIED
  on the 16** (no boolean change, §7.1). Fresh-set risk: a clause-only
  pending signal on a long multi-issue fresh question would be lost — the
  pending threshold (0.12) is very low, so the full-question score usually
  clears it when the phrase is present, but "usually" is not a proof. Adopt
  with the risk recorded; if the coordinator prefers, adopt only the
  `in_scope` half (33 keys) and keep clause scoring for `divorce_pending`.
- **§4.1, §4.2, §4.6: VERIFIED zero-risk** (reasons as in `latency-analysis.md`
  §4.1/§4.2/§4.6; counts confirmed exactly above).

### 7.4 Optimisations (score-preserving first) with estimates

Planning unit: **1.27 s/inference** (v4r measured; range 1.10–1.69 s per
question). Estimates carry ±15% (see §7.1 regression note). "Risk to scores"
means risk to `fired_issues` / `kept_ids` / court / escalates.

| # | Optimisation | Keys saved / run | Est. time saved | Risk to scores |
|---|---|---|---|---|
| O1 | Skip clause pass when C == 1 (H8/H9/H11/H13) | 40 `noul` | ~51 s | **Zero.** Clause == full question; max-pool unchanged. |
| O2 | Drop residence R0 from all passes (keep behind a flag for comparison runs) | 45 `noul` net of O1 (16 full + 29 clause) | ~57 s | **Zero to scores.** R0 never fires. Loses the R0/R1 comparison diagnostic (already published). |
| O3 | Skip an issue's aux prompts once it already fires pre-aux | 106 `noul` | ~135 s | **Zero to firing — verified offline on v4r (§7.3).** Diagnostics only (`aux_max` partial, `fired_source` loses `'aux'` for pre-fired issues). Re-verify on v5 JSON. |
| O4 | Restrict `in_scope` + `divorce_pending` to full question (+ aux for pending) | 58 `noul` net of O1 (2 keys × 29 remaining clause passes) | ~74 s | **None on the 16 — verified (§7.3).** Low but non-zero fresh-set risk for clause-only pending signals. Diagnostic cost: clause_max lost for those two keys. |
| O5 | Drop dead sub-choice calls (custody, stridhan — answers never read by `stage2()`) | 12 `choice` keys in v5 (15 in v4r; v5 vetoes remove 3) / 10 calls | ~15 s | **Zero to scores** — or the graph lane fixes `stage2()` to read them; one of the two must happen. |
| O6 | Cache identical (body, prompt) pairs within a run | ~0 on this set | ~0 s | Zero. Insurance for fresh/Kannada sets only. |
| **Combined O1–O5** | **433 `noul` (from 682) + 28 `choice` keys (from 40 in v5) = 461 inferences (from 728)** | **~584 s/run, mean ~36.5 s, max ~61 s (K0)** | **Still fails G14 (see §7.5)** | |

Per-question post-trim estimates (CPU, 1.27 s/inference; v5 predicted fired sets):

| Q | Inferences (was → trimmed) | Est. s (was) |
|---|---|---|
| K0 | 79 → 48 | 60.8 (133.32) |
| H1 | 56 → 37 | 46.8 (68.83) |
| H2 | 44 → 30 | 38.0 (51.97) |
| H3 | 45 → 32 | 40.5 (55.22) |
| H4 | 45 → 37 | 46.8 (52.23) |
| H5 | 55 → 34 | 43.0 (65.87) |
| H6 | 47 → 29 | 36.7 (60.52) |
| H7 | 43 → 29 | 36.7 (48.90) |
| H8 | 33 → 16 | 20.3 (41.26) |
| H9 | 33 → 16 | 20.3 (36.31) |
| H10 | 46 → 30 | 38.0 (57.64) |
| H11 | 34 → 16 | 20.3 (42.15) |
| H12 | 43 → 32 | 40.5 (50.79) |
| H13 | 35 → 15 | 19.0 (44.12) |
| H14 | 45 → 25 | 31.7 (60.10) |
| H15 | 45 → 35 | 44.3 (52.42) |

Note H15 trims least (35 inferences): its maintenance fires only via aux, so
O3 saves nothing there, and its stridhan sub-choice is dead (O5) but its
maintenance sub-choice still runs. K0 remains the max at ~61 s — every trim
helps it, and it still fails the 30 s max.

### 7.5 G14 verdict — CPU cannot pass; GPU can (to be measured)

| Scenario | Mean / q | Max / q | Full run (excl. load) | G14? |
|---|---|---|---|---|
| v4r as-is (CPU) | 57.6 s | 133.3 s | 921.6 s | Fail |
| v6, O1–O5 trims (CPU) | ~36.5 s | ~61 s | ~584 s | **Fail** (2.4× over run budget) |
| v6, O1–O5 trims + T4 GPU at 0.3 s/inference (planning figure) | ~8.6 s | ~18 s | ~138 s | **Pass** (with margin) |
| v6, trims + GPU at 0.2 / 0.4 s/inference | ~5.8 / ~11.5 s | ~12 / ~24 s | ~92 / ~184 s | Pass / Pass |
| v6, **untrimmed** + GPU at 0.3 s/inference | ~13.8 s | ~25 s | ~218 s | Borderline pass |

**Recommended v6 target: mean ≤ 12 s/question, max ≤ 25 s, full run
≤ 200 s excl. load, on a recorded GPU runtime, with O1–O5 applied.** That
passes G14 with margin and keeps classification semantics intact. Two
conditions: (a) the 0.2–0.4 s/inference GPU figure is a **planning estimate
from `latency-analysis.md` §5, not a measurement** — the first GPU run must
report per-inference cost by group, and if it comes in above ~0.5 s the
target fails; (b) the run log must record the runtime (GPU type) alongside
the per-question figures — CPU and GPU numbers must never be compared as if
they were the same thing. Model load on GPU is expected to stay ≤ 60 s but
must be reported, not assumed.

**Not recommended:** restructuring scoring to ~10–12 inferences/question on
CPU (full pass only + targeted rescue) as the v6 path. It is the only
CPU-only route that could approach G14, but it is semantics-changing: it
re-derives the empty-5 fix under a latency budget, and the clause/aux rescue
it would cut is exactly what delivers the current recall of 1.000. It needs
its own offline simulation from the filed v4r JSON plus a live A/B against v5
exact/F1 before it can be trusted. Keep it as a v7 fallback, not a v6 plan.
Amending G14 is the coordinator's decision, not this lane's — the gate is
frozen, and v4r already fails it, so no run may be presented as gate-passing
on a silent reading.

### 7.6 The "fraction of a second" aspiration — plain answer: not achievable with this model on CPU, and not with this architecture at all

- The cheapest observed question (H9) took **36.31 s** for 4 predict calls /
  33 inferences. The lowest observed per-inference cost is **1.10 s**; the
  lowest per-call cost is **7.3 s**. A single inference per question would
  still be ~1 s on CPU at the very best — and no single-inference question
  has ever been timed, so even that floor is inferred, not measured.
- The v5 pattern needs **32–79 inferences per question**. Sub-second per
  question at that count would need ~0.01–0.03 s per inference — roughly
  50× faster than the measured CPU cost.
- What sub-second would actually require, all three together: (1) a **single
  forward pass per question** — a multi-label classification head scoring all
  issues at once, instead of 32–79 separate `noul` judgements; (2) **GPU
  serving, or INT8-quantised ONNX on CPU**, to bring one forward pass under
  ~0.2 s; (3) **bypassing the `agent.predict` per-call overhead** (direct
  model call / batching), since the per-call floor alone is ~7 s on the
  current path.
- **Accuracy risk of that rebuild:** the per-prompt scores *are* the
  mechanism that delivers the current recall — clause-split and aux max-pool
  rescue the issues the full pass misses (H5 custody fires only via aux at
  0.2189; H7 maintenance fired only via clause at 0.1971). A single-pass
  model must learn those rescues implicitly. That means fine-tuning or
  distilling Laya into a multi-label classifier on the 16 + rater-approved
  paraphrases, then re-proving the full gate (current 16 + fresh 16 + Kannada
  8, twice). Expect recall regression risk; it is unmeasured until built.
  This is a model rebuild, out of scope for v6, and it must not be promised
  as a v6 deliverable.
- What **is** achievable in v6: ~9–12 s/question on GPU with the current
  architecture + O1–O5 (§7.5). That is ~5× faster than v4r and inside the
  gate. It is not a fraction of a second, and it must not be presented as one.
  The aspiration stays a separate stretch goal, as the gate document already
  records it.

### 7.7 Latency instrumentation required in v6 (no semantic change)

Cell 7 must log wall time **per `agent.predict` call**, not just per question
— otherwise the next latency analysis will be guessing again (as this one had
to be, from per-question totals). Log to `rec['predict_call_log']`, one entry
per `_ask` invocation:

```python
{'call_no': int, 'group': 'full' | 'clause' | 'aux' | 'sub_choice',
 'n_keys': int, 'body_chars': int, 'wall_s': float}
```

Cell 8 aggregates it into the run JSON: `predict_calls_total`,
`inferences_total`, `wall_by_group` (full/clause/aux/sub_choice seconds),
`mean_s_per_inference`, `mean_s_per_call`. The prose renderer (§2) adds
`prose_render_ms` per question (§5.3) — expected < 5 ms, reported to prove
prose costs nothing.

---

## 8. Where prose generation lives — v6 notebook cell plan

**Prose lives in a new Cell 9, after Cell 8 (scoring/saving).** Not in Cell 7
(classification must not depend on prose) and not in a separate stage file
(the run record must be one filed JSON + MD per run, gate §4 step 10).

### 8.1 Cell plan

| Cell | Change in v6 | Why |
|---|---|---|
| Cell 6 | Add `child_fact`, `school_fees_fact`, `stridhan_sold` to every `TEST_SET` entry (§1.4 values); fresh/Kannada sets annotated by the GT rater | Renderer conditionals; annotation-only, GT untouched, no classification effect |
| Cell 7 | Apply O1–O5 latency trims (§7.4); add per-call timing log (§7.7); reword the `fact`-kind escalation text to remove "salary slips" (§2.6) | Latency (the v6 classification change class); instrumentation; prose hygiene |
| Cell 7 | **No other change.** No threshold, prompt, graph, or GT change rides with the trims in the same run (gate §4 step 3: one change per cycle — the trims are one change class) | Attribution: if exact/F1 moves, the trims are the only candidate cause |
| Cell 8 | Carry `predict_call_log` + latency aggregates into the JSON/MD; add a comment that Fp is computed in Cell 9; no scoring-logic change | Latency reporting; Fp placeholder |
| **Cell 9 (new)** | Templates §2 verbatim + self-checker (existing design §8 code + the two additions in §5.1) + steps below | Prose + Fp + rating |

**Cell 9 steps:**
1. For each question, call `render_prose(rec, t)` (§2) → `prose`.
2. Call `prose_forbidden_check(prose, rec['kept_ids'], rec['dropped'],
   t['facts'])` → `hits` (checker code from existing design §8, plus the
   two additions in §5.1 of this document — record the additions in the
   builder's change log).
3. Attach to the record: `prose`, `prose_citations`, `prose_court_named`,
   `prose_amounts_stated`, `prose_forbidden_hits`, `prose_forbidden`
   (1 if hits else 0), `prose_render_ms`, `prose_template_version`,
   `prose_facts_used` (§5.3).
4. Compute `Fp = sum(rec['prose_forbidden'])` and
   `prose_forbidden_total_instances = sum(len(hits))`.
5. Compute the §2 rating (Cell 8 currently does **not** compute a rating —
   that gap is closed here): `Rating = 10 × [0.60·E + 0.15·Rm + 0.10·Pm +
   0.075·C + 0.075·S] − 0.5·Fb − 1.0·Fp`, clamped to [0, 10], rounded to
   1 decimal, then the §2 caps applied (Fp ≥ 1 caps at ≤ 5.0; the
   prose-not-measured ≤ 9.0 cap is lifted *only* by actually measuring Fp
   in this cell).
6. Re-open the saved results JSON/MD, add the prose fields, the Fp
   aggregates and the §2 rating, and rewrite both files. Cell 8's files are
   not final until Cell 9 has run; the run report must say so.

### 8.2 One-change-per-cycle question (for the coordinator)

Prose (Cell 9) is **measurement-only with respect to classification**: it
cannot change exact, precision, recall, court, escalates, or Fb, because it
reads only already-computed outputs and makes zero model calls. Including
Cell 9 in the same live run as the latency trims therefore does not confound
attribution of any classification change. Recommendation: **one v6 live run
carrying both** (trims + Cell 9). If the coordinator wants strict
one-change discipline, the fallback is two runs — trims first, prose second —
and prose can be rehearsed offline against the filed v5 JSON in the meantime
(§5.4), since it needs no live model.

### 8.3 Builder checklist (v6)

1. Cell 6: three new fact fields, values §1.4; assert they exist on every
   entry (fresh/Kannada sets too, annotated by the GT rater).
2. Cell 7: O1–O5 trims with a flag for O2 (`SCORE_R0 = False` default);
   per-call timing log; `stage2()` fact-text rewording.
3. Cell 9: templates §2 verbatim (including the §4 corrections — do **not**
   copy the existing design's unconditional child/school-fee sentences or its
   unconditional residence base sentence); checker with the §5.1 additions;
   rating computation with caps.
4. Cell 8: latency aggregates + Fp comment only.
5. Validate: `nbformat.validate` PASS; compile Cells 7–9 PASS; run the
   renderer + checker offline against the filed v4r JSON and confirm Fp = 0
   and every template string passes the checker (regression set); confirm
   `prose_render_ms` < 5 ms/question offline.
6. Nothing else. No threshold, prompt, graph, or GT change.

---

## 9. Open decisions (for the coordinator / parent — not decided here)

1. **No-escalation prose gap (§2.6, §4 #5):** H2/H4 (and H7/H15 under v5)
   have no typed escalation kind, so their prose has no "what next" line.
   Proposed generic line (coordinator decision only — not adopted here):
   "If you need help with the next steps, a human adviser can look at your
   full facts." It states no law, names no court, no amount, no document —
   it cannot trip any of the 9 items — but adding user-facing text is a
   content decision. Alternatively the parent may resolve the underlying
   escalate expectations (v5-precision §6: H7/H15) first, which changes which
   questions have kinds.
2. **Stridhan-sold wording (§2.3.3):** "ask for their value back" needs legal
   confirmation before the v6 live run; fallback is the held-variant sentence.
3. **O4 scope (§7.3):** adopt the full restriction (saves 58 keys) or only
   the `in_scope` half (saves 29 keys), keeping clause scoring for
   `divorce_pending` as insurance for clause-only pending signals on fresh
   questions.
4. **GPU runtime for the v6 live run (§7.5):** the gate's "live Colab run"
   wording and the v1 CPU baseline need a coordinator reading — a GPU run is
   still a live Colab run, but the runtime must be recorded and CPU/GPU
   numbers never compared silently. If GPU is not approved, the honest v6
   latency target is mean ~36 s (a documented G14 failure), and the 10/10
   claim cannot include G14.
5. **O5 alternative:** delete the custody/stridhan sub-choice calls, or fix
   `stage2()` to read them (graph lane's call). One of the two must happen;
   shipping calls whose answers are ignored is the worst of both worlds.
6. **Rater identity (§6.1):** who the independent prose rater is for the
   current 16, and the Kannada-fluent rater for the Kannada 8. Named before
   the v6 live run, not after.
7. **"Fraction of a second" (§7.6):** stays a stretch goal. If the user wants
   it pursued, it is a separate model-rebuild project (single-pass multi-label
   head + GPU/quantised serving), not a v6 notebook task.

---

## 10. Sources (all read, none modified)

- `laya-10-10-gate-definition.md` — frozen gate, §5 items 1–9, §1 G12/G14, §2
  formula + caps (Fp ≥ 1 caps ≤ 5.0; prose-not-measured caps ≤ 9.0).
- `prose-renderer-design.md` — existing v8 design; adopted as base, corrected
  in §4.
- `latency-analysis.md` — v3 analysis; verified/corrected against v4r in §7.1.
- `v5-precision-report.md` — v5 predicted kept sets (16/16), escalates 12/16
  prediction, H7/H15 open expectations.
- v4r live JSON (`sess-2184034649`, 2026-11-27 ~00:19 IST) — per-question
  `latency_s` (total 921.6 s), clause counts (33), fired issues, sub-choice
  keys (46), `stage1_raw` / `stage1_clause_max` / `aux_max` (used for the
  O3/O4 offline verifications).
- v5 notebook Cell 7 (`live-laya-colab-test-v5-precision.ipynb`, 704 lines) —
  4 `_ask` call sites, 10-key full payload, 10-key clause payload, 12-key aux
  payload, 1–2 `choice` keys per fired issue; v5 adds zero model calls over
  v4r. Cell 6 TEST_SET — question texts, GT ids, facts (incl. `money_fact` /
  `gold_fact`).
