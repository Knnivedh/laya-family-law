#!/usr/bin/env python3
"""Build the v5 PRECISION notebook from the v4r base — Lane D.

Phase 1 (skeleton): copies
    live-laya-colab-test-v4r-residence-only.ipynb
to
    live-laya-colab-test-v5-precision.ipynb
changing ONLY version strings / output filenames (v4r -> v5).

Phase 2 (this run): applies the MERGED v5 fix spec
(v5-precision-report.md) — four veto fixes, all in Cell 7 except the
FP-by-issue metric + v4r baseline reference in Cell 8, plus the two
Cell 6 fact fields. Nothing beyond the spec. Every edit asserts its
anchor string / count BEFORE changing anything; on any mismatch the
build FAILS LOUDLY instead of improvising.

Fixes (all vetoes — force a final score to 0.0 only, never fire):
  Fix 1 — evidence gates: Cell 6 money_fact / gold_fact per question;
          Cell 7 vetoes maintenance (money_fact False) and stridhan
          (gold_fact False) after the residence gate, before firing.
  Fix 2 — custody gate: verbatim per-clause patterns; custody fires
          only on a who-gets-the-child / guardianship claim in some
          clause that is not a residence co-location clause.
  Fix 3 — single-issue guard: arms iff exactly one issue clears its own
          per-issue threshold on the RAW full-question scores; any other
          issue with full <= 0.01 needs lift >= 0.80 or is blocked.
  Fix 4 — H14 exclusive primary route in stage2(): proceeding_pending
          -> {hma-26, hmga-1956-s6, welfare-principle}, else the
          unchanged {gwa-1890, hmga-1956-s6, welfare-principle}.
Doc-only: Cell 7 header stale divorce thresholds 0.40/0.13 -> 0.45/0.12;
Cell 8 header stale v3 baseline -> v4r baseline + v4r_baseline_reference.

NOT shipped (per spec): maintenance bar 0.30, Gemini 4-option choice,
keyword token guards, H6 split-trigger extension, residence 2-option
choice gate. No threshold changes. No GT/facts/expectations changes
except the two added fact fields in Cell 6.

Deterministic: re-running this script on the same v4r base reproduces
the v5 file byte-for-byte (same sha256). The v4r file is written with
json.dumps(indent=1, ensure_ascii=False) and no trailing newline; this
builder uses the same dump.

Usage:
    python3 build_laya_v5_precision.py [--base PATH] [--out PATH]
Defaults resolve next to this script.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_BASE = HERE / "live-laya-colab-test-v4r-residence-only.ipynb"
DEFAULT_OUT = HERE / "live-laya-colab-test-v5-precision.ipynb"

# --- Phase 1 skeleton renames: (old, new, expected occurrence count) ---
SKELETON_RENAMES = [
    ("# Cell 7 — v4r (residence precision ONLY; v3 thresholds kept) LIVE Stage 1 + Stage 2.",
     "# Cell 7 — v5 (PRECISION skeleton — v4r logic unchanged; merged Lane A+B+C fixes pending) LIVE Stage 1 + Stage 2.",
     1),
    ("# Cell 8 — v4 score, save, download.",
     "# Cell 8 — v5 score, save, download.",
     1),
    ("'v4r-residence-only (R0 residence + residence_claim fact gate + residence full set 17/18/19; v3 thresholds M 0.10 / C 0.20 / R 0.15 / D-asked 0.45 / D-pend 0.12)'",
     "'v5-precision (skeleton of v4r: R0 residence + residence_claim fact gate + residence full set 17/18/19; v3 thresholds M 0.10 / C 0.20 / R 0.15 / D-asked 0.45 / D-pend 0.12)'",
     1),
    ("Colab results (v4r residence-only)",
     "Colab results (v5-precision)",
     1),
    ("live-laya-colab-results-v4r-residence-only.json",
     "live-laya-colab-results-v5-precision.json",
     3),
    ("live-laya-colab-results-v4r-residence-only.md",
     "live-laya-colab-results-v5-precision.md",
     3),
    ("Colab run v4r-residence-only (Laya 421M + v2 graph)",
     "Colab run v5-precision (Laya 421M + v2 graph)",
     1),
    ("Downloaded both v4r result files.",
     "Downloaded both v5 result files.",
     1),
]

# --- Phase 2, Fix 1: Cell 6 fact values (spec table, verified Q by Q) ---
# money_fact True exactly on the GT-maintenance set; gold_fact True exactly
# on the GT-stridhan set. residence_claim True exactly on {K0, H4, H6, H13}
# (carried over from v4r — asserted, not changed).
FACT_TABLE = {
    "K0":  (True,  True,  True),
    "H1":  (True,  False, False),
    "H2":  (False, False, False),
    "H3":  (False, True,  False),
    "H4":  (False, False, True),
    "H5":  (True,  False, False),
    "H6":  (True,  False, True),
    "H7":  (False, False, False),
    "H8":  (True,  False, False),
    "H9":  (True,  False, False),
    "H10": (True,  True,  False),
    "H11": (True,  False, False),
    "H12": (False, False, False),
    "H13": (True,  False, True),
    "H14": (True,  False, False),
    "H15": (False, True,  False),
}
# FACT_TABLE[id] = (money_fact, gold_fact, residence_claim)


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
            f"RENAME MISMATCH in {where}: expected {expected} occurrence(s) of "
            f"{old[:80]!r}, found {count}. Base has drifted — refusing to build."
        )
    _set_source(cell, src.replace(old, new))


def _insert_after_anchor(cell, anchor, new_block, where):
    """Insert new_block (a string ending in \\n) right after the first
    occurrence of anchor. Fails loudly if anchor is absent or ambiguous."""
    src = _cell_source(cell)
    count = src.count(anchor)
    if count != 1:
        raise SystemExit(
            f"ANCHOR MISMATCH in {where}: expected exactly 1 occurrence of "
            f"{anchor[:80]!r}, found {count}. Refusing to build."
        )
    _set_source(cell, src.replace(anchor, anchor + new_block, 1))


def _insert_before_anchor(cell, anchor, new_block, where):
    """Insert new_block (a string ending in \\n) right before the first
    occurrence of anchor. Fails loudly if anchor is absent or ambiguous."""
    src = _cell_source(cell)
    count = src.count(anchor)
    if count != 1:
        raise SystemExit(
            f"ANCHOR MISMATCH in {where}: expected exactly 1 occurrence of "
            f"{anchor[:80]!r}, found {count}. Refusing to build."
        )
    _set_source(cell, src.replace(anchor, new_block + anchor, 1))


def apply_skeleton_renames(nb):
    """Phase 1: version strings / output filenames only."""
    cell7, cell8 = nb["cells"][7], nb["cells"][8]
    _replace_in_cell(cell7, *SKELETON_RENAMES[0], where="Cell 7")
    for old, new, expected in SKELETON_RENAMES[1:]:
        _replace_in_cell(cell8, old, new, expected, where="Cell 8")
    return nb


# ---------------------------------------------------------------------------
# Phase 2 — merged fixes. Every edit asserts its anchor first.
# ---------------------------------------------------------------------------

def apply_fix1_cell6(nb):
    """Cell 6: add money_fact / gold_fact to every question's facts dict."""
    cell6 = nb["cells"][6]
    src = _cell_source(cell6)
    id_pat = re.compile(r'"id": "(K0|H\d+)"')
    matches = list(id_pat.finditer(src))
    if len(matches) != 16:
        raise SystemExit(
            f"ANCHOR MISMATCH in Cell 6: expected 16 question ids, found {len(matches)}.")
    ids = [m.group(1) for m in matches]
    if ids != ["K0"] + [f"H{i}" for i in range(1, 16)]:
        raise SystemExit(f"ANCHOR MISMATCH in Cell 6: ids are not K0+H1-H15: {ids}")
    out_parts = []
    prev_end = 0
    for k, m in enumerate(matches):
        block_start = m.start()
        block_end = matches[k + 1].start() if k + 1 < len(matches) else len(src)
        block = src[block_start:block_end]
        qid = m.group(1)
        money, gold, res_claim = FACT_TABLE[qid]
        rc_pat = re.compile(r'   "residence_claim": (True|False)')
        rc = list(rc_pat.finditer(block))
        if len(rc) != 1:
            raise SystemExit(
                f"ANCHOR MISMATCH in Cell 6 {qid}: expected 1 residence_claim, found {len(rc)}.")
        if (rc[0].group(1) == "True") != res_claim:
            raise SystemExit(
                f"ANCHOR MISMATCH in Cell 6 {qid}: residence_claim is {rc[0].group(1)}, "
                f"expected {res_claim} (v4r value). Refusing to build.")
        new_line = (f'   "residence_claim": {rc[0].group(1)},\n'
                    f'   "money_fact": {money},\n'
                    f'   "gold_fact": {gold}')
        block = block[:rc[0].start()] + new_line + block[rc[0].end():]
        out_parts.append(src[prev_end:block_start])
        out_parts.append(block)
        prev_end = block_end
    out_parts.append(src[prev_end:])
    _set_source(cell6, "".join(out_parts))
    return nb


def apply_merged_fixes(nb):
    """Phase 2: apply ONLY the merged Lane A+B+C fix spec."""
    cell7, cell8 = nb["cells"][7], nb["cells"][8]

    # --- Doc-only: Cell 7 header stale divorce thresholds (code is right). ---
    _replace_in_cell(
        cell7,
        "#      divorce-asked 0.40 / divorce-pending 0.13);",
        "#      divorce-asked 0.45 / divorce-pending 0.12);",
        1, where="Cell 7 header")

    # --- Fix 4: H14 exclusive primary route in stage2() (lines 262-265). ---
    _replace_in_cell(
        cell7,
        "    if 'custody' in fired:\n"
        "        kept_pre |= {'gwa-1890', 'hmga-1956-s6', 'welfare-principle'}\n"
        "        if facts['proceeding_pending']:\n"
        "            kept_pre.add('hma-26')\n",
        "    if 'custody' in fired:\n"
        "        # v5 Fix 4 (H14 exclusive primary route): proceeding pending ->\n"
        "        # HMA 26 primary; otherwise the unchanged GWA 1890 primary.\n"
        "        # HMGA s.6 + WELFARE ride with either primary. The recheck\n"
        "        # below (hma-26 dropped with no proceeding pending) stays as\n"
        "        # Layer-B defence-in-depth; no symmetric remove-GWA recheck.\n"
        "        if facts['proceeding_pending']:\n"
        "            kept_pre |= {'hma-26', 'hmga-1956-s6', 'welfare-principle'}\n"
        "        else:\n"
        "            kept_pre |= {'gwa-1890', 'hmga-1956-s6', 'welfare-principle'}\n",
        1, where="Cell 7 stage2 custody block")

    # --- rec init: record the new per-question fields (live run output). ---
    _replace_in_cell(
        cell7,
        "           'residence_claim': None, 'residence_gated': None,\n",
        "           'residence_claim': None, 'residence_gated': None,\n"
        "           'money_fact': None, 'gold_fact': None,\n"
        "           'custody_claim': None, 'custody_gated': None,\n"
        "           'custody_final_pre_gate': None, 'single_issue_guard': None,\n",
        1, where="Cell 7 rec init")

    # --- Fix 2 definitions: verbatim patterns + helper, just before the
    # residence-gate block (inside the live loop, so all Stage 1 vetoes sit
    # together). re is imported at the top of Cell 7. ---
    _insert_after_anchor(
        cell7,
        "        rec['stage1_final']['divorce_pending'] = rec['divorce_pending_prob']\n",
        "        # --- v5 CUSTODY-GATE PATTERNS (Fix 2, verbatim): deterministic\n"
        "        # per-clause veto patterns. A clause matching the residence\n"
        "        # co-location pattern can never carry a custody claim. A veto,\n"
        "        # not a pick — same shape as the v4 residence gate; every pick\n"
        "        # still comes from agent.predict().\n"
        "        _CUSTODY_PATTERNS = [re.compile(r\"who will get my\", re.IGNORECASE), re.compile(r\"\\b(want|wish|need)\\b.{0,30}\\bmy (son|daughter|child) to stay with me\\b\", re.IGNORECASE), re.compile(r\"\\b(custody|guardianship|guardian)\\b\", re.IGNORECASE), re.compile(r\"\\btake (him|her|them) away\\b\", re.IGNORECASE)]\n"
        "        _RESIDENCE_COLOC_RE = re.compile(r\"\\bstay in the (house|home)\\b.{0,40}\\bwith my (son|daughter|child)\\b\", re.IGNORECASE)\n"
        "        def _has_custody_claim(clauses):\n"
        "            for cl in clauses:\n"
        "                if _RESIDENCE_COLOC_RE.search(cl):\n"
        "                    continue\n"
        "                if any(p.search(cl) for p in _CUSTODY_PATTERNS):\n"
        "                    return True\n"
        "            return False\n",
        where="Cell 7 custody-gate patterns")

    # --- Fixes 1+2+3 application: after the residence gate, before firing.
    # Order per the merged report §2: Fix 1, Fix 2, Fix 3. ---
    _insert_after_anchor(
        cell7,
        "        else:\n"
        "            rec['residence_gated'] = False\n",
        "        # --- v5 EVIDENCE GATES (Fix 1): money_fact / gold_fact (Cell 6\n"
        "        # frozen annotations, same style as residence_claim). Veto only:\n"
        "        # a missing grounding fact forces the final to 0.0; the\n"
        "        # per-issue threshold still applies on top (maintenance fires\n"
        "        # only if money_fact True AND final >= 0.10; stridhan only if\n"
        "        # gold_fact True AND final >= 0.50). H8 rests on the explicit\n"
        "        # \"maintenance\"-ask rule; H10's gold fact holds although demand\n"
        "        # has not yet been made (demand_made stays separate).\n"
        "        rec['money_fact'] = bool(facts.get('money_fact', False))\n"
        "        rec['gold_fact'] = bool(facts.get('gold_fact', False))\n"
        "        if not rec['money_fact']:\n"
        "            final['maintenance'] = 0.0\n"
        "            rec['stage1_final']['maintenance'] = 0.0\n"
        "            gated_out_a.append('evidence gate: maintenance gated, money_fact=false')\n"
        "        if not rec['gold_fact']:\n"
        "            final['stridhan'] = 0.0\n"
        "            rec['stage1_final']['stridhan'] = 0.0\n"
        "            gated_out_a.append('evidence gate: stridhan gated, gold_fact=false')\n"
        "        # --- v5 CUSTODY GATE (Fix 2): veto — custody fires only if some\n"
        "        # clause carries a who-gets-the-child / guardianship claim and\n"
        "        # is not itself a residence co-location clause (\"stay in the\n"
        "        # house with my daughter\"). fired_clause / fired_source stay as\n"
        "        # computed (they record what WOULD have fired) — only the final\n"
        "        # score is forced. Pre-gate final recorded for audit.\n"
        "        # THRESHOLDS['custody'] (0.20), AUX_PROMPTS custody entries,\n"
        "        # the main custody prompt and split_clauses are untouched.\n"
        "        rec['custody_final_pre_gate'] = (round(final['custody'], 4)\n"
        "                                         if final.get('custody') is not None else None)\n"
        "        rec['custody_claim'] = _has_custody_claim(clauses)\n"
        "        if not rec['custody_claim']:\n"
        "            final['custody'] = 0.0\n"
        "            rec['stage1_final']['custody'] = 0.0\n"
        "            gated_out_a.append('custody: gated, no who-gets-the-child / guardianship claim in any clause (custody_claim=false)')\n"
        "            rec['custody_gated'] = True\n"
        "        else:\n"
        "            rec['custody_gated'] = False\n"
        "        # --- v5 SINGLE-ISSUE GUARD (Fix 3): defence-in-depth on top of\n"
        "        # Fix 1. Arms iff exactly ONE issue clears its OWN per-issue\n"
        "        # threshold on the FULL-question score alone (raw, BEFORE any\n"
        "        # veto — dominance must use raw full scores, not vetoed finals).\n"
        "        # Divorce is judged on its ASKED signal only (>= 0.45).\n"
        "        # Residence uses the R0 full score, never R1. For any other\n"
        "        # issue with full <= 0.01, the clause/aux lift must reach 0.80\n"
        "        # or the issue is blocked (divorce lift also includes the\n"
        "        # pending clause/full/aux). The residence fact gate runs before\n"
        "        # the guard and takes precedence (its reason string is the\n"
        "        # recorded reason where it fires). No in_scope firing gate\n"
        "        # (rejected: H13 in_scope final 0.0985 is BELOW H7's 0.113).\n"
        "        # No global aux/clause bar.\n"
        "        # NOTE: divorce firing reads asked_fires/pending_fires, computed\n"
        "        # before the guard — a guard veto on divorce zeroes the recorded\n"
        "        # final only and cannot change the firing decision. On the 16\n"
        "        # this is inert (H7/H15 divorce asked/pending are both False);\n"
        "        # flagged for v6, not changed here (spec does not authorise it).\n"
        "        GUARD_LIFT_BAR = 0.80\n"
        "        GUARD_FULL_CEILING = 0.01\n"
        "        _guard_dominant = []\n"
        "        for _gname, _ in ISSUES:\n"
        "            if _gname == 'divorce':\n"
        "                _gfull, _gthr = raw.get('divorce'), THRESHOLDS['divorce_asked']\n"
        "            else:\n"
        "                _gfull, _gthr = raw.get(_gname), THRESHOLDS[_gname]\n"
        "            if _gfull is not None and _gfull >= _gthr:\n"
        "                _guard_dominant.append((_gname, _gfull))\n"
        "        _guard_blocked = []\n"
        "        _guard_armed = len(_guard_dominant) == 1\n"
        "        if _guard_armed:\n"
        "            _dom_name, _dom_full = _guard_dominant[0]\n"
        "            for _gname, _ in ISSUES:\n"
        "                if _gname == _dom_name:\n"
        "                    continue\n"
        "                _full_j = raw.get('divorce') if _gname == 'divorce' else raw.get(_gname)\n"
        "                if _full_j is None or _full_j > GUARD_FULL_CEILING:\n"
        "                    continue\n"
        "                _lifts = [clause_max.get(_gname), rec['aux_max'].get(_gname)]\n"
        "                if _gname == 'divorce':\n"
        "                    _lifts += [clause_max.get('divorce_pending'),\n"
        "                               raw.get('divorce_pending'),\n"
        "                               rec['aux_max'].get('divorce_pending')]\n"
        "                _lifts = [v for v in _lifts if v is not None]\n"
        "                _lift_j = max(_lifts) if _lifts else None\n"
        "                if _lift_j is None or _lift_j < GUARD_LIFT_BAR:\n"
        "                    final[_gname] = 0.0\n"
        "                    rec['stage1_final'][_gname] = 0.0\n"
        "                    _lift_disp = _lift_j if _lift_j is not None else 0.0\n"
        "                    gated_out_a.append(\n"
        "                        f\"single-issue guard: {_gname} blocked (dominant={_dom_name}, \"\n"
        "                        f\"full={_full_j:.4f}<=0.01, lift={_lift_disp:.4f}<0.80)\")\n"
        "                    _guard_blocked.append((_gname, round(_full_j, 4),\n"
        "                                           round(_lift_j, 4) if _lift_j is not None else None))\n"
        "        rec['single_issue_guard'] = {\n"
        "            'armed': _guard_armed,\n"
        "            'dominant': _guard_dominant[0][0] if _guard_armed else None,\n"
        "            'dominant_full': round(_guard_dominant[0][1], 4) if _guard_armed else None,\n"
        "            'blocked': _guard_blocked,\n"
        "        }\n",
        where="Cell 7 Fixes 1+2+3 application")

    # --- Cell 8: header baseline v3 -> v4r (doc-only, approved). ---
    _replace_in_cell(
        cell8,
        "# Scoring is the backtest's (exact section-set match, per-section precision /\n"
        "# recall, forbidden mappings, court correct, escalates correctly) PLUS the\n"
        "# v4 diagnostics below. Original metrics are kept verbatim so v4 compares\n"
        "# directly with the v3 live baseline (exact 5/16, mean P/R 0.673/0.866,\n"
        "# micro P/R 0.671/0.895, TP/FP/FN 51/25/6, court 11/16, escalates 14/16).",
        "# Scoring is the backtest's (exact section-set match, per-section precision /\n"
        "# recall, forbidden mappings, court correct, escalates correctly) PLUS the\n"
        "# v5 diagnostics below. Original metrics are kept verbatim so v5 compares\n"
        "# directly with the v4r live baseline (exact 10/16, mean P/R 0.833/1.000,\n"
        "# micro P/R 0.826/1.000, TP/FP/FN 57/12/0, court 13/16, escalates 14/16).",
        1, where="Cell 8 header")

    # --- Cell 8: FP-by-issue metric, after the rows loop, before empty-5. ---
    _insert_after_anchor(
        cell8,
        "micro_r = tot_tp / (tot_tp + tot_fn) if (tot_tp + tot_fn) else 0.0\n",
        "\n"
        "# --- FP by issue (v5: which issues still produce FPs; expect all zero) ---\n"
        "# Section -> issue map. PWDVA 18 is shared (residence full set /\n"
        "# violence fallback) and is counted as 'residence-or-violence'.\n"
        "SECTION_ISSUE = {\n"
        "    'bnss-144': 'maintenance', 'pwdva-20': 'maintenance',\n"
        "    'hma-24': 'maintenance', 'hma-25': 'maintenance',\n"
        "    'gwa-1890': 'custody', 'hmga-1956-s6': 'custody',\n"
        "    'welfare-principle': 'custody', 'hma-26': 'custody',\n"
        "    'hma-27': 'stridhan', 'bns-316': 'stridhan',\n"
        "    'pwdva-17': 'residence', 'pwdva-19': 'residence',\n"
        "    'pwdva-18': 'residence-or-violence',\n"
        "    'hma-13': 'divorce', 'hma-13b': 'divorce',\n"
        "    'births-deaths-act-1969': 'birth_certificate',\n"
        "}\n"
        "fp_by_section = {}\n"
        "fp_by_issue = {}\n"
        "for _x in rows:\n"
        "    _pred = set(rec_by_id[_x['id']]['kept_ids'])\n"
        "    _gt = set(rec_by_id[_x['id']]['gt_ids'])\n"
        "    for _s in sorted(_pred - _gt):\n"
        "        fp_by_section[_s] = fp_by_section.get(_s, 0) + 1\n"
        "        _iss = SECTION_ISSUE.get(_s, 'unknown')\n"
        "        fp_by_issue[_iss] = fp_by_issue.get(_iss, 0) + 1\n",
        where="Cell 8 FP-by-issue")

    # --- Cell 8: agg entries for the new metric + v4r baseline reference. ---
    _replace_in_cell(
        cell8,
        "    'micro_tp_fp_fn': [tot_tp, tot_fp, tot_fn],\n",
        "    'micro_tp_fp_fn': [tot_tp, tot_fp, tot_fn],\n"
        "    'fp_total': tot_fp,\n"
        "    'fp_by_section': fp_by_section,\n"
        "    'fp_by_issue': fp_by_issue,\n",
        1, where="Cell 8 agg FP entries")
    _replace_in_cell(
        cell8,
        "    'v3_baseline_reference': 'v3 live: exact 5/16, mean P/R 0.673/0.866, micro P/R 0.671/0.895, TP/FP/FN 51/25/6, court 11/16, escalates 14/16, residence fired R1 11/16 vs R0 5/16.',\n",
        "    'v3_baseline_reference': 'v3 live: exact 5/16, mean P/R 0.673/0.866, micro P/R 0.671/0.895, TP/FP/FN 51/25/6, court 11/16, escalates 14/16, residence fired R1 11/16 vs R0 5/16.',\n"
        "    'v4r_baseline_reference': 'v4r live: exact 10/16, mean P/R 0.833/1.000, micro P/R 0.826/1.000, TP/FP/FN 57/12/0, court 13/16, escalates 14/16, residence fired 4/16, gated 12/16.',\n",
        1, where="Cell 8 agg v4r baseline")

    # --- Cell 8: FP-by-issue in the markdown output (after the Empty-5
    # table, before the Residence R0 vs R1 markdown table loop). ---
    _insert_before_anchor(
        cell8,
        "for x in res_rows:\n    md.append(",
        "md += ['', '## FP by issue (v5: expect all zero)', '']\n"
        "if fp_by_issue:\n"
        "    for _iss in sorted(fp_by_issue):\n"
        "        md.append(f'- **{_iss}**: {fp_by_issue[_iss]}')\n"
        "    for _s in sorted(fp_by_section):\n"
        "        md.append(f'- section **{_s}**: {fp_by_section[_s]}')\n"
        "else:\n"
        "    md.append('- none — zero FPs on the 16.')\n",
        where="Cell 8 FP-by-issue markdown")
    return nb


def validate(base_nb, out_nb):
    """Phase 2 guarantees. Raises SystemExit on any failure."""
    # 1. Cells 0-5 byte-identical to the v4r base.
    for i in range(6):
        if _cell_source(base_nb["cells"][i]) != _cell_source(out_nb["cells"][i]):
            raise SystemExit(f"VALIDATION FAIL: Cell {i} differs from v4r base.")
    # 2. Cell 6 diff vs v4r is EXACTLY the two added fact fields: strip them
    # (and the comma added after residence_claim) and require equality.
    c6_out = _cell_source(out_nb["cells"][6])
    stripped = re.sub(
        r',\n   "money_fact": (True|False),\n   "gold_fact": (True|False)',
        "", c6_out)
    if stripped != _cell_source(base_nb["cells"][6]):
        raise SystemExit(
            "VALIDATION FAIL: Cell 6 differs from v4r by more than the two added fact fields.")
    # 2b. money_fact / gold_fact values equal the spec table, all 16 present.
    id_pat = re.compile(r'"id": "(K0|H\d+)"')
    matches = list(id_pat.finditer(c6_out))
    if len(matches) != 16:
        raise SystemExit("VALIDATION FAIL: Cell 6 does not have 16 questions.")
    for k, m in enumerate(matches):
        block = c6_out[m.start():matches[k + 1].start() if k + 1 < 16 else len(c6_out)]
        qid = m.group(1)
        money, gold, _ = FACT_TABLE[qid]
        for field, want in (("money_fact", money), ("gold_fact", gold)):
            mm = re.search(rf'   "{field}": (True|False)', block)
            if not mm or (mm.group(1) == "True") != want:
                raise SystemExit(
                    f"VALIDATION FAIL: Cell 6 {qid} {field} is not {want}.")
    # 3. TEST_SET ids and GT ids unchanged.
    def _testset_ids(cell):
        return re.findall(r'"id": "(K0|H\d+)"', _cell_source(cell))
    def _gt_ids(cell):
        return [tuple(re.findall(r'"([a-z0-9\-]+)"', b))
                for b in re.findall(r'"gt_ids": \[(.*?)\]', _cell_source(cell), flags=re.S)]
    if _testset_ids(base_nb["cells"][6]) != _testset_ids(out_nb["cells"][6]):
        raise SystemExit("VALIDATION FAIL: TEST_SET ids changed.")
    if _gt_ids(base_nb["cells"][6]) != _gt_ids(out_nb["cells"][6]):
        raise SystemExit("VALIDATION FAIL: GT ids changed.")
    if _testset_ids(out_nb["cells"][6]) != ["K0"] + [f"H{i}" for i in range(1, 16)]:
        raise SystemExit("VALIDATION FAIL: TEST_SET ids are not K0+H1-H15.")
    # 4. No stale v4r version string / filename left in Cells 7-8.
    for i in (7, 8):
        src = _cell_source(out_nb["cells"][i])
        for leftover in ("v4r-residence-only", "v4r residence-only"):
            if leftover in src:
                raise SystemExit(
                    f"VALIDATION FAIL: Cell {i} still contains {leftover!r}.")
    # 5. nbformat validation.
    import nbformat
    nbformat.validate(out_nb)
    # 6. Cells 7-8 compile.
    for i in (7, 8):
        compile(_cell_source(out_nb["cells"][i]), f"<cell {i}>", "exec")
    # 7. Carried-over invariants still present.
    all_src = "".join(_cell_source(c) for c in out_nb["cells"])
    for anchor in (
        "assert 'hma-25' not in _k",
        "HMA25 gate shadow test: PASS",
        "32/46/77",
        "NO fallback to keyword",
    ):
        if anchor not in all_src:
            raise SystemExit(f"VALIDATION FAIL: invariant anchor missing: {anchor!r}")
    c8 = _cell_source(out_nb["cells"][8])
    if "esc_live = bool(kinds & {'quantum', 'court', 'demand'})" not in c8:
        raise SystemExit("VALIDATION FAIL: esc_live 'demand' patch missing in Cell 8.")
    # 8. Phase 2 fix anchors present (and no forbidden ship-items).
    c7 = _cell_source(out_nb["cells"][7])
    for anchor in (
        "'money_fact': None, 'gold_fact': None,",
        "evidence gate: maintenance gated, money_fact=false",
        "evidence gate: stridhan gated, gold_fact=false",
        "_CUSTODY_PATTERNS",
        "_RESIDENCE_COLOC_RE",
        "def _has_custody_claim(clauses):",
        "custody: gated, no who-gets-the-child / guardianship claim in any clause (custody_claim=false)",
        "GUARD_LIFT_BAR = 0.80",
        "GUARD_FULL_CEILING = 0.01",
        "single-issue guard:",
        "'single_issue_guard'",
        "if facts['proceeding_pending']:\n            kept_pre |= {'hma-26', 'hmga-1956-s6', 'welfare-principle'}",
        "divorce-asked 0.45 / divorce-pending 0.12);",
    ):
        if anchor not in c7:
            raise SystemExit(f"VALIDATION FAIL: Fix 2/3/4 anchor missing in Cell 7: {anchor[:60]!r}")
    for anchor in ("fp_by_section", "fp_by_issue", "v4r_baseline_reference",
                   "FP by issue (v5: expect all zero)"):
        if anchor not in c8:
            raise SystemExit(f"VALIDATION FAIL: Cell 8 addition missing: {anchor!r}")
    if "0.40 / divorce-pending 0.13" in c7:
        raise SystemExit("VALIDATION FAIL: stale Cell 7 header thresholds still present.")
    # 9. THRESHOLDS unchanged (no threshold moves in v5).
    if "'maintenance': 0.10" not in c7 or "'custody': 0.20" not in c7 \
            or "'stridhan': 0.50" not in c7 or "'residence': 0.15" not in c7:
        raise SystemExit("VALIDATION FAIL: THRESHOLDS changed.")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", type=Path, default=DEFAULT_BASE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    base_nb = json.loads(args.base.read_text(encoding="utf-8"))
    nb = json.loads(args.base.read_text(encoding="utf-8"))  # fresh copy

    apply_skeleton_renames(nb)
    apply_fix1_cell6(nb)
    apply_merged_fixes(nb)
    validate(base_nb, nb)

    text = json.dumps(nb, indent=1, ensure_ascii=False)
    args.out.write_text(text, encoding="utf-8")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print(f"built {args.out}")
    print(f"sha256: {sha}")
    print("validation: Cells 0-5 identical to v4r; Cell 6 diff is exactly the "
          "two added fact fields; TEST_SET K0+H1-H15; GT ids unchanged; "
          "THRESHOLDS unchanged; nbformat.validate PASS; Cells 7-8 compile PASS; "
          "HMA25 shadow test / graph 32/46/77 / esc_live incl. demand / "
          "no-keyword-fallback all present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
