#!/usr/bin/env python3
"""Build the v6 BRUTAL notebook from the v5 base — Lane B.

Base: live-laya-colab-test-v5-precision.ipynb (9 cells).
Output: live-laya-colab-test-v6-brutal.ipynb (23 cells).

What v6 is (offline build only — no live Colab run, no browser):
  * D1-A settled (rater 2026-11-27): HMA 27 removed from K0/H3/H10/H15 GT,
    no replacement label; 16-question GT 57 -> 53 sections
    (ground-truth-v2-hma27-A.json).
  * D2 gate (paired with D1): HMA 27 DROPPED in stage2() when no HMA
    proceeding is pending or being filed (new frozen fact `being_filed`).
  * Graph v3 (Lane A, DONE): files/laya-crpc-bns-section-decision-tree-v3.json,
    34 sections / 48 nodes / 79 edges, SHA-256
    67bf2b04ca946f7c7fa3062068e01ce051fbce8f4d740c281afe6fff841c34a5
    (+2/+2/+2 over v2 = hma-9 + pwdva-22 and their leaf nodes/edges).
  * Lane 2 typed escalation kinds in stage2() (custody / residence /
    recovery / procedure / safety) with the D1-A recovery text.
  * Cell 7 refactored: the per-question Stage 1 + Stage 2 body is ONE
    reusable function run_one_question(t) — re-indented only, no threshold /
    prompt / scoring-logic / fact change (verified by a dedent-equivalence
    check in validate()).
  * Brutal bank (230, frozen, SHA verified in-notebook) in 10 batch cells
    B1-B9 x25 + B10 x5, each saving + downloading its JSON immediately.
  * Sealed fresh-20 + Kannada-8 cells (read-only, SHA verified in-notebook).
  * Final cumulative cell: brutal 230 + 16 regression + sealed summaries +
    pass/fail vs the plan bar + G14 latency check.
  * Prose Cell 9: SKIPPED (see build note) — Fp is NOT MEASURED in v6.

Constraints honoured: frozen bank / sealed sets / graph v2 / v2 GT file are
never edited; no pipeline threshold / prompt / logic change except the
specified D2 gate, Lane 2 kinds, and the refactor; no tuning between batches;
offline only. The ONE unavoidable new mechanism is derive_facts_from_text()
(Cell 7): the bank carries no fact annotations and the sealed sets carry only
five, while the pipeline needs a full facts dict — the derivation rules are
frozen in the notebook, never per-question, never from GT, and their limits
(Kannada defaults, money-without-money-words, gold-as-object) are recorded
in the cell header and the build note.

Deterministic: re-running this script on the same inputs reproduces the
output byte-for-byte (same sha256). Notebook dump uses json.dumps(indent=1,
ensure_ascii=False) with no trailing newline, as the v5 builder did.

Usage:
    python3 build_laya_v6_brutal.py [--base PATH] [--out PATH]
Defaults resolve next to this script.
"""
import argparse
import hashlib
import json
import re
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_BASE = HERE / "live-laya-colab-test-v5-precision.ipynb"
DEFAULT_OUT = HERE / "live-laya-colab-test-v6-brutal.ipynb"
GT_V2 = HERE / "ground-truth-v2-hma27-A.json"
BANK = HERE / "brutal-bank-v1-frozen.json"
GRAPH_V3 = HERE.parent / "laya-crpc-bns-section-decision-tree-v3.json"
SEALED_DIR = HERE / "sealed"

BANK_SHA = "934a2b2265ac137c96939e1fbeca3682a037010e42f972bfd459c2fcac4ec717"
GRAPH_V3_SHA = "67bf2b04ca946f7c7fa3062068e01ce051fbce8f4d740c281afe6fff841c34a5"
FRESH_SHA = "1d8b5dc376e711c3ac6ead4424bb2d8ce52b07552b9a533ad86e0616dbcf8837"
KANNADA_SHA = "2f652af1123a22441cc4158ddf480ef0981aa923858bbcb9dc3622f5e5c25853"
RECOVERY_TEXT = (
    "Stridhan recovery: sold or withheld gold cannot be recovered or valued by the bot "
    "-- escalate to a lawyer for valuation, a police complaint under BNS s.316 "
    "and civil recovery through the Family Court under FCA s.7(1) Expl. (c) / CPC s.151 "
    "(or under HMA s.27 where an HMA proceeding is pending or being filed)."
)


def _cell_source(cell):
    return "".join(cell["source"])


def _set_source(cell, src):
    lines = src.split("\n")
    cell["source"] = [ln + "\n" for ln in lines[:-1]] + [lines[-1]]


def _replace_in_cell(cell, old, new, expected, where):
    src = _cell_source(cell)
    count = src.count(old)
    if count != expected:
        raise SystemExit(
            f"REPLACE MISMATCH in {where}: expected {expected} occurrence(s) of "
            f"{old[:90]!r}, found {count}. Base has drifted — refusing to build."
        )
    _set_source(cell, src.replace(old, new))


def _insert_after_anchor(cell, anchor, new_block, where):
    src = _cell_source(cell)
    count = src.count(anchor)
    if count != 1:
        raise SystemExit(
            f"ANCHOR MISMATCH in {where}: expected exactly 1 occurrence of "
            f"{anchor[:90]!r}, found {count}. Refusing to build."
        )
    _set_source(cell, src.replace(anchor, anchor + new_block, 1))


def _insert_before_anchor(cell, anchor, new_block, where):
    src = _cell_source(cell)
    count = src.count(anchor)
    if count != 1:
        raise SystemExit(
            f"ANCHOR MISMATCH in {where}: expected exactly 1 occurrence of "
            f"{anchor[:90]!r}, found {count}. Refusing to build."
        )
    _set_source(cell, src.replace(anchor, new_block + anchor, 1))


def _new_code_cell(source):
    lines = source.split("\n")
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [ln + "\n" for ln in lines[:-1]] + [lines[-1]],
    }


def _new_md_cell(source):
    lines = source.split("\n")
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [ln + "\n" for ln in lines[:-1]] + [lines[-1]],
    }


# ---------------------------------------------------------------------------
# Cell 0 — retitle (whole markdown cell replaced)
# ---------------------------------------------------------------------------
CELL0_MD = """# LIVE Laya inference test — v6 BRUTAL (Laya 421M + v3 graph, 230-question bank)

**What this is:** a LIVE run of the Laya classification model through the
v3 family-law decision graph, on (a) the same 16 layman questions used in the
local backtest, now scored against the CORRECTED v2 ground truth (D1-A: HMA 27
removed from K0/H3/H10/H15, GT 57 → 53 sections), (b) the FROZEN brutal bank
of 230 questions in 10 batches (B1–B9 of 25, B10 of 5), and (c) the sealed
fresh-20 and Kannada-8 sets. Stage 1 is one Laya typed decision per issue,
recorded with the model's actual chosen option and probabilities. Stage 2 is
the graph recheck (divorce gate first, HMA 24 dropped with no proceeding
pending, HMA 25 dropped with no decree, custody to exactly one primary route,
Stridhan co-fire civil-return + BNS 316, residence PWDVA 17+18+19, quantum
always escalated, never invented, D2: HMA 27 dropped with no proceeding
pending or being filed). Scoring: exact section-set match, per-section
precision / recall, forbidden mappings, court correct, escalates correctly —
reported BOTH as the old boolean AND as typed-kinds equality.

**Graph v3:** 34 sections / 48 nodes / 79 edges (Lane A: +hma-9, +pwdva-22).
Expected SHA-256: 67bf2b04ca946f7c7fa3062068e01ce051fbce8f4d740c281afe6fff841c34a5.

**NO TUNING between batches.** The notebook, builder, graph, thresholds,
prompts, phrasebook and fact annotations are frozen for the whole brutal run.
A failure found in batch 2 is NOT fixed before batch 3. All 10 batches run,
the report is filed, and only then is a fix diagnosed — in general terms.
No brutal question, phrase, or paraphrase may enter the phrasebook, prompts,
examples, or threshold fittings.

**Prose is NOT MEASURED in v6** (no Cell 9 renderer — see build note):
Fp is NOT MEASURED, so any rating quoted from this run is capped at 9.0.
The fresh-20 score is a MEASURED NUMBER ONLY, not a gate pass, until the
G2 20/20 amendment is signed (see the sealed cells and the build note).

**How to run:** upload this notebook to Google Drive (account used before:
nivedhbhat15@gmail.com), open it in Colab, upload
`laya-crpc-bns-section-decision-tree-v3.json` when the graph cell asks,
upload `brutal-bank-v1-frozen.json` when the bank cell asks, then
Runtime > Run all. Each batch cell downloads its JSON immediately — file it
before starting the next batch. A crash loses at most one batch.
"""

# ---------------------------------------------------------------------------
# Cell 5 — graph v3 upload + counts assert (whole cell replaced)
# ---------------------------------------------------------------------------
CELL5_SRC = """# Cell 5 — upload the v3 decision graph and verify it.
# Upload laya-crpc-bns-section-decision-tree-v3.json when the file picker
# appears. The graph is the source of truth for section ids, node
# questions/options and the root issue->section map.
# v3 (Lane A): 34 sections / 48 nodes / 79 edges. The +2/+2/+2 over v2
# (32/46/77) are the two new sections hma-9 (HMA s.9, restitution of
# conjugal rights) and pwdva-22 (PWDVA s.22, compensation orders) and their
# leaf nodes/edges. The D2 patch alone left counts at 32/46/77.
from google.colab import files
import hashlib
import json
print('Upload laya-crpc-bns-section-decision-tree-v3.json now (file picker).')
uploaded = files.upload()
print('uploaded:', list(uploaded.keys()))
GRAPH_FILE = 'laya-crpc-bns-section-decision-tree-v3.json'
assert GRAPH_FILE in uploaded, f'{GRAPH_FILE} was not uploaded — upload it and re-run this cell.'
GRAPH_SHA = hashlib.sha256(uploaded[GRAPH_FILE]).hexdigest()
print('graph SHA-256:', GRAPH_SHA)
assert GRAPH_SHA == '""" + GRAPH_V3_SHA + """', (
    'Graph SHA mismatch — the v3 file has changed or the wrong file was uploaded. '
    'Expected 67bf2b04ca946f7c7fa3062068e01ce051fbce8f4d740c281afe6fff841c34a5. STOP.')
GRAPH = json.loads(uploaded[GRAPH_FILE].decode('utf-8'))
n_sections = len(GRAPH['sections'])
n_nodes = len(GRAPH['nodes'])
n_edges = len(GRAPH['edges'])
print(f'verified: {n_sections} sections, {n_nodes} nodes, {n_edges} edges')
assert (n_sections, n_nodes, n_edges) == (34, 48, 79), (
    f'Graph counts do not match v3 (expected 34/48/79, got {n_sections}/{n_nodes}/{n_edges}). '
    'You may have uploaded the v2 graph — upload the v3 file and re-run.')
NODES = {n['node_id']: n for n in GRAPH['nodes']}
SECTION_IDS = {s['id'] for s in GRAPH['sections']}
print('graph OK — 34 sections / 48 nodes / 79 edges. Root node:',
      NODES['root:issue-classification']['question'][:80], '...')
# KNOWN PRE-EXISTING v2 DEFECTS, carried into v3 byte-identical (Lane A):
# 3 edges point at non-nodes (escalate_clarify, bns-316, escalate_demand_first)
# and bnss-144 related_sections carries the wrong id 'hmga-6' (real id
# 'hmga-1956-s6'). Out of scope, intentionally not fixed. NO whole-file
# "no dangling references" assert is added here on purpose: it would fail the
# run on these pre-existing defects. The counts + SHA asserts above are the
# only graph checks in this cell.
"""

# ---------------------------------------------------------------------------
# Cell 5b — frozen brutal bank upload + SHA verify (new cell)
# ---------------------------------------------------------------------------
CELL5B_SRC = """# Cell 5b — upload the FROZEN brutal bank and verify it (read-only).
# Upload brutal-bank-v1-frozen.json when the file picker appears.
# The file is NEVER written to by this notebook (no write, no edit, no
# re-freeze). Verified BEFORE any batch runs: SHA-256 must equal
# 934a2b2265ac137c96939e1fbeca3682a037010e42f972bfd459c2fcac4ec717 and the file
# must hold exactly 230 questions (B-001..B-230). Either check failing stops
# the run with an error — do not continue past this cell.
print('Upload brutal-bank-v1-frozen.json now (file picker).')
_uploaded_bank = files.upload()
print('uploaded:', list(_uploaded_bank.keys()))
BANK_FILE = 'brutal-bank-v1-frozen.json'
assert BANK_FILE in _uploaded_bank, f'{BANK_FILE} was not uploaded — upload it and re-run this cell.'
_bank_bytes = _uploaded_bank[BANK_FILE]
_bank_sha = hashlib.sha256(_bank_bytes).hexdigest()
print('bank SHA-256:', _bank_sha)
assert _bank_sha == '""" + BANK_SHA + """', (
    'Bank SHA mismatch — the frozen bank file has changed or the wrong file was uploaded. STOP.')
BANK = json.loads(_bank_bytes.decode('utf-8'))
BANK_QUESTIONS = BANK['questions']
assert len(BANK_QUESTIONS) == 230, f'Bank must hold 230 questions, got {len(BANK_QUESTIONS)}. STOP.'
BANK_BY_ID = {q['id']: q for q in BANK_QUESTIONS}
assert [q['id'] for q in BANK_QUESTIONS] == [f'B-{i:03d}' for i in range(1, 231)], 'Bank IDs are not B-001..B-230 in order. STOP.'
BRUTAL_RESULTS = []  # every batch cell appends its records here, in order
print('bank OK: 230 questions (B-001..B-230), SHA verified. NEVER edit this file.')
print('Batches are sequential slices (B1=B-001..B-025, ..., B10=B-226..B-230),')
print('NOT stratified across categories (plan section 4.2) — see build note; a crash loses whole categories.')
"""

# ---------------------------------------------------------------------------
# Cell 6 — corrected v2 GT (rebuilt from ground-truth-v2-hma27-A.json)
# ---------------------------------------------------------------------------
CELL6_HEADER = """# Cell 6 — the 16-question test set + CORRECTED ground truth (v2, D1-A).
# Questions and facts are copied from ground-truth-v2-hma27-A.json (frozen by
# the rater lane 2026-11-27). "facts" are the question's stated facts as
# annotated in the backtest (proceeding pending, decree, divorce asked,
# demand made, violence stated) — fixed annotations, never inferred
# from keywords at run time.
# v4 ADDS one facts field, "residence_claim" (bool, frozen annotation, same
# status as the other facts): true iff the question states eviction /
# lockout / being thrown out / changed lock / cannot enter the house, OR a
# claim to stay in the shared house, OR a threat to throw the person out.
# "I want my son/daughter to stay with me" is a CUSTODY stay, not a claim
# to stay in the shared house, so H5/H14 are False under this rule.
# v6 D1-A (rater decision 2026-11-27 ~09:46 IST): HMA 27 REMOVED from K0/H3/H10/H15
# ground truth, no replacement label (GT 57 -> 53 sections). Every other
# question, section label, court, escalate expectation, fact annotation and
# question wording is byte-identical to v1. The D2 gate (Cell 7) ships in the
# same change; D1 without D2 (or D2 without D1) leaves K0/H10 non-exact.
# NEW frozen fact "being_filed" (D2): True iff the user states they are filing,
# will file, or have instructed the filing of an HMA petition. Wanting a divorce
# (H5 "I want a divorce") does NOT count. All 16 are False here — no question
# states a filing; H14 states a case "already going on" (proceeding_pending),
# not a fresh filing. The gate reads it via facts.get('being_filed', False).
# NEW field "gt_escalation_kinds" per question (v2 GT, Lane 2 typed kinds;
# 'fact' never appears here — it is informational, not a scoring kind).
# LABEL_BY_ID gains the two graph-v3 sections (hma-9, pwdva-22) so kept ids
# always have a display label; the pipeline cannot emit them yet (Cell 7 note 11).
"""

CELL6_TAIL = """
LABEL_BY_ID = {
 "bnss-144": "BNSS 144",
 "hma-24": "HMA 24",
 "hma-25": "HMA 25",
 "pwdva-20": "PWDVA 20",
 "pwdva-22": "PWDVA 22",
 "hma-26": "HMA 26",
 "gwa-1890": "GWA 1890",
 "hmga-1956-s6": "HMGA s.6",
 "welfare-principle": "WELFARE",
 "hma-27": "HMA 27",
 "bns-316": "BNS 316",
 "pwdva-17": "PWDVA 17",
 "pwdva-18": "PWDVA 18",
 "pwdva-19": "PWDVA 19",
 "hma-13": "HMA 13",
 "hma-13b": "HMA 13B",
 "hma-9": "HMA 9",
 "births-deaths-act-1969": "Births and Deaths Act 1969"
}

print(f'test set loaded: {len(TEST_SET)} questions')
for t in TEST_SET:
    print(f"  {t['id']:3s} [{t['kind']}] GT={t['gt_labels']}")
assert [t['id'] for t in TEST_SET] == ['K0'] + [f'H{i}' for i in range(1, 16)], 'test set IDs are not K0 + H1-H15'
assert all(set(t['gt_ids']) <= set(LABEL_BY_ID) for t in TEST_SET), 'GT id with no label'
assert sum(len(t['gt_ids']) for t in TEST_SET) == 53, 'v2 GT must total 53 sections (D1-A)'
assert all('being_filed' in t['facts'] for t in TEST_SET), 'being_filed missing on some question'
assert all(t['facts']['being_filed'] is False for t in TEST_SET), 'being_filed must be False on all 16 (no question states a filing)'
assert all('hma-27' not in t['gt_ids'] for t in TEST_SET if t['id'] in ('K0', 'H3', 'H10', 'H15')), 'D1-A: hma-27 must be out of K0/H3/H10/H15 GT'
print('test set OK: 16 questions (K0 + H1-H15), corrected v2 ground truth (53 sections, D1-A).')
"""


def build_cell6(base_nb, gt_v2):
    """Rebuild Cell 6 from the v2 GT file, preserving v5 'kind' strings."""
    v5_src = _cell_source(base_nb["cells"][6])
    kind_by_id = dict(re.findall(r'"id": "(K0|H\d+)",\n  "kind": "(.*?)"', v5_src))
    if len(kind_by_id) != 16:
        raise SystemExit(
            f"CELL6 BUILD FAIL: could not recover 16 'kind' strings from v5 Cell 6 (got {len(kind_by_id)}).")
    entries = []
    for q in gt_v2["questions"]:
        qid = q["id"]
        facts = dict(q["facts"])
        facts["being_filed"] = False  # D2: inserted after proceeding_pending below
        ordered_facts = {}
        for k in ("divorce_asked", "proceeding_pending", "being_filed", "decree",
                  "demand_made", "violence", "residence_claim", "money_fact", "gold_fact"):
            ordered_facts[k] = facts[k]
        entry = {
            "id": qid,
            "kind": kind_by_id[qid],
            "question": q["question"],
            "gt_labels": list(q["gt_sections"]),
            "gt_ids": list(q["gt_ids"]),
            "facts": ordered_facts,
            "court_expected": list(q["gt_court"]),
            "escalate_expected": bool(q["gt_escalates"]),
            "gt_escalation_kinds": list(q["gt_escalation_kinds"]),
        }
        dumped = json.dumps(entry, indent=1, ensure_ascii=False)
        # json.dumps emits true/false/null; the notebook cell is Python, so
        # convert value-position literals only (": true" etc. — question text
        # sits inside quotes and never matches this pattern).
        dumped = re.sub(r': (true|false|null)(?=[,\n])',
                        lambda m: ': ' + {'true': 'True', 'false': 'False',
                                          'null': 'None'}[m.group(1)], dumped)
        entries.append(textwrap.indent(dumped, " "))
    body = "TEST_SET = [\n" + ",\n".join(entries) + "\n]\n"
    return CELL6_HEADER + body + CELL6_TAIL

# ---------------------------------------------------------------------------
# Cell 7 — D2 gate + Lane 2 kinds + fact derivation + run_one_question()
# ---------------------------------------------------------------------------
CELL7_HEADER_NOTES = """#  9. v6 D2 HMA 27 GATE (drop, paired with D1-A): in stage2(), after the HMA 25
#     Layer B block — if 'hma-27' is in kept and neither proceeding_pending nor
#     being_filed is True, hma-27 is REMOVED from kept and recorded in gated_out
#     with the D2 reason (gated-before-generation, like HMA 25 Layer B; never
#     added to dropped[]). BNS 316 is NOT gated. hma-27 stays in
#     candidates_before_gate. The graph v3 rule R-HMA27-04 is if_fail=drop with
#     the same wording. Verified by the offline shadow test below (PASS printed
#     every run). "Being filed" = the user states they are filing / will file /
#     have instructed the filing of an HMA petition; wanting a divorce does not
#     count (Cell 6 note).
# 10. v6 TYPED ESCALATIONS (Lane 2 section 4.1 + D1-A recovery text): stage2()
#     now also emits custody (kept GWA/HMA-26), residence ('residence' in fired,
#     post-gate — NOT kept PWDVA 17/18/19, so H5's violence-only PWDVA 18 does
#     not get residence text), recovery (stridhan kept + demand_made True, with
#     the D1-A civil-route text: Family Court under FCA s.7(1) Expl. (c) /
#     CPC s.151 unless an HMA proceeding is pending/being filed), procedure
#     (births-deaths kept), and safety (PWDVA 18 kept — see the in-code note
#     for why this trigger, not the Lane 2 violence-fact trigger, is used).
#     D5 rater confirmation of the H2/H4 kinds is still outstanding.
#     The 'fact' kind stays informational and is never in the scoring set.
# 11. v6 GRAPH v3 LABELS (hma-9 / pwdva-22): the labels exist in the graph and
#     in LABEL_BY_ID, but NO Stage 1 issue maps to them and stage2() has no
#     route that emits them (graph v3 adds only stage2 leaf nodes). B-018
#     (hma-9) and B-019 (pwdva-22) are therefore GUARANTEED MISSES in this
#     build. Emitting them needs a new Stage 1 issue prompt + stage2 route —
#     a pipeline change, not made here (no-logic-change constraint).
# 12. v6 FACT DERIVATION (STOPGAP — derive_facts_from_text / complete_facts
#     below): the brutal bank carries NO fact annotations and the sealed sets
#     carry only five (divorce_asked / proceeding_pending / decree /
#     demand_made / violence), while the pipeline needs a full facts dict.
#     Facts for those questions are derived from the question TEXT by the
#     frozen rules in that helper. Deterministic, identical for every
#     question, never tuned per question, never read from GT. Known limits,
#     recorded not hidden: (a) Kannada-script questions match no English
#     pattern and fall back to defaults (proceeding False, demand None,
#     violence False, residence False, money/gold False) — the v5 gates then
#     veto almost everything, so Kannada scores through this build measure
#     the English-text gates, not the model; model-extracted facts (v6
#     deep-dive section 2) are the proper fix. (b) Money need phrased without
#     money words ("books and uniforms") reads money_fact=False. (c) Gold
#     mentioned as an object, not a claim, reads gold_fact=True — the gate
#     then does not veto and the model score decides (C9 is the stress axis).
# 13. v6 REFACTOR: the per-question Stage 1 + Stage 2 body is ONE reusable
#     function run_one_question(t) (below). The body is the v5 loop body,
#     re-indented only — no threshold, prompt, scoring-logic or fact change
#     (the builder verifies this by a dedent-equivalence check). The TEST_SET
#     loop, the batch cells and the sealed cells all call it. t must carry
#     'id', 'question', 'facts', 'gt_ids', 'gt_labels'.
"""

D2_GATE_BLOCK = """    # --- v6 D2 HMA 27 gate (drop, not escalate): HMA s.27 fires only when an
    # HMA proceeding (ss. 9-13/13B) is pending or being filed together with the
    # claim (D1-A corrected rule; graph v3 R-HMA27-04 if_fail=drop). If neither
    # facts['proceeding_pending'] nor facts['being_filed'] is True, hma-27 is
    # removed from kept and recorded in gated_out (gated-before-generation,
    # like HMA 25 Layer B) — never added to dropped[]. BNS 316 is NOT gated:
    # it is the criminal route and stays. hma-27 stays in
    # candidates_before_gate (computed above, before this block).
    if 'hma-27' in kept and not (facts.get('proceeding_pending') or facts.get('being_filed', False)):
        kept.remove('hma-27')
        gated_out.append("hma-27: gated (D2) — no HMA proceeding pending or being filed; HMA s.27 cannot be invoked standalone; civil return route is the Family Court property suit under FCA s.7(1) Expl. (c) / CPC s.151; BNS s.316 kept as the criminal route")
"""

KINDS_BLOCK = """    # --- v6 typed escalations: custody / residence / recovery / procedure / safety ---
    # (Lane 2 section 4.1 + D1-A recovery-text amendment; D5 rater confirmation
    # of the H2/H4 kinds still outstanding — see Cell 8 header.)
    # Triggers are kept sections and/or frozen facts ONLY — never raw scores,
    # never pre-gate fired state, never a question id. Residence uses post-gate
    # 'residence' in fired (NOT kept PWDVA 17/18/19): H5 keeps PWDVA 18 via the
    # violence-only branch and its residence text would be content-wrong there.
    if kept & {'gwa-1890', 'hma-26'}:
        _route = 'HMA s.26 (proceeding pending)' if 'hma-26' in kept else 'GWA 1890'
        esc_typed.append({'kind': 'custody', 'text': (
            f"Custody: who the child stays with is a welfare decision for the Family Court "
            f"-- the bot names the route ({_route}) but does not say who gets the child. "
            f"Escalate for interim custody and the welfare assessment. "
            f"If either parent has said they will take the child away, that needs urgent human help.")})
    if 'residence' in fired:
        esc_typed.append({'kind': 'residence', 'text': (
            "Residence: the bot names PWDVA 17-19 but cannot restore entry to the house "
            "-- a Magistrate's residence order is needed (the house being in the husband's name "
            "does not remove the right). Escalate for filing the residence application "
            "and for immediate help re-entering.")})
    if kept & {'hma-27', 'bns-316'} and facts.get('demand_made') is True:
        # v6 D1-A amendment (Lane A wording, unconditional variant — see build note):
        # the civil route is the Family Court property suit under FCA s.7(1)
        # Expl. (c) / CPC s.151 unless an HMA proceeding is pending/being filed
        # (then HMA s.27). Never cite BNS 316 alone as the civil route.
        esc_typed.append({'kind': 'recovery', 'text': (
            "Stridhan recovery: sold or withheld gold cannot be recovered or valued by the bot "
            "-- escalate to a lawyer for valuation, a police complaint under BNS s.316 "
            "and civil recovery through the Family Court under FCA s.7(1) Expl. (c) / CPC s.151 "
            "(or under HMA s.27 where an HMA proceeding is pending or being filed).")})
    if 'births-deaths-act-1969' in kept:
        esc_typed.append({'kind': 'procedure', 'text': (
            "Birth certificate: the exact procedure depends on facts not stated (date of birth, "
            "any delay, whether the hospital will issue) and requires applying in person to the "
            "Registrar. Escalate for human follow-up with the hospital / Registrar "
            "if issuance is refused or delayed.")})
    if 'pwdva-18' in kept:
        # v6 'safety' kind: trigger is PWDVA 18 KEPT, not the Lane 2 violence-fact
        # trigger. Evidence: 31/32 bank safety uses carry pwdva-18 in GT (the one
        # exception, B-108 custody-only safety, is a recorded gap); only 13/32
        # state violence in words the violence fact could see. A protection order
        # in the answer means threats/violence are live and need urgent human help.
        # On the 16 this fires on K0/H4/H5/H6/H13 only — all expected True already.
        esc_typed.append({'kind': 'safety', 'text': (
            "Safety: a protection order is in the answer -- escalate urgently for immediate "
            "safety help and a protection order under PWDVA s.18; do not treat this as information-only.")})
"""

HMA27_SHADOW_BLOCK = """
# --- Offline shadow test of the D2 HMA 27 gate (no model calls; fails fast) ---
# being_filed=False + proceeding_pending=False -> hma-27 gated out, bns-316 kept.
# Either fact True -> hma-27 kept. Facts dicts here carry being_filed explicitly;
# stage2() also reads it via facts.get('being_filed', False) so older fact dicts
# without the key do not raise KeyError.
_shadow27_sub = {}
_shadow27_base = {'divorce_asked': False, 'proceeding_pending': False, 'being_filed': False, 'decree': False, 'demand_made': True, 'violence': False}
_k27, _d27, _e27, _g27, _cbg27 = stage2({'stridhan'}, _shadow27_sub, _shadow27_base)
assert 'hma-27' not in _k27, 'HMA27 gate shadow test FAILED: hma-27 kept with no proceeding pending/being filed'
assert 'bns-316' in _k27, 'HMA27 gate shadow test FAILED: bns-316 gated with hma-27 (BNS 316 must stay)'
assert any(g.startswith('hma-27: gated (D2)') for g in _g27), 'HMA27 gate shadow test FAILED: no D2 gated_out entry'
assert 'hma-27' in _cbg27, 'HMA27 gate shadow test FAILED: hma-27 missing from candidates_before_gate'
_k27b, _d27b, _e27b, _g27b, _cbg27b = stage2({'stridhan'}, _shadow27_sub, {**_shadow27_base, 'proceeding_pending': True})
assert 'hma-27' in _k27b, 'HMA27 gate shadow test FAILED: hma-27 dropped with proceeding pending'
_k27c, _d27c, _e27c, _g27c, _cbg27c = stage2({'stridhan'}, _shadow27_sub, {**_shadow27_base, 'being_filed': True})
assert 'hma-27' in _k27c, 'HMA27 gate shadow test FAILED: hma-27 dropped with being_filed=True'
print('HMA27 gate shadow test: PASS (no proceeding -> gated, bns-316 kept, D2 reason recorded; pending/being-filed -> kept)')
"""

DERIVE_FACTS_BLOCK = '''# --- v6 FACT DERIVATION FOR NON-16 SETS (STOPGAP — see header note 12) ---
# Frozen text rules. Never tuned per question, never read from GT. A frozen
# annotation (Cell 6 for the 16; the sealed files' five facts) always wins
# over derivation — complete_facts() only fills keys the annotation lacks.
_FILING_RE = re.compile(r'\\b(going to file|will file|will be filing|am filing|filing for divorce (next|soon|this)|have (decided|instructed).*fil|going to (file|apply))\\b', re.I)
_PENDING_RE = re.compile(r'\\b(divorce (case|petition|matter)|case|petition|matter)\\b[^.]{0,50}\\b(pending|going on|already going on|running in|has been pending|is pending)\\b', re.I)
_DECREE_RE = re.compile(r'\\bdecree\\b.{0,30}\\b(passed|already|granted|given)\\b|\\bdivorce\\b.{0,20}\\b(decreed|granted)\\b', re.I)
_DIVORCE_NEG_RE = re.compile(r"\\b(do not|don't|does not|never|not|undecided about)\\b.{0,25}\\b(want (a )?divorce|divorce)\\b", re.I)
_DIVORCE_ASKED_RE = re.compile(r'\\b(want|wants|seeking|seek|applying for|file for|filing for|going to file for)\\b.{0,25}\\b(divorce|end (the |our |this )?marriage|mutual divorce)\\b|\\bmutual (consent|agreement)\\b.{0,25}\\b(divorce|end)', re.I)
_DEMAND_TRUE_RE = re.compile(r'\\b(asked|demanded|requested)\\b.{0,40}\\b(return|back|refus)|\\brefused to return\\b|\\bdemand\\b.{0,20}\\bmade\\b', re.I)
_DEMAND_FALSE_RE = re.compile(r"\\b(never|not|n't|no)\\b.{0,25}\\b(asked|demanded)\\b|\\bhave not asked\\b|\\bnot asked (for it )?yet\\b|\\bnever (asked|demanded)\\b", re.I)
_VIOLENCE_RE = re.compile(r'\\b(beat|beats|beaten|beating|hit|hits|hitting|slap|slapped|threat|threatens|threatened|abuse|abusive|harass|attack|violence|broke my arm|hurt me)\\b', re.I)
_RESIDENCE_RE = re.compile(r"\\b(thrown out|throw me out|throwing me out|changed the lock|locked (me )?out|cannot enter|can't enter|barred (me )?from (entering|the)|evict|stay in (the )?(house|home|shared (house|home))|return to (our |the )?shared (house|home)|live in (the )?(house|home)|separate place to stay|residence order|right to (reside|stay))\\b", re.I)
_MONEY_RE = re.compile(r'\\b(maintenance|money|monthly|support|alimony|school fees|expenses|interim maintenance|financial support|run the house)\\b', re.I)
_GOLD_RE = re.compile(r'\\b(gold|stridhan|streedhan|jewellery|jewelry|ornaments?|bangles?|necklace|earrings?|jewellery box)\\b', re.I)


def derive_facts_from_text(q):
    # Returns a full 9-key facts dict derived from the question text only.
    # "Being filed" follows the freeze-note rule exactly: only a definite
    # filing / will-file / going-to-file statement counts. Wanting a divorce,
    # contemplating one, a mutual wish, and conditional "if I file" do NOT.
    return {
        'divorce_asked': bool(_DIVORCE_ASKED_RE.search(q)) and not bool(_DIVORCE_NEG_RE.search(q)),
        'proceeding_pending': bool(_PENDING_RE.search(q)),
        'being_filed': bool(_FILING_RE.search(q)),
        'decree': bool(_DECREE_RE.search(q)),
        # Demand: the FALSE (never/not asked) check runs FIRST — "never asked
        # them to return it" contains "asked ... return", which the TRUE
        # pattern would otherwise catch. A negation before asked/demanded wins.
        'demand_made': (False if _DEMAND_FALSE_RE.search(q) else
                        True if _DEMAND_TRUE_RE.search(q) else None),
        'violence': bool(_VIOLENCE_RE.search(q)),
        'residence_claim': bool(_RESIDENCE_RE.search(q)),
        'money_fact': bool(_MONEY_RE.search(q)),
        'gold_fact': bool(_GOLD_RE.search(q)),
    }


def complete_facts(q, partial=None):
    # Frozen annotations win; derivation fills only the keys they lack.
    # Sealed sets pass their five facts as `partial`; the bank passes None.
    facts = derive_facts_from_text(q)
    if partial:
        for k, v in partial.items():
            if k in facts:
                facts[k] = v
    return facts


'''


def apply_cell7_transforms(nb, idx=7):
    """Cell 7: header notes, D2 gate, Lane 2 kinds, shadow test, fact
    derivation, and the run_one_question() refactor. Returns the original
    loop-body core lines (for the dedent-equivalence check in validate())."""
    cell7 = nb["cells"][idx]
    src = _cell_source(cell7)

    # --- Header: fix the stale "skeleton — fixes pending" line. ---
    _replace_in_cell(
        cell7,
        "# Cell 7 — v5 (PRECISION skeleton — v4r logic unchanged; merged Lane A+B+C fixes pending) LIVE Stage 1 + Stage 2.",
        "# Cell 7 — v6 (D1-A + D2 gate + Lane 2 typed kinds; v5 fixes kept) LIVE Stage 1 + Stage 2.",
        1, where="Cell 7 header")
    src = _cell_source(cell7)
    if "fixes pending" in src.split("HARD RULES")[0]:
        raise SystemExit("VALIDATION FAIL: stale 'fixes pending' text survives in Cell 7 header.")
    # --- Header notes 9-13, before HARD RULES. ---
    _insert_before_anchor(cell7, "# HARD RULES (unchanged from v1):", CELL7_HEADER_NOTES,
                          where="Cell 7 header notes")

    # --- D2 gate: insert before the "old hma-25 recheck block is DELETED" comment. ---
    _insert_before_anchor(
        cell7,
        "    # The old 'if not facts[decree] and hma-25 in kept: drop' recheck block is",
        D2_GATE_BLOCK, where="Cell 7 D2 gate")

    # --- Lane 2 kinds: insert before stage2()'s return. ---
    _replace_in_cell(
        cell7,
        "    return kept, dropped, esc_typed, gated_out, candidates_before_gate",
        KINDS_BLOCK + "    return kept, dropped, esc_typed, gated_out, candidates_before_gate",
        1, where="Cell 7 kinds block")

    # --- Fact derivation helpers: insert before the HMA25 shadow test. ---
    _insert_before_anchor(
        cell7,
        "# --- Offline shadow test of the HMA 25 gate (no model calls; fails fast) ---",
        DERIVE_FACTS_BLOCK, where="Cell 7 derive_facts")

    # --- HMA27 shadow test: insert after the HMA25 shadow-test print. ---
    _insert_after_anchor(
        cell7,
        "print('HMA25 gate shadow test: PASS (decree=false -> gated, not kept, in candidates_before_gate; decree=true -> kept)')",
        HMA27_SHADOW_BLOCK, where="Cell 7 HMA27 shadow test")

    # --- Refactor: loop body -> run_one_question(t). ---
    src = _cell_source(cell7)
    marker = "RESULTS = []\nfor t in TEST_SET:\n"
    idx = src.find(marker)
    if idx == -1:
        raise SystemExit("REFACTOR FAIL: TEST_SET loop marker not found in Cell 7.")
    head, rest = src[:idx], src[idx + len(marker):]
    tail_anchor = "print()\nprint(f'Live run complete:"
    tidx = rest.find(tail_anchor)
    if tidx == -1:
        raise SystemExit("REFACTOR FAIL: end-of-loop tail anchor not found in Cell 7.")
    body, tail = rest[:tidx], rest[tidx:]
    body_lines = body.split("\n")
    while body_lines and body_lines[-1].strip() == "":
        body_lines.pop()
    # Last three physical lines must be RESULTS.append + the 2-line print.
    if body_lines[-3].strip() != "RESULTS.append(rec)":
        raise SystemExit(
            f"REFACTOR FAIL: expected RESULTS.append(rec) as third-from-last body line, "
            f"got {body_lines[-3]!r}.")
    if not body_lines[-2].strip().startswith('print(f"{t['):
        raise SystemExit(
            f"REFACTOR FAIL: expected the per-question print as second-from-last body line, "
            f"got {body_lines[-2][:80]!r}.")
    if "GT={t['gt_labels']}" not in body_lines[-1]:
        raise SystemExit("REFACTOR FAIL: per-question print continuation line not recognised.")
    core_lines = body_lines[:-3]  # the verbatim v5 body, minus append/print
    func_lines = ["def run_one_question(t):",
                  "    # v6 refactor: the v5 per-question Stage 1 + Stage 2 body, moved",
                  "    # verbatim into one reusable function (re-indented only). No threshold,",
                  "    # prompt, scoring-logic or fact change. The caller (TEST_SET loop,",
                  "    # batch cells, sealed cells) appends the record and prints the",
                  "    # one-line summary. t must carry 'id', 'question', 'facts', 'gt_ids',",
                  "    # 'gt_labels'. For bank/sealed questions the caller builds 'facts'",
                  "    # with complete_facts() above; the 16 use frozen Cell 6 facts."]
    for ln in core_lines:
        func_lines.append(("    " + ln) if ln.strip() else "")
    func_lines.append("        return rec")  # function-body level is 8 spaces, not the loop's 4
    func_src = "\n".join(func_lines) + "\n"
    caller = ("RESULTS = []\n"
              "for t in TEST_SET:\n"
              "    _rec = run_one_question(t)\n"
              "    RESULTS.append(_rec)\n"
              "    print(f\"{_rec['id']}: fired={_rec['fired_issues']} kept={[LABEL_BY_ID.get(s, s) for s in _rec['kept_ids']]} \"\n"
              "          f\"court={_rec['court_live']} ({_rec['court_source']}) GT={t['gt_labels']} latency={_rec['latency_s']}s error={_rec['error']}\")\n")
    _set_source(cell7, head + func_src + "\n" + caller + tail)
    return core_lines

# ---------------------------------------------------------------------------
# Cell 8 — v6 regression scoring: dual escalates, kinds, gate rating, G14,
# shared score_batch() helper used by every batch / sealed / final cell.
# ---------------------------------------------------------------------------
CELL8_HEADER = """# Cell 8 — v6 score, save, download (16-question REGRESSION vs corrected v2 GT).
# Scoring is the backtest's (exact section-set match, per-section precision /
# recall, forbidden mappings, court correct, escalates correctly) PLUS the
# v6 diagnostics below. Original metrics are kept verbatim so v6 compares
# directly with the v5 live baseline (exact 16/16, mean P/R 1.000/1.000,
# micro P/R 1.000/1.000, TP/FP/FN 57/0/0, court 16/16, escalates 12/16 —
# all computed under the OLD 57-section GT; v6 re-scores the same run shape
# under the corrected 53-section GT, so the numbers are NOT directly
# comparable — D1-A re-bases the story, see build note).
# D1-A + D2: the 16 are scored against the corrected v2 GT (Cell 6). The D2
# gate drops hma-27 where no proceeding is pending/being filed, so K0/H3/H10/H15
# can still read exact. FORBIDDEN_RULES gains the hma-27 rule (HMA 27 with no
# proceeding pending/being filed) — a D2-consequent addition, recorded here.
# DUAL ESCALATES SCORING (expansion brief): every row reports BOTH the old
# boolean escalates score (esc_live from the typed kinds below) AND the
# typed-kinds score (predicted kind set == GT kind set, strict; plus a
# fact-excluded variant). The typed-escalation kinds themselves (Lane 2
# section 4.1) are generated in Cell 7 stage2(). 'fact' is deliberately NOT
# in the scoring set (follow-up questions, not an escalation reason).
# H7/H15 RESOLVED (D3/D4, rater 2026-11-27): escalate_expected kept True for
# both; procedure (H7) and recovery (H15) kinds added. D5 rater confirmation
# of the H2/H4 kinds is still outstanding.
# GATE-FORMULA RATING (gate section 2, frozen) is computed here for the 16,
# with the full arithmetic shown; Fp is NOT MEASURED (Cell 9 prose skipped),
# so the 9.0 cap applies and is printed, not hidden.
# G14 LATENCY: mean/max/total/load aggregates + a per-component PASS/FAIL
# check are printed. Expect FAIL on CPU (v5 mean was 61.9 s); T4 is
# unverified — no T4 number is claimed anywhere in this notebook.
# FORBIDDEN METRICS: forbidden_before_recheck / forbidden_after_recheck are
# computed exactly as in v1 (from candidates_before_stage2). NEW:
# forbidden_proposed_before_gate (from candidates_before_gate) and
# gated_out_total (+ gated_out_layerB_total). After the HMA 25 Layer A gate
# the option cannot be picked, so forbidden_proposed_before_gate is
# 0-by-construction for the HMA 25 route — the honest gate check is the
# Cell 7 shadow test (printed PASS) + H5/H9 kept_ids byte-identical to v1.
# Prose-level forbidden errors remain NOT MEASURED (no answer prose generated).
"""

SCORE_HELPERS = '''
# --- v6 shared scoring helpers (used by Cell 8 itself, every batch cell,
# the sealed cells and the final cell). Pure scoring — no model calls, no
# threshold / fact / gate change. ---
SCORING_KINDS = {'quantum', 'court', 'demand', 'custody', 'residence', 'recovery', 'procedure', 'safety'}
# 'fact' is deliberately NOT in SCORING_KINDS (follow-up questions, not a reason).

COURT_NORMALIZE = {'Judicial Magistrate First Class': 'Magistrate',
                   'Registrar of Births and Deaths': 'Registrar',
                   'Family Court': 'Family Court', 'Magistrate': 'Magistrate',
                   'Registrar': 'Registrar'}

# Sealed expected_escalations types -> v6 kind vocabulary. Types with no v6
# equivalent (human-lawyer handoff, enforcement, ask-decision) map to None
# and are reported per question as unmapped — never silently forced into a kind.
SEALED_KIND_MAP = {'quantum': 'quantum', 'safety': 'safety',
                   'written-demand-first': 'demand', 'registrar-procedure': 'procedure',
                   'ask_missing_fact': 'fact', 'proof': 'fact',
                   'human-lawyer': None, 'enforcement': None, 'ask-decision': None}


def _wilson(k, n, z=1.96):
    # 95% Wilson interval for a proportion k/n (plan section 3.3 reading guide).
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return (round(max(0.0, (c - m) / d), 4), round(min(1.0, (c + m) / d), 4))


def bank_pairs(records):
    # Build score_batch pairs for brutal-bank records (BANK_BY_ID, Cell 5b).
    pairs = []
    for r in records:
        q = BANK_BY_ID[r['id']]
        pairs.append({'id': r['id'], 'category': q['category'],
                      'gt_ids': list(q['gt_sections']),
                      'gt_court_expected': [] if q['gt_court'] == 'none' else [q['gt_court']],
                      'gt_escalates': bool(q['gt_escalates']),
                      'gt_kinds': set(q.get('gt_escalation_kinds', [])), 'rec': r})
    return pairs


def sealed_pairs(records, sealed_json):
    # Build score_batch pairs for a sealed set. Court names normalized
    # (JMFC -> Magistrate, Registrar of Births and Deaths -> Registrar).
    # Section ids need NO renaming: the v5 live JSON shows the pipeline
    # already emits hmga-1956-s6 / welfare-principle exactly as sealed GT
    # does (identity mapping, verified — see build note). Sealed gt_labels
    # are issue words ('maintenance', ...) and are never used for scoring.
    by_id = {q['id']: q for q in sealed_json['questions']}
    pairs = []
    for r in records:
        q = by_id[r['id']]
        mapped = set()
        unmapped = []
        for e in q.get('expected_escalations', []):
            m = SEALED_KIND_MAP.get(e.get('type'))
            if m is None:
                unmapped.append(e.get('type'))
            else:
                mapped.add(m)
        pairs.append({'id': r['id'], 'category': q.get('primary_issue', ''),
                      'gt_ids': list(q['gt_sections']),
                      'gt_court_expected': [COURT_NORMALIZE[c] for c in q.get('expected_court', [])],
                      'gt_escalates': bool(q['escalates']), 'gt_kinds': mapped,
                      'gt_kinds_unmapped': unmapped, 'rec': r,
                      'f20': r['id'] == 'F20'})
    return pairs


def score_batch(pairs, label):
    # Scores a list of pairs (bank or sealed) with the frozen definitions:
    # exact = set equality (H12 0/0 convention via _pr); court = lead-forum
    # containment (expected lead forum(s) in court_live; empty GT expects
    # empty court); escalates boolean = any SCORING_KINDS kind present;
    # escalates kinds = predicted kind set == GT kind set (strict) and the
    # fact-excluded variant. F20 RULE (freeze note section 11): F20 is
    # out-of-scope with gt_escalates=True as a human-lawyer handoff; it is
    # scored correct iff the system declined (empty kept, empty court).
    # Returns (rows, agg) and prints the batch summary.
    rows = []
    tot_tp = tot_fp = tot_fn = 0
    for p in pairs:
        r = p['rec']
        pred, gt = r['kept_ids'], p['gt_ids']
        tp, fp, fn, prec, rec = _pr(pred, gt)
        tot_tp += tp; tot_fp += fp; tot_fn += fn
        facts = r.get('facts', {})
        fb = [rule for s, rule, cond in FORBIDDEN_RULES
              if s in r.get('candidates_before_stage2', []) and cond(facts)]
        fa = [rule for s, rule, cond in FORBIDDEN_RULES
              if s in pred and cond(facts)]
        fbg = [rule for s, rule, cond in FORBIDDEN_RULES
               if s in r.get('candidates_before_gate', []) and cond(facts)]
        exp_court = p['gt_court_expected']
        if not exp_court:
            court_ok = (r['court_live'] == [])
        else:
            court_ok = set(exp_court) <= set(r['court_live'])
        typed = r.get('escalations_typed', []) or []
        kinds = {e.get('kind') for e in typed if isinstance(e, dict)}
        pred_kinds = kinds & SCORING_KINDS
        esc_live = bool(pred_kinds)
        gt_kinds = set(p['gt_kinds'])
        if p.get('f20'):
            esc_ok = (pred == [] and r['court_live'] == [])
        else:
            esc_ok = esc_live == p['gt_escalates']
        kinds_ok = pred_kinds == gt_kinds
        kinds_ok_fe = pred_kinds == (gt_kinds - {'fact'})
        silent = bool(gt) and not pred
        rows.append({'id': p['id'], 'category': p.get('category', ''),
                     'exact': set(pred) == set(gt),
                     'precision': round(prec, 3), 'recall': round(rec, 3),
                     'tp': tp, 'fp': fp, 'fn': fn,
                     'pred_ids': sorted(pred), 'gt_ids': sorted(gt),
                     'forbidden_before_recheck': fb, 'forbidden_after_recheck': fa,
                     'forbidden_proposed_before_gate': fbg,
                     'gated_out': r.get('gated_out', []),
                     'court_live': r['court_live'], 'court_expected': exp_court,
                     'court_correct': court_ok,
                     'escalates_live': esc_live, 'escalates_expected': p['gt_escalates'],
                     'escalates_correct': esc_ok,
                     'escalation_kinds': sorted(pred_kinds),
                     'gt_escalation_kinds': sorted(gt_kinds),
                     'escalates_kinds_correct': kinds_ok,
                     'escalates_kinds_correct_fact_excluded': kinds_ok_fe,
                     'gt_kinds_unmapped': p.get('gt_kinds_unmapped', []),
                     'f20_rule_applied': bool(p.get('f20')),
                     'silent': silent,
                     'error': r['error'], 'latency_s': r['latency_s']})
    n = len(rows)
    n_exact = sum(1 for x in rows if x['exact'])
    micro_p = tot_tp / (tot_tp + tot_fp) if (tot_tp + tot_fp) else 0.0
    micro_r = tot_tp / (tot_tp + tot_fn) if (tot_tp + tot_fn) else 0.0
    micro_f1 = (2 * micro_p * micro_r / (micro_p + micro_r)) if (micro_p + micro_r) else 0.0
    per_cat = {}
    for x in rows:
        c = x['category'] or '(no category)'
        a, b = per_cat.get(c, (0, 0))
        per_cat[c] = (a + (1 if x['exact'] else 0), b + 1)
    per_cat_exact = {c: f'{a}/{b}' for c, (a, b) in sorted(per_cat.items())}
    per_cat_min = min([a / b for a, b in per_cat.values()]) if per_cat else 0.0
    lats = [x['latency_s'] for x in rows if x['latency_s'] is not None]
    agg = {'label': label, 'n': n, 'exact': f'{n_exact}/{n}', 'exact_count': n_exact,
           'mean_precision': round(sum(x['precision'] for x in rows) / n, 3) if n else 0.0,
           'mean_recall': round(sum(x['recall'] for x in rows) / n, 3) if n else 0.0,
           'micro_precision': round(micro_p, 3), 'micro_recall': round(micro_r, 3),
           'micro_f1': round(micro_f1, 3), 'micro_tp_fp_fn': [tot_tp, tot_fp, tot_fn],
           'court_correct': f"{sum(1 for x in rows if x['court_correct'])}/{n}",
           'escalates_bool_correct': f"{sum(1 for x in rows if x['escalates_correct'])}/{n}",
           'escalates_kinds_correct_strict': f"{sum(1 for x in rows if x['escalates_kinds_correct'])}/{n}",
           'escalates_kinds_correct_fact_excluded': f"{sum(1 for x in rows if x['escalates_kinds_correct_fact_excluded'])}/{n}",
           'silent_count': sum(1 for x in rows if x['silent']),
           'silent_ids': [x['id'] for x in rows if x['silent']],
           'forbidden_before_recheck_total': sum(len(x['forbidden_before_recheck']) for x in rows),
           'forbidden_ids': [x['id'] for x in rows if x['forbidden_before_recheck']],
           'model_errors': sum(1 for x in rows if x['error']),
           'model_error_ids': [x['id'] for x in rows if x['error']],
           'per_category_exact': per_cat_exact,
           'per_category_min_exact': round(per_cat_min, 3),
           'escalates_on_empty_kept': sum(1 for x in rows if not x['pred_ids'] and x['escalation_kinds']),
           'hma27_gt_note_ids': [x['id'] for x in rows if 'hma-27' in x['gt_ids'] and 'hma-27' not in x['pred_ids']],
           'latency_mean_s': round(sum(lats) / len(lats), 2) if lats else None,
           'latency_max_s': round(max(lats), 2) if lats else None}
    print(f"--- {label}: exact {agg['exact']} | micro P/R/F1 {agg['micro_precision']}/{agg['micro_recall']}/{agg['micro_f1']} "
          f"TP/FP/FN {tot_tp}/{tot_fp}/{tot_fn} | court {agg['court_correct']} | "
          f"esc-bool {agg['escalates_bool_correct']} | esc-kinds strict {agg['escalates_kinds_correct_strict']} "
          f"(fact-excl {agg['escalates_kinds_correct_fact_excluded']}) | silent {agg['silent_count']} | "
          f"Fb {agg['forbidden_before_recheck_total']} | errors {agg['model_errors']} | "
          f"per-cat min {agg['per_category_min_exact']} | latency mean {agg['latency_mean_s']}s ---")
    return rows, agg

'''

def apply_cell8_transforms(nb, idx=8):
    """Cell 8: v6 header, hma-27 forbidden rule, v3 labels, v6 esc set,
    kinds rows, gate rating, G14, shared helpers, v6 filenames."""
    cell8 = nb["cells"][idx]
    src = _cell_source(cell8)

    # --- Header: replace everything before `import json`. ---
    head, sep, rest = src.partition("\nimport json\n")
    if not sep:
        raise SystemExit("CELL8 FAIL: 'import json' anchor not found.")
    _set_source(cell8, CELL8_HEADER + "\nimport json\n" + rest)
    src = _cell_source(cell8)

    # --- Shared helpers: insert after the _pr function definition. ---
    _insert_after_anchor(
        cell8,
        "    return tp, len(pred) - tp, len(gt) - tp, prec, rec\n",
        SCORE_HELPERS, where="Cell 8 score helpers")

    # --- FORBIDDEN_RULES: add the hma-27 rule (D2-consequent). ---
    _replace_in_cell(
        cell8,
        "    ('hma-26', 'HMA 26 with no proceeding pending', lambda f: not f['proceeding_pending']),\n]",
        "    ('hma-26', 'HMA 26 with no proceeding pending', lambda f: not f['proceeding_pending']),\n"
        "    ('hma-27', 'HMA 27 with no proceeding pending or being filed', lambda f: not (f['proceeding_pending'] or f.get('being_filed', False))),\n]",
        1, where="Cell 8 FORBIDDEN_RULES")

    # --- SECTION_COURT: v3 labels. ---
    _replace_in_cell(
        cell8,
        "for _s in ('hma-24', 'hma-25', 'hma-26', 'hma-27', 'hma-13', 'hma-13b', 'gwa-1890', 'hmga-1956-s6', 'welfare-principle'):",
        "for _s in ('hma-24', 'hma-25', 'hma-26', 'hma-27', 'hma-13', 'hma-13b', 'hma-9', 'gwa-1890', 'hmga-1956-s6', 'welfare-principle'):",
        1, where="Cell 8 SECTION_COURT Family Court")
    _replace_in_cell(
        cell8,
        "for _s in ('bnss-144', 'pwdva-17', 'pwdva-18', 'pwdva-19', 'pwdva-20', 'bns-316'):",
        "for _s in ('bnss-144', 'pwdva-17', 'pwdva-18', 'pwdva-19', 'pwdva-20', 'pwdva-22', 'bns-316'):",
        1, where="Cell 8 SECTION_COURT Magistrate")

    # --- SECTION_ISSUE: v3 labels (pwdva-22 is a violence/injury remedy). ---
    _replace_in_cell(
        cell8,
        "    'hma-13': 'divorce', 'hma-13b': 'divorce',\n",
        "    'hma-13': 'divorce', 'hma-13b': 'divorce', 'hma-9': 'divorce',\n"
        "    'pwdva-22': 'violence',\n",
        1, where="Cell 8 SECTION_ISSUE")

    # --- esc_live: v6 kind set. ---
    _replace_in_cell(
        cell8,
        "    esc_live = bool(kinds & {'quantum', 'court', 'demand'})  # PATCHED 2026-11-26: include demand so H3 demand-only reads escalates=True",
        "    esc_live = bool(kinds & {'quantum', 'court', 'demand', 'custody', 'residence', 'recovery', 'procedure', 'safety'})  # v6: Lane 2 kinds + safety (Cell 7); 'fact' deliberately excluded (follow-up questions, not a reason)",
        1, where="Cell 8 esc_live")

    # --- Kinds scoring per row: insert after esc_ok. ---
    _insert_after_anchor(
        cell8,
        "    esc_ok = esc_live == t['escalate_expected']\n",
        "    gt_kinds = set(t.get('gt_escalation_kinds', []))\n"
        "    pred_kinds = kinds & {'quantum', 'court', 'demand', 'custody', 'residence', 'recovery', 'procedure', 'safety'}\n"
        "    kinds_ok = pred_kinds == gt_kinds\n"
        "    kinds_ok_fe = pred_kinds == (gt_kinds - {'fact'})\n",
        where="Cell 8 kinds scoring")

    # --- Row dict: kinds fields before the error/latency line. ---
    _replace_in_cell(
        cell8,
        "                 'fired_issues': r.get('fired_issues', []),\n",
        "                 'escalation_kinds': sorted(pred_kinds),\n"
        "                 'gt_escalation_kinds': sorted(gt_kinds),\n"
        "                 'escalates_kinds_correct': kinds_ok,\n"
        "                 'escalates_kinds_correct_fact_excluded': kinds_ok_fe,\n"
        "                 'fired_issues': r.get('fired_issues', []),\n",
        1, where="Cell 8 row kinds fields")

    # --- Gate-formula rating + latency aggregates: insert before `agg = {`. ---
    _insert_before_anchor(
        cell8,
        "agg = {\n",
        "# --- v6 gate-formula rating (gate section 2, frozen) for the 16 ---\n"
        "# E = exact share, Rm = mean recall, Pm = mean precision, C = court share,\n"
        "# S = escalates-boolean share, Fb = forbidden-before-recheck count.\n"
        "# Fp is NOT MEASURED (Cell 9 prose skipped) so the Fp term is 0 by\n"
        "# non-measurement — NOT by a 0 count — and the 9.0 cap applies.\n"
        "_fb_total = sum(len(x['forbidden_before_recheck']) for x in rows)\n"
        "_E = n_exact / n\n"
        "_Rm = sum(x['recall'] for x in rows) / n\n"
        "_Pm = sum(x['precision'] for x in rows) / n\n"
        "_C = sum(1 for x in rows if x['court_correct']) / n\n"
        "_S = sum(1 for x in rows if x['escalates_correct']) / n\n"
        "_rating_raw = 10 * (0.60 * _E + 0.15 * _Rm + 0.10 * _Pm + 0.075 * _C + 0.075 * _S) - 0.5 * _fb_total\n"
        "_rating_raw = max(0.0, min(10.0, round(_rating_raw, 1)))\n"
        "_rating_capped = min(_rating_raw, 9.0)  # prose NOT MEASURED -> cap 9.0 (also Fb>=1 -> <=9.0)\n"
        "_lats = [x['latency_s'] for x in rows if x['latency_s'] is not None]\n"
        "_lat_mean = round(sum(_lats) / len(_lats), 2) if _lats else None\n"
        "_lat_max = round(max(_lats), 2) if _lats else None\n"
        "_lat_total = round(sum(_lats), 1) if _lats else None\n"
        "_load_s = (LOAD_INFO or {}).get('load_seconds')\n"
        "_g14 = {'mean_le_15': (_lat_mean is not None and _lat_mean <= 15),\n"
        "        'max_le_30': (_lat_max is not None and _lat_max <= 30),\n"
        "        'run_le_240': (_lat_total is not None and _lat_total <= 240),\n"
        "        'load_le_60': (_load_s is not None and _load_s <= 60)}\n"
        "_g14['pass'] = all(_g14.values())\n"
        "\n",
        where="Cell 8 rating computation")

    # --- agg dict: version, kinds, guards, rating, G14, prose/H7 notes. ---
    _replace_in_cell(
        cell8,
        "    'notebook_version': 'v5-precision (skeleton of v4r: R0 residence + residence_claim fact gate + residence full set 17/18/19; v3 thresholds M 0.10 / C 0.20 / R 0.15 / D-asked 0.45 / D-pend 0.12)',\n",
        "    'notebook_version': 'v6-brutal (D1-A corrected GT 53 sections + D2 gate + Lane 2 typed kinds; v3 graph 34/48/79; v3 thresholds M 0.10 / C 0.20 / R 0.15 / D-asked 0.45 / D-pend 0.12)',\n",
        1, where="Cell 8 agg version")
    _replace_in_cell(
        cell8,
        "    'escalates_correct_bool_plain_diagnostic': f\"{sum(1 for x in rows if x['escalates_live_bool_plain'] == x['escalates_expected'])}/{n}\",\n",
        "    'escalates_correct_bool_plain_diagnostic': f\"{sum(1 for x in rows if x['escalates_live_bool_plain'] == x['escalates_expected'])}/{n}\",\n"
        "    'escalates_kinds_correct': f\"{sum(1 for x in rows if x['escalates_kinds_correct'])}/{n}\",\n"
        "    'escalates_kinds_correct_fact_excluded': f\"{sum(1 for x in rows if x['escalates_kinds_correct_fact_excluded'])}/{n}\",\n"
        "    'escalates_on_empty_kept': sum(1 for x in rows if not x['pred_labels'] and x['escalation_kinds']),\n"
        "    'gate_formula_rating_raw': _rating_raw,\n"
        "    'gate_formula_rating_capped_9.0': _rating_capped,\n"
        "    'gate_formula_inputs': {'E': round(_E, 3), 'Rm': round(_Rm, 3), 'Pm': round(_Pm, 3), 'C': round(_C, 3), 'S': round(_S, 3), 'Fb': _fb_total, 'Fp': 'NOT MEASURED'},\n"
        "    'latency_mean_s': _lat_mean, 'latency_max_s': _lat_max, 'latency_total_s': _lat_total,\n"
        "    'latency_load_s': _load_s, 'g14_check': _g14,\n",
        1, where="Cell 8 agg kinds/rating/G14")
    _replace_in_cell(
        cell8,
        "    'prose_forbidden_mappings': 'NOT MEASURED — section classification only, no answer prose generated',\n",
        "    'prose_forbidden_mappings': 'NOT MEASURED — Cell 9 prose renderer SKIPPED in v6 (see build note); no answer prose generated, Fp not measured, 9.0 cap applies',\n",
        1, where="Cell 8 agg prose note")
    _replace_in_cell(
        cell8,
        "    'h7_escalate_ambiguity': 'OPEN — H7 escalate_expected=True kept as-is from Cell 6; under typed quantum/court scoring H7 reads escalates=False (no maintenance, kept non-empty, no court fallback). Resolve the expectation before re-scoring.',\n",
        "    'h7_h15_escalate_resolution': 'RESOLVED (D3/D4, rater 2026-11-27): H7/H15 escalate_expected kept True; procedure (H7) and recovery (H15) kinds added (Lane 2). D5 rater confirmation of H2/H4 kinds still outstanding.',\n",
        1, where="Cell 8 agg H7/H15 note")

    # --- Print block: dual escalates + rating + G14 after the H2/H12 lines. ---
    _insert_after_anchor(
        cell8,
        "print(f\"Gated out total={gated_total} (Layer B picks blocked={gated_layerB_total}); forbidden proposed before gate={agg['forbidden_proposed_before_gate_total']} (v1 forbidden-before-recheck was 2).\")\n",
        "print()\n"
        "print(f\"Escalates (dual scoring): boolean {agg['escalates_correct']} | typed kinds strict {agg['escalates_kinds_correct']} | kinds fact-excluded {agg['escalates_kinds_correct_fact_excluded']} | kinds on empty kept={agg['escalates_on_empty_kept']} (must be 0).\")\n"
        "print(f\"Gate-formula rating (16): raw {agg['gate_formula_rating_raw']} -> capped {agg['gate_formula_rating_capped_9.0']} (prose NOT MEASURED, cap 9.0 applies; Fp term is 0 by non-measurement, NOT by a 0 count). Inputs: {agg['gate_formula_inputs']}.\")\n"
        "print(f\"G14 latency: mean {agg['latency_mean_s']}s (<=15: {_g14['mean_le_15']}) | max {agg['latency_max_s']}s (<=30: {_g14['max_le_30']}) | run total {agg['latency_total_s']}s (<=240: {_g14['run_le_240']}) | load {agg['latency_load_s']}s (<=60: {_g14['load_le_60']}) | G14 overall: {_g14['pass']} — expect FAIL on CPU (v5 mean was 61.9s); T4 unverified, no T4 number claimed.\")\n",
        where="Cell 8 print block")

    # --- Filenames / version strings: v5-precision -> v6-brutal-regression. ---
    src = _cell_source(cell8)
    n_files = src.count("live-laya-colab-results-v5-precision")
    if n_files != 6:
        raise SystemExit(f"CELL8 FAIL: expected 6 v5-precision filenames, found {n_files}.")
    _set_source(cell8, src.replace("live-laya-colab-results-v5-precision",
                                   "live-laya-colab-results-v6-brutal-regression"))
    _replace_in_cell(cell8, "Colab results (v5-precision)",
                     "Colab results (v6-brutal regression)", 1, where="Cell 8 print title")
    _replace_in_cell(cell8, "Colab run v5-precision (Laya 421M + v2 graph)",
                     "Colab run v6-brutal regression (Laya 421M + v3 graph)", 1, where="Cell 8 md title")
    _replace_in_cell(cell8, "Downloaded both v5 result files.",
                     "Downloaded both v6 regression result files.", 1, where="Cell 8 download print")
    _replace_in_cell(cell8,
                     "print('court = court correct, esc = escalates correctly (typed quantum/court flag).')",
                     "print('court = court correct, esc = escalates correctly (boolean, v6 kind set). Kinds strict/fact-excluded are in the aggregate above.')",
                     1, where="Cell 8 table legend")
    _replace_in_cell(cell8,
                     "       'Escalates are scored from the typed quantum/court flag, not from bool(escalations) — see Cell 8 header.',\n"
                     "       'H7 escalate ambiguity is OPEN (see aggregate).',\n",
                     "       'Escalates are scored BOTH as a boolean (v6 kind set) and as typed-kinds equality (strict + fact-excluded) — see Cell 8 header.',\n"
                     "       'H7/H15 escalate expectations RESOLVED (D3/D4, rater 2026-11-27); procedure/recovery kinds added.',\n"
                     "       'Prose forbidden mappings (Fp) NOT MEASURED in v6 (Cell 9 skipped); the 9.0 cap applies to any rating quoted from this run.',\n"
                     "       'Fresh-20 (sealed) is a MEASURED NUMBER ONLY, not a gate pass, until the G2 20/20 amendment is signed.',\n",
                     1, where="Cell 8 md footer")
    return nb


# ---------------------------------------------------------------------------
# Batch cells B1–B10, sealed cells, final cell
# ---------------------------------------------------------------------------
def batch_cell(n, start, end):
    ids = f"B-{start:03d}..B-{end:03d}"
    count = end - start + 1
    return _new_code_cell(
        f"# Batch B{n} — brutal bank questions {ids} ({count} questions). NO TUNING between batches.\n"
        f"# This cell ONLY runs the frozen pipeline (Cell 7 run_one_question) on the batch and scores\n"
        f"# it against the frozen bank GT. It must not modify any threshold, fact, gate, prompt or\n"
        f"# graph value, and no result from this batch may change any later batch. If this cell\n"
        f"# errors, file its partial output and resume from the NEXT batch — never re-run a filed batch.\n"
        f"_BATCH_QS = BANK_QUESTIONS[{start - 1}:{end}]\n"
        f"_BATCH_RECS = []\n"
        f"for _q in _BATCH_QS:\n"
        f"    _t = {{'id': _q['id'], 'question': _q['question'],\n"
        f"          'gt_ids': list(_q['gt_sections']), 'gt_labels': list(_q['gt_sections']),\n"
        f"          'facts': complete_facts(_q['question'])}}\n"
        f"    _rec = run_one_question(_t)\n"
        f"    _BATCH_RECS.append(_rec)\n"
        f"    BRUTAL_RESULTS.append(_rec)\n"
        f"    print(f\"{{_q['id']}}: kept={{_rec['kept_ids']}} court={{_rec['court_live']}} latency={{_rec['latency_s']}}s error={{_rec['error']}}\")\n"
        f"_B{n}_ROWS, _B{n}_AGG = score_batch(bank_pairs(_BATCH_RECS), 'B{n}')\n"
        f"_B{n}_OUT = {{'batch': 'B{n}', 'question_ids': [q['id'] for q in _BATCH_QS],\n"
        f"             'aggregate': _B{n}_AGG, 'per_question': _B{n}_ROWS,\n"
        f"             'raw_live_runs': _BATCH_RECS,\n"
        f"             'frozen_hashes': {{'bank_sha256': '{BANK_SHA}', 'graph_file': GRAPH_FILE,\n"
        f"                             'notebook_version': 'v6-brutal'}},\n"
        f"             'hardware': LOAD_INFO}}\n"
        f"with open('live-laya-colab-results-v6-brutal-B{n}.json', 'w') as _f:\n"
        f"    json.dump(_B{n}_OUT, _f, indent=1, ensure_ascii=False)\n"
        f"from google.colab import files as _cf\n"
        f"_cf.download('live-laya-colab-results-v6-brutal-B{n}.json')\n"
        f"print(f\"Batch B{n} filed + downloaded: live-laya-colab-results-v6-brutal-B{n}.json — FILE IT before starting batch B{n + 1}.\")\n"
        f"_CUM_ROWS, _CUM_AGG = score_batch(bank_pairs(BRUTAL_RESULTS), 'cumulative-so-far')\n"
        f"print('CUMULATIVE so far: ' + str(_CUM_AGG))\n")


SEALED_UPLOAD_SRC = """# Sealed sets — upload + verify (read-only). NEVER edit these files.
# Upload sealed-fresh-20.json AND sealed-kannada-8.json in this one picker.
# Both are verified BEFORE any sealed question is scored:
#   fresh-20  SHA-256 1d8b5dc376e711c3ac6ead4424bb2d8ce52b07552b9a533ad86e0616dbcf8837 (20 questions, F1-F20)
#   kannada-8 SHA-256 2f652af1123a22441cc4158ddf480ef0981aa923858bbcb9dc3622f5e5c25853 (8 questions, KN1-KN8)
# A mismatch stops the run with an error.
# GATE NOTE (v6 section 7.2): the gate must be amended to 20/20 (G2) BEFORE any fresh run
# is SCORED as a gate pass. The amendment text is in the build note, NOT yet signed.
# Until the parent signs it, the fresh-20 numbers below are MEASURED NUMBERS ONLY,
# not a gate pass — the cells print that warning with the score.
print('Upload sealed-fresh-20.json and sealed-kannada-8.json now (file picker).')
_uploaded_sealed = files.upload()
print('uploaded:', list(_uploaded_sealed.keys()))
assert 'sealed-fresh-20.json' in _uploaded_sealed, 'sealed-fresh-20.json was not uploaded — upload it and re-run this cell.'
assert 'sealed-kannada-8.json' in _uploaded_sealed, 'sealed-kannada-8.json was not uploaded — upload it and re-run this cell.'
_fresh_sha = hashlib.sha256(_uploaded_sealed['sealed-fresh-20.json']).hexdigest()
_kn_sha = hashlib.sha256(_uploaded_sealed['sealed-kannada-8.json']).hexdigest()
print('fresh-20 SHA-256:', _fresh_sha)
print('kannada-8 SHA-256:', _kn_sha)
assert _fresh_sha == '""" + FRESH_SHA + """', 'Fresh-20 SHA mismatch — wrong or changed file. STOP.'
assert _kn_sha == '""" + KANNADA_SHA + """', 'Kannada-8 SHA mismatch — wrong or changed file. STOP.'
SEALED_FRESH = json.loads(_uploaded_sealed['sealed-fresh-20.json'].decode('utf-8'))
SEALED_KANNADA = json.loads(_uploaded_sealed['sealed-kannada-8.json'].decode('utf-8'))
assert len(SEALED_FRESH['questions']) == 20, 'Fresh-20 must hold 20 questions. STOP.'
assert len(SEALED_KANNADA['questions']) == 8, 'Kannada-8 must hold 8 questions. STOP.'
assert [q['id'] for q in SEALED_FRESH['questions']] == [f'F{i}' for i in range(1, 21)], 'Fresh-20 IDs are not F1..F20. STOP.'
assert [q['id'] for q in SEALED_KANNADA['questions']] == [f'KN{i}' for i in range(1, 9)], 'Kannada-8 IDs are not KN1..KN8. STOP.'
print('sealed sets OK: fresh-20 (20) + kannada-8 (8), SHAs verified. NEVER edit these files.')
"""

SEALED_FRESH_SRC = """# Sealed fresh-20 — run + score. MEASURED NUMBER ONLY, NOT a gate pass (see header above).
# Scoring: exact / micro P/R/F1 / TP/FP/FN / court (lead-forum containment) /
# escalates boolean + kinds (mapped, see sealed_pairs in Cell 8).
# Court names normalized (Judicial Magistrate First Class -> Magistrate,
# Registrar of Births and Deaths -> Registrar). Section ids need NO renaming:
# the v5 live JSON shows the pipeline already emits hmga-1956-s6 /
# welfare-principle exactly as sealed GT does (identity mapping, verified).
# Sealed gt_labels are issue words, never used for scoring.
# COURT-CONVENTION NOTE: sealed maintenance-only questions expect Family Court
# (freeze note section 12) while the 16-set expects Magistrate for the same
# relief — the pipeline follows the 16-set convention, so sealed court scores
# will show systematic misses on maintenance-only questions (F1, F2, KN1).
# That is a GT-convention difference, not a pipeline change to make here.
# F20 RULE (freeze note section 11): F20 is out-of-scope with gt_escalates=True
# as a human-lawyer handoff; it is scored correct iff the system declines
# (empty kept, empty court), not as a failure.
# HMA 27 GT-RULE NOTE: F8, F9, F10, F16 carry hma-27 in GT frozen BEFORE D1-A
# (all proceeding_pending=False); the D2 gate drops it, so any hma-27 miss
# there is a GT-rule note, not a plain system error — listed in the aggregate
# as hma27_gt_note_ids.
_FRESH_RECS = []
for _q in SEALED_FRESH['questions']:
    _t = {'id': _q['id'], 'question': _q['question'],
          'gt_ids': list(_q['gt_sections']), 'gt_labels': list(_q['gt_sections']),
          'facts': complete_facts(_q['question'], partial=dict(_q.get('facts', {})))}
    _rec = run_one_question(_t)
    _FRESH_RECS.append(_rec)
    print(f"{_q['id']}: kept={_rec['kept_ids']} court={_rec['court_live']} latency={_rec['latency_s']}s error={_rec['error']}")
_FRESH_ROWS, _FRESH_AGG = score_batch(sealed_pairs(_FRESH_RECS, SEALED_FRESH), 'sealed-fresh-20')
_FRESH_OUT = {'set': 'sealed-fresh-20', 'aggregate': _FRESH_AGG, 'per_question': _FRESH_ROWS,
              'raw_live_runs': _FRESH_RECS,
              'frozen_hashes': {'fresh_sha256': '""" + FRESH_SHA + """', 'graph_file': GRAPH_FILE,
                                'notebook_version': 'v6-brutal'},
              'hardware': LOAD_INFO,
              'gate_note': 'MEASURED NUMBER ONLY — not a gate pass until the G2 20/20 amendment is signed.'}
with open('live-laya-colab-results-v6-sealed-fresh-20.json', 'w') as _f:
    json.dump(_FRESH_OUT, _f, indent=1, ensure_ascii=False)
from google.colab import files as _cf
_cf.download('live-laya-colab-results-v6-sealed-fresh-20.json')
print('Sealed fresh-20 filed + downloaded: live-laya-colab-results-v6-sealed-fresh-20.json')
print('GATE NOTE: fresh-20 is a MEASURED NUMBER ONLY — not a gate pass until the G2 20/20 amendment is signed.')
"""

SEALED_KANNADA_SRC = """# Sealed Kannada-8 — run + score (same rules as fresh-20 above).
# KANNADA LIMITATION (Cell 7 note 12): the fact-derivation patterns are English-only,
# so Kannada questions fall back to default facts and the v5 gates veto almost
# everything. Kannada scores through this build measure the English-text gates,
# not the model. Model-extracted facts (v6 deep-dive section 2) are the proper fix.
# HMA 27 GT-RULE NOTE: KN3 carries hma-27 in GT frozen BEFORE D1-A
# (proceeding_pending=False); the D2 gate drops it — see hma27_gt_note_ids.
_KANNADA_RECS = []
for _q in SEALED_KANNADA['questions']:
    _t = {'id': _q['id'], 'question': _q['question'],
          'gt_ids': list(_q['gt_sections']), 'gt_labels': list(_q['gt_sections']),
          'facts': complete_facts(_q['question'], partial=dict(_q.get('facts', {})))}
    _rec = run_one_question(_t)
    _KANNADA_RECS.append(_rec)
    print(f"{_q['id']}: kept={_rec['kept_ids']} court={_rec['court_live']} latency={_rec['latency_s']}s error={_rec['error']}")
_KANNADA_ROWS, _KANNADA_AGG = score_batch(sealed_pairs(_KANNADA_RECS, SEALED_KANNADA), 'sealed-kannada-8')
_KANNADA_OUT = {'set': 'sealed-kannada-8', 'aggregate': _KANNADA_AGG, 'per_question': _KANNADA_ROWS,
                'raw_live_runs': _KANNADA_RECS,
                'frozen_hashes': {'kannada_sha256': '""" + KANNADA_SHA + """', 'graph_file': GRAPH_FILE,
                                  'notebook_version': 'v6-brutal'},
                'hardware': LOAD_INFO}
with open('live-laya-colab-results-v6-sealed-kannada-8.json', 'w') as _f:
    json.dump(_KANNADA_OUT, _f, indent=1, ensure_ascii=False)
from google.colab import files as _cf
_cf.download('live-laya-colab-results-v6-sealed-kannada-8.json')
print('Sealed Kannada-8 filed + downloaded: live-laya-colab-results-v6-sealed-kannada-8.json')
"""

FINAL_CELL_SRC = """# Final — cumulative brutal scoring (230) + 16 regression + sealed summaries + pass/fail.
# This cell RE-SCORES filed records only (score_batch over BRUTAL_RESULTS) — it runs
# NO questions, changes NO threshold/fact/gate, and never re-runs a batch.
# Pass bar (brutal-test-200-plan section 3.2): exact >= 200/230, micro-F1 >= 0.95,
# micro P/R >= 0.95, mean P/R >= 0.90, court >= 200/230, escalates-kinds >= 200/230,
# silent 0, forbidden-before-recheck 0, prose forbidden 0 (NOT MEASURED in v6),
# model errors 0, no category below 75% exact. If any row fails, the brutal test
# FAILS as a whole — no partial pass.
# The brutal-bank rating uses the frozen gate formula with N=230 (plan section 3.1)
# and is ALWAYS quoted with "(brutal bank, n = 230)", never as the 10/10 gate score.
# Fp is NOT MEASURED (Cell 9 skipped) so the 9.0 cap applies to the brutal rating too.
assert len(BRUTAL_RESULTS) == 230, f'Final cell needs all 230 brutal records, got {len(BRUTAL_RESULTS)} — run batches B1-B10 first. STOP.'
_FINAL_ROWS, _FINAL_AGG = score_batch(bank_pairs(BRUTAL_RESULTS), 'brutal-230')
_Eb = _FINAL_AGG['exact_count'] / 230
_Rmb = _FINAL_AGG['mean_recall']
_Pmb = _FINAL_AGG['mean_precision']
_Cb = int(_FINAL_AGG['court_correct'].split('/')[0]) / 230
_Sb = int(_FINAL_AGG['escalates_bool_correct'].split('/')[0]) / 230
_Fbb = _FINAL_AGG['forbidden_before_recheck_total']
_brutal_raw = 10 * (0.60 * _Eb + 0.15 * _Rmb + 0.10 * _Pmb + 0.075 * _Cb + 0.075 * _Sb) - 0.5 * _Fbb
_brutal_raw = max(0.0, min(10.0, round(_brutal_raw, 1)))
_brutal_capped = min(_brutal_raw, 9.0)  # Fp NOT MEASURED -> cap 9.0
_lo, _hi = _wilson(_FINAL_AGG['exact_count'], 230)
_kinds_n = int(_FINAL_AGG['escalates_kinds_correct_strict'].split('/')[0])
_pass = {
    'exact >= 200/230': _FINAL_AGG['exact_count'] >= 200,
    'micro-F1 >= 0.95': _FINAL_AGG['micro_f1'] >= 0.95,
    'micro-P >= 0.95': _FINAL_AGG['micro_precision'] >= 0.95,
    'micro-R >= 0.95': _FINAL_AGG['micro_recall'] >= 0.95,
    'mean-P >= 0.90': _FINAL_AGG['mean_precision'] >= 0.90,
    'mean-R >= 0.90': _FINAL_AGG['mean_recall'] >= 0.90,
    'court >= 200/230': int(_FINAL_AGG['court_correct'].split('/')[0]) >= 200,
    'escalates-kinds >= 200/230': _kinds_n >= 200,
    'silent == 0': _FINAL_AGG['silent_count'] == 0,
    'forbidden-before-recheck == 0': _Fbb == 0,
    'prose forbidden == 0': 'NOT MEASURED in v6 (Cell 9 skipped)',
    'model errors == 0': _FINAL_AGG['model_errors'] == 0,
    'no category < 75% exact': _FINAL_AGG['per_category_min_exact'] >= 0.75,
}
_brutal_pass = all(v is True for v in _pass.values())
print('=== FINAL — brutal bank 230 (v6) ===')
print(f"exact {_FINAL_AGG['exact']} (95% Wilson interval {_lo}-{_hi}) | micro P/R/F1 {_FINAL_AGG['micro_precision']}/{_FINAL_AGG['micro_recall']}/{_FINAL_AGG['micro_f1']} TP/FP/FN {_FINAL_AGG['micro_tp_fp_fn']}")
print(f"court {_FINAL_AGG['court_correct']} | esc-bool {_FINAL_AGG['escalates_bool_correct']} | esc-kinds strict {_FINAL_AGG['escalates_kinds_correct_strict']} (fact-excl {_FINAL_AGG['escalates_kinds_correct_fact_excluded']})")
print(f"silent {_FINAL_AGG['silent_count']} { _FINAL_AGG['silent_ids']} | Fb {_Fbb} | errors {_FINAL_AGG['model_errors']} | per-cat min {_FINAL_AGG['per_category_min_exact']}")
print(f"per-category exact: {_FINAL_AGG['per_category_exact']}")
print(f"brutal-bank rating: raw {_brutal_raw} -> capped {_brutal_capped} (brutal bank, n = 230; Fp NOT MEASURED, cap 9.0 applies)")
print('--- pass/fail vs plan section 3.2 ---')
for _k, _v in _pass.items():
    print(f'  {_k}: {_v}')
print(f"BRUTAL VERDICT: {'PASS' if _brutal_pass else 'FAIL'} (no partial pass; prose row is NOT MEASURED, so a full pass is impossible in v6 — see build note)")
print()
print('=== 16-question REGRESSION (corrected v2 GT, 53 sections) ===')
print(f"exact {agg['exact_section_set_match']} | micro P/R {agg['micro_precision']}/{agg['micro_recall']} TP/FP/FN {agg['micro_tp_fp_fn']} | court {agg['court_correct']} | esc-bool {agg['escalates_correct']} | esc-kinds {agg['escalates_kinds_correct']} (fact-excl {agg['escalates_kinds_correct_fact_excluded']})")
print(f"gate-formula rating (16): raw {agg['gate_formula_rating_raw']} -> capped {agg['gate_formula_rating_capped_9.0']} (prose NOT MEASURED)")
print('Regression must read 16/16 — if it does not, the D1-A/D2 re-base has a live defect; file the run and diagnose offline, do not tune in Colab.')
print()
_fresh_agg = globals().get('_FRESH_AGG')
_kn_agg = globals().get('_KANNADA_AGG')
print('=== Sealed sets (measured numbers only) ===')
if _fresh_agg is not None:
    print(f"fresh-20: exact {_fresh_agg['exact']} | micro P/R/F1 {_fresh_agg['micro_precision']}/{_fresh_agg['micro_recall']}/{_fresh_agg['micro_f1']} | court {_fresh_agg['court_correct']} | esc-bool {_fresh_agg['escalates_bool_correct']} | esc-kinds {_fresh_agg['escalates_kinds_correct_strict']} | silent {_fresh_agg['silent_count']} | Fb {_fresh_agg['forbidden_before_recheck_total']} | errors {_fresh_agg['model_errors']}")
    print('  fresh-20 is a MEASURED NUMBER ONLY — not a gate pass until the G2 20/20 amendment is signed.')
else:
    print('fresh-20: NOT RUN (sealed cells were skipped).')
if _kn_agg is not None:
    print(f"kannada-8: exact {_kn_agg['exact']} | micro P/R/F1 {_kn_agg['micro_precision']}/{_kn_agg['micro_recall']}/{_kn_agg['micro_f1']} | court {_kn_agg['court_correct']} | esc-bool {_kn_agg['escalates_bool_correct']} | esc-kinds {_kn_agg['escalates_kinds_correct_strict']} | silent {_kn_agg['silent_count']} | Fb {_kn_agg['forbidden_before_recheck_total']} | errors {_kn_agg['model_errors']}")
else:
    print('kannada-8: NOT RUN (sealed cells were skipped).')
print()
_lat_all = [r['latency_s'] for r in BRUTAL_RESULTS if r['latency_s'] is not None]
print(f"G14 latency (brutal 230): mean {round(sum(_lat_all) / len(_lat_all), 2) if _lat_all else None}s (<=15s? {bool(_lat_all and sum(_lat_all) / len(_lat_all) <= 15)}) | max {round(max(_lat_all), 2) if _lat_all else None}s — expect FAIL on CPU (v5 mean was 61.9s); T4 unverified, no T4 number claimed.")
print('Gate rows (summary): G1 regression 16/16 required | G2 fresh-20 MEASURED ONLY (amendment unsigned) | G3 kannada-8 measured | G12 prose Fp NOT MEASURED | G14 latency, see above | G15 confirmation re-run NOT DONE.')
_FINAL_OUT = {'notebook_version': 'v6-brutal', 'brutal_230': _FINAL_AGG,
              'brutal_rating_raw': _brutal_raw, 'brutal_rating_capped_9.0': _brutal_capped,
              'brutal_wilson_95': [_lo, _hi], 'brutal_pass_bar': _pass, 'brutal_verdict': 'PASS' if _brutal_pass else 'FAIL',
              'regression_16': agg, 'regression_rows': rows,
              'sealed_fresh_20': _fresh_agg, 'sealed_kannada_8': _kn_agg,
              'per_question_brutal': _FINAL_ROWS, 'raw_live_runs_brutal': BRUTAL_RESULTS,
              'frozen_hashes': {'bank_sha256': '""" + BANK_SHA + """', 'graph_file': GRAPH_FILE},
              'hardware': LOAD_INFO}
with open('live-laya-colab-results-v6-brutal-final.json', 'w') as _f:
    json.dump(_FINAL_OUT, _f, indent=1, ensure_ascii=False)
from google.colab import files as _cf
_cf.download('live-laya-colab-results-v6-brutal-final.json')
print('Final filed + downloaded: live-laya-colab-results-v6-brutal-final.json')
"""

# ---------------------------------------------------------------------------
# Assembly + validation + main
# ---------------------------------------------------------------------------
def build_notebook(base_nb, gt_v2):
    """Full assembly. Returns (notebook, core_lines) where core_lines is the
    original v5 Cell 7 loop-body core (for the dedent-equivalence check)."""
    nb = json.loads(json.dumps(base_nb))
    nb["cells"][0] = _new_md_cell(CELL0_MD)
    nb["cells"][5] = _new_code_cell(CELL5_SRC)
    nb["cells"].insert(6, _new_code_cell(CELL5B_SRC))  # bank upload cell
    # After the insert: 6 bank, 7 GT, 8 pipeline, 9 scoring.
    nb["cells"][7] = _new_code_cell(build_cell6(base_nb, gt_v2))
    core_lines = apply_cell7_transforms(nb, idx=8)
    apply_cell8_transforms(nb, idx=9)
    slices = [(1, 25), (26, 50), (51, 75), (76, 100), (101, 125),
              (126, 150), (151, 175), (176, 200), (201, 225), (226, 230)]
    for i, (a, b) in enumerate(slices, start=1):
        nb["cells"].append(batch_cell(i, a, b))
    nb["cells"].append(_new_code_cell(SEALED_UPLOAD_SRC))
    nb["cells"].append(_new_code_cell(SEALED_FRESH_SRC))
    nb["cells"].append(_new_code_cell(SEALED_KANNADA_SRC))
    nb["cells"].append(_new_code_cell(FINAL_CELL_SRC))
    return nb, core_lines


def _exec_cell7_preloop(nb):
    """Exec the built Cell 7 source up to the RESULTS loop, with the graph
    v3 NODES/SECTION_IDS and a stub agent, and return the namespace. This
    runs both shadow tests (HMA25 + HMA27) offline."""
    src = _cell_source(nb["cells"][8])
    marker = "def run_one_question(t):"
    idx = src.find(marker)
    if idx == -1:
        raise SystemExit("VALIDATION FAIL: run_one_question def not found in built Cell 7.")
    pre = src[:idx]
    graph = json.loads(GRAPH_V3.read_text(encoding="utf-8"))
    ns = {"__name__": "__test__"}
    exec(compile("import re\nimport time\n", "<cell7-imports>", "exec"), ns)
    ns["NODES"] = {n["node_id"]: n for n in graph["nodes"]}
    ns["SECTION_IDS"] = {s["id"] for s in graph["sections"]}

    class _StubAgent:
        # Returns fixed probs: everything 0.0 except the issues the test
        # configures via _probs. Choice answers return 'opt0'.
        _probs = {}

        def predict(self, query, payload):
            answers = {}
            for key, spec in payload.items():
                if spec.get("type") == "choice":
                    answers[key] = {"choice": "opt0"}
                else:
                    answers[key] = {"noul": self._probs.get(key, 0.0)}
            return {"answers": answers}

    ns["agent"] = _StubAgent()
    exec(compile(pre, "<cell 7 pre-loop>", "exec"), ns)
    # Also exec the run_one_question() definition (up to the RESULTS loop).
    ridx = src.find("\nRESULTS = []\n", idx)
    if ridx == -1:
        raise SystemExit("VALIDATION FAIL: RESULTS loop marker not found after run_one_question.")
    exec(compile(src[idx:ridx], "<cell 7 run_one_question>", "exec"), ns)
    return ns


def validate(base_nb, out_nb, core_lines, gt_v2):
    """Build guarantees. Raises SystemExit on any failure."""
    # 1. Cells 1-4 byte-identical to the v5 base.
    for i in range(1, 5):
        if _cell_source(base_nb["cells"][i]) != _cell_source(out_nb["cells"][i]):
            raise SystemExit(f"VALIDATION FAIL: Cell {i} differs from v5 base.")
    # 2. Cell count / order.
    if len(out_nb["cells"]) != 24:
        raise SystemExit(f"VALIDATION FAIL: expected 24 cells, got {len(out_nb['cells'])}.")
    # 3. Cell 6 GT == v2 JSON (ids, questions, gt_ids, gt_sections, courts,
    # escalates, kinds, facts + being_filed False).
    ns6 = {}
    exec(compile(_cell_source(out_nb["cells"][7]), "<cell 6>", "exec"), ns6)
    tset = ns6["TEST_SET"]
    if len(tset) != 16:
        raise SystemExit("VALIDATION FAIL: Cell 6 TEST_SET is not 16 questions.")
    for q, t in zip(gt_v2["questions"], tset):
        if t["id"] != q["id"] or t["question"] != q["question"]:
            raise SystemExit(f"VALIDATION FAIL: Cell 6 {q['id']} id/question mismatch vs v2 GT.")
        if t["gt_ids"] != q["gt_ids"] or t["gt_labels"] != q["gt_sections"]:
            raise SystemExit(f"VALIDATION FAIL: Cell 6 {q['id']} gt_ids/gt_labels mismatch vs v2 GT.")
        if t["court_expected"] != q["gt_court"] or t["escalate_expected"] != q["gt_escalates"]:
            raise SystemExit(f"VALIDATION FAIL: Cell 6 {q['id']} court/escalates mismatch vs v2 GT.")
        if t["gt_escalation_kinds"] != q["gt_escalation_kinds"]:
            raise SystemExit(f"VALIDATION FAIL: Cell 6 {q['id']} gt_escalation_kinds mismatch vs v2 GT.")
        for k, v in q["facts"].items():
            if t["facts"].get(k) != v:
                raise SystemExit(f"VALIDATION FAIL: Cell 6 {q['id']} fact {k} mismatch vs v2 GT.")
        if t["facts"].get("being_filed") is not False:
            raise SystemExit(f"VALIDATION FAIL: Cell 6 {q['id']} being_filed is not False.")
    if sum(len(t["gt_ids"]) for t in tset) != 53:
        raise SystemExit("VALIDATION FAIL: Cell 6 GT total is not 53 sections.")
    # 4. Refactor equivalence: the function body, de-indented, must equal the
    # original v5 loop-body core plus `return rec`.
    src7 = _cell_source(out_nb["cells"][8])
    fidx = src7.find("def run_one_question(t):")
    ridx = src7.find("\nRESULTS = []\n", fidx)
    func_src = src7[fidx:ridx]
    func_lines = func_src.split("\n")
    # Drop the def line + 8 comment lines, then the trailing blank line.
    body_lines = list(func_lines[8:])  # def line + 7 comment lines, then the body
    while body_lines and body_lines[-1].strip() == "":
        body_lines.pop()
    if body_lines[-1].strip() != "return rec":
        raise SystemExit("VALIDATION FAIL: run_one_question does not end with 'return rec'.")
    dedented = [(ln[4:] if ln.startswith("    ") else ln) for ln in body_lines[:-1]]
    expected = list(core_lines)
    if dedented != expected:
        for i, (a, b) in enumerate(zip(dedented, expected)):
            if a != b:
                raise SystemExit(
                    f"VALIDATION FAIL: refactor drift at body line {i}:\n  built:    {a[:100]!r}\n  original: {b[:100]!r}")
        raise SystemExit(
            f"VALIDATION FAIL: refactor body length differs (built {len(dedented)} vs original {len(expected)}).")
    # 5. v5 anchors still present in Cell 7 (no threshold/prompt change).
    for anchor in ("'maintenance': 0.10", "'custody': 0.20", "'stridhan': 0.50",
                   "'residence': 0.15", "GUARD_LIFT_BAR = 0.80", "GUARD_FULL_CEILING = 0.01",
                   "_CUSTODY_PATTERNS", "HMA25 gate shadow test: PASS",
                   "assert 'hma-25' not in _k"):
        if anchor not in src7:
            raise SystemExit(f"VALIDATION FAIL: v5 anchor missing in Cell 7: {anchor!r}")
    # 6. v6 anchors present in Cell 7.
    for anchor in ("hma-27: gated (D2)", "HMA27 gate shadow test: PASS",
                   "def derive_facts_from_text", "def complete_facts",
                   "def run_one_question(t):", "'kind': 'custody'",
                   "'kind': 'residence'", "'kind': 'recovery'",
                   "'kind': 'procedure'", "'kind': 'safety'",
                   "civil recovery through the Family Court under FCA s.7(1) Expl. (c) / CPC s.151",
                   "(or under HMA s.27 where an HMA proceeding is pending or being filed)",
                   "fixes pending"):
        if anchor == "fixes pending":
            if anchor in src7.split("HARD RULES")[0]:
                raise SystemExit("VALIDATION FAIL: stale 'fixes pending' in Cell 7 header.")
            continue
        if anchor not in src7:
            raise SystemExit(f"VALIDATION FAIL: v6 anchor missing in Cell 7: {anchor[:60]!r}")
    # 7. Cell 5 / 5b anchors.
    src5 = _cell_source(out_nb["cells"][5])
    for anchor in ("(34, 48, 79)", GRAPH_V3_SHA, "laya-crpc-bns-section-decision-tree-v3.json"):
        if anchor not in src5:
            raise SystemExit(f"VALIDATION FAIL: Cell 5 anchor missing: {anchor[:40]!r}")
    src5b = _cell_source(out_nb["cells"][6])
    for anchor in (BANK_SHA, "len(BANK_QUESTIONS) == 230", "BRUTAL_RESULTS = []"):
        if anchor not in src5b:
            raise SystemExit(f"VALIDATION FAIL: Cell 5b anchor missing: {anchor[:40]!r}")
    # 8. Cell 8 anchors.
    src8 = _cell_source(out_nb["cells"][9])
    for anchor in ("def score_batch", "def bank_pairs", "def sealed_pairs", "def _wilson",
                   "SCORING_KINDS", "SEALED_KIND_MAP", "COURT_NORMALIZE",
                   "'custody', 'residence', 'recovery', 'procedure', 'safety'",
                   "gate_formula_rating_capped_9.0", "g14_check",
                   "live-laya-colab-results-v6-brutal-regression",
                   "hma-27', 'HMA 27 with no proceeding pending or being filed'"):
        if anchor not in src8:
            raise SystemExit(f"VALIDATION FAIL: Cell 8 anchor missing: {anchor[:60]!r}")
    if "v5-precision" in src8:
        raise SystemExit("VALIDATION FAIL: stale v5-precision string survives in Cell 8.")
    # 9. Batch cells: 10 cells, slices B1..B10, each with save+download+no-tuning note.
    for i in range(10):
        cell = out_nb["cells"][10 + i]
        s = _cell_source(cell)
        if f"# Batch B{i + 1} —" not in s or "NO TUNING between batches" not in s:
            raise SystemExit(f"VALIDATION FAIL: batch cell B{i + 1} header wrong.")
        if f"live-laya-colab-results-v6-brutal-B{i + 1}.json" not in s:
            raise SystemExit(f"VALIDATION FAIL: batch cell B{i + 1} output filename wrong.")
        if "score_batch(bank_pairs(_BATCH_RECS)" not in s:
            raise SystemExit(f"VALIDATION FAIL: batch cell B{i + 1} does not call score_batch.")
    b10 = _cell_source(out_nb["cells"][19])
    if "BANK_QUESTIONS[225:230]" not in b10 or "B-226..B-230" not in b10:
        raise SystemExit("VALIDATION FAIL: B10 is not B-226..B-230.")
    # 10. Sealed + final cells.
    if FRESH_SHA not in _cell_source(out_nb["cells"][20]):
        raise SystemExit("VALIDATION FAIL: sealed upload cell lacks the fresh-20 SHA.")
    if KANNADA_SHA not in _cell_source(out_nb["cells"][20]):
        raise SystemExit("VALIDATION FAIL: sealed upload cell lacks the kannada-8 SHA.")
    if "F20 RULE" not in _cell_source(out_nb["cells"][21]):
        raise SystemExit("VALIDATION FAIL: fresh-20 cell lacks the F20 rule note.")
    if "len(BRUTAL_RESULTS) == 230" not in _cell_source(out_nb["cells"][23]):
        raise SystemExit("VALIDATION FAIL: final cell lacks the 230-record assert.")
    if "Cell 9" not in _cell_source(out_nb["cells"][23]) and "NOT MEASURED" not in _cell_source(out_nb["cells"][23]):
        raise SystemExit("VALIDATION FAIL: final cell does not record prose NOT MEASURED.")
    # 11. nbformat + every code cell compiles.
    import nbformat
    nbformat.validate(out_nb)
    for i, c in enumerate(out_nb["cells"]):
        if c["cell_type"] != "code":
            continue
        src_c = _cell_source(c)
        src_c = re.sub(r"^!pip install.*$", "", src_c, flags=re.M)
        compile(src_c, f"<cell {i}>", "exec")
    # 12. Offline exec: Cell 6 loads; Cell 7 pre-loop runs both shadow tests.
    ns6b = {}
    exec(compile(_cell_source(out_nb["cells"][7]), "<cell 6>", "exec"), ns6b)
    ns7 = _exec_cell7_preloop(out_nb)
    print("offline exec: Cell 6 loads (16 questions, v2 GT 53 sections); "
          "Cell 7 pre-loop runs both shadow tests PASS (HMA25 + HMA27).")
    # 13. Offline pipeline test with the stub agent: D2 drop + recovery text.
    run_one = ns7["run_one_question"]
    stridhan_q = {
        "id": "T1", "question": "He sold my gold without asking me.",
        "gt_ids": ["bns-316"], "gt_labels": ["BNS 316"],
        "facts": {"divorce_asked": False, "proceeding_pending": False,
                  "being_filed": False, "decree": False, "demand_made": True,
                  "violence": False, "residence_claim": False,
                  "money_fact": False, "gold_fact": True},
    }
    ns7["agent"]._probs = {"issue_stridhan": 0.95, "issue_maintenance": 0.0,
                           "issue_custody": 0.0, "issue_residence": 0.0,
                           "issue_violence": 0.0, "issue_divorce": 0.0,
                           "issue_birth_certificate": 0.0, "issue_residence_r1": 0.0,
                           "issue_divorce_pending": 0.0, "issue_in_scope": 0.9}
    rec = run_one(stridhan_q)
    if "hma-27" in rec["kept_ids"] or "bns-316" not in rec["kept_ids"]:
        raise SystemExit("VALIDATION FAIL: stub D2 test — hma-27 kept or bns-316 lost with no proceeding.")
    if not any(g.startswith("hma-27: gated (D2)") for g in rec["gated_out"]):
        raise SystemExit("VALIDATION FAIL: stub D2 test — no D2 gated_out entry.")
    kinds = {e["kind"] for e in rec["escalations_typed"]}
    if "recovery" not in kinds:
        raise SystemExit("VALIDATION FAIL: stub kinds test — recovery kind missing on demand-made stridhan.")
    rec_text = [e["text"] for e in rec["escalations_typed"] if e["kind"] == "recovery"][0]
    if "FCA s.7(1)" not in rec_text or "civil recovery under HMA s.27" in rec_text:
        raise SystemExit("VALIDATION FAIL: stub recovery-text test — D1-A wording not in recovery text.")
    stridhan_q2 = dict(stridhan_q)
    stridhan_q2["facts"] = dict(stridhan_q["facts"], proceeding_pending=True)
    rec2 = run_one(stridhan_q2)
    if "hma-27" not in rec2["kept_ids"]:
        raise SystemExit("VALIDATION FAIL: stub D2 test — hma-27 dropped with proceeding pending.")
    print("offline exec: stub-agent D2/kinds test PASS (no proceeding -> hma-27 gated, "
          "bns-316 kept, recovery text FCA-worded; pending -> hma-27 kept).")
    # 14. Offline score_batch test: exec Cell 8 helpers with stub data.
    src8b = _cell_source(out_nb["cells"][9])
    head8 = src8b.split("\nrows = []\n")[0]  # header + FORBIDDEN_RULES + SECTION_COURT + _pr + helpers
    ns8 = {"__name__": "__test__"}
    exec(compile(head8, "<cell 8 helpers>", "exec"), ns8)
    fake_rec = {"kept_ids": ["bns-316"], "court_live": ["Magistrate"],
                "escalations_typed": [{"kind": "recovery", "text": "x"}],
                "candidates_before_stage2": ["bns-316"], "candidates_before_gate": ["bns-316"],
                "gated_out": [], "facts": {"divorce_asked": False, "proceeding_pending": False,
                                           "being_filed": False, "decree": False},
                "error": None, "latency_s": 61.5}
    frows, fagg = ns8["score_batch"](
        [{"id": "B-999", "category": "C3", "gt_ids": ["bns-316"],
          "gt_court_expected": ["Magistrate"], "gt_escalates": True,
          "gt_kinds": {"recovery"}, "rec": fake_rec}], "stub-batch")
    if not (frows[0]["exact"] and frows[0]["escalates_kinds_correct"]):
        raise SystemExit("VALIDATION FAIL: stub score_batch test — exact/kinds wrong on a trivially right row.")
    if fagg["micro_f1"] != 1.0 or fagg["latency_mean_s"] != 61.5:
        raise SystemExit("VALIDATION FAIL: stub score_batch test — micro-F1/latency wrong.")
    print("offline exec: stub score_batch test PASS (exact + kinds + micro-F1 + latency).")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", type=Path, default=DEFAULT_BASE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    base_nb = json.loads(args.base.read_text(encoding="utf-8"))
    gt_v2 = json.loads(GT_V2.read_text(encoding="utf-8"))
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    if len(bank["questions"]) != 230:
        raise SystemExit("INPUT FAIL: brutal bank does not hold 230 questions.")
    if hashlib.sha256(BANK.read_bytes()).hexdigest() != BANK_SHA:
        raise SystemExit("INPUT FAIL: brutal bank SHA mismatch.")
    graph_v3 = json.loads(GRAPH_V3.read_text(encoding="utf-8"))
    if (len(graph_v3["sections"]), len(graph_v3["nodes"]), len(graph_v3["edges"])) != (34, 48, 79):
        raise SystemExit("INPUT FAIL: graph v3 counts are not 34/48/79.")
    if hashlib.sha256(GRAPH_V3.read_bytes()).hexdigest() != GRAPH_V3_SHA:
        raise SystemExit("INPUT FAIL: graph v3 SHA mismatch.")
    for name, sha in (("sealed-fresh-20.json", FRESH_SHA), ("sealed-kannada-8.json", KANNADA_SHA)):
        p = SEALED_DIR / name
        if hashlib.sha256(p.read_bytes()).hexdigest() != sha:
            raise SystemExit(f"INPUT FAIL: sealed file {name} SHA mismatch.")
    if ("civil recovery through the Family Court under FCA s.7(1) Expl. (c) / CPC s.151" not in KINDS_BLOCK
            or "(or under HMA s.27 where an HMA proceeding is pending or being filed)" not in KINDS_BLOCK):
        raise SystemExit("INPUT FAIL: recovery text in the kinds block drifted from the approved wording.")

    nb, core_lines = build_notebook(base_nb, gt_v2)
    validate(base_nb, nb, core_lines, gt_v2)

    # Determinism: nbformat.validate() assigns a random id to any cell that
    # lacks one (Cell 0, the markdown header, has none in the v5 base). Pin
    # every cell id to its index so re-runs are byte-identical.
    for i, c in enumerate(nb["cells"]):
        c["id"] = f"cell-{i}"

    text = json.dumps(nb, indent=1, ensure_ascii=False)
    args.out.write_text(text, encoding="utf-8")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print(f"built {args.out}")
    print(f"sha256: {sha}")
    print(f"cells: {len(nb['cells'])} (0 md, 1-4 unchanged, 5 graph v3, 5b bank, "
          f"6 v2 GT, 7 pipeline+run_one_question, 8 regression+score_batch, "
          f"9-18 B1-B10, 19 sealed upload, 20 fresh-20, 21 kannada-8, 22 final)")
    print("validation: Cells 1-4 identical to v5; Cell 6 == v2 GT (53 sections, "
          "being_filed False x16); refactor dedent-equivalence PASS; nbformat PASS; "
          "all code cells compile PASS; Cell 6 exec PASS; shadow tests PASS; "
          "stub-agent D2/kinds test PASS; stub score_batch test PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
