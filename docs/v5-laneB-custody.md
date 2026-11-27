# v5 Lane B — custody / residence disambiguation (PRECISION round, round 2)

**Lane:** B (custody / residence disambiguation). **Scope:** H6 (3 custody FPs) + H14 (1 GWA FP) only.
**Starting point (verified live, Colab 2026-11-27 ~00:19 IST, v4r):** exact 10/16, micro P/R 0.826/1.000,
micro-F1 0.905, TP/FP/FN 57/12/0. Recall 1.000, zero FN. All 12 FPs are precision-only.
**Method:** offline analysis only — no Colab live run. All numbers below are copied from
`workspace/browser_downloads/sess-2184034649/browser-download-20261126T185447.300061282Z-0-live-laya-colab-results-v4r-residence-only.json`
(`raw_live_runs`) and from Cell 7 of
`live-laya-colab-test-v4r-residence-only.ipynb` (line numbers refer to that Cell 7 source).
**Bottom line:** recommend option **(c)** for H6 — a custody gate requiring an explicit
who-gets-the-child / guardianship claim, implemented as a deterministic per-clause veto after
scoring (modelled on the v4 residence gate) — and an exclusive primary-route branch in
`stage2()` for H14. Predicted effect if both work live: **−4 FPs (12 → 8), TP 57 unchanged,
FN 0, micro-P 0.826 → 0.877, micro-F1 0.905 → 0.934, exact 10/16 → 12/16** (H6 and H14 both
become exact). H6's court error is also fixed as a side effect (Family Court no longer added).

---

## 0. Correction to the brief — H6's custody fire does NOT come from the full-question score

The brief says custody fired on "full-question custody 0.1602". That understates the mechanism.
The v4r JSON for H6 (`raw_live_runs`, H6) is:

| H6 custody score source | Value | Threshold (0.20) |
|---|---|---|
| full-question (`stage1_raw`) | 0.1602 | below |
| clause-max (`stage1_clause_max`) | 0.1712 | below |
| aux-max (`aux_scores['custody']['I want my daughter to stay with me']`) | **0.3669** | **above** |
| final (`stage1_final`) = max of the three | **0.3669** | fires |
| `fired_source['custody']` | **`aux`** | — |

So the custody fire is driven **solely by the custody auxiliary prompt**
`"I want my daughter to stay with me"` (Cell 7, `AUX_PROMPTS` line 190), scored against the
**full question** (Cell 7 line 446: `_ask(aux_payload, q)`). Neither the main custody prompt
(0.1602) nor any clause (0.1712) reaches the 0.20 threshold on its own. The aux prompt's
paraphrase match ("Does this question say 'I want my daughter to stay with me' or mean the
same thing?") cannot distinguish:

- genuine custody claim (H5): *"I want my daughter to stay with me"* — verbatim, own clause; and
- residence co-location (H6): *"to stay in the house with my daughter"* — "stay … with my daughter"
  with a **place** ("in the house") instead of a **person** ("with me").

The same aux prompt is the *only* thing keeping H5's custody alive (see §4): H5 custody final
0.2189 is entirely aux-driven (full 0.1098, clause-max 0.0957). Any fix that weakens, rewords,
or removes the custody aux prompts breaks H5 recall. The fix must therefore discriminate the
two aux matches, not remove the aux mechanism. That is what the gate in §2 does.

A second correction: H6's custody sub-choice was **A: "Custody inside a matrimonial proceeding
(HMA s.26)"** with `proceeding_pending=false`. Stage 2's recheck (lines 298–300) correctly
dropped `hma-26`, so the 3 FPs are the GWA set (`gwa-1890`, `hmga-1956-s6`, `welfare-principle`)
only — the sub-choice error left no trace in `kept_ids` beyond the GWA set itself. Gating
custody at Stage 1 prevents the sub-choice from running at all on H6.

---

## 1. H6 — diagnosis

**Question (Cell 6, verbatim):** "I do not want a divorce. I just want money every month from my
husband and to stay in the house with my daughter."

**Facts (Cell 6):** `divorce_asked=false, proceeding_pending=false, decree=false, demand_made=null,
violence=false, residence_claim=true`.

**v4r result:** pred `[BNSS 144, GWA 1890, HMGA s.6, PWDVA 17, PWDVA 18, PWDVA 19, PWDVA 20,
WELFARE]` vs GT `[BNSS 144, PWDVA 20, PWDVA 17, PWDVA 18, PWDVA 19]` — TP 5 / FP 3 / FN 0,
precision 0.625. Fired issues: maintenance, custody, residence, divorce. Court WRONG
(`[Family Court, Magistrate]` vs expected `[Magistrate]` — Family Court enters via the spurious
custody set). Escalates correct.

**FP mechanism, step by step:**
1. Stage 1 main custody prompt (line 158: "Does this question ask who will get or look after the
   child, or about guardianship or custody?") scores 0.1602 full / 0.1712 clause-max — below 0.20.
2. Aux prompt "I want my daughter to stay with me" scores **0.3669** against the full question —
   Laya reads "to stay in the house with my daughter" as meaning the same thing.
3. `final['custody'] = max(0.1712, 0.1602, 0.3669) = 0.3669 ≥ 0.20` → custody fires (lines 456–512).
4. Stage 2 (lines 262–263) adds the full GWA set unconditionally on custody firing:
   `{gwa-1890, hmga-1956-s6, welfare-principle}` → 3 FPs. (HMA 26 is added only if
   `proceeding_pending`, false here, and the recheck drops it anyway.)
5. Residence fires correctly in parallel: residence aux "to stay in the house with my daughter"
   scores **0.7318**, residence final 0.7318 ≥ 0.15, `residence_claim=true` → PWDVA 17/18/19 kept.
   The residence side of this sentence is already handled; only the custody misread is broken.

**Root cause (one sentence):** the custody aux prompt paraphrase-matches a residence
co-location mention ("stay *in the house* with my daughter") as if it were a custody claim
("stay *with me*"), and the aux pass is scored on the full question, so no clause boundary can
separate the two readings.

---

## 2. H6 — recommended fix: option (c), custody gate (ONE recommendation)

### 2.1 Why (a) and (b) are rejected — with evidence

**(a) Extend the split trigger to infinitives "to stay / to live" after "and" — REJECTED as a
standalone fix.** It does not touch the live firing mechanism. The aux pass is scored against
the **full question** (Cell 7 line 446, `_ask(aux_payload, q)`), not per clause, so splitting
clause 2 changes neither the aux score (0.3669) nor the final (0.3669 ≥ 0.20): custody would
still fire. The split would only change the *clause-max* component (currently 0.1712, on the
unsplit clause); the custody score of the new isolated clause "to stay in the house with my
daughter." is **unmeasured** — it can only be obtained from a live run, and it is irrelevant
while the aux score dominates. Option (a) becomes useful only if aux scoring is re-scoped to
per-clause max, which is a second, untested change. Do not bundle it. (Worked splits under the
current and proposed rules are in §2.4.)

**(b) Add a residence aux prompt for verbatim "stay in the house" — REJECTED: already exists.**
`AUX_PROMPTS` line 191 already contains `{'issue': 'residence', 'phrase': 'to stay in the house
with my daughter'}`, and on H6 it scores **0.7318** — residence already fires correctly via it.
Adding another residence prompt cannot remove a custody FP; it only re-proves the residence side.

**(c) Custody gate requiring a who-gets-the-child claim — RECOMMENDED.** It is the only option
that acts on the actual firing path (the aux-driven final score) without touching the aux
prompts that H5's recall depends on (H5 aux 0.2189 vs threshold 0.20 — a 0.0189 margin; see §4).
The gate is a **veto on firing, not a keyword-based pick**: no issue ever fires because of the
gate; the gate can only block a fire whose text contains no explicit custody claim. That keeps
the Cell 7 hard rule intact in spirit (every *pick* still comes from `agent.predict()`), and it
mirrors the v4 residence gate precedent (lines 486–502), which likewise forces a final score to
0.0 on a fact-style condition and records the block in `gated_out`.

### 2.2 Exact code-level change

**Location:** Cell 7, immediately after the v4 residence fact-gate block (lines 486–502) and
before the firing block (lines 503–512), so it applies to `final['custody']` before any
threshold comparison, sub-choice, or Stage 2 call.

**Change 1 — gate definition (new code, placed just before the residence-gate block, ~line 486):**

```python
# --- v5 CUSTODY GATE (Stage 1): custody fires ONLY on an explicit
# who-gets-the-child / guardianship claim, never on a co-location
# mention ("stay in the house with my daughter/son") inside a residence
# clause. Modelled on the v4 residence_claim gate (same shape: force the
# final to 0.0, record in gated_out). The gate is a VETO only — it never
# fires custody itself; every custody pick still comes from agent.predict().
# Per-clause check: a clause counts as a custody claim iff it matches a
# custody pattern AND is not itself a residence co-location clause.
# (H6 clause 2 matches the residence pattern and no custody pattern, so it
# is blocked; H5/H14/K0/H2 each have a clause matching a custody pattern.)
_CUSTODY_PATTERNS = [
    re.compile(r"who will get my", re.IGNORECASE),                                   # K0, H2
    re.compile(r"\b(want|wish|need)\b.{0,30}\bmy (son|daughter|child) to stay with me\b", re.IGNORECASE),  # H5, H14
    re.compile(r"\b(custody|guardianship|guardian)\b", re.IGNORECASE),                # explicit term (none in the 16; future-proofing)
    re.compile(r"\btake (him|her|them) away\b", re.IGNORECASE),                       # H2 clause 2 (backup; H2 already passes via "who will get")
]
_RESIDENCE_COLOC_RE = re.compile(
    r"\bstay in the (house|home)\b.{0,40}\bwith my (son|daughter|child)\b", re.IGNORECASE)

def _has_custody_claim(clauses):
    for cl in clauses:
        if _RESIDENCE_COLOC_RE.search(cl):
            continue  # residence co-location clause: cannot carry a custody claim
        if any(p.search(cl) for p in _CUSTODY_PATTERNS):
            return True
    return False
```

**Change 2 — apply the gate (new block, immediately after the residence gate, ~line 502):**

```python
        # --- v5 CUSTODY GATE (Stage 1): see _has_custody_claim above.
        # If no clause states a who-gets-the-child / guardianship claim,
        # custody final is forced to 0.0 and custody can never fire, however
        # high the aux paraphrase score is (H6 aux 0.3669 is blocked this
        # way). fired_clause / fired_source stay as computed (they record
        # what WOULD have fired) — only the final score is forced, exactly
        # as the residence gate does at lines 496-499.
        rec['custody_claim'] = _has_custody_claim(clauses)
        if not rec['custody_claim']:
            final['custody'] = 0.0
            rec['stage1_final']['custody'] = 0.0
            gated_out_a.append('custody: gated, no who-gets-the-child / guardianship claim in any clause (custody_claim=false)')
            rec['custody_gated'] = True
        else:
            rec['custody_gated'] = False
```

**What is deliberately NOT changed:**
- `THRESHOLDS['custody']` stays 0.20. Raising it to e.g. 0.40 would also block H6 (0.3669) but
  would kill H5 (0.2189) — a recall loss. The gate discriminates; a threshold cannot (H5's true
  0.2189 < H6's false 0.3669 — the ranges are inverted).
- `AUX_PROMPTS` custody entries (lines 187, 190) are untouched. H5's custody lives entirely on
  the daughter aux prompt (0.2189); rewording it risks H5.
- The main custody prompt (line 158) is untouched.
- `split_clauses` (lines 195–222) is untouched — see §2.4 for why the split alone cannot fix H6.

**Predicted live effect on H6:** `final['custody']` 0.3669 → 0.0 → custody not fired → no custody
sub-choice runs → Stage 2 adds no GWA set → kept becomes
`[bnss-144, pwdva-17, pwdva-18, pwdva-19, pwdva-20]` = GT exactly → **H6 exact, −3 FPs**.
Court becomes `[Magistrate]` = expected → **H6 court error fixed as a side effect**
(Family Court entered only via the spurious custody set). Maintenance/residence/divorce firing
is untouched (maintenance 0.898, residence 0.7318 both fire as before).

### 2.3 Why the gate passes the genuine custody questions (per-clause verification)

Applied to each question's recorded `clauses` (v4r JSON `raw_live_runs[].clauses`):

| ID | Clause carrying the custody claim | Pattern matched | Gate |
|---|---|---|---|
| H5 | "I want my daughter to stay with me." | stay-with-me | PASS |
| H14 | "I want my son to stay with me and money for his school fees while the case goes on." | stay-with-me | PASS |
| K0 | "Who will get my daughter, how do I get my gold back, and which court do I go to?" | who-will-get | PASS |
| H2 | "Who will get my six year old son?" | who-will-get (+ "take him away" in clause 2 as backup) | PASS |
| H6 | clause 2 "I just want money every month from my husband and to stay in the house with my daughter." | residence co-location; **no** custody pattern ("to stay *in the house* with my daughter" ≠ "to stay *with me*") | **BLOCK** |
| H10 | "he gives no money for me and my child." / gold clause | none | BLOCK (already not firing; no change) |
| H13 | "He beats me, throws me out of the house and gives no money for my son's school fees." | none | BLOCK (already not firing; no change) |
| H12 | "Who owns it and can I stop him selling it?" / ancestral-house clause | none ("Who owns it" ≠ "Who will get my…") | BLOCK (already not firing; kept stays `[]`) |

### 2.4 Worked H6 splits — current rule vs proposed split rule (option (a))

**Current rule** (Cell 7 lines 195–222): split on sentence boundaries, then within a sentence on
`\s+and\s+` / `\s+but\s+` **only when followed by** `I|he|they|my (husband|son|daughter)`;
never split inside a negation; drop fragments <3 words.

H6 question: *"I do not want a divorce. I just want money every month from my husband and to stay
in the house with my daughter."*

- Sentence split → `["I do not want a divorce.", "I just want money every month from my husband and to stay in the house with my daughter."]`
- Sentence 2: the only "and" is followed by **"to"** ("and to stay…") — "to" is not in the
  lookahead set (`I|he|they|my…`) → **no split**. (The `_negated` check is not reached for it.)
- **Result (2 clauses — matches `rec['clauses']` in the v4r JSON exactly):**
  1. `"I do not want a divorce."`
  2. `"I just want money every month from my husband and to stay in the house with my daughter."`
- Custody clause-max on these = 0.1712 (clause 2, per JSON); custody still fires only via aux 0.3669.

**Proposed split rule (option (a)):** extend `_SPLIT_RE` with an infinitive alternative —
`\s+and\s+(?=to\s+(?:stay|live)\b)` — i.e. also split on "and" when followed by "to stay" / "to live".

- Sentence 2 now splits at "and to stay" → **result (3 clauses):**
  1. `"I do not want a divorce."`
  2. `"I just want money every month from my husband"`
  3. `"to stay in the house with my daughter."` (8 words, ≥3, kept)
- **But this does not fix H6 live:** the aux pass still scores the full question (line 446), so
  aux custody stays 0.3669 and custody still fires. The custody clause-max of the new clause 3
  is **unmeasured** (no live run has scored the isolated clause "to stay in the house with my
  daughter." under the main custody prompt). Option (a) is therefore recorded here as a
  *possible companion* change (it would make the residence clause score alone, which is the
  right shape for the residence aux), not as the H6 fix. If the merge coordinator wants it,
  it must be tested in its own live run with the aux re-scoped to per-clause max — out of scope
  for this lane.

---

## 3. H14 — diagnosis and Stage 2 fix

**Question (Cell 6, verbatim):** "My divorce case is already going on in the Family Court. I want
my son to stay with me and money for his school fees while the case goes on."

**Facts (Cell 6):** `divorce_asked=true, proceeding_pending=true, decree=false, demand_made=null,
violence=false, residence_claim=false`.

**v4r result:** pred `[BNSS 144, GWA 1890, HMA 13, HMA 24, HMA 26, HMGA s.6, PWDVA 20, WELFARE]`
vs GT `[HMA 13, HMA 26, HMGA s.6, WELFARE, HMA 24, BNSS 144, PWDVA 20]` — TP 7 / FP 1 / FN 0,
precision 0.875. Fired issues: maintenance, custody, divorce. Court correct, escalates correct.
The single FP is **standalone `gwa-1890`**.

**Mechanism (Stage 2, Cell 7 lines 262–265):**

```python
if 'custody' in fired:
    kept_pre |= {'gwa-1890', 'hmga-1956-s6', 'welfare-principle'}
    if facts['proceeding_pending']:
        kept_pre.add('hma-26')
```

The GWA set is added **unconditionally** whenever custody fires, and HMA 26 is added *on top*
when a proceeding is pending. So a pending-proceeding question keeps **both** primary routes,
violating the custody-set rule (exact-plan §2 Step 3 / §3.2; planning-note §3): exactly one of
HMA 26 / GWA 1890 is the primary route. H14's custody sub-choice was in fact **A: "Custody
inside a matrimonial proceeding (HMA s.26)"** — the model chose the right route and Stage 2
ignored the choice, keeping both. This is a Stage 2 primary-route bug, not a threshold issue:
custody legitimately fires here (final 0.7895, aux "I want my son to stay with me" 0.7895, well
above 0.20), and no threshold change can remove GWA without also removing the genuine HMA 26
route, since both come from the same `fired` flag.

**Note on the recheck (lines 298–300):** `if not facts['proceeding_pending'] and 'hma-26' in
kept_pre: remove hma-26` — this only ever removes HMA 26 in the no-proceeding case. There is no
symmetric branch removing GWA 1890 in the pending case. That asymmetry is the bug.

### Exact `stage2()` fix

**Location:** Cell 7 `stage2()`, lines 262–265. Replace the block with an exclusive branch:

```python
    if 'custody' in fired:
        # v5 PRIMARY-ROUTE RULE (exact-plan §3.2 custody-set rule): exactly ONE
        # of HMA 26 / GWA 1890 is the primary custody route.
        # proceeding_pending=True  -> HMA 26 is primary; standalone GWA 1890
        #   must NOT also be kept (H14: drop gwa-1890, keep hma-26).
        # proceeding_pending=False -> GWA 1890 is primary (H2/H5/K0 unchanged).
        # HMGA s.6 + WELFARE ride with EITHER primary and are kept in both arms.
        if facts['proceeding_pending']:
            kept_pre |= {'hma-26', 'hmga-1956-s6', 'welfare-principle'}
        else:
            kept_pre |= {'gwa-1890', 'hmga-1956-s6', 'welfare-principle'}
```

**What is dropped vs kept (H14):**
- Dropped: `gwa-1890` only (and only when `proceeding_pending` is True).
- Kept: `hma-26` (primary) + `hmga-1956-s6` + `welfare-principle` + everything else H14 already
  keeps (`hma-13`, `hma-24`, `bnss-144`, `pwdva-20`).
- Predicted H14 kept becomes `[bnss-144, hma-13, hma-24, hma-26, hmga-1956-s6, pwdva-20,
  welfare-principle]` = GT exactly → **H14 exact, −1 FP**. Court stays `[Family Court,
  Magistrate]` (HMA 26 → Family Court; BNSS 144/PWDVA 20 → Magistrate) — unchanged and correct.

**Recheck lines 298–300:** after this change, `hma-26` can only enter `kept_pre` when
`proceeding_pending` is True, so the recheck becomes unreachable — keep it as Layer-B
defence-in-depth (it can only fire if a future edit re-adds HMA 26 unconditionally), following
the HMA-25 precedent in reverse: there the dead recheck was deleted because Layer B replaced
it; here the recheck guards the same invariant from the other direction, so retaining it costs
nothing. Do **not** add a symmetric "remove GWA when pending" recheck — the exclusive branch
already guarantees it at generation time; a recheck would re-introduce the propose-then-drop
shape the plan is removing elsewhere.

**Interaction with the H6 gate:** none. H14's custody passes the §2.2 gate (clause "I want my son
to stay with me…" matches the stay-with-me pattern), so custody still fires and reaches this
`stage2()` branch. H6's custody never reaches `stage2()` at all.

---

## 4. Guardrail check — the 4 exact custody questions + K0 + H12

All evidence from v4r JSON `raw_live_runs` (custody `stage1_raw` / `stage1_clause_max` /
`stage1_final` / `aux_scores['custody']` / `fired_issues` / `kept_ids` / `sub_choices`).

| ID | v4r custody evidence | What must be preserved | Gate (§2.2) | Stage 2 (§3) | Verdict |
|---|---|---|---|---|---|
| **H2** (custody-only, no proceeding) | final **0.852** (full 0.852, clause-max 0.7647, aux 0.0605); fired; sub-choice **B** (GWA route); kept `[gwa-1890, hmga-1956-s6, welfare-principle]` = GT; exact | GWA 1890 + HMGA s.6 + WELFARE stay; HMA 26 must NOT appear | PASS — clause "Who will get my six year old son?" matches who-will-get | `proceeding_pending=false` → else-branch keeps GWA set, no HMA 26 | **PRESERVED** |
| **H5** (custody + divorce asked, no proceeding) | final **0.2189** — entirely aux ("I want my daughter to stay with me" 0.2189; full 0.1098, clause-max 0.0957); fired; sub-choice A (HMA s.26) but Stage 2 correctly kept GWA by facts; kept `[bnss-144, gwa-1890, hma-13, hmga-1956-s6, pwdva-18, pwdva-20, welfare-principle]` = GT; exact | GWA route stays | PASS — clause "I want my daughter to stay with me." matches stay-with-me | `proceeding_pending=false` → else-branch, GWA kept, HMA 26 not added | **PRESERVED** — but knife-edge: aux 0.2189 vs threshold 0.20 (margin 0.0189). The gate does not touch scores, so it cannot break this; any future aux rewording or threshold rise would. |
| **H10** (Stridhan + maintenance; custody must NOT fire) | final 0.1713 (full 0.1082, clause-max 0.1713, aux 0.0805); **not fired**; kept `[bns-316, bnss-144, hma-27, pwdva-20]` = GT; exact | Custody stays unfired | BLOCK — no clause matches any custody pattern ("he gives no money for me and my child" is maintenance, not custody) | Custody not fired → branch not entered | **PRESERVED** (gate is a no-op here; it only confirms the existing non-fire) |
| **H13** (violence + residence + maintenance; custody must NOT fire) | final 0.0485 (full 0.035, clause-max 0.035, aux 0.0485); **not fired**; kept `[bnss-144, pwdva-17, pwdva-18, pwdva-19, pwdva-20]` = GT; exact | Custody stays unfired | BLOCK — single clause contains no custody pattern ("gives no money for my son's school fees" is maintenance) | Custody not fired → branch not entered | **PRESERVED** |
| **K0** (custody must still fire) | final **0.741** (clause-max 0.741 on "Who will get my daughter…", full 0.222, aux 0.0553); fired; sub-choice B; kept includes `gwa-1890, hmga-1956-s6, welfare-principle`; exact | Custody fires; GWA route; HMA 26 absent | PASS — "Who will get my daughter…" matches who-will-get | `proceeding_pending=false` → else-branch, GWA kept | **PRESERVED** |
| **H12** (out-of-scope sibling fight; custody must NOT fire) | final 0.1397 (full 0.1218, clause-max 0.1397, aux 0.0); **not fired**; kept `[]` = GT; exact | Custody stays unfired; kept stays empty | BLOCK — "Who owns it and can I stop him selling it?" matches no custody pattern ("Who owns it" ≠ "Who will get my…") | Custody not fired → branch not entered | **PRESERVED** |

**No guardrail question is at risk from either fix.** The H6 gate's only binding constraint is
H5's 0.0189 aux margin, and the gate is score-neutral, so it cannot disturb it. The H14 Stage 2
change is branch-exclusive on `proceeding_pending`, and H14 is the **only** question in the 16
with `proceeding_pending=true` — every other custody question takes the unchanged else-branch
by construction.

### Open items / trade-offs (recorded, not hidden)

1. **OPEN — gate pattern coverage on unseen phrasings.** The four `_CUSTODY_PATTERNS` cover
   exactly the phrasings in the 16 ("Who will get my…", "I want my son/daughter to stay with
   me", explicit "custody/guardianship", "take him/her away"). A fresh question phrasing custody
   differently — e.g. "I want my child to live with me", "who gets the kids", "can I keep my
   son" — matches **no** pattern and would be gated out, turning a true custody claim into a
   recall loss (FN) on the sealed fresh-20. Mitigation: extend the pattern list only from
   rater-approved paraphrases (never from live-run tuning), and have the v5 live run report
   `custody_claim` / `custody_gated` per question so any gate block on a custody-positive
   question is visible immediately. The frozen-annotation alternative (a Cell 6 `custody_claim`
   fact, mirroring `residence_claim`) would have the same generalisation gap in a different form
   — it needs a human annotation per unseen question — so the runtime gate is preferred, but
   the gap is real either way and must be measured on the fresh set, not assumed away.
2. **OPEN — H5's sub-choice contradiction is untouched.** H5's custody sub-choice was A
   ("Custody inside a matrimonial proceeding (HMA s.26)") with `proceeding_pending=false`;
   Stage 2 silently ignored it and kept the GWA route by facts (correct outcome, wrong
   process — exact-plan §3.2). This lane does not fix sub-choice gating (offer only B/C/D when
   no proceeding is pending); that belongs to the Stage 2 lane / a later run. No score impact.
3. **NOT a risk — H6 divorce firing.** H6's divorce issue fires via the pending signal
   (0.2363 ≥ 0.12) but Stage 2 drops HMA 13 because `divorce_asked=false`; it contributes no FP
   and neither fix touches it.
4. **Interaction note for the merger:** Lane A's financial-claim change (if it alters Stage 1
   firing) does not interact with either fix — the custody gate reads only `clauses` and the
   H14 branch reads only `fired['custody']` + `facts['proceeding_pending']`. If Lane A changes
   H14's custody firing itself, re-check §3 against the new fired set before merging.

---

## 5. Predicted v5 effect (Lane B alone, arithmetic from v4r)

| Metric | v4r live | Lane B predicted (if both fixes work live) |
|---|---|---|
| Exact | 10/16 | **12/16** (H6, H14 fixed) |
| TP / FP / FN | 57 / 12 / 0 | **57 / 8 / 0** |
| Micro precision | 0.826 | **0.877** (57/65) |
| Micro recall | 1.000 | **1.000** (unchanged) |
| Micro-F1 | 0.905 | **0.934** (114/122) |
| Court correct | 13/16 | **14/16** (H6 fixed as a side effect; H14 already correct) |
| H6 | 5/3/0, court wrong | exact, court correct |
| H14 | 7/1/0 | exact |

These are **predictions from the frozen v4r numbers, not live results**: the gate's H6 block and
the Stage 2 exclusive branch are both deterministic given the v4r fired set, so the arithmetic
is exact *conditional on the v4r scores reproducing* — the live v5 run must confirm the scores
(H5 aux 0.2189 in particular) and report `custody_gated` per question.

## 6. What the v5 live run must record (for the merger / verification)

- Per question: `custody_claim` (bool), `custody_gated` (bool), `stage1_final['custody']`
  before and after the gate (the gate forces 0.0 — record the pre-gate value too, as the
  residence gate does for `fired_clause`/`fired_source`).
- H6: custody must read `custody_gated=true`, kept without any of
  `gwa-1890/hmga-1956-s6/welfare-principle`, court `[Magistrate]`.
- H14: kept must contain `hma-26` and must **not** contain `gwa-1890`.
- H2/H5/K0: kept custody set byte-identical to v4r; H5 custody final must still be ≥ 0.20.
- H10/H13/H12: custody still unfired, kept byte-identical to v4r.
- Regression tripwire: if any question's custody final changes vs v4r other than H6's forced
  0.0, the run is not a clean Lane B test — report it before merging.
