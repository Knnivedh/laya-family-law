#!/usr/bin/env python3
"""Build live-laya-colab-test-v4-residence.ipynb from live-laya-colab-test-v3-empty5.ipynb.

v4 notebook engineer (overnight 10/10 push). ONE focused fix: residence
precision + Lane A PRIMARY thresholds. No external model consulted, no Colab
run here — this builder only writes the notebook. Derived from
build_laya_v3_empty5.py: same structure (9 cells, cells 0-5 copied untouched,
Cell 6 annotated, Cells 7-8 replaced), but Cells 7-8 are produced here by
surgical string replacements on the ON-DISK v3 notebook sources (not by
re-typing them), so nothing else can drift — in particular the Cell 8
esc_live patch (quantum/court/demand, patched 2026-11-26 on the v3 notebook
after the v3 builder ran) is preserved by construction.

What v4 changes vs v3 (full diff in v4-change-log.md):
  1. THRESHOLDS (Lane A PRIMARY vector): maintenance 0.05 (v3 0.10),
     custody 0.13 (v3 0.20), residence 0.15 (unchanged value),
     divorce-asked 0.40 (v3 0.45), divorce-pending 0.13 (v3 0.12),
     stridhan 0.50, violence 0.50, birth_certificate 0.50 (unchanged).
     NOTE: the task brief says "change ONLY maintenance and custody" while
     also listing divorce-asked 0.40 / divorce-pending 0.13. The listed
     values are applied. It is behaviourally moot: no v3 live final falls
     in the divorce delta bands (asked [0.40, 0.45), pending [0.12, 0.13)),
     so both readings produce identical firing.
  2. RESIDENCE PROMPT: fires on R0 (the exact v1 prompt text, copied from
     v1 Cell 7 — see RESIDENCE_R0 below), threshold 0.15, clause-max/aux
     as in v3. R1 is still recorded per question for diagnosis and never
     fires.
  3. NEW Cell 6 facts field `residence_claim` (bool, frozen annotation,
     same status as the other facts). RULE: true iff the question states
     eviction / lockout / being thrown out / changed lock / cannot enter
     the house, OR a claim to stay in the shared house, OR a threat to
     throw the person out. Values: K0/H4/H6/H13 True, all others False.
     Rule-vs-list check: NO discrepancy. "I want my son/daughter to stay
     with me" (H5, H14) is a custody stay, not a claim to stay in the
     shared house, so both are False under the rule as written.
  4. RESIDENCE FACT GATE in Stage 1: residence_claim False forces the
     residence final score to 0.0 and residence never fires; a gated_out
     entry 'residence: gated, no residence claim in facts
     (residence_claim=false)' is recorded.
  5. RESIDENCE FULL-SET in Stage 2: when residence fires (and passed the
     gate), keep PWDVA 17 + 18 + 19 as a set. The residence sub-choice
     outcome is recorded informationally only and NEVER splits the set.
     The violence -> PWDVA 18 path is completely untouched.

DO NOT CHANGE (enforced by the diff check in build()): ground truth, any
other facts field, court logic, escalate logic, clause-split rules, aux
prompts, the HMA 25 gate, the esc_live patch, graph v2 JSON, cells 0-5.

Run: python3 build_laya_v4_residence.py
Output: live-laya-colab-test-v4-residence.ipynb (same directory).
"""

import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "live-laya-colab-test-v3-empty5.ipynb")
OUT = os.path.join(HERE, "live-laya-colab-test-v4-residence.ipynb")

# Exact v1 residence prompt (R0), copied verbatim from v1 Cell 7
# (live-laya-colab-test.ipynb, ISSUES list). v3's RESIDENCE_R0 already
# carried this exact text; v4 fires on it.
RESIDENCE_R0 = ('Does this question ask about staying in, or being thrown out of, '
                'the shared house, or about protection from threats or violence at home?')

# Frozen residence_claim annotations (Cell 6 facts field). Rule: true iff the
# question states eviction / lockout / being thrown out / changed lock /
# cannot enter the house, OR a claim to stay in the shared house, OR a
# threat to throw the person out. Verified against the question text:
# K0 "throwing me out" True; H4 "changed the lock / cannot enter" True;
# H6 "to stay in the house with my daughter" True; H13 "throws me out of
# the house" True. H2 "take him [son] away" is custody, not a house
# eviction — False. H5/H14 "stay with me" is a custody stay, not a
# house-stay claim — False. H12 ancestral-house ownership/sale dispute —
# False. All others state no residence claim — False.
RESIDENCE_CLAIM = {
    'K0': True, 'H1': False, 'H2': False, 'H3': False, 'H4': True,
    'H5': False, 'H6': True, 'H7': False, 'H8': False, 'H9': False,
    'H10': False, 'H11': False, 'H12': False, 'H13': True,
    'H14': False, 'H15': False,
}


def replace_once(src, old, new, label):
    """Replace exactly one occurrence of `old` in `src`; fail loudly otherwise."""
    n = src.count(old)
    assert n == 1, f"v4 edit {label}: expected exactly 1 occurrence, found {n}: {old[:90]!r}"
    return src.replace(old, new)


# ---------------------------------------------------------------------------
# Cell 6 edit: add "residence_claim" to every facts dict + header comment.
# ---------------------------------------------------------------------------
CELL6_HEADER_OLD = """# fixed BEFORE any run. "facts" are the question's stated facts as
# annotated in the backtest (proceeding pending, decree, divorce asked,
# demand made, violence stated) — fixed annotations, never inferred
# from keywords at run time.
"""
CELL6_HEADER_NEW = """# fixed BEFORE any run. "facts" are the question's stated facts as
# annotated in the backtest (proceeding pending, decree, divorce asked,
# demand made, violence stated) — fixed annotations, never inferred
# from keywords at run time.
# v4 ADDS one facts field, "residence_claim" (bool, frozen annotation, same
# status as the other facts): true iff the question states eviction /
# lockout / being thrown out / changed lock / cannot enter the house, OR a
# claim to stay in the shared house, OR a threat to throw the person out.
# "I want my son/daughter to stay with me" is a CUSTODY stay, not a claim
# to stay in the shared house, so H5/H14 are False under this rule.
# Ground truth is otherwise byte-identical to v3.
"""


def edit_cell6_source(lines):
    """Insert residence_claim after each facts 'violence' line.

    Returns (new_lines, n_inserted). Tracks the current question id from
    the '"id": "..."' lines; the 'violence' line is the last key of each
    facts dict, so a comma is added to it before the new key.
    """
    new_lines = []
    cur_id = None
    n_ins = 0
    for line in lines:
        m_id = re.match(r'\s*"id":\s*"([^"]+)"', line)
        if m_id:
            cur_id = m_id.group(1)
        m_v = re.match(r'(\s*"violence":\s*)(True|False)\s*\n$', line)
        if m_v:
            assert cur_id in RESIDENCE_CLAIM, f"unknown question id {cur_id!r} in Cell 6"
            new_lines.append(f"{m_v.group(1)}{m_v.group(2)},\n")
            new_lines.append(f'   "residence_claim": {RESIDENCE_CLAIM[cur_id]}\n')
            n_ins += 1
            continue
        new_lines.append(line)
    assert n_ins == 16, f"expected 16 residence_claim insertions, got {n_ins}"
    return new_lines, n_ins


# ---------------------------------------------------------------------------
# Cell 7 edits (surgical replacements on the on-disk v3 Cell 7 source).
# ---------------------------------------------------------------------------
CELL7_EDITS = [
    ("header",
     """# Cell 7 — v3 (empty-5 fix) LIVE Stage 1 + Stage 2.
# SCOPE: fix the 5 silent questions only (H1, H4, H8, H11, H14 — all 0/0/empty
# in the v1 live run, 2026-11-26: exact 5/16, mean P/R 0.656/0.492, micro
# P/R 0.875/0.368, TP/FP/FN 21/3/36, court 10/16, escalates 11/16).
# Plan source: laya-10-10-exact-plan.md §2 Steps 1-4, §3.1 (HMA 25 gate),
# §3.3 (court fallback), §3.4 (typed escalations). No live Colab run here.
""",
     """# Cell 7 — v4 (residence precision + Lane A PRIMARY thresholds) LIVE Stage 1 + Stage 2.
# SCOPE: residence precision ONLY, on top of v3. v3 live (2026-11-26):
# exact 5/16, mean P/R 0.673/0.866, micro P/R 0.671/0.895, TP/FP/FN
# 51/25/6, court 11/16, escalates 14/16. Main leak: residence R1 fired
# 11/16 (R0: 5/16) — H2/H10/H12 residence FPs, H13 split, H6 miss.
# v4 changes (see v4-change-log.md for the full diff + predictions):
#  (a) Lane A PRIMARY per-issue thresholds (M 0.05, C 0.13, R 0.15,
#      divorce-asked 0.40 / divorce-pending 0.13);
#  (b) residence fires on the R0 prompt (exact v1 text) at 0.15, R1 recorded
#      for diagnosis only and never fires;
#  (c) NEW Cell 6 facts field residence_claim + Stage 1 fact gate
#      (claim False -> residence final forced to 0.0, never fires);
#  (d) Stage 2 residence keeps PWDVA 17+18+19 as a full set, never split.
# No live Colab run here — this builder only writes the notebook.
"""),
    ("note-3-thresholds",
     """#  3. PER-ISSUE THRESHOLDS (plan §2 Step 1 ranges) — NEVER a single global
#     threshold drop alone. Recommended vector (in-sample on n=16, will
#     overfit — validate on a fresh held-out set before locking anything):
#     maintenance 0.10 (range 0.05-0.20), custody 0.20 (0.10-0.22),
#     stridhan 0.50 (keep; H1 0.4948 FP risk below), residence 0.15 R1
#     (0.10-0.20, conditional on R1 + clause-split), violence 0.50 (keep),
#     divorce-asked 0.45 (0.40-0.50), divorce-pending 0.12 (0.10-0.15),
#     birth_certificate 0.50 (keep), in_scope 0.50 (no plan range; default).
#     Divorce IS split into two signals (asked vs pending) as the plan
#     requires: divorce fires if asked-final >= 0.45 OR pending-final >= 0.12.
""",
     """#  3. PER-ISSUE THRESHOLDS — Lane A PRIMARY vector (v4), NEVER a single
#     global threshold. maintenance 0.05 (v3: 0.10), custody 0.13 (v3: 0.20),
#     stridhan 0.50 (keep), residence 0.15 R0 (keep the value, change the
#     prompt), violence 0.50 (keep), divorce-asked 0.40 (v3: 0.45),
#     divorce-pending 0.13 (v3: 0.12), birth_certificate 0.50 (keep),
#     in_scope 0.50 (no plan range; default).
#     Divorce IS split into two signals (asked vs pending) as the plan
#     requires: divorce fires if asked-final >= 0.40 OR pending-final >= 0.13.
#     WARNING, recorded before the live run (see v4-change-log.md §5):
#     applying this PRIMARY vector to the v3 live finals newly fires
#     maintenance on H2/H4/H12 and custody on H7/H10/H12 — those are
#     PREDICTED new FPs. The residence-only counterfactual (v3 thresholds
#     kept) predicts 10/16 exact; the full PRIMARY vector predicts 6/16.
#     The vector is applied as specified; the numbers decide in Colab.
"""),
    ("note-4-residence",
     """#  4. RESIDENCE R0/R1 A/B (plan §2 Step 4.4): R0 = v1 prompt (with the threat
#     clause that misfired H2 at 0.8247); R1 = residence-only: "Does this
#     question ask about staying in, or being thrown out of, the shared house
#     or home?" Both probs recorded (residence_r0 / residence_r1, full and
#     clause-max). RESIDENCE_PROMPT="R1" (default) selects which one fires;
#     R0 is retained for comparison only and never fires.
""",
     """#  4. RESIDENCE R0 FIRES (v4; v3 fired R1). R0 = the exact v1 prompt:
#     "Does this question ask about staying in, or being thrown out of, the
#     shared house, or about protection from threats or violence at home?"
#     R1 = residence-only: "Does this question ask about staying in, or being
#     thrown out of, the shared house or home?" Both probs recorded
#     (residence_r0 / residence_r1, full and clause-max) plus the aux
#     residence max; the R0 final = max(R0 full, R0 clause-max, aux).
#     RESIDENCE_PROMPT="R0" selects the firing prompt; R1 is retained for
#     comparison only and never fires. R0 alone does NOT fix H2: its R0
#     clause-max is 0.8464 ("take him away" read as a threat). The fact
#     gate (note 8) is what blocks H2/H3/H5/H10/H12/H14.
"""),
    ("note-5-residence-gate-fitted",
     """#     NOT fitted in this lane (plan §3.2, out of scope — stated, not hidden):
#     HMA 24 / HMA 26 / divorce-gate / custody-route pre-generation gating
#     and the residence fact gate (needs a new Cell 6 facts field, which
#     would change ground truth). HMA 24 / HMA 26 still use the v1
#     add-then-drop recheck shape inside stage2().
""",
     """#     NOT fitted in this lane (plan §3.2, out of scope — stated, not hidden):
#     HMA 24 / HMA 26 / divorce-gate / custody-route pre-generation gating.
#     The residence fact gate (note 8) IS fitted in v4 — it needed the new
#     Cell 6 facts field residence_claim, added as a frozen annotation.
#     HMA 24 / HMA 26 still use the v1 add-then-drop recheck shape inside
#     stage2().
"""),
    ("note-8-fact-gate-full-set",
     """#     buried. Do NOT "fix" it by re-attaching the v1 boilerplate.
""",
     """#     buried. Do NOT "fix" it by re-attaching the v1 boilerplate.
#  8. v4 RESIDENCE FACT GATE + FULL SET (this version's focused fix):
#     residence_claim (Cell 6, frozen annotation) is true iff the question
#     states eviction / lockout / being thrown out / changed lock / cannot
#     enter the house, OR a claim to stay in the shared house, OR a threat
#     to throw the person out. Values: K0/H4/H6/H13 True, all others False.
#     "I want my son/daughter to stay with me" (H5, H14) is a custody stay,
#     NOT a claim to stay in the shared house, so both are False under the
#     rule as written — no value contradicts the rule. Gate: claim False
#     forces residence final to 0.0 before firing (recorded in gated_out);
#     claim True fires per the R0 score. Stage 2 then keeps PWDVA 17+18+19
#     as a full set when residence fires; the sub-choice outcome is recorded
#     in rec['residence_sub_choice_info'] for information only and never
#     splits the set. The violence -> PWDVA 18 path is COMPLETELY UNTOUCHED:
#     when residence is gated out and violence fires, PWDVA 18 still comes
#     in through violence (that is how H5's missing PWDVA 18 is predicted
#     to return — see v4-change-log.md §5).
"""),
    ("thresholds-dict",
     """THRESHOLDS = {
    'maintenance': 0.10,
    'custody': 0.20,
    'stridhan': 0.50,
    'residence': 0.15,
    'violence': 0.50,
    'divorce_asked': 0.45,
    'divorce_pending': 0.12,
    'birth_certificate': 0.50,
    'in_scope': 0.50,
}""",
     """THRESHOLDS = {
    'maintenance': 0.05,
    'custody': 0.13,
    'stridhan': 0.50,
    'residence': 0.15,
    'violence': 0.50,
    'divorce_asked': 0.40,
    'divorce_pending': 0.13,
    'birth_certificate': 0.50,
    'in_scope': 0.50,
}"""),
    ("residence-prompt-flag",
     "RESIDENCE_PROMPT = 'R1'  # default; set to 'R0' only for a comparison run",
     "RESIDENCE_PROMPT = 'R0'  # v4: R0 fires; set to 'R1' only for a comparison run"),
    ("rec-residence-fields",
     """           'residence_r0': None, 'residence_r1': None,
           'residence_r0_clause_max': None,""",
     """           'residence_r0': None, 'residence_r1': None,
           'residence_r0_clause_max': None,
           'residence_claim': None, 'residence_gated': None,
           'residence_sub_choice_info': {},"""),
    ("residence-r0-comment",
     "        rec['residence_r0'] = raw.get('residence')  # full-question R0, comparison only",
     "        rec['residence_r0'] = raw.get('residence')  # full-question R0 — the v4 firing prompt"),
    ("final-scores-comment",
     "        # --- final scores: max(clause_max, full, aux); residence uses R1 ---",
     "        # --- final scores: max(clause_max, full, aux); residence uses R0 (v4) ---"),
    ("track-r0",
     "        TRACK = {'residence': 'residence_r1'}  # R1 selects; R0 never fires",
     "        TRACK = {'residence': 'residence'}  # v4: R0 selects; R1 never fires"),
    ("gated-out-init-early",
     """    try:
        # --- full-question pass (baseline, recorded, never deleted) ---""",
     """    try:
        gated_out_a = []  # v4: initialised here so the residence fact gate (below) can append before sub-choices run
        # --- full-question pass (baseline, recorded, never deleted) ---"""),
    ("fact-gate-block",
     "        # --- firing (per-issue thresholds; residence = R1 final) ---",
     """        # --- v4 RESIDENCE FACT GATE (Stage 1): residence_claim is a frozen
        # Cell 6 facts annotation (see builder / change log for the rule).
        # If False, residence final is forced to 0.0 and residence can never
        # fire, however high the R0 score is (H2 R0 0.8464, H5 0.4882,
        # H12 0.2177, H10 0.1901, H3 0.1727, H14 0.1550 are all gated out
        # this way). The gate entry is recorded in gated_out (Layer A style).
        # If True, residence fires per the R0 score at threshold 0.15.
        # fired_clause / fired_source for residence stay as computed (they
        # record what WOULD have fired) — only the final score is forced.
        rec['residence_claim'] = bool(facts.get('residence_claim', False))
        if not rec['residence_claim']:
            final['residence'] = 0.0
            rec['stage1_final']['residence'] = 0.0
            gated_out_a.append('residence: gated, no residence claim in facts (residence_claim=false)')
            rec['residence_gated'] = True
        else:
            rec['residence_gated'] = False
        # --- firing (per-issue thresholds; residence = R0 final, fact-gated) ---"""),
    ("gated-out-init-remove-late",
     """        # --- sub-choices, one call per fired issue, body = its argmax clause ---
        gated_out_a = []
        sub = {}""",
     """        # --- sub-choices, one call per fired issue, body = its argmax clause ---
        # (gated_out_a was initialised at the top of this try block, v4.)
        sub = {}"""),
    ("stage2-residence-full-set",
     """    if 'residence' in fired:
        r = sub.get('residence:residence_sub_issue', '')
        p = sub.get('residence:protection_vs_residence', '')
        res = set()
        if 'Already thrown out' in r or 'Combination' in r:
            res |= {'pwdva-17', 'pwdva-18', 'pwdva-19'}
        elif 'Threatened with eviction' in r:
            res |= {'pwdva-17', 'pwdva-19'}
        elif 'Violence, threats' in r:
            res |= {'pwdva-18'}
        elif 'Money cut off' in r:
            res |= {'pwdva-20'}
        if 'Both' in p:
            res |= {'pwdva-17', 'pwdva-18', 'pwdva-19'}
        elif 'Stop the violence' in p:
            res |= {'pwdva-18'}
        elif 'Secure the right to stay' in p:
            res |= {'pwdva-17', 'pwdva-19'}
        elif 'Money only' in p:
            res |= {'pwdva-20'}
        if not res:
            dropped.append(('residence sections', 'residence fired but the sub-choice gave no section set — recorded as a miss, not guessed'))
        kept_pre |= res""",
     """    if 'residence' in fired:
        # v4 FULL SET: when residence fires (it already passed the fact gate
        # in Stage 1), keep PWDVA 17 + 18 + 19 as a set. The residence
        # sub-choice outcomes are recorded informationally by the caller in
        # rec['residence_sub_choice_info'] and NEVER split the set (v3 split
        # it: H13 kept only PWDVA 18, H5 kept 17+19 and lost 18).
        kept_pre |= {'pwdva-17', 'pwdva-18', 'pwdva-19'}"""),
    ("sub-choice-info-record",
     """        rec['sub_choices'] = sub
        rec['sub_choice_body'] = sub_body""",
     """        rec['sub_choices'] = sub
        rec['sub_choice_body'] = sub_body
        if 'residence' in fired:
            # v4: informational only — the Stage 2 full set never reads this.
            rec['residence_sub_choice_info'] = {k: v for k, v in sub.items() if k.startswith('residence:')}"""),
]

# ---------------------------------------------------------------------------
# Cell 8 edits (surgical replacements on the on-disk v3 Cell 8 source).
# The esc_live PATCHED line (quantum/court/demand) is NOT in this list and
# is therefore carried over verbatim; build() asserts it is still there.
# ---------------------------------------------------------------------------
CELL8_EDITS = [
    ("header",
     """# Cell 8 — v3 score, save, download.
# Scoring is the backtest's (exact section-set match, per-section precision /
# recall, forbidden mappings, court correct, escalates correctly) PLUS the
# v3 diagnostics below. Original metrics are kept verbatim so v3 compares
# directly with the v1 baseline (exact 5/16, mean P/R 0.656/0.492, micro
# P/R 0.875/0.368, TP/FP/FN 21/3/36, court 10/16, escalates 11/16).
""",
     """# Cell 8 — v4 score, save, download.
# Scoring is the backtest's (exact section-set match, per-section precision /
# recall, forbidden mappings, court correct, escalates correctly) PLUS the
# v4 diagnostics below. Original metrics are kept verbatim so v4 compares
# directly with the v3 live baseline (exact 5/16, mean P/R 0.673/0.866,
# micro P/R 0.671/0.895, TP/FP/FN 51/25/6, court 11/16, escalates 14/16).
# v4 residence diagnostics: corrected R0/R1 clause-max keys (v3 read a
# non-existent 'residence_r0' key, so its R0 clause-max column was always
# None and its R1 column actually showed the R0 clause-max), R0/R1 finals
# (max of full, clause-max, aux), residence_claim / residence_gated /
# residence_fired per question, residence gated count.
# NOTE (carried over from v3, not introduced by v4): the header comment
# above about escalates describes the flag as quantum/court, but the
# esc_live line below is the PATCHED 2026-11-26 version that also includes
# 'demand'. The patched line is kept verbatim; only this note records it.
"""),
    ("residence-rows-corrected",
     """# --- residence R0 vs R1 comparison ---
res_rows = []
for t, r in zip(TEST_SET, RESULTS):
    r0_full = r.get('residence_r0')
    r1_full = r.get('residence_r1')
    r0_cl = (r.get('stage1_clause_max') or {}).get('residence_r0')
    r1_cl = (r.get('stage1_clause_max') or {}).get('residence')
    fired_r0 = any(v is not None and v >= 0.15 for v in (r0_full, r0_cl))
    fired_r1 = 'residence' in r.get('fired_issues', [])
    res_rows.append({'id': t['id'], 'r0_full': r0_full, 'r1_full': r1_full,
                     'r0_clause_max': r0_cl, 'r1_clause_max': r1_cl,
                     'fired_r0_at_0.15': fired_r0, 'fired_r1': fired_r1})""",
     """# --- residence R0 vs R1 comparison (v4: CORRECTED key lookup) ---
# v3 read stage1_clause_max['residence_r0'] (a key that does not exist ->
# always None) for R0 clause-max and ['residence'] (the R0 clause-max) for
# R1 clause-max, so the v3 table mislabelled R0 clause-max as R1. v4 reads
# the true keys: R0 clause-max = stage1_clause_max['residence'],
# R1 clause-max = stage1_clause_max['residence_r1']. R0 final here =
# max(R0 full, R0 clause-max, aux residence max) — the same max Cell 7
# fires on. R1 final is the same max with R1 in place of R0 (diagnostic
# only; R1 never fires in v4). residence_gated comes from Cell 7.
res_rows = []
for t, r in zip(TEST_SET, RESULTS):
    r0_full = r.get('residence_r0')
    r1_full = r.get('residence_r1')
    r0_cl = (r.get('stage1_clause_max') or {}).get('residence')
    r1_cl = (r.get('stage1_clause_max') or {}).get('residence_r1')
    aux_res = (r.get('aux_max') or {}).get('residence')
    r0_final = max([v for v in (r0_full, r0_cl, aux_res) if v is not None], default=None)
    r1_final = max([v for v in (r1_full, r1_cl, aux_res) if v is not None], default=None)
    fired_r0 = r0_final is not None and r0_final >= 0.15
    fired_r1 = r1_final is not None and r1_final >= 0.15
    res_rows.append({'id': t['id'], 'r0_full': r0_full, 'r1_full': r1_full,
                     'r0_clause_max': r0_cl, 'r1_clause_max': r1_cl,
                     'aux_residence_max': aux_res, 'r0_final': r0_final,
                     'r1_final': r1_final,
                     'residence_claim': r.get('residence_claim'),
                     'residence_gated': r.get('residence_gated'),
                     'fired_r0_at_0.15': fired_r0, 'fired_r1': fired_r1,
                     'residence_fired': 'residence' in r.get('fired_issues', [])})"""),
    ("agg-version",
     "    'notebook_version': 'v3-empty5 (clause-split + aux prompts + per-issue thresholds + R1 residence + HMA25 gate + court fallback + typed escalations)',",
     "    'notebook_version': 'v4-residence (R0 residence + residence_claim fact gate + residence full set 17/18/19 + Lane A PRIMARY thresholds M 0.05 / C 0.13 / R 0.15 / D-asked 0.40 / D-pend 0.13)',"),
    ("agg-residence-counts",
     """    'residence_fired_r0_count_at_0.15': sum(1 for x in res_rows if x['fired_r0_at_0.15']),
    'residence_fired_r1_count': sum(1 for x in res_rows if x['fired_r1']),""",
     """    'residence_fired_r0_count_at_0.15': sum(1 for x in res_rows if x['fired_r0_at_0.15']),
    'residence_fired_r1_count_at_0.15_diagnostic': sum(1 for x in res_rows if x['fired_r1']),
    'residence_fired_count': sum(1 for x in res_rows if x['residence_fired']),
    'residence_gated_count': sum(1 for x in res_rows if x['residence_gated']),"""),
    ("agg-v3-baseline",
     "    'v1_baseline_reference': 'v1 live: exact 5/16, mean P/R 0.656/0.492, micro P/R 0.875/0.368, TP/FP/FN 21/3/36, court 10/16, escalates 11/16, forbidden-before-recheck 2.',",
     "    'v1_baseline_reference': 'v1 live: exact 5/16, mean P/R 0.656/0.492, micro P/R 0.875/0.368, TP/FP/FN 21/3/36, court 10/16, escalates 11/16, forbidden-before-recheck 2.',\n    'v3_baseline_reference': 'v3 live: exact 5/16, mean P/R 0.673/0.866, micro P/R 0.671/0.895, TP/FP/FN 51/25/6, court 11/16, escalates 14/16, residence fired R1 11/16 vs R0 5/16.',"),
    ("print-header",
     "print('=== LIVE Laya + v2 graph — Colab results (v3 empty-5) ===')",
     "print('=== LIVE Laya + v2 graph — Colab results (v4 residence) ===')"),
    ("residence-print-table",
     """print('=== Residence R0 vs R1 (threshold 0.15 for the comparison) ===')
print(f"{'ID':4s} {'R0 full':>7s} {'R1 full':>7s} {'R0 clmax':>8s} {'R1 clmax':>8s} {'fire R0':>7s} {'fire R1':>7s}")
for x in res_rows:
    def _f(v):
        return f'{v:.4f}' if v is not None else '  None'
    print(f"{x['id']:4s} {_f(x['r0_full']):>7s} {_f(x['r1_full']):>7s} {_f(x['r0_clause_max']):>8s} {_f(x['r1_clause_max']):>8s} "
          f"{str(x['fired_r0_at_0.15']):>7s} {str(x['fired_r1']):>7s}")""",
     """print('=== Residence R0 vs R1 (v4: R0 fires, fact-gated; R1 diagnostic only) ===')
print(f"{'ID':4s} {'R0 full':>7s} {'R1 full':>7s} {'R0 clmax':>8s} {'R1 clmax':>8s} {'aux':>7s} {'R0 fin':>7s} {'claim':>5s} {'gated':>5s} {'fired':>5s}")
for x in res_rows:
    def _f(v):
        return f'{v:.4f}' if v is not None else '  None'
    print(f"{x['id']:4s} {_f(x['r0_full']):>7s} {_f(x['r1_full']):>7s} {_f(x['r0_clause_max']):>8s} {_f(x['r1_clause_max']):>8s} {_f(x['aux_residence_max']):>7s} {_f(x['r0_final']):>7s} "
          f"{str(x['residence_claim']):>5s} {str(x['residence_gated']):>5s} {str(x['residence_fired']):>5s}")"""),
    ("filenames-json",
     "live-laya-colab-results-v3-empty5",
     "live-laya-colab-results-v4-residence"),
    ("md-title",
     "md = ['# Live Laya inference test — Colab run v3-empty5 (Laya 421M + v2 graph)',",
     "md = ['# Live Laya inference test — Colab run v4-residence (Laya 421M + v2 graph)',"),
    ("md-residence-table",
     """md += ['', '## Residence R0 vs R1', '',
       '| ID | R0 full | R1 full | R0 clause-max | R1 clause-max | Fired R0 (0.15) | Fired R1 |',
       '|----|---------|---------|---------------|---------------|-----------------|----------|']
for x in res_rows:
    md.append(f"| {x['id']} | {x['r0_full']} | {x['r1_full']} | {x['r0_clause_max']} | {x['r1_clause_max']} | {x['fired_r0_at_0.15']} | {x['fired_r1']} |")""",
     """md += ['', '## Residence R0 vs R1 (v4: R0 fires, fact-gated; R1 diagnostic only)', '',
       '| ID | R0 full | R1 full | R0 clause-max | R1 clause-max | Aux residence max | R0 final | Residence claim | Gated | Residence fired |',
       '|----|---------|---------|---------------|---------------|-------------------|----------|-----------------|-------|---------------|']
for x in res_rows:
    md.append(f"| {x['id']} | {x['r0_full']} | {x['r1_full']} | {x['r0_clause_max']} | {x['r1_clause_max']} | {x['aux_residence_max']} | {x['r0_final']} | {x['residence_claim']} | {x['residence_gated']} | {x['residence_fired']} |")"""),
    ("download-print",
     "print('Downloaded both v3 result files. Send them back to Muse to record the live score.')",
     "print('Downloaded both v4 result files. Send them back to Muse to record the live score.')"),
]


def build():
    with open(ORIG, "r", encoding="utf-8") as f:
        nb = json.load(f)
    cells = nb["cells"]
    assert len(cells) == 9, f"v3 notebook has {len(cells)} cells, expected 9"
    orig_cells = json.loads(json.dumps(cells))  # deep copy for the diff check

    # Cells 0-5: copied untouched (same objects).
    # Cell 6: header comment + residence_claim insertions only.
    c6_src = "".join(cells[6]["source"])
    assert not re.search(r"\b(false|true|null)\b", c6_src), "JSON literals remain in v3 Cell 6"
    c6_src = replace_once(c6_src, CELL6_HEADER_OLD, CELL6_HEADER_NEW, "cell6-header")
    c6_lines, c6_nins = edit_cell6_source(c6_src.splitlines(keepends=True))
    cells[6]["source"] = c6_lines

    # Cell 7: surgical v4 edits on the on-disk v3 source.
    c7_src = "".join(cells[7]["source"])
    assert RESIDENCE_R0 in c7_src, "R0 prompt text not found verbatim in v3 Cell 7"
    assert "RESIDENCE_R0 = 'Does this question ask about staying in, or being thrown out of, the shared house, or about protection from threats or violence at home?'" in c7_src
    for label, old, new in CELL7_EDITS:
        c7_src = replace_once(c7_src, old, new, f"cell7-{label}")
    # Sanity: no R1-firing remnant, violence path untouched.
    assert "TRACK = {'residence': 'residence'}" in c7_src
    assert "RESIDENCE_PROMPT = 'R0'" in c7_src
    assert "if 'violence' in fired and 'residence' not in fired:" in c7_src
    assert "kept_pre.add('pwdva-18')" in c7_src
    cells[7]["source"] = c7_src.splitlines(keepends=True)

    # Cell 8: surgical v4 edits on the on-disk v3 source (esc_live patch preserved).
    c8_src = "".join(cells[8]["source"])
    assert "esc_live = bool(kinds & {'quantum', 'court', 'demand'})" in c8_src, (
        "esc_live patch missing from v3 Cell 8 — refusing to build")
    for label, old, new in CELL8_EDITS:
        if label == "filenames-json":
            n = c8_src.count(old)
            assert n == 6, f"cell8-filenames-json: expected 6 occurrences, found {n}"
            c8_src = c8_src.replace(old, new)
        else:
            c8_src = replace_once(c8_src, old, new, f"cell8-{label}")
    assert "esc_live = bool(kinds & {'quantum', 'court', 'demand'})" in c8_src, (
        "esc_live patch lost during Cell 8 edits")
    assert "live-laya-colab-results-v3-empty5" not in c8_src
    cells[8]["source"] = c8_src.splitlines(keepends=True)

    # --- diff check: cells 0-5 identical; Cell 6 only header + 16 insertions ---
    for i in range(6):
        assert cells[i] == orig_cells[i], f"cell {i} changed — must stay untouched"
    old6 = orig_cells[6]["source"]
    new6 = cells[6]["source"]
    assert len(new6) == len(old6) + 16 + 7, (
        f"Cell 6 line count: {len(old6)} -> {len(new6)}, expected +23 (16 claims + 7 header lines)")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write("\n")

    # --- validate the written notebook ---
    with open(OUT, "rb") as f:
        raw_bytes = f.read()
    sha = hashlib.sha256(raw_bytes).hexdigest()
    nb2 = json.loads(raw_bytes)
    assert len(nb2["cells"]) == 9
    # Cell 6 executes and carries the exact residence_claim values; GT untouched.
    ns6 = {}
    exec("".join(nb2["cells"][6]["source"]), ns6)
    got_claim = {t["id"]: t["facts"]["residence_claim"] for t in ns6["TEST_SET"]}
    assert got_claim == RESIDENCE_CLAIM, f"residence_claim mismatch: {got_claim}"
    ns6_orig = {}
    exec("".join(orig_cells[6]["source"]), ns6_orig)
    for t_new, t_old in zip(ns6["TEST_SET"], ns6_orig["TEST_SET"]):
        assert t_new["id"] == t_old["id"] and t_new["question"] == t_old["question"]
        assert t_new["gt_ids"] == t_old["gt_ids"] and t_new["gt_labels"] == t_old["gt_labels"]
        assert t_new["court_expected"] == t_old["court_expected"]
        assert t_new["escalate_expected"] == t_old["escalate_expected"]
        old_facts = dict(t_old["facts"])
        new_facts = {k: v for k, v in t_new["facts"].items() if k != "residence_claim"}
        assert new_facts == old_facts, f"facts changed for {t_new['id']}"
    # Cells 7-8 compile as Python.
    for ci in (7, 8):
        compile("".join(nb2["cells"][ci]["source"]), f"cell{ci}", "exec")
    # nbformat validation when available.
    try:
        import nbformat
        nbformat.validate(nb2)
        nb_ok = "nbformat.validate PASS"
    except ImportError:
        nb_ok = "nbformat not installed — skipped (JSON parse + compile checks passed)"
    print(f"wrote {OUT}")
    print(f"Cell 6: {c6_nins} residence_claim insertions; GT/facts otherwise identical to v3")
    print(f"Cells 0-5: untouched. Cells 7-8: v4 edits applied ({len(CELL7_EDITS)} + {len(CELL8_EDITS)} replacements)")
    print(f"Cells 7-8 compile: PASS. {nb_ok}.")
    print(f"sha256: {sha}")
    return OUT, sha


if __name__ == "__main__":
    build()
