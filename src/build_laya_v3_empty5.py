#!/usr/bin/env python3
"""Build live-laya-colab-test-v3-empty5.ipynb from live-laya-colab-test.ipynb.

Lane D (empty-5 fix). Scope ONLY H1, H4, H8, H11, H14. No live Colab run.

What this builder does:
  * Copies the original notebook (9 cells) unchanged, except:
  * Cell 6: ONLY the JSON-literals bug is fixed (false->False, true->True,
    null->None in the Python TEST_SET dicts). GT, facts, court_expected and
    escalate_expected are otherwise byte-identical.
  * Cell 7: rewritten (Stage 1 clause-split + aux prompts + per-issue
    thresholds + residence R0/R1 + divorce asked/pending split + HMA 25
    pre-generation gate + court fallback + typed escalations).
  * Cell 8: rewritten (same original metrics + empty-5 table, gate/court
    diagnostics, residence R0-vs-R1 table, H2/H12 checks; new output
    filenames live-laya-colab-results-v3-empty5.json/.md).
  * Cells 0-5 are copied byte-identical (same JSON objects).

Run: python3 build_laya_v3_empty5.py
Output: live-laya-colab-test-v3-empty5.ipynb (same directory as this script).
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "live-laya-colab-test.ipynb")
OUT = os.path.join(HERE, "live-laya-colab-test-v3-empty5.ipynb")

CELL7_SRC = r'''# Cell 7 — v3 (empty-5 fix) LIVE Stage 1 + Stage 2.
# SCOPE: fix the 5 silent questions only (H1, H4, H8, H11, H14 — all 0/0/empty
# in the v1 live run, 2026-11-26: exact 5/16, mean P/R 0.656/0.492, micro
# P/R 0.875/0.368, TP/FP/FN 21/3/36, court 10/16, escalates 11/16).
# Plan source: laya-10-10-exact-plan.md §2 Steps 1-4, §3.1 (HMA 25 gate),
# §3.3 (court fallback), §3.4 (typed escalations). No live Colab run here.
#
# WHAT CHANGED vs v1 (Cell 7):
#  1. CLAUSE-SPLIT (plan §2 Step 2, rule implemented verbatim): split on
#     sentence boundaries [.!?;] then on "and"/"but" ONLY when followed by
#     I|he|they|my husband|my son|my daughter (so "gold and cash" and "money
#     and my child" do NOT split); NEVER split inside a negation (a fragment
#     whose first 4 words contain not / n't / never / cannot stays attached —
#     "they will not return it", "have not filed any case yet", "cannot enter
#     my house"); drop clauses with <3 words. Full question kept as baseline
#     (stage1_raw) and included in the max pool as the fallback. Per-issue
#     score = MAX over clauses (+ full fallback), NEVER mean. fired_clause =
#     argmax clause text; fired_source = which source won (clause/full/aux).
#     KNOWN DEVIATION, documented not hidden: the plan's worked splits also
#     split at bare commas ("He beats me, throws me out...", "Who will get my
#     daughter, how do I get my gold back..."). The verbatim rule has no
#     comma-only split, so H13 stays a single clause and H5/K0 keep some
#     comma-joined clauses whole. rec['clauses'] records the actual split per
#     question, so this is auditable in the results file.
#  2. AUX PROMPTS (plan §2 Step 3): the 12 verbatim phrases as auxiliary
#     noul prompts, each 'Does this question say "<verbatim phrase>" or mean
#     the same thing?', run on the FULL question. Issue score =
#     max(main prompt, aux prompts). Includes the H4 lock, H8 salary-slips,
#     H11 not-filed-yet, H14 pending-case + son-custody + school-fees phrases.
#  3. PER-ISSUE THRESHOLDS (plan §2 Step 1 ranges) — NEVER a single global
#     threshold drop alone. Recommended vector (in-sample on n=16, will
#     overfit — validate on a fresh held-out set before locking anything):
#     maintenance 0.10 (range 0.05-0.20), custody 0.20 (0.10-0.22),
#     stridhan 0.50 (keep; H1 0.4948 FP risk below), residence 0.15 R1
#     (0.10-0.20, conditional on R1 + clause-split), violence 0.50 (keep),
#     divorce-asked 0.45 (0.40-0.50), divorce-pending 0.12 (0.10-0.15),
#     birth_certificate 0.50 (keep), in_scope 0.50 (no plan range; default).
#     Divorce IS split into two signals (asked vs pending) as the plan
#     requires: divorce fires if asked-final >= 0.45 OR pending-final >= 0.12.
#  4. RESIDENCE R0/R1 A/B (plan §2 Step 4.4): R0 = v1 prompt (with the threat
#     clause that misfired H2 at 0.8247); R1 = residence-only: "Does this
#     question ask about staying in, or being thrown out of, the shared house
#     or home?" Both probs recorded (residence_r0 / residence_r1, full and
#     clause-max). RESIDENCE_PROMPT="R1" (default) selects which one fires;
#     R0 is retained for comparison only and never fires.
#  5. HMA 25 PRE-GENERATION GATE (plan §3.1) — FITTED, both layers:
#     Layer A filters the option 'permanent alimony at/after an HMA decree'
#     out of maintenance:maintenance-root BEFORE offering it to Laya when
#     facts['decree'] is False (recorded in gated_out). Layer B in stage2():
#     hma-25 is added ONLY if facts['decree'] is True, otherwise it goes to
#     gated_out, NOT to dropped[] (it was never a candidate). The old
#     add-then-drop recheck block for hma-25 is DELETED. Consequence, stated
#     in Cell 8 too: forbidden_proposed_before_gate is 0-by-construction for
#     the HMA 25 route after Layer A (the option cannot be picked); the honest
#     check is the offline shadow test below (PASS printed every run) plus
#     kept_ids for H5/H9 byte-identical to the v1 run.
#     NOT fitted in this lane (plan §3.2, out of scope — stated, not hidden):
#     HMA 24 / HMA 26 / divorce-gate / custody-route pre-generation gating
#     and the residence fact gate (needs a new Cell 6 facts field, which
#     would change ground truth). HMA 24 / HMA 26 still use the v1
#     add-then-drop recheck shape inside stage2().
#  6. COURT FALLBACK (plan §3.3): court_for(kept, fired, probs, facts,
#     in_scope). Kept non-empty: as v1, except Registrar is now membership
#     ('births-deaths-act-1969' in kept), not equality. Kept empty + in-scope:
#     NO guessed court and never [] — court is ["ESCALATE — no section kept,
#     court cannot be derived"] + top-2 candidate issues as payload + a typed
#     court escalation. A provisional court is emitted ONLY if top prob >= 0.40
#     AND margin over second >= 0.15 — that condition holds for NONE of the 5
#     empty questions, so on this set the fallback is escalation-only.
#     Kept empty + out-of-scope: [] / escalate False (H12 must stay empty).
#     in_scope comes from an 8th Stage 1 noul question: "Does this question
#     concern a Hindu matrimonial / domestic-relationship family-law matter?"
#  7. TYPED ESCALATIONS (plan §3.4): escalations_typed entries {kind, text},
#     kinds quantum / court / demand / fact. Quantum ONLY for maintenance
#     questions (maintenance fired OR a maintenance section kept), never an
#     amount, ask-income text, never demand salary slips. Demand-first
#     Stridhan escalation typed as demand (kept, BNS 316 NOT gated — plan
#     §3.2: deliberately propose-and-escalate). Plain-text escalations list is
#     ALSO kept (backward compatible); Cell 8 scores from the typed
#     quantum/court flag, NOT from bool(escalations) — see Cell 8 header.
#     KNOWN CONSEQUENCE (flagged, not hidden): under typed quantum/court
#     scoring, H2/H3/H7/H15 have no quantum/court reason (H2 custody+residence,
#     H3 demand-only, H7 birth-certificate, H15 stridhan-only with demand
#     already made), so they read escalates=False against expected True.
#     H7 is the plan's flagged OPEN ambiguity (fully answerable question with
#     escalate_expected=True and no named reason). Cell 8 also reports the
#     any-typed and bool-plain diagnostics so this effect is visible, not
#     buried. Do NOT "fix" it by re-attaching the v1 boilerplate.
# HARD RULES (unchanged from v1): every issue pick comes from agent.predict().
# If a predict call raises on the FULL-question pass, the question is recorded
# as an ERROR and scored as a miss. There is NO fallback to keyword / phrase /
# rule matching. Clause/aux call failures are recorded per clause and that
# clause is skipped (partial scores stand); they never invent a score.
# Sub-choices run ONLY for fired issues, options from the uploaded v2 graph,
# body = the issue's argmax clause (full question if that clause has <5 words).
import re
import time

# --- Recommended per-issue threshold vector (plan §2 Step 1) ---
THRESHOLDS = {
    'maintenance': 0.10,
    'custody': 0.20,
    'stridhan': 0.50,
    'residence': 0.15,
    'violence': 0.50,
    'divorce_asked': 0.45,
    'divorce_pending': 0.12,
    'birth_certificate': 0.50,
    'in_scope': 0.50,
}
# NEVER a single global threshold: true-positive floors differ by 0.82 across
# issues (maintenance 0.0773 vs stridhan 0.8929) and residence/custody/divorce
# ranges are inverted/overlapping (plan §2 Step 1, "Why a single global
# threshold cannot work"). Keep this dict explicit; change one value at a time.

RESIDENCE_R0 = 'Does this question ask about staying in, or being thrown out of, the shared house, or about protection from threats or violence at home?'
RESIDENCE_R1 = 'Does this question ask about staying in, or being thrown out of, the shared house or home?'
RESIDENCE_PROMPT = 'R1'  # default; set to 'R0' only for a comparison run
DIVORCE_PENDING_Q = 'Does this question say a divorce case is already going on or pending in court?'
IN_SCOPE_Q = 'Does this question concern a Hindu matrimonial / domestic-relationship family-law matter?'

ISSUES = [
    ('maintenance', 'Does this question ask for monthly money or maintenance for the wife or a child?'),
    ('custody', 'Does this question ask who will get or look after the child, or about guardianship or custody?'),
    ('stridhan', 'Does this question ask about gold, cash or gifts given to the wife at marriage that are held by the husband or his family?'),
    ('residence', RESIDENCE_R0),
    ('violence', 'Does this question say the husband beats, threatens or harasses the wife?'),
    ('divorce', 'Does this question ask for a divorce, or for ending the marriage?'),
    ('birth_certificate', "Does this question ask how to get a child's birth certificate?"),
]
ISSUE_NODE = {
    'maintenance': 'maintenance:maintenance-root',
    'custody': 'custody:custody_sub_issue_choice',
    'stridhan': 'stridhan:stridhan-subissue',
    'residence': 'residence:residence_sub_issue',
    'divorce': 'procedure:divorce-gate',
}
ISSUE_EXTRA_NODE = {
    'stridhan': 'stridhan:civil-vs-criminal',
    'residence': 'residence:protection_vs_residence',
}

# --- 12 auxiliary noul prompts, verbatim phrases from plan §2 Step 3 ---
# Each becomes: Does this question say "<phrase>" or mean the same thing?
AUX_PROMPTS = [
    {'issue': 'residence', 'phrase': 'They changed the lock and I cannot enter my house'},
    {'issue': 'maintenance', 'phrase': 'I need money while my case is going on, but I have not filed any case yet'},
    {'issue': 'maintenance', 'phrase': "I need maintenance but I do not have my husband's salary slips and I do not know what he earns"},
    {'issue': 'maintenance', 'phrase': "gives no money for my son's school fees"},
    {'issue': 'maintenance', 'phrase': 'money for his school fees while the case goes on'},
    {'issue': 'maintenance', 'phrase': 'he gives no money for me and my child'},
    {'issue': 'maintenance', 'phrase': 'My husband has not given me any money for three months'},
    {'issue': 'custody', 'phrase': 'I want my son to stay with me'},
    {'issue': 'residence', 'phrase': 'throws me out of the house'},
    {'issue': 'divorce_pending', 'phrase': 'My divorce case is already going on in the Family Court'},
    {'issue': 'custody', 'phrase': 'I want my daughter to stay with me'},
    {'issue': 'residence', 'phrase': 'to stay in the house with my daughter'},
]


def split_clauses(q):
    # Plan §2 Step 2 deterministic rule, verbatim (see header note 1 for the
    # one documented deviation: no comma-only split, so H13 stays one clause
    # and H5/K0 keep some comma-joined clauses whole).
    _NEG = ('not', 'never', 'cannot', "can't", "couldn't", "won't", "don't", "isn't", "wasn't")
    def _negated(fragment):
        words = fragment.split()[:4]
        return any((w.strip('.,;:').lower() in _NEG) or w.lower().endswith("n't") for w in words)
    _SPLIT_RE = re.compile(
        r'\s+and\s+(?=(?:I|he|they|my\s+(?:husband|son|daughter))\b)'
        r'|\s+but\s+(?=(?:I|he|they|my\s+(?:husband|son|daughter))\b)')
    out = []
    for sent in re.split(r'(?<=[.!?;])\s+', q.strip()):
        # Cut points: text before each kept match start, text after its end.
        # The matched " and " / " but " separator itself is dropped.
        pieces = []
        prev_end = 0
        for m in _SPLIT_RE.finditer(sent):
            if _negated(sent[m.end():]):
                continue
            pieces.append(sent[prev_end:m.start()])
            prev_end = m.end()
        pieces.append(sent[prev_end:])
        for ch in pieces:
            ch = ch.strip().strip(',;').strip()
            if len(ch.split()) >= 3:
                out.append(ch)
    return out if out else [q.strip()]


def _parse(answer, qtype):
    if isinstance(answer, dict):
        for k in ('choice', 'value', 'option', 'answer', 'probability', 'score'):
            if k in answer:
                return answer[k]
        return str(answer)
    return answer


def _ask(payload, body):
    res = agent.predict({'body': body}, payload)
    return res['answers']


def _prob_from(ans_dict, key):
    try:
        return float(_parse(ans_dict[key]['noul'], 'noul'))
    except Exception:
        return None


def stage2(fired, sub, facts):
    # Returns (kept, dropped, esc_typed, gated_out, candidates_before_gate).
    # candidates_before_gate = what Stage 1 + sub-choices proposed BEFORE the
    # HMA 25 gate (kept pre-gate union dropped section ids). HMA 25 Layer B
    # is applied here; Layer A filtered the option before offering it.
    kept_pre = set()
    dropped = []
    esc_typed = []
    gated_out = []
    if 'maintenance' in fired:
        kept_pre |= {'bnss-144', 'pwdva-20'}
        ans = sub.get('maintenance:maintenance-root', '')
        if 'interim maintenance during a pending HMA proceeding' in ans:
            kept_pre.add('hma-24')
        if 'permanent alimony at/after an HMA decree' in ans:
            kept_pre.add('hma-25')
    if 'custody' in fired:
        kept_pre |= {'gwa-1890', 'hmga-1956-s6', 'welfare-principle'}
        if facts['proceeding_pending']:
            kept_pre.add('hma-26')
    if 'stridhan' in fired:
        kept_pre |= {'hma-27', 'bns-316'}
        if facts['demand_made'] is False:
            esc_typed.append({'kind': 'demand', 'text': 'Stridhan: make a written demand for return first, then re-evaluate BNS s.316'})
    if 'residence' in fired:
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
        kept_pre |= res
    if 'violence' in fired and 'residence' not in fired:
        kept_pre.add('pwdva-18')
    if 'divorce' in fired:
        gate = sub.get('procedure:divorce-gate', '')
        if facts['divorce_asked'] and 'open gate' in gate:
            kept_pre.add('hma-13')
        elif facts['divorce_asked']:
            dropped.append(('hma-13', 'divorce issue fired but the divorce-gate choice did not open the gate'))
        # HMA 13B (mutual consent) is never added: no test question states mutual consent.
    if 'birth_certificate' in fired:
        kept_pre.add('births-deaths-act-1969')
    # --- recheck / drops (v1 rules; HMA 24 / HMA 26 still add-then-drop here,
    # out of scope for this lane — see header note 5) ---
    if not facts['divorce_asked']:
        for s in ('hma-13', 'hma-13b'):
            if s in kept_pre:
                kept_pre.remove(s)
                dropped.append((s, 'divorce gate: divorce not asked'))
    if not facts['proceeding_pending'] and 'hma-24' in kept_pre:
        kept_pre.remove('hma-24')
        dropped.append(('hma-24', 'no HMA proceeding pending'))
    if not facts['proceeding_pending'] and 'hma-26' in kept_pre:
        kept_pre.remove('hma-26')
        dropped.append(('hma-26', 'no HMA proceeding pending — GWA 1890 route'))
    candidates_before_gate = sorted(kept_pre | {d[0] for d in dropped if d[0] in SECTION_IDS})
    # --- HMA 25 gate, Layer B: add ONLY if a decree exists ---
    kept = set(kept_pre)
    if 'hma-25' in kept:
        if facts['decree']:
            pass  # decree exists: keep (never exercised on this 16 — no question has decree True)
        else:
            kept.remove('hma-25')
            gated_out.append("hma-25: gated before generation (Layer B) — sub-choice said 'permanent alimony at/after an HMA decree' but decree=false")
            # NOT added to dropped[]: it was never a candidate after gating.
    # The old 'if not facts[decree] and hma-25 in kept: drop' recheck block is
    # DELETED per plan §3.1 (it would preserve the propose-then-drop shape).
    # --- typed escalations: quantum ONLY for maintenance questions ---
    # Income-unknown is assumed: Cell 6 has no income_known fact field (GT
    # unchanged by design), so no per-question income check is possible here.
    maint_kept = bool(kept & {'bnss-144', 'pwdva-20', 'hma-24', 'hma-25'})
    if 'maintenance' in fired or maint_kept:
        esc_typed.append({'kind': 'quantum', 'text': "Quantum: husband's income / school fees unknown — escalate the amount, never invent it"})
        esc_typed.append({'kind': 'fact', 'text': "Ask husband's income (estimate/range), school-fee amount, where husband lives now; never demand salary slips"})
    return kept, dropped, esc_typed, gated_out, candidates_before_gate


def _court_for_issue(issue):
    return {'maintenance': {'Magistrate'}, 'custody': {'Family Court'},
            'stridhan': {'Family Court', 'Magistrate'}, 'residence': {'Magistrate'},
            'violence': {'Magistrate'}, 'divorce': {'Family Court'},
            'birth_certificate': {'Registrar'}}.get(issue, set())


def court_for(kept, fired, probs, facts, in_scope):
    # Returns (courts_list, court_source, top2_list).
    # court_source: 'kept' | 'provisional' | 'fallback-escalate' | 'out-of-scope'.
    if kept:
        courts = set()
        if kept & {'hma-24', 'hma-25', 'hma-26', 'hma-27', 'hma-13', 'hma-13b'}:
            courts.add('Family Court')
        if kept & {'gwa-1890', 'hmga-1956-s6', 'welfare-principle'}:
            courts.add('Family Court')
        if kept & {'bnss-144', 'pwdva-17', 'pwdva-18', 'pwdva-19', 'pwdva-20', 'bns-316'}:
            courts.add('Magistrate')
        if 'births-deaths-act-1969' in kept:  # v3 fix: membership, not equality
            courts.add('Registrar')
        return sorted(courts), 'kept', []
    ranked = sorted(probs.items(), key=lambda kv: (kv[1] if kv[1] is not None else -1), reverse=True)
    top2 = [(k, round(v, 4) if v is not None else None) for k, v in ranked[:2]]
    if not in_scope:
        return [], 'out-of-scope', top2
    if len(ranked) >= 2:
        top_prob = ranked[0][1] or 0.0
        second_prob = ranked[1][1] or 0.0
        # Provisional court ONLY on dominance (top >= 0.40 AND margin >= 0.15).
        # Holds for NONE of the 5 empty questions — on this set the fallback
        # below is escalation-only. Do not tune thresholds to force a court.
        if top_prob >= 0.40 and (top_prob - second_prob) >= 0.15:
            return sorted(_court_for_issue(ranked[0][0])), 'provisional', top2
    return ['ESCALATE — no section kept, court cannot be derived'], 'fallback-escalate', top2


# --- Offline shadow test of the HMA 25 gate (no model calls; fails fast) ---
_shadow_sub = {'maintenance:maintenance-root': 'permanent alimony at/after an HMA decree'}
_shadow_facts = {'divorce_asked': False, 'proceeding_pending': False, 'decree': False, 'demand_made': None, 'violence': False}
_k, _d, _e, _g, _cbg = stage2({'maintenance'}, _shadow_sub, _shadow_facts)
assert 'hma-25' not in _k, 'HMA25 gate shadow test FAILED: hma-25 kept with decree=false'
assert _g, 'HMA25 gate shadow test FAILED: no gated_out entry with decree=false'
assert 'hma-25' in _cbg, 'HMA25 gate shadow test FAILED: hma-25 missing from candidates_before_gate'
_k2, _d2, _e2, _g2, _cbg2 = stage2({'maintenance'}, _shadow_sub, {**_shadow_facts, 'decree': True})
assert 'hma-25' in _k2, 'HMA25 gate shadow test FAILED: hma-25 dropped with decree=true'
print('HMA25 gate shadow test: PASS (decree=false -> gated, not kept, in candidates_before_gate; decree=true -> kept)')


RESULTS = []
for t in TEST_SET:
    q = t['question']
    facts = t['facts']
    t0 = time.perf_counter()
    rec = {'id': t['id'], 'question': q, 'gt_ids': t['gt_ids'],
           'gt_labels': t['gt_labels'], 'facts': facts,
           'stage1_raw': {}, 'stage1_probs': {}, 'stage1_clause_max': {},
           'stage1_final': {}, 'fired_issues': [], 'fired_clause': {},
           'fired_source': {}, 'aux_scores': {}, 'aux_max': {},
           'clauses': [], 'clause_errors': [], 'aux_errors': [],
           'residence_r0': None, 'residence_r1': None,
           'residence_r0_clause_max': None,
           'divorce_asked_prob': None, 'divorce_pending_prob': None,
           'divorce_signal': 'none',
           'in_scope': None, 'in_scope_prob': None,
           'sub_choices': {}, 'sub_choice_body': {},
           'candidates_before_stage2': [], 'candidates_before_gate': [],
           'gated_out': [], 'kept_ids': [], 'dropped': [],
           'escalations': [], 'escalations_typed': [],
           'court_live': [], 'court_source': None, 'court_top2': [],
           'error': None, 'latency_s': None}
    try:
        # --- full-question pass (baseline, recorded, never deleted) ---
        full_payload = {}
        for name, instr in ISSUES:
            full_payload[f'issue_{name}'] = {'type': 'noul', 'instructions': instr}
        full_payload['issue_residence_r1'] = {'type': 'noul', 'instructions': RESIDENCE_R1}
        full_payload['issue_divorce_pending'] = {'type': 'noul', 'instructions': DIVORCE_PENDING_Q}
        full_payload['issue_in_scope'] = {'type': 'noul', 'instructions': IN_SCOPE_Q}
        ans_full = _ask(full_payload, q)
        raw = {}
        for name, _ in ISSUES:
            raw[name] = _prob_from(ans_full, f'issue_{name}')
        raw['residence_r1'] = _prob_from(ans_full, 'issue_residence_r1')
        raw['divorce_pending'] = _prob_from(ans_full, 'issue_divorce_pending')
        raw['in_scope'] = _prob_from(ans_full, 'issue_in_scope')
        rec['stage1_raw'] = {k: (round(v, 4) if v is not None else None) for k, v in raw.items()}
        rec['stage1_probs'] = dict(rec['stage1_raw'])  # v1 field name, kept for compat
        rec['residence_r0'] = raw.get('residence')  # full-question R0, comparison only
        rec['residence_r1'] = raw.get('residence_r1')
        # --- clause-split passes (one predict call per clause) ---
        clauses = split_clauses(q)
        rec['clauses'] = clauses
        clause_scores = {name: {} for name, _ in ISSUES}
        clause_scores['residence_r1'] = {}
        clause_scores['divorce_pending'] = {}
        clause_scores['in_scope'] = {}
        for clause in clauses:
            payload = {}
            for name, instr in ISSUES:
                payload[f'issue_{name}'] = {'type': 'noul', 'instructions': instr}
            payload['issue_residence_r1'] = {'type': 'noul', 'instructions': RESIDENCE_R1}
            payload['issue_divorce_pending'] = {'type': 'noul', 'instructions': DIVORCE_PENDING_Q}
            payload['issue_in_scope'] = {'type': 'noul', 'instructions': IN_SCOPE_Q}
            try:
                ans_c = _ask(payload, clause)
            except Exception as e:
                rec['clause_errors'].append([clause, repr(e)])
                continue
            for key in list(clause_scores.keys()):
                p = _prob_from(ans_c, f'issue_{key}')
                if p is not None:
                    clause_scores[key][clause] = p
        clause_max = {k: (max(v.values()) if v else None) for k, v in clause_scores.items()}
        rec['stage1_clause_max'] = {k: (round(v, 4) if v is not None else None) for k, v in clause_max.items()}
        rec['residence_r0_clause_max'] = clause_max.get('residence')
        # --- auxiliary layman-phrase prompts (full question) ---
        aux_payload = {}
        for ai, aux in enumerate(AUX_PROMPTS):
            aux_payload[f'aux_{ai}'] = {'type': 'noul', 'instructions': 'Does this question say "' + aux['phrase'] + '" or mean the same thing?'}
        try:
            ans_aux = _ask(aux_payload, q)
        except Exception as e:
            rec['aux_errors'].append(repr(e))
            ans_aux = {}
        aux_scores = {}
        for ai, aux in enumerate(AUX_PROMPTS):
            p = _prob_from(ans_aux, f'aux_{ai}') if f'aux_{ai}' in ans_aux else None
            aux_scores.setdefault(aux['issue'], {})[aux['phrase']] = p
        rec['aux_scores'] = aux_scores
        rec['aux_max'] = {iss: max([v for v in d.values() if v is not None], default=None) for iss, d in aux_scores.items()}
        # --- final scores: max(clause_max, full, aux); residence uses R1 ---
        TRACK = {'residence': 'residence_r1'}  # R1 selects; R0 never fires
        final = {}
        fired_clause = {}
        fired_source = {}
        for name, _ in ISSUES:
            tk = TRACK.get(name, name)
            best_clause, best_cprob = None, None
            for cl, p in clause_scores.get(tk, {}).items():
                if best_cprob is None or p > best_cprob:
                    best_clause, best_cprob = cl, p
            aux_m = rec['aux_max'].get(name)
            cands = [(v, s) for v, s in [(best_cprob, 'clause'), (raw.get(tk), 'full'), (aux_m, 'aux')] if v is not None]
            final[name] = max(v for v, s in cands) if cands else None
            fired_clause[name] = best_clause if best_clause is not None else '(full question)'
            fired_source[name] = max(cands, key=lambda vs: vs[0])[1] if cands else None
        rec['stage1_final'] = {k: (round(v, 4) if v is not None else None) for k, v in final.items()}
        rec['fired_clause'] = fired_clause
        rec['fired_source'] = fired_source
        # --- divorce: two signals (asked vs pending) ---
        asked_final = final['divorce']
        pending_final = max([v for v in [clause_max.get('divorce_pending'), raw.get('divorce_pending'), rec['aux_max'].get('divorce_pending')] if v is not None], default=None)
        rec['divorce_asked_prob'] = round(asked_final, 4) if asked_final is not None else None
        rec['divorce_pending_prob'] = round(pending_final, 4) if pending_final is not None else None
        asked_fires = asked_final is not None and asked_final >= THRESHOLDS['divorce_asked']
        pending_fires = pending_final is not None and pending_final >= THRESHOLDS['divorce_pending']
        rec['divorce_signal'] = ('both' if (asked_fires and pending_fires) else
                                  'asked' if asked_fires else
                                  'pending' if pending_fires else 'none')
        rec['stage1_final']['divorce_pending'] = rec['divorce_pending_prob']
        # --- firing (per-issue thresholds; residence = R1 final) ---
        fired = []
        for name, _ in ISSUES:
            if name == 'divorce':
                if asked_fires or pending_fires:
                    fired.append('divorce')
                continue
            score, thr = final[name], THRESHOLDS[name]
            if score is not None and score >= thr:
                fired.append(name)
        rec['fired_issues'] = fired
        # --- in_scope (8th question; clause-max vs full max, threshold 0.50) ---
        in_scope_final = max([v for v in [clause_max.get('in_scope'), raw.get('in_scope')] if v is not None], default=None)
        rec['in_scope_prob'] = round(in_scope_final, 4) if in_scope_final is not None else None
        rec['in_scope'] = bool(in_scope_final is not None and in_scope_final >= THRESHOLDS['in_scope'])
        # --- sub-choices, one call per fired issue, body = its argmax clause ---
        gated_out_a = []
        sub = {}
        sub_body = {}
        for iss in fired:
            body = fired_clause.get(iss) or q
            if len(body.split()) < 5:
                body = q
            nodes = []
            for node_id in [ISSUE_NODE.get(iss), ISSUE_EXTRA_NODE.get(iss)]:
                if node_id and node_id in NODES:
                    node = NODES[node_id]
                    opts = node.get('options')
                    if isinstance(opts, list) and opts and all(isinstance(o, str) for o in opts):
                        opts = list(opts)
                        # HMA 25 gate, Layer A: filter the decree option before offering it.
                        if node_id == 'maintenance:maintenance-root' and not facts['decree']:
                            if 'permanent alimony at/after an HMA decree' in opts:
                                opts.remove('permanent alimony at/after an HMA decree')
                                gated_out_a.append("hma-25: option 'permanent alimony at/after an HMA decree' removed from maintenance:maintenance-root before offering (Layer A), decree=false")
                        nodes.append((node_id, opts, node))
            if not nodes:
                continue
            payload = {}
            for node_id, opts, node in nodes:
                payload[node_id] = {'type': 'choice', 'instructions': node.get('question', node_id),
                                    'criteria': {f'opt{i}': o for i, o in enumerate(opts)}}
            ans2 = _ask(payload, body)
            for node_id, opts, node in nodes:
                raw2 = _parse(ans2[node_id]['choice'], 'choice')
                if isinstance(raw2, str) and raw2.startswith('opt') and raw2[3:].isdigit():
                    raw2 = opts[int(raw2[3:])]
                sub[node_id] = raw2
                sub_body[node_id] = body
        rec['sub_choices'] = sub
        rec['sub_choice_body'] = sub_body
        # --- Stage 2 + court fallback ---
        kept, dropped, esc_typed, gated_out_b, cbg = stage2(set(fired), sub, facts)
        rec['kept_ids'] = sorted(kept)
        rec['candidates_before_stage2'] = sorted(kept | {d[0] for d in dropped if d[0] in SECTION_IDS})
        rec['candidates_before_gate'] = cbg
        rec['gated_out'] = gated_out_a + gated_out_b
        rec['dropped'] = [[a, b] for a, b in dropped]
        probs_for_court = dict(final)
        probs_for_court['divorce'] = max([v for v in [asked_final, pending_final] if v is not None], default=None)
        courts, court_source, top2 = court_for(kept, set(fired), probs_for_court, facts, rec['in_scope'])
        rec['court_live'] = courts
        rec['court_source'] = court_source
        rec['court_top2'] = [[k, v] for k, v in top2]
        if court_source == 'fallback-escalate':
            esc_typed.append({'kind': 'court', 'text': 'Court: no section kept and question is in scope — escalate to a human; court cannot be derived from sub-threshold scores'})
        rec['escalations_typed'] = esc_typed
        rec['escalations'] = [e['text'] for e in esc_typed]  # plain-text, backward compatible
    except Exception as e:
        rec['error'] = repr(e)
        print(f"{t['id']}: LIVE ERROR — {e!r} (scored as a miss, no fallback)")
    rec['latency_s'] = round(time.perf_counter() - t0, 2)
    RESULTS.append(rec)
    print(f"{t['id']}: fired={rec['fired_issues']} kept={[LABEL_BY_ID.get(s, s) for s in rec['kept_ids']]} "
          f"court={rec['court_live']} ({rec['court_source']}) GT={t['gt_labels']} latency={rec['latency_s']}s error={rec['error']}")
print()
print(f'Live run complete: {len(RESULTS)} questions, '
      f"{sum(1 for r in RESULTS if r['error'] is None)}/16 with no model error.")
print('Note: v3 makes up to ~1 (full) + n_clauses + 1 (aux) + n_fired sub-choice calls per question,')
print('so expect a longer run than v1 (188 s) — roughly 10-20 min on CPU.')
'''

CELL8_SRC = r'''# Cell 8 — v3 score, save, download.
# Scoring is the backtest's (exact section-set match, per-section precision /
# recall, forbidden mappings, court correct, escalates correctly) PLUS the
# v3 diagnostics below. Original metrics are kept verbatim so v3 compares
# directly with the v1 baseline (exact 5/16, mean P/R 0.656/0.492, micro
# P/R 0.875/0.368, TP/FP/FN 21/3/36, court 10/16, escalates 11/16).
#
# ESCALATES SCORING CHANGE (plan §3.4, task rule): escalates_live is now the
# typed quantum/court flag — True iff escalations_typed contains kind
# 'quantum' or 'court' — NOT bool(escalations). The plain-text list is kept
# for backward compatibility and two diagnostics are reported alongside so
# the change is visible: escalates_live_any_typed (any typed kind, incl.
# demand) and escalates_live_bool_plain (v1 rule, bool of the plain list).
# KNOWN CONSEQUENCE: H2/H3/H7/H15 read escalates=False under the primary
# rule (no quantum/court reason — see Cell 7 header note 7). H7 is OPEN
# (plan §3.4: escalate_expected=True on a fully answerable birth-certificate
# question with no named reason). H7 escalate_expected is kept EXACTLY as in
# Cell 6 — NOT changed to make the score look better.
#
# FORBIDDEN METRICS: forbidden_before_recheck / forbidden_after_recheck are
# computed exactly as in v1 (from candidates_before_stage2). NEW:
# forbidden_proposed_before_gate (from candidates_before_gate) and
# gated_out_total (+ gated_out_layerB_total). After the HMA 25 Layer A gate
# the option cannot be picked, so forbidden_proposed_before_gate is
# 0-by-construction for the HMA 25 route — the honest gate check is the
# Cell 7 shadow test (printed PASS) + H5/H9 kept_ids byte-identical to v1.
# Prose-level forbidden errors remain NOT MEASURED (no answer prose generated).
import json

FORBIDDEN_RULES = [
    ('hma-13', 'HMA 13/13B with no divorce asked', lambda f: not f['divorce_asked']),
    ('hma-13b', 'HMA 13/13B with no divorce asked', lambda f: not f['divorce_asked']),
    ('hma-24', 'HMA 24 with no proceeding pending', lambda f: not f['proceeding_pending']),
    ('hma-25', 'HMA 25 with no decree', lambda f: not f['decree']),
    ('hma-26', 'HMA 26 with no proceeding pending', lambda f: not f['proceeding_pending']),
]

# Section id -> courts it supports (same mapping as court_for in Cell 7).
SECTION_COURT = {}
for _s in ('hma-24', 'hma-25', 'hma-26', 'hma-27', 'hma-13', 'hma-13b', 'gwa-1890', 'hmga-1956-s6', 'welfare-principle'):
    SECTION_COURT.setdefault(_s, set()).add('Family Court')
for _s in ('bnss-144', 'pwdva-17', 'pwdva-18', 'pwdva-19', 'pwdva-20', 'bns-316'):
    SECTION_COURT.setdefault(_s, set()).add('Magistrate')
SECTION_COURT.setdefault('births-deaths-act-1969', set()).add('Registrar')

EMPTY5 = ['H1', 'H4', 'H8', 'H11', 'H14']


def _pr(pred, gt):
    pred, gt = set(pred), set(gt)
    tp = len(pred & gt)
    prec = tp / len(pred) if pred else (1.0 if not gt else 0.0)
    rec = tp / len(gt) if gt else (1.0 if not pred else 0.0)
    return tp, len(pred) - tp, len(gt) - tp, prec, rec


rows = []
tot_tp = tot_fp = tot_fn = 0
for t, r in zip(TEST_SET, RESULTS):
    pred, gt = r['kept_ids'], t['gt_ids']
    tp, fp, fn, prec, rec = _pr(pred, gt)
    tot_tp += tp; tot_fp += fp; tot_fn += fn
    fb = [rule for s, rule, cond in FORBIDDEN_RULES
          if s in r['candidates_before_stage2'] and cond(t['facts'])]
    fa = [rule for s, rule, cond in FORBIDDEN_RULES
          if s in pred and cond(t['facts'])]
    fbg = [rule for s, rule, cond in FORBIDDEN_RULES
           if s in r.get('candidates_before_gate', []) and cond(t['facts'])]
    court_ok = set(r['court_live']) == set(t['court_expected'])
    kept_gt = set(pred) & set(gt)
    if not t['court_expected']:
        cfk = court_ok
    else:
        cfk = court_ok and all(
            any(c in SECTION_COURT.get(s, set()) for s in kept_gt)
            for c in t['court_expected'])
    typed = r.get('escalations_typed', []) or []
    kinds = {e.get('kind') for e in typed if isinstance(e, dict)}
    esc_live = bool(kinds & {'quantum', 'court'})  # PRIMARY v3 rule
    esc_live_any = bool(kinds)  # diagnostic: any typed kind incl. demand
    esc_live_bool = bool(r.get('escalations'))  # diagnostic: v1 rule
    esc_ok = esc_live == t['escalate_expected']
    rows.append({'id': t['id'], 'exact': set(pred) == set(gt),
                 'precision': round(prec, 3), 'recall': round(rec, 3),
                 'tp': tp, 'fp': fp, 'fn': fn,
                 'pred_labels': [LABEL_BY_ID.get(s, s) for s in pred],
                 'gt_labels': t['gt_labels'],
                 'forbidden_before_recheck': fb, 'forbidden_after_recheck': fa,
                 'forbidden_proposed_before_gate': fbg,
                 'gated_out': r.get('gated_out', []),
                 'court_live': r['court_live'], 'court_expected': t['court_expected'],
                 'court_correct': court_ok,
                 'court_from_kept_ok': cfk,
                 'court_source': r.get('court_source'),
                 'escalates_live': esc_live, 'escalates_expected': t['escalate_expected'],
                 'escalates_correct': esc_ok,
                 'escalates_live_any_typed': esc_live_any,
                 'escalates_live_bool_plain': esc_live_bool,
                 'fired_issues': r.get('fired_issues', []),
                 'fired_clause': r.get('fired_clause', {}),
                 'error': r['error'], 'latency_s': r['latency_s']})

rows_by_id = {x['id']: x for x in rows}
rec_by_id = {r['id']: r for r in RESULTS}
n = len(rows)
n_exact = sum(1 for x in rows if x['exact'])
micro_p = tot_tp / (tot_tp + tot_fp) if (tot_tp + tot_fp) else 0.0
micro_r = tot_tp / (tot_tp + tot_fn) if (tot_tp + tot_fn) else 0.0

# --- empty-5 slice ---
e5 = [x for x in rows if x['id'] in EMPTY5]
e5_exact = sum(1 for x in e5 if x['exact'])
# --- H2 / H12 checks ---
h2_rec = rec_by_id.get('H2', {})
h2_res_fired = 'residence' in h2_rec.get('fired_issues', [])
h2_pwdva_kept = sorted(set(h2_rec.get('kept_ids', [])) & {'pwdva-17', 'pwdva-18', 'pwdva-19'})
h12_rec = rec_by_id.get('H12', {})
h12_row = rows_by_id.get('H12', {})
h12_empty = (h12_rec.get('kept_ids', None) == [] and h12_rec.get('court_live', None) == []
             and h12_row.get('escalates_live') is False)
# --- residence R0 vs R1 comparison ---
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
                     'fired_r0_at_0.15': fired_r0, 'fired_r1': fired_r1})
gated_total = sum(len(x['gated_out']) for x in rows)
gated_layerB_total = sum(1 for x in rows for g in x['gated_out'] if 'Layer B' in str(g))

agg = {
    'notebook_version': 'v3-empty5 (clause-split + aux prompts + per-issue thresholds + R1 residence + HMA25 gate + court fallback + typed escalations)',
    'system': 'Laya 421M (classic ModernBERT checkpoint) + v2 two-stage graph, LIVE in Colab',
    'loader': LOAD_INFO,
    'n_questions': n,
    'exact_section_set_match': f'{n_exact}/{n}',
    'mean_precision': round(sum(x['precision'] for x in rows) / n, 3),
    'mean_recall': round(sum(x['recall'] for x in rows) / n, 3),
    'micro_precision': round(micro_p, 3),
    'micro_recall': round(micro_r, 3),
    'micro_tp_fp_fn': [tot_tp, tot_fp, tot_fn],
    'empty5_exact': f'{e5_exact}/5',
    'empty5_court_correct': f"{sum(1 for x in e5 if x['court_correct'])}/5",
    'empty5_escalates_correct': f"{sum(1 for x in e5 if x['escalates_correct'])}/5",
    'forbidden_before_recheck_total': sum(len(x['forbidden_before_recheck']) for x in rows),
    'forbidden_after_recheck_total': sum(len(x['forbidden_after_recheck']) for x in rows),
    'forbidden_proposed_before_gate_total': sum(len(x['forbidden_proposed_before_gate']) for x in rows),
    'gated_out_total': gated_total,
    'gated_out_layerB_total': gated_layerB_total,
    'court_correct': f"{sum(1 for x in rows if x['court_correct'])}/{n}",
    'court_from_kept_correct': f"{sum(1 for x in rows if x['court_from_kept_ok'])}/{n}",
    'escalates_correct': f"{sum(1 for x in rows if x['escalates_correct'])}/{n}",
    'escalates_correct_any_typed_diagnostic': f"{sum(1 for x in rows if x['escalates_live_any_typed'] == x['escalates_expected'])}/{n}",
    'escalates_correct_bool_plain_diagnostic': f"{sum(1 for x in rows if x['escalates_live_bool_plain'] == x['escalates_expected'])}/{n}",
    'questions_with_model_error': sum(1 for x in rows if x['error']),
    'h2_residence_fired': h2_res_fired,
    'h2_pwdva_17_18_19_kept': h2_pwdva_kept,
    'h12_stays_empty': h12_empty,
    'residence_fired_r0_count_at_0.15': sum(1 for x in res_rows if x['fired_r0_at_0.15']),
    'residence_fired_r1_count': sum(1 for x in res_rows if x['fired_r1']),
    'prose_forbidden_mappings': 'NOT MEASURED — section classification only, no answer prose generated',
    'h7_escalate_ambiguity': 'OPEN — H7 escalate_expected=True kept as-is from Cell 6; under typed quantum/court scoring H7 reads escalates=False (no maintenance, kept non-empty, no court fallback). Resolve the expectation before re-scoring.',
    'walk_ceiling_reference': 'Graph-walk ceiling was 16/16 exact (deterministic walk, NOT live). Do not compare live numbers to it as if it were a baseline.',
    'v1_baseline_reference': 'v1 live: exact 5/16, mean P/R 0.656/0.492, micro P/R 0.875/0.368, TP/FP/FN 21/3/36, court 10/16, escalates 11/16, forbidden-before-recheck 2.',
}
print('=== LIVE Laya + v2 graph — Colab results (v3 empty-5) ===')
for k, v in agg.items():
    print(f'{k}: {v}')
print()
print(f"{'ID':4s} {'exact':>5s} {'prec':>5s} {'rec':>5s} {'fb':>2s} {'fbg':>3s} {'court':>5s} {'esc':>3s}  predicted sections")
for x in rows:
    print(f"{x['id']:4s} {str(x['exact']):>5s} {x['precision']:5.3f} {x['recall']:5.3f} "
          f"{len(x['forbidden_before_recheck']):2d} {len(x['forbidden_proposed_before_gate']):3d} {str(x['court_correct']):>5s} {str(x['escalates_correct']):>3s}  "
          f"{', '.join(x['pred_labels']) if x['pred_labels'] else '(none)'}")
print()
print('fb = forbidden BEFORE Stage 2 recheck (v1 metric). fbg = forbidden PROPOSED before the HMA25 gate.')
print('court = court correct, esc = escalates correctly (typed quantum/court flag).')
print()
print('=== Empty-5 detail (H1/H4/H8/H11/H14) ===')
print(f"{'ID':4s} {'exact':>5s} {'prec':>5s} {'rec':>5s} {'TP':>2s} {'FP':>2s} {'FN':>2s} {'court':>5s} {'esc':>3s}  fired issues / fired clauses")
for x in e5:
    fc = x['fired_clause'] or {}
    fc_s = '; '.join(f"{k}={str(v)[:55]}" for k, v in fc.items() if k in x['fired_issues'])
    print(f"{x['id']:4s} {str(x['exact']):>5s} {x['precision']:5.3f} {x['recall']:5.3f} "
          f"{x['tp']:2d} {x['fp']:2d} {x['fn']:2d} {str(x['court_correct']):>5s} {str(x['escalates_correct']):>3s}  "
          f"{', '.join(x['fired_issues']) if x['fired_issues'] else '(none)'} | {fc_s if fc_s else '(no fired clause)'}")
print()
print('=== Residence R0 vs R1 (threshold 0.15 for the comparison) ===')
print(f"{'ID':4s} {'R0 full':>7s} {'R1 full':>7s} {'R0 clmax':>8s} {'R1 clmax':>8s} {'fire R0':>7s} {'fire R1':>7s}")
for x in res_rows:
    def _f(v):
        return f'{v:.4f}' if v is not None else '  None'
    print(f"{x['id']:4s} {_f(x['r0_full']):>7s} {_f(x['r1_full']):>7s} {_f(x['r0_clause_max']):>8s} {_f(x['r1_clause_max']):>8s} "
          f"{str(x['fired_r0_at_0.15']):>7s} {str(x['fired_r1']):>7s}")
print()
print(f"H2 check: residence fired={h2_res_fired} (v1: True at 0.8247), PWDVA 17/18/19 kept={h2_pwdva_kept} (v1: all three — target: none).")
print(f"H12 check: stays empty={h12_empty} (kept=[], court=[], escalates=False). Must stay True.")
print(f"Gated out total={gated_total} (Layer B picks blocked={gated_layerB_total}); forbidden proposed before gate={agg['forbidden_proposed_before_gate_total']} (v1 forbidden-before-recheck was 2).")

out = {'aggregate': agg, 'per_question': rows, 'residence_r0_vs_r1': res_rows,
       'empty5': e5, 'raw_live_runs': RESULTS, 'load_info': LOAD_INFO}
with open('live-laya-colab-results-v3-empty5.json', 'w') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
md = ['# Live Laya inference test — Colab run v3-empty5 (Laya 421M + v2 graph)',
      '',
      '## Aggregate (live, measured in Colab)',
      '']
for k, v in agg.items():
    md.append(f'- **{k}**: {v}')
md += ['', '## Per-question', '',
       '| ID | Exact | Precision | Recall | Forbidden (before recheck) | Forbidden (proposed before gate) | Court | Escalates | Predicted |',
       '|----|-------|-----------|--------|----------------------------|----------------------------------|-------|-----------|-----------|']
for x in rows:
    md.append(f"| {x['id']} | {x['exact']} | {x['precision']} | {x['recall']} | "
              f"{len(x['forbidden_before_recheck'])} | {len(x['forbidden_proposed_before_gate'])} | {x['court_correct']} | {x['escalates_correct']} | "
              f"{', '.join(x['pred_labels']) if x['pred_labels'] else '(none)'} |")
md += ['', '## Empty-5 detail (H1/H4/H8/H11/H14)', '',
       '| ID | Exact | Precision | Recall | TP | FP | FN | Court | Escalates | Fired issues |',
       '|----|-------|-----------|--------|----|----|----|-------|-----------|--------------|']
for x in e5:
    md.append(f"| {x['id']} | {x['exact']} | {x['precision']} | {x['recall']} | {x['tp']} | {x['fp']} | {x['fn']} | "
              f"{x['court_correct']} | {x['escalates_correct']} | {', '.join(x['fired_issues']) if x['fired_issues'] else '(none)'} |")
md += ['', '## Residence R0 vs R1', '',
       '| ID | R0 full | R1 full | R0 clause-max | R1 clause-max | Fired R0 (0.15) | Fired R1 |',
       '|----|---------|---------|---------------|---------------|-----------------|----------|']
for x in res_rows:
    md.append(f"| {x['id']} | {x['r0_full']} | {x['r1_full']} | {x['r0_clause_max']} | {x['r1_clause_max']} | {x['fired_r0_at_0.15']} | {x['fired_r1']} |")
md += ['', f"H2 check: residence fired={h2_res_fired}, PWDVA 17/18/19 kept={h2_pwdva_kept}.",
       f"H12 check: stays empty={h12_empty}.",
       '',
       'Escalates are scored from the typed quantum/court flag, not from bool(escalations) — see Cell 8 header.',
       'H7 escalate ambiguity is OPEN (see aggregate).',
       'Forbidden-after-recheck is 0 by construction when Stage 2 ran (Stage 2 drops those sections); '
       'quote forbidden-before-recheck / forbidden-proposed-before-gate as the live error counts.',
       'Prose-level forbidden mappings (Rajnesh / Satish / tenancy label) are NOT MEASURED here.',
       '']
with open('live-laya-colab-results-v3-empty5.md', 'w') as f:
    f.write('\n'.join(md))
print('saved live-laya-colab-results-v3-empty5.json and live-laya-colab-results-v3-empty5.md')
from google.colab import files as _cf
_cf.download('live-laya-colab-results-v3-empty5.json')
_cf.download('live-laya-colab-results-v3-empty5.md')
print('Downloaded both v3 result files. Send them back to Muse to record the live score.')
'''


# ---------------------------------------------------------------------------
# Cell 6 fix: JSON literals -> Python literals, nothing else.
# ---------------------------------------------------------------------------
_BOOL_NULL_RE = re.compile(r":\s*(false|true|null)\b")
_LITERAL_MAP = {"false": "False", "true": "True", "null": "None"}


def fix_cell6_source(lines):
    """Replace ': false' / ': true' / ': null' with Python literals.

    Returns (new_lines, changed_line_numbers_1based, n_replacements).
    Only the TEST_SET facts dicts use these tokens in Cell 6; anything else
    matching is reported by the caller so it can be inspected.
    """
    new_lines = []
    changed = []
    n_rep = 0
    for i, line in enumerate(lines, start=1):
        def _sub(m):
            nonlocal n_rep
            n_rep += 1
            return ": " + _LITERAL_MAP[m.group(1)]
        new_line = _BOOL_NULL_RE.sub(_sub, line)
        if new_line != line:
            changed.append(i)
        new_lines.append(new_line)
    return new_lines, changed, n_rep


def build():
    with open(ORIG, "r", encoding="utf-8") as f:
        nb = json.load(f)
    cells = nb["cells"]
    assert len(cells) == 9, f"original notebook has {len(cells)} cells, expected 9"

    # Cells 0-5: copied untouched (same objects).
    # Cell 6: literals fix only.
    c6_lines = list(cells[6]["source"])
    c6_new, c6_changed, c6_nrep = fix_cell6_source(c6_lines)
    assert c6_nrep > 0, "no JSON literals found in Cell 6 — fix did not apply"
    assert not re.search(r"\b(false|true|null)\b", "".join(c6_new)), (
        "JSON literals remain in Cell 6 after fix")
    cells[6]["source"] = c6_new

    # Cells 7 and 8: full replacement.
    cells[7]["source"] = CELL7_SRC.splitlines(keepends=True)
    cells[8]["source"] = CELL8_SRC.splitlines(keepends=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {OUT}")
    print(f"Cell 6: {c6_nrep} literal replacements on lines {c6_changed}")
    print("Cells 0-5: untouched. Cells 7-8: replaced with v3 sources.")
    return OUT


if __name__ == "__main__":
    build()
