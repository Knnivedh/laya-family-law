#!/usr/bin/env python3
"""Build live-laya-colab-test-v4-1-evidence-first.ipynb from
live-laya-colab-test-v4r-residence-only.ipynb.

v4.1 notebook builder (overnight 10/10 push). ONE focused change on top of
v4r: the residence rule becomes EVIDENCE-FIRST (ChatGPT GPT-6.2, thinking
High, Option D — see chatgpt-v4-consultation.md), plus the violence->PWDVA 18
path becomes a TRUE UNION. Thresholds stay at v3 values (both models agree:
lowering maintenance to 0.05 / custody to 0.13 buys 0 new TPs, only FPs).

What v4.1 changes vs v4r (full diff in v4-1-change-log.md):
  1. RESIDENCE RULE (Cell 7, Stage 1): residence_claim True FIRES residence
     regardless of the R0 score; claim False blocks it (final forced to
     0.0). There is NO unknown branch: residence_claim is a bool on every
     question in Cell 6, so no score-fallback branch exists. The R0 score
     itself is NOT overwritten — stage1_final['residence'] keeps the
     computed max(full, clause-max, aux) so Cell 8 diagnostics stay
     truthful; firing is forced separately (flag
     rec['residence_evidence_fired']) after the firing loop.
  2. VIOLENCE UNION (Cell 7, Stage 2): `if 'violence' in fired:` now adds
     PWDVA 18 unconditionally. v4/v4r made it conditional on residence NOT
     firing. On the current 16 that was equivalent (a fired residence always
     brought the full 17/18/19 set), but the conditional let a residence
     sub-choice delete violence's 18 in v3 (H5: violence fired at 0.8343
     and PWDVA 18 was still lost). A union can never do that.
  3. CELL 8 DIAGNOSTICS: per-question residence_evidence_fired,
     violence_final (raw Stage 1 violence score) and violence_fired, plus
     aggregate residence_evidence_fired_count / violence_fired_count.
     (H5 diagnostic: the raw violence score is now visible in the output,
     so the live run shows whether violence fired — no more guessing.)
  4. HEADER COMMENTS corrected: v4r carried two stale v4 wordings — the
     header scope line listed divorce-asked 0.40 / divorce-pending 0.13
     (the PRIMARY values; v4r keeps 0.45 / 0.12) and note 3's WARNING
     described applying the PRIMARY vector. Both are fixed here; no
     behaviour changes with them.

DO NOT CHANGE (enforced by the diff check in build()): cells 0-6
(byte-identical to v4r, so ground truth and all facts — including
residence_claim — are untouched), thresholds, clause-split rules, aux
prompts, the HMA 25 gate, the esc_live patch, graph v2 JSON, the residence
full-set rule. No live Colab run here — this builder only writes the
notebook. Run order: v4r live first, then v4.1 (see v4-1-change-log.md).

Run: python3 build_laya_v4_1_evidence_first.py
Output: live-laya-colab-test-v4-1-evidence-first.ipynb (same directory).
"""

import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "live-laya-colab-test-v4r-residence-only.ipynb")
OUT = os.path.join(HERE, "live-laya-colab-test-v4-1-evidence-first.ipynb")


def replace_once(src, old, new, label):
    """Replace exactly one occurrence of `old` in `src`; fail loudly otherwise."""
    n = src.count(old)
    assert n == 1, f"v4.1 edit {label}: expected exactly 1 occurrence, found {n}: {old[:90]!r}"
    return src.replace(old, new)


# ---------------------------------------------------------------------------
# Cell 7 edits (surgical replacements on the on-disk v4r Cell 7 source).
# ---------------------------------------------------------------------------
CELL7_EDITS = [
    ("header-line",
     "# Cell 7 — v4r (residence precision ONLY; v3 thresholds kept) LIVE Stage 1 + Stage 2.",
     "# Cell 7 — v4.1 (evidence-first residence; ChatGPT Option D) LIVE Stage 1 + Stage 2."),
    ("scope-block",
     """# v4 changes (see v4-change-log.md for the full diff + predictions):
#  (a) v3 thresholds KEPT (M 0.10, C 0.20, R 0.15,
#      divorce-asked 0.40 / divorce-pending 0.13);
#  (b) residence fires on the R0 prompt (exact v1 text) at 0.15, R1 recorded
#      for diagnosis only and never fires;
#  (c) NEW Cell 6 facts field residence_claim + Stage 1 fact gate
#      (claim False -> residence final forced to 0.0, never fires);
#  (d) Stage 2 residence keeps PWDVA 17+18+19 as a full set, never split.""",
     """# v4.1 changes vs v4r (see v4-1-change-log.md for the full diff + H4 verdict):
#  (a) v3 thresholds KEPT (M 0.10, C 0.20, R 0.15,
#      divorce-asked 0.45 / divorce-pending 0.12) — both models consulted
#      on v4 (ChatGPT GPT-6.2, Gemini Neon) agree: lowering M to 0.05 /
#      C to 0.13 buys 0 new TPs, only new FPs;
#  (b) residence rule becomes EVIDENCE-FIRST (ChatGPT Option D):
#      residence_claim True FIRES residence regardless of the R0 score;
#      claim False blocks it (final forced to 0.0). No unknown branch —
#      residence_claim is a bool on every question in Cell 6;
#  (c) Stage 2 violence -> PWDVA 18 becomes a TRUE UNION (was conditional
#      on residence NOT firing): violence fired always adds PWDVA 18;
#  (d) Stage 2 residence keeps PWDVA 17+18+19 as a full set, never split.
#      R0 still fires at 0.15 for claim-True questions whose score clears
#      it; R1 recorded for diagnosis only and never fires."""),
    ("note3-title",
     "#  3. PER-ISSUE THRESHOLDS — Lane A PRIMARY vector (v4), NEVER a single",
     "#  3. PER-ISSUE THRESHOLDS — v3 vector KEPT (v4.1), NEVER a single"),
    ("note3-warning",
     """#     WARNING, recorded before the live run (see v4-change-log.md §5):
#     applying this PRIMARY vector to the v3 live finals newly fires
#     maintenance on H2/H4/H12 and custody on H7/H10/H12 — those are
#     PREDICTED new FPs. The residence-only counterfactual (v3 thresholds
#     kept) predicts 10/16 exact; the full PRIMARY vector predicts 6/16.
#     The vector is applied as specified; the numbers decide in Colab.""",
     """#     NOTE (v4.1, correcting a stale v4/v4r comment): the PRIMARY vector
#     (M 0.05 / C 0.13) is NOT applied here. Both models consulted on v4
#     (ChatGPT GPT-6.2, Gemini Neon) agree it buys 0 new TPs — v3 already
#     has 0 maintenance FNs and 0 custody FNs — and only adds FPs (M 0.05
#     newly fires H2/H4/H12; C 0.13 newly fires H7/H10/H12). v3 thresholds
#     are kept; the numbers decide in Colab."""),
    ("note4-title",
     "#  4. RESIDENCE R0 FIRES (v4; v3 fired R1). R0 = the exact v1 prompt:",
     "#  4. RESIDENCE R0 FIRES, EVIDENCE-FIRST (v4.1; v3 fired R1). R0 = the exact v1 prompt:"),
    ("note8-title",
     "#  8. v4 RESIDENCE FACT GATE + FULL SET (this version's focused fix):",
     "#  8. v4.1 EVIDENCE-FIRST RESIDENCE RULE + FULL SET (this version's focused fix):"),
    ("note8-claim-true",
     """#     forces residence final to 0.0 before firing (recorded in gated_out);
#     claim True fires per the R0 score. Stage 2 then keeps PWDVA 17+18+19""",
     """#     forces residence final to 0.0 before firing (recorded in gated_out);
#     claim True FIRES residence regardless of the R0 score (v4.1
#     evidence-first, ChatGPT Option D). Stage 2 then keeps PWDVA 17+18+19"""),
    ("note8-violence",
     """#     splits the set. The violence -> PWDVA 18 path is COMPLETELY UNTOUCHED:
#     when residence is gated out and violence fires, PWDVA 18 still comes
#     in through violence (that is how H5's missing PWDVA 18 is predicted
#     to return — see v4-change-log.md §5).""",
     """#     splits the set. The violence -> PWDVA 18 path is now a TRUE UNION
#     (v4.1): violence fired always adds PWDVA 18, whether or not residence
#     fired — in v3, H5's violence fired at 0.8343 and PWDVA 18 was still
#     lost because the path was conditional on residence NOT firing and
#     the residence sub-choice split the set. A union can never do that.
#     (H5's 18 is predicted to return via the union AND via the residence
#     gate unblocking it — see v4-1-change-log.md §4.)"""),
    ("gate-block",
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
            rec['residence_gated'] = False""",
     """        # --- v4.1 EVIDENCE-FIRST RESIDENCE RULE (Stage 1; ChatGPT Option D):
        # residence_claim is a frozen Cell 6 boolean annotation (see builder /
        # change log for the rule). There is NO unknown case: the field is a
        # bool on every question, so no score-fallback branch exists.
        # If True, residence FIRES regardless of the R0 score (the claim
        # itself is the evidence — this is what rescues H4 if the R0/aux
        # scores ever dip: H4 R0 full 0.1267, R0 clause-max 0.1254,
        # aux residence max 0.6474). If False, residence final is forced to
        # 0.0 and residence can never fire, however high the R0 score is
        # (H2 R0 final 0.8464, H5 0.4882, H12 0.2177, H10 0.1901,
        # H3 0.1727, H14 0.1550 are all gated out this way). The gate entry
        # is recorded in gated_out (Layer A style). The R0 score itself is
        # NOT overwritten: stage1_final['residence'] keeps the computed
        # max(full, clause-max, aux) so the Cell 8 diagnostics stay truthful;
        # firing is forced separately below (evidence-first force-fire).
        # fired_clause / fired_source for residence stay as computed.
        rec['residence_claim'] = bool(facts.get('residence_claim', False))
        rec['residence_evidence_fired'] = False
        if not rec['residence_claim']:
            final['residence'] = 0.0
            rec['stage1_final']['residence'] = 0.0
            gated_out_a.append('residence: gated, no residence claim in facts (residence_claim=false)')
            rec['residence_gated'] = True
        else:
            rec['residence_gated'] = False"""),
    ("force-fire",
     "        rec['fired_issues'] = fired\n",
     """        # --- v4.1 EVIDENCE-FIRST FORCE-FIRE: claim True fires residence
        # even when the R0 final is below 0.15. On the current 16 this branch
        # is not load-bearing (every claim-True question already clears 0.15
        # on its R0 final: K0 0.8905, H4 0.6474 via aux, H6 0.7318,
        # H13 0.8786) — it is the robustness guarantee for unseen lockout
        # phrasings where the scores dip. The score is NOT rewritten; only
        # the fired list changes, and the flag is recorded for Cell 8.
        if rec.get('residence_claim') and 'residence' not in fired:
            fired.append('residence')
            rec['residence_evidence_fired'] = True
        rec['fired_issues'] = fired
"""),
    ("violence-union",
     """    if 'violence' in fired and 'residence' not in fired:
        kept_pre.add('pwdva-18')""",
     """    # v4.1 TRUE UNION (ChatGPT §5 / H5 diagnostic): violence adds PWDVA 18
    # whenever it fires, independently of residence. v4/v4r made it
    # conditional (only when residence did NOT fire) — on the current 16
    # that was equivalent, because a fired residence always brought the
    # full 17/18/19 set with it, but the conditional let a residence
    # sub-choice delete violence's 18 in v3 (H5: violence fired at 0.8343
    # and still lost PWDVA 18). A union can never do that.
    if 'violence' in fired:
        kept_pre.add('pwdva-18')"""),
]

# ---------------------------------------------------------------------------
# Cell 8 edits (surgical replacements on the on-disk v4r Cell 8 source).
# The esc_live PATCHED line (quantum/court/demand) is NOT in this list and
# is therefore carried over verbatim; build() asserts it is still there.
# ---------------------------------------------------------------------------
CELL8_EDITS = [
    ("header-line",
     "# Cell 8 — v4 score, save, download.",
     "# Cell 8 — v4.1 score, save, download."),
    ("header-version",
     "# v4 diagnostics below. Original metrics are kept verbatim so v4 compares",
     "# v4.1 diagnostics below. Original metrics are kept verbatim so v4.1 compares"),
    ("header-diag-list",
     """# (max of full, clause-max, aux), residence_claim / residence_gated /
# residence_fired per question, residence gated count.""",
     """# (max of full, clause-max, aux), residence_claim / residence_gated /
# residence_fired / residence_evidence_fired per question, residence gated
# count, and the raw violence final + violence fired per question (H5
# diagnostic: violence fired at 0.8343 in v3 yet PWDVA 18 was lost)."""),
    ("residence-rows-fields",
     """                     'residence_claim': r.get('residence_claim'),
                     'residence_gated': r.get('residence_gated'),
                     'fired_r0_at_0.15': fired_r0, 'fired_r1': fired_r1,
                     'residence_fired': 'residence' in r.get('fired_issues', [])})""",
     """                     'residence_claim': r.get('residence_claim'),
                     'residence_gated': r.get('residence_gated'),
                     'residence_evidence_fired': r.get('residence_evidence_fired'),
                     'violence_final': (r.get('stage1_final') or {}).get('violence'),
                     'violence_fired': 'violence' in r.get('fired_issues', []),
                     'fired_r0_at_0.15': fired_r0, 'fired_r1': fired_r1,
                     'residence_fired': 'residence' in r.get('fired_issues', [])})"""),
    ("agg-version",
     "    'notebook_version': 'v4r-residence-only (R0 residence + residence_claim fact gate + residence full set 17/18/19; v3 thresholds M 0.10 / C 0.20 / R 0.15 / D-asked 0.45 / D-pend 0.12)',",
     "    'notebook_version': 'v4.1-evidence-first (residence_claim True fires residence regardless of R0 score; claim False blocks; residence full set 17/18/19; violence->18 true union; v3 thresholds M 0.10 / C 0.20 / R 0.15 / D-asked 0.45 / D-pend 0.12)',"),
    ("agg-counts",
     "    'residence_gated_count': sum(1 for x in res_rows if x['residence_gated']),",
     "    'residence_gated_count': sum(1 for x in res_rows if x['residence_gated']),\n    'residence_evidence_fired_count': sum(1 for x in res_rows if x['residence_evidence_fired']),\n    'violence_fired_count': sum(1 for x in res_rows if x['violence_fired']),"),
    ("print-header",
     "print('=== LIVE Laya + v2 graph — Colab results (v4r residence-only) ===')",
     "print('=== LIVE Laya + v2 graph — Colab results (v4.1 evidence-first) ===')"),
    ("print-residence-title",
     "print('=== Residence R0 vs R1 (v4: R0 fires, fact-gated; R1 diagnostic only) ===')",
     "print('=== Residence R0 vs R1 (v4.1: evidence-first; R1 diagnostic only) ===')"),
    ("print-residence-columns",
     "print(f\"{'ID':4s} {'R0 full':>7s} {'R1 full':>7s} {'R0 clmax':>8s} {'R1 clmax':>8s} {'aux':>7s} {'R0 fin':>7s} {'claim':>5s} {'gated':>5s} {'fired':>5s}\")",
     "print(f\"{'ID':4s} {'R0 full':>7s} {'R1 full':>7s} {'R0 clmax':>8s} {'R1 clmax':>8s} {'aux':>7s} {'R0 fin':>7s} {'claim':>5s} {'gated':>5s} {'fired':>5s} {'evid':>5s} {'viol':>6s}\")"),
    ("print-residence-row",
     "          f\"{str(x['residence_claim']):>5s} {str(x['residence_gated']):>5s} {str(x['residence_fired']):>5s}\")",
     "          f\"{str(x['residence_claim']):>5s} {str(x['residence_gated']):>5s} {str(x['residence_fired']):>5s} {str(x['residence_evidence_fired']):>5s} {_f(x['violence_final']):>6s}\")"),
    ("filenames-json",
     "live-laya-colab-results-v4r-residence-only",
     "live-laya-colab-results-v4-1-evidence-first"),
    ("md-title",
     "md = ['# Live Laya inference test — Colab run v4r-residence-only (Laya 421M + v2 graph)',",
     "md = ['# Live Laya inference test — Colab run v4.1-evidence-first (Laya 421M + v2 graph)',"),
    ("md-residence-title",
     "md += ['', '## Residence R0 vs R1 (v4: R0 fires, fact-gated; R1 diagnostic only)', '',",
     "md += ['', '## Residence R0 vs R1 (v4.1: evidence-first; R1 diagnostic only)', '',"),
    ("md-residence-header",
     "       '| ID | R0 full | R1 full | R0 clause-max | R1 clause-max | Aux residence max | R0 final | Residence claim | Gated | Residence fired |',",
     "       '| ID | R0 full | R1 full | R0 clause-max | R1 clause-max | Aux residence max | R0 final | Residence claim | Gated | Residence fired | Evidence fired | Violence final |',"),
    ("md-residence-row",
     "    md.append(f\"| {x['id']} | {x['r0_full']} | {x['r1_full']} | {x['r0_clause_max']} | {x['r1_clause_max']} | {x['aux_residence_max']} | {x['r0_final']} | {x['residence_claim']} | {x['residence_gated']} | {x['residence_fired']} |\")",
     "    md.append(f\"| {x['id']} | {x['r0_full']} | {x['r1_full']} | {x['r0_clause_max']} | {x['r1_clause_max']} | {x['aux_residence_max']} | {x['r0_final']} | {x['residence_claim']} | {x['residence_gated']} | {x['residence_fired']} | {x['residence_evidence_fired']} | {x['violence_final']} |\")"),
    ("download-print",
     "print('Downloaded both v4r result files. Send them back to Muse to record the live score.')",
     "print('Downloaded both v4.1 result files. Send them back to Muse to record the live score.')"),
]


def build():
    with open(ORIG, "r", encoding="utf-8") as f:
        nb = json.load(f)
    cells = nb["cells"]
    assert len(cells) == 9, f"v4r notebook has {len(cells)} cells, expected 9"
    orig_cells = json.loads(json.dumps(cells))  # deep copy for the diff check

    # Cells 0-6: copied untouched (Cell 6 carries GT + residence_claim as in v4r).
    # Cell 7: surgical v4.1 edits on the on-disk v4r source.
    c7_src = "".join(cells[7]["source"])
    assert "RESIDENCE_PROMPT = 'R0'" in c7_src
    assert "TRACK = {'residence': 'residence'}" in c7_src
    for label, old, new in CELL7_EDITS:
        c7_src = replace_once(c7_src, old, new, f"cell7-{label}")
    # Sanity: evidence-first present, violence is a true union now, R0 still fires.
    assert c7_src.count("residence_evidence_fired") == 2, (
        f"expected 2 residence_evidence_fired mentions in Cell 7, got {c7_src.count('residence_evidence_fired')}")
    assert "if 'violence' in fired:" in c7_src
    assert "if 'violence' in fired and 'residence' not in fired:" not in c7_src
    assert "'maintenance': 0.10" in c7_src and "'custody': 0.20" in c7_src
    assert "'divorce_asked': 0.45" in c7_src and "'divorce_pending': 0.12" in c7_src
    cells[7]["source"] = c7_src.splitlines(keepends=True)

    # Cell 8: surgical v4.1 edits on the on-disk v4r source (esc_live patch preserved).
    c8_src = "".join(cells[8]["source"])
    assert "esc_live = bool(kinds & {'quantum', 'court', 'demand'})" in c8_src, (
        "esc_live patch missing from v4r Cell 8 — refusing to build")
    for label, old, new in CELL8_EDITS:
        if label == "filenames-json":
            n = c8_src.count(old)
            assert n == 6, f"cell8-filenames-json: expected 6 occurrences, found {n}"
            c8_src = c8_src.replace(old, new)
        else:
            c8_src = replace_once(c8_src, old, new, f"cell8-{label}")
    assert "esc_live = bool(kinds & {'quantum', 'court', 'demand'})" in c8_src, (
        "esc_live patch lost during Cell 8 edits")
    assert "live-laya-colab-results-v4r-residence-only" not in c8_src
    assert "v4r residence-only" not in c8_src
    cells[8]["source"] = c8_src.splitlines(keepends=True)

    # --- diff check: cells 0-6 identical to v4r ---
    for i in range(7):
        assert cells[i] == orig_cells[i], f"cell {i} changed — must stay untouched"

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write("\n")

    # --- validate the written notebook ---
    with open(OUT, "rb") as f:
        raw_bytes = f.read()
    sha = hashlib.sha256(raw_bytes).hexdigest()
    nb2 = json.loads(raw_bytes)
    assert len(nb2["cells"]) == 9
    # Cell 6 executes and is identical to v4r's Cell 6 (GT + facts untouched).
    ns6 = {}
    exec("".join(nb2["cells"][6]["source"]), ns6)
    ns6_orig = {}
    exec("".join(orig_cells[6]["source"]), ns6_orig)
    assert ns6["TEST_SET"] == ns6_orig["TEST_SET"], "Cell 6 TEST_SET differs from v4r"
    assert all("residence_claim" in t["facts"] for t in ns6["TEST_SET"])
    assert all(isinstance(t["facts"]["residence_claim"], bool) for t in ns6["TEST_SET"])
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
    print("Cells 0-6: untouched (identical to v4r — GT and facts, incl. residence_claim, unchanged).")
    print(f"Cells 7-8: v4.1 edits applied ({len(CELL7_EDITS)} + {len(CELL8_EDITS)} replacements)")
    print(f"Cells 7-8 compile: PASS. {nb_ok}.")
    print(f"sha256: {sha}")
    return OUT, sha


if __name__ == "__main__":
    build()
