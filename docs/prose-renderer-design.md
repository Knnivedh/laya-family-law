# Prose renderer design — Laya family-law system (v8 build)

**Status:** DESIGN ONLY. Nothing in this document modifies any notebook, builder,
graph, or results file. It is the specification the v8 notebook builder implements.
**Source of the forbidden list:** `laya-10-10-gate-definition.md` §5, items 1–9
(frozen). **Classification it renders from:** v3 Cell 7 outputs
(`kept_ids`, `dropped`, `court_live`, `court_source`, `escalations_typed`,
`facts`, `in_scope`).

## 0. Design principle

**Prose is generated from `kept_ids` only — never from fired issues, never from
candidates, never from the question text, never from a model.**

- Paragraph selection is keyed by **kept section id**. A section that Stage 2
  dropped cannot appear in prose, because the renderer never sees it: its only
  section input is `kept_ids`. That makes forbidden #7 (a dropped section in
  prose) impossible by construction, not by checking.
- The renderer is a **deterministic template assembler** (pure string
  substitution). It makes zero model calls, so it adds ~0 s to latency and
  cannot hallucinate a precedent, an amount, or a section.
- Every template below is written out in full. The v8 builder copies these
  strings verbatim; it does not paraphrase them.
- **Hard invariants of every template:**
  - No precedent / case name is cited anywhere (kills forbidden #1 and #2).
  - No maintenance amount, in figures or words, appears anywhere (kills #8).
  - The phrase "salary slips" (and "pay slips") never appears (kills #9).
  - The phrase "tenancy rights" (and "tenant rights") never appears (kills #4).
  - No template contains a question mark. Generated prose contains zero `?`
    characters, so it can never ask the user to pick a court (kills #5).
  - Birth certificate is always under the Registration of Births and Deaths
    Act, 1969, never under HMA (kills #6).
  - HMA ss. 13/13B appear only in the divorce paragraph, which is emitted
    only when `hma-13` / `hma-13b` is in `kept_ids` (kills #3).
  - There is **no template at all for `hma-13b`** (mutual consent). If
    `hma-13b` is ever kept, the renderer emits the escalation line instead of
    a divorce paragraph (§4 fail-safe). No test question states mutual
    consent, so this path should never fire on the current sets.

## 1. Assembly order (fixed, deterministic)

For each question, prose is assembled in this exact order:

1. Intro line (§2) — only if `kept_ids` is non-empty and `in_scope` is true.
2. Issue paragraphs (§3), in this fixed order: maintenance, custody,
   Stridhan, residence, divorce, birth certificate. A paragraph is included
   only if at least one of its section ids is in `kept_ids`.
3. Court line (§5) — from `court_live` / `court_source`.
4. Escalation lines (§6) — one per typed escalation kind present.
5. Closing line (§2) — on every in-scope answer.
6. Out-of-scope paragraph (§7) instead of 1–5 when `kept_ids` is empty and
   `in_scope` is false.
7. Kept empty but in scope: no issue paragraphs, no court line; escalation
   line (court kind) + closing line only.

Paragraphs are joined with a blank line. No other text is ever added.

## 2. Intro and closing lines

**Intro (in-scope, non-empty kept):**

> Based on what you have said, the following applies to your question. This is
> general information, not legal advice, and a lawyer or the court will look
> at your full facts before deciding anything.

**Closing (every in-scope answer):**

> This answer is general information based only on the sections identified
> for your question. It is not legal advice for your full situation.

## 3. Issue paragraphs (full template text)

Each paragraph is built from conditional clauses keyed to kept section ids.
A clause is included only when its section id is in `kept_ids`. Section ids
that are not legal citations (e.g. `welfare-principle`) render as plain
sentences, never as a cited section.

### 3.1 Maintenance — sections `bnss-144`, `pwdva-20`, `hma-24`, `hma-25`

Base paragraph (included if `bnss-144` or `pwdva-20` is kept):

> You can ask for monthly maintenance for yourself and for your child.
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

Quantum sentence, always appended to the maintenance paragraph (it is the
user-facing form of the quantum escalation — the amount is escalated, never
stated):

> The monthly amount cannot be fixed from the information given. It will
> depend on your husband's income, your needs, and your child's school fees,
> and it will be decided by the court. No amount is stated here because the
> amount is not decided by this system.

### 3.2 Custody — sections `gwa-1890`, `hmga-1956-s6`, `welfare-principle`, `hma-26`

> The question of who your child stays with will be decided keeping the
> welfare of the child first.
> [IF `gwa-1890` kept:] The Guardians and Wards Act, 1890 is the law that
> applies to guardianship.
> [IF `hmga-1956-s6` kept:] Section 6 of the Hindu Minority and Guardianship
> Act, 1956 is also relevant to guardianship of a Hindu child.
> [IF `hma-26` kept:] Because your case under the Hindu Marriage Act, 1955 is
> already going on, the Family Court can also pass orders about the child
> under Section 26 of the Hindu Marriage Act, 1955 while that case is pending.

Note: `welfare-principle` is not a citable section; it renders only as the
first sentence ("welfare of the child first"). It must never be rendered as
"Section" anything.

### 3.3 Stridhan — sections `hma-27`, `bns-316`

> The gold, cash, and gifts given to you at your marriage belong to you.
> [IF `hma-27` kept:] You can ask for them back under Section 27 of the Hindu
> Marriage Act, 1955.
> [IF `bns-316` kept:] Keeping back a wife's property can also be an offence
> under Section 316 of the Bharatiya Nyaya Sanhita, 2023.

### 3.4 Residence — sections `pwdva-17`, `pwdva-18`, `pwdva-19`

> You have the right to stay in the shared household.
> [IF `pwdva-17` kept:] Under Section 17 of the Protection of Women from
> Domestic Violence Act, 2005, you have the right to reside in the shared
> household.
> [IF `pwdva-19` kept:] Under Section 19 of the Protection of Women from
> Domestic Violence Act, 2005, the court can pass a residence order about the
> shared household.
> [IF `pwdva-18` kept:] Under Section 18 of the Protection of Women from
> Domestic Violence Act, 2005, the court can pass a protection order stopping
> violence, threats, and harassment at home.

Note: `pwdva-20` kept via the residence route is a maintenance section; it is
rendered by the maintenance paragraph (§3.1), not here. Paragraph selection is
by section id, so a `pwdva-20`-only residence outcome still produces the
maintenance paragraph and no residence paragraph. The words "tenancy rights"
appear nowhere in this system.

### 3.5 Divorce — section `hma-13` only

Included only if `hma-13` is in `kept_ids`:

> You have asked for a divorce. A divorce can be sought under Section 13 of
> the Hindu Marriage Act, 1955, and the Family Court will decide it on the
> facts and evidence in your case.

**There is no template for `hma-13b`.** If `hma-13b` is in `kept_ids` (no
current test question should produce this), the renderer emits no divorce
paragraph and instead appends the escalation line from §6 (kind `court`,
reworded by the v8 builder as a human-review line for the divorce point).
This is a deliberate fail-safe: a mutual-consent provision must never be
explained from a template that assumes a contested divorce.

### 3.6 Birth certificate — section `births-deaths-act-1969`

> You can get your child's birth certificate from the Registrar of Births and
> Deaths. Birth registration is done under the Registration of Births and
> Deaths Act, 1969. If the hospital did not give a certificate, you can apply
> to the Registrar with the hospital record or other proof of birth.

The Hindu Marriage Act is never mentioned in this paragraph. The Act named
here is the only Act the paragraph is allowed to name.

## 4. Section-id → paragraph map (the renderer's only dispatch table)

| Kept section id | Paragraph |
|---|---|
| `bnss-144`, `pwdva-20`, `hma-24`, `hma-25` | §3.1 maintenance |
| `gwa-1890`, `hmga-1956-s6`, `welfare-principle`, `hma-26` | §3.2 custody |
| `hma-27`, `bns-316` | §3.3 Stridhan |
| `pwdva-17`, `pwdva-18`, `pwdva-19` | §3.4 residence |
| `hma-13` | §3.5 divorce |
| `births-deaths-act-1969` | §3.6 birth certificate |
| `hma-13b`, or any section id not in this table | **no paragraph** — escalation line instead (fail-safe) |

Unknown section ids must never render a paragraph. If a future Stage 2
change keeps a new section id, the v8 builder must add its template first;
until then the system escalates instead of inventing prose.

## 5. Court line

Built from Cell 7's `court_live` (list) and `court_source`. It is a statement,
never a question. Court names are mapped to fixed fragments:

| `court_live` entry | Fragment |
|---|---|
| `Family Court` | the Family Court |
| `Magistrate` | the Magistrate |
| `Registrar` | the Registrar of Births and Deaths |

- One court: `You would approach the Family Court.`
- Two courts: `You would approach the Family Court and the Magistrate.`
  (fragments joined with `and`; three courts joined with commas and a final
  `and`.)
- `court_source == 'fallback-escalate'`, or `kept_ids` empty but in scope:
  **no court line at all**; the court-kind escalation line (§6) is used
  instead. The system never names a court it did not derive from kept
  sections, and never asks the user to choose.
- Out of scope: no court line at all (§7).

## 6. Escalation lines (renderer-owned, keyed by typed kind)

These are **not** the verbatim `escalations_typed` texts from Cell 7 — those
are internal system wording (e.g. "re-evaluate BNS s.316", "escalate the
amount, never invent it") and must never reach the user. The renderer maps
each kind to its own fixed user-facing sentence:

| Kind | User-facing line |
|---|---|
| `quantum` | The monthly amount is not fixed here. It will be decided after your husband's income, your needs, and your child's school fees are known. |
| `court` | The court cannot be named from the information given. This question needs to be looked at by a human adviser, who will say which court applies. |
| `demand` | Before going to court, make a written demand for the return of your property and keep a copy of it. |
| `fact` | Some facts are still needed: your husband's income, in an estimate or a range, the school-fee amount, and where your husband lives now. Give whatever records you have. If a record is missing, say that it is missing. |

One line per kind present, in the order quantum, court, demand, fact.
Duplicates of a kind collapse to one line.

**Required v8 change to Cell 7 (noted here, not made here):** the
`fact`-kind escalation text in `stage2()` currently contains the phrase
"never demand salary slips". The renderer never reuses that string, but the
phrase must not survive anywhere in user-facing output. The v8 builder must
reword the Cell 7 fact text to "Ask husband's income (estimate/range),
school-fee amount, where husband lives now; never demand income proof you do
not have" so that the string "salary slips" occurs nowhere in the notebook's
user-facing paths. The self-check (§8, item 9) flags any occurrence, so this
will be caught if the rewording is missed.

## 7. Out-of-scope prose

When `kept_ids` is empty and `in_scope` is false (H12 shape):

> This question is outside the family-law matters this system covers. It does
> not say anything about your rights in this matter. A human adviser will need
> to look at it.

No intro, no issue paragraph, no court line, no closing line, no section
citation. `escalates` for such a question stays False, as in v3.

## 8. Prose forbidden self-check (no model — pure string matching)

Runs on the **generated prose only**, never on the question text. Inputs:
`prose` (str), `kept_ids` (list), `dropped_ids` (list of section ids from
`dropped`), `facts` (dict, for `divorce_asked`). Output: list of hits,
each `{item: <1–9>, detail: <str>}`. Fp for the question is 1 if the list is
non-empty, else 0.

```python
import re

# Map every citable section pattern in prose to its canonical section id.
SECTION_PATTERNS = [
    (r'\bSection 144\b.{0,40}Bharatiya Nagarik Suraksha Sanhita', 'bnss-144'),
    (r'\bBNSS\b.{0,10}s\.?\s*144\b', 'bnss-144'),
    (r'\bSection 20\b.{0,40}Protection of Women from Domestic Violence Act', 'pwdva-20'),
    (r'\bSection 17\b.{0,40}Protection of Women from Domestic Violence Act', 'pwdva-17'),
    (r'\bSection 18\b.{0,40}Protection of Women from Domestic Violence Act', 'pwdva-18'),
    (r'\bSection 19\b.{0,40}Protection of Women from Domestic Violence Act', 'pwdva-19'),
    (r'\bSection 24\b.{0,40}Hindu Marriage Act', 'hma-24'),
    (r'\bSection 25\b.{0,40}Hindu Marriage Act', 'hma-25'),
    (r'\bSection 26\b.{0,40}Hindu Marriage Act', 'hma-26'),
    (r'\bSection 27\b.{0,40}Hindu Marriage Act', 'hma-27'),
    (r'\bSection 13B?\b.{0,40}Hindu Marriage Act', 'hma-13'),  # 13B split out below
    (r'\bSection 13B\b.{0,40}Hindu Marriage Act', 'hma-13b'),
    (r'\bSection 316\b.{0,40}Bharatiya Nyaya Sanhita', 'bns-316'),
    (r'\bBNS\b.{0,10}s\.?\s*316\b', 'bns-316'),
    (r'\bSection 6\b.{0,40}Hindu Minority and Guardianship Act', 'hmga-1956-s6'),
    (r'\bGuardians and Wards Act, 1890\b', 'gwa-1890'),
    (r'\bRegistration of Births and Deaths Act, 1969\b', 'births-deaths-act-1969'),
]

AMOUNT_WORDS = (r'\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|'
                r'twelve|fifteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|'
                r'ninety|hundred)\s+(?:thousand|lakh|lakhs)\b')

def prose_forbidden_check(prose, kept_ids, dropped_ids, facts):
    hits = []
    kept = set(kept_ids)
    dropped = {d[0] for d in dropped_ids}  # dropped entries are [section_id, reason] pairs
    # 1+2. Any precedent / case citation at all. Renderer cites none, so any hit is a bug.
    for pat in (r'\b[A-Z][a-z]+ v\. [A-Z][a-z]+\b',           # "Rajnesh v. Neha"
                r'\bRajnesh\b', r'\bSatish Chander Ahuja\b',
                r'\bAIR \d{4}\b', r'\bSCC\b', r'\(\d{4}\) \d+ SCC'):
        if re.search(pat, prose):
            hits.append({'item': 1, 'detail': f'precedent/case citation matched {pat!r}'})
            break
    # 3. HMA 13/13B in prose when divorce not asked, or when not kept.
    if re.search(r'\bSection 13B?\b.{0,40}Hindu Marriage Act', prose):
        if not facts.get('divorce_asked') or not (kept & {'hma-13', 'hma-13b'}):
            hits.append({'item': 3, 'detail': 'HMA 13/13B in prose without divorce asked / not kept'})
    if re.search(r'\bSection 13B\b', prose) and 'hma-13b' not in kept:
        hits.append({'item': 3, 'detail': 'HMA 13B in prose but hma-13b not kept'})
    # 4. Residence called "tenancy rights" (or any tenant variant).
    if re.search(r'tenancy rights?|tenant rights?', prose, re.I):
        hits.append({'item': 4, 'detail': '"tenancy rights" / "tenant rights" in prose'})
    # 5. User asked to pick the court. Templates contain no "?", so any "?" is a hit;
    #    plus the explicit pick-a-court phrasings as a backstop.
    if '?' in prose:
        hits.append({'item': 5, 'detail': 'question mark in generated prose (prose must never ask)'})
    if re.search(r'which court (do you|should you|will you|do I)|choose (a|the) court|'
                 r'pick (a|the) court|decide which court', prose, re.I):
        hits.append({'item': 5, 'detail': 'prose asks user to pick the court'})
    # 6. Birth certificate under the wrong Act.
    if re.search(r'birth certificate', prose, re.I):
        if re.search(r'birth certificate.{0,80}Hindu Marriage Act|'
                     r'Hindu Marriage Act.{0,80}birth certificate', prose, re.I):
            hits.append({'item': 6, 'detail': 'birth certificate linked to HMA'})
        if 'births-deaths-act-1969' in kept and \
                'Registration of Births and Deaths Act, 1969' not in prose:
            hits.append({'item': 6, 'detail': 'birth-certificate paragraph missing the 1969 Act'})
    # 7. Any section cited in prose that is not in kept_ids (covers dropped ids too,
    #    since dropped and kept are disjoint by construction in Stage 2).
    cited = set()
    for pat, sid in SECTION_PATTERNS:
        if re.search(pat, prose):
            cited.add(sid)
    for sid in sorted(cited - kept):
        hits.append({'item': 7, 'detail': f'prose cites {sid} which is not in kept_ids'})
    for sid in sorted(cited & dropped):
        hits.append({'item': 7, 'detail': f'prose cites {sid} which Stage 2 dropped'})
    # 8. A maintenance amount stated as a number.
    for pat in (r'₹\s?[\d,]+', r'\bRs\.?\s?[\d,]+', r'\brupees\s+[\d,]+',
                r'\b[\d,]+\s*(?:per month|a month|/month|monthly)\b', AMOUNT_WORDS):
        if re.search(pat, prose, re.I):
            hits.append({'item': 8, 'detail': f'maintenance amount pattern matched {pat!r}'})
            break
    # 9. Salary slips demanded. The templates never contain the phrase at all.
    if re.search(r'salary slips?|pay slips?|payslips?', prose, re.I):
        hits.append({'item': 9, 'detail': '"salary slips" / "pay slips" appears in prose'})
    if re.search(r'(must|need to|have to|should|required|bring|provide|submit|give|'
                 r'produce|attach).{0,40}(salary|income proof|income document)', prose, re.I):
        hits.append({'item': 9, 'detail': 'prose demands income proof as an obligation'})
    return hits
```

Notes on the checker:

- Items 1+2 share one check because the renderer cites **no** precedents: any
  case citation is a hit regardless of which issue it attaches to. The
  `item` recorded is 1 (the detail string names the match); a rater can
  re-attribute to item 2 if the citation is the Satish one.
- Item 7's `dropped` set: Cell 7's `dropped` entries are `[section_id,
  reason]` pairs; the checker takes the ids. The `cited - kept` check alone
  would catch a dropped section (dropped ∩ kept is empty by Stage 2
  construction), but the explicit dropped check gives the right diagnostic
  message.
- Item 8 deliberately does **not** flag bare years (1969, 1890, 1956) or bare
  section numbers ("Section 20") — those are the only numbers the templates
  legitimately contain. It flags currency symbols, `Rs`, `rupees` + digits,
  digits + per-month, and amount words ("forty thousand", "five lakh").
- Item 9's second pattern is intentionally narrow: it flags an *obligation
  verb* aimed at income proof. The §6 `fact` line ("Give whatever records you
  have") contains no obligation verb + income-proof pairing, so it passes.
  If the v8 builder rewords §6, it must re-run this checker, not hand-wave it.
- The checker is pure `re` + set operations. It needs no model, no graph,
  and no network. Expected runtime: milliseconds per question.

## 9. How it plugs into the notebook (new Cell 9)

**Position:** new Cell 9, after the current Cell 8 (scoring/saving). It does
not edit Cells 1–8 except for the two v8 edits listed in §9.3.

**Inputs** (all already present after Cell 8 runs — no new model calls):

| Input | Source |
|---|---|
| `kept_ids`, `dropped`, `court_live`, `court_source`, `escalations_typed`, `in_scope`, `facts` | `RESULTS[i]` per question (Cell 7) |
| `gt_ids`, `court_expected`, `escalate_expected` | `TEST_SET[i]` (Cell 6) |
| Templates §2–§7 and checker §8 | this document, copied verbatim into Cell 9 |

**Cell 9 steps:**

1. For each question, call `render_prose(rec, t)` (§§1–7) → `prose` string.
2. Call `prose_forbidden_check(prose, rec['kept_ids'], rec['dropped'],
   t['facts'])` → `hits` list.
3. Attach to the record: `rec['prose']`, `rec['prose_forbidden_hits']`,
   `rec['prose_forbidden'] = 1 if hits else 0`.
4. Compute `Fp = sum(rec['prose_forbidden'] for rec in RESULTS)` (gate
   definition: number of questions with ≥ 1 prose forbidden mapping) and
   `prose_forbidden_total_instances = sum(len(hits))`.
5. Compute the §2 rating (Cell 8 currently does **not** compute a rating —
   that is a gap Cell 9 closes): `Rating = 10 × [0.60·E + 0.15·Rm + 0.10·Pm
   + 0.075·C + 0.075·S] − 0.5·Fb − 1.0·Fp`, clamped to [0, 10], rounded to
   1 decimal, then the §2 caps applied (Fp ≥ 1 caps at ≤ 5.0; prose not
   measured would have capped at ≤ 9.0 — Cell 9 removes that cap *only* by
   actually measuring Fp).
6. Re-open the saved `live-laya-colab-results-v3-empty5.json/.md` (v8 names),
   add `prose`, `prose_forbidden_hits`, `prose_forbidden`, the `Fp` aggregate
   and the §2 rating, and rewrite both files. Cell 8's files are not final
   until Cell 9 has run; the run report must say so.

**Outputs per question:** `prose` (str), `prose_forbidden_hits` (list),
`prose_forbidden` (0/1). **Outputs aggregate:** `Fp`,
`prose_forbidden_total_instances`, §2 rating (formula + caps).

**Cell 8 extension (the Fp metric):** Cell 8 gains nothing except a comment
that Fp is computed in Cell 9 and that its aggregate `prose_forbidden_mappings`
field is overwritten there. The Fp value itself lives in Cell 9 because prose
does not exist until Cell 9 renders it. Do not compute Fp in Cell 8 from
anything else — there is no prose to check before Cell 9.

### 9.3 v8 edits this design requires (builder checklist)

1. Cell 7 `stage2()`: reword the `fact`-kind escalation text to remove the
   phrase "salary slips" (§6).
2. Cell 9 (new): templates §§2–7 verbatim + checker §8 verbatim + steps 1–6.
3. Cell 8: one comment noting Fp is filled by Cell 9; no logic change.
4. Nothing else. No threshold, prompt, graph, or Cell 6 change is needed for
   prose. Prose is orthogonal to classification: it can neither raise nor
   lower exact match, precision, recall, court, or escalates scores. Its only
   score effect is Fp (and lifting the ≤ 9.0 prose-not-measured cap).

## 10. What this design does not do (honest limits)

- **It does not fix classification.** If `kept_ids` is wrong, the prose is a
  fluent, well-formed statement of the wrong law. Prose quality is bounded by
  classification quality; the self-check catches forbidden *mappings*, not
  wrong-but-allowed sections.
- **It does not handle multi-issue nuance beyond the templates.** E.g. a
  question with both maintenance and residence gets both paragraphs joined;
  there is no cross-issue synthesis sentence. That is deliberate: synthesis
  is where a generator would invent law.
- **It does not answer follow-up questions.** It renders one answer per
  classified question. Multi-turn prose is out of scope for v8.
- **The self-check is string matching, not legal judgement.** A novel
  forbidden phrasing that matches no pattern (e.g. a new wrong label for
  residence other than "tenancy rights") would pass the checker. The defence
  is that the renderer can only emit the fixed template strings: the checker's
  job is to catch builder mistakes (a template edited wrong, a wrong
  conditional), not to judge free text — because there is no free text.
- **Fp = 0 is expected on every run, by construction.** If a live run ever
  reports Fp ≥ 1, that is a renderer/template bug, not a tuning signal: fix
  the template or the dispatch table, do not tune thresholds to fix it. A
  single Fp ≥ 1 caps the run at ≤ 5.0 under the frozen formula, so this is
  not a cosmetic check.
- **Independent-rater note:** the gate (§5) says prose is "scored by an
  independent rater against this list". This self-check is the automated
  tripwire that runs in the notebook; it does not replace the independent
  rater on the fresh/Kannada sets. Both should agree at 0; if they disagree,
  the rater is right and the checker gains a pattern.
