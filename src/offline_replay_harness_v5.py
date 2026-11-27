#!/usr/bin/env python3
"""End-to-end offline harness for the BUILT v5 notebook (not a re-logic sim).

Executes the actual Cell 6 + Cell 7 (pre-loop defs + live loop) + Cell 8
code from live-laya-colab-test-v5-precision.ipynb with a fake `agent`
that replays the recorded v4r live scores. Clause calls replay the
recorded clause-max for every clause (max-pool outcome identical;
fired_clause text may differ — it does not affect kept sections).
Sub-choice calls replay the recorded v4r option text via opt-index.
google.colab is stubbed; Cell 8 outputs land in /tmp/v5-harness/.

Expected: exact 16/16, TP/FP/FN 57/0/0, micro-F1 1.000, court 16/16,
escalates 12/16 (H7/H15 dip is the known OPEN expectation decision).
"""
import json
import os
import sys
import types

NB = "/home/hatch/workspace/goals/english-family-law-chatbot-retest/files/laya-graph/live-laya-colab-test-v5-precision.ipynb"
V4R = "/home/hatch/workspace/browser_downloads/sess-2184034649/browser-download-20261126T185447.300061282Z-0-live-laya-colab-results-v4r-residence-only.json"
GRAPH = "/home/hatch/workspace/goals/english-family-law-chatbot-retest/files/laya-graph/colab_bundle/laya-crpc-bns-section-decision-tree-v2.json"
OUT = "/tmp/v5-harness"
os.makedirs(OUT, exist_ok=True)
os.chdir(OUT)

# --- stub google.colab before any cell exec ---
colab = types.ModuleType("google.colab")
files_mod = types.ModuleType("google.colab.files")
files_mod.upload = lambda: {"laya-crpc-bns-section-decision-tree-v2.json": open(GRAPH, "rb").read()}
files_mod.download = lambda name: print(f"[stub download] {name}")
colab.files = files_mod
sys.modules["google"] = types.ModuleType("google")
sys.modules["google.colab"] = colab
sys.modules["google.colab.files"] = files_mod

nb = json.load(open(NB))
cell = lambda i: "".join(nb["cells"][i]["source"])

# --- Cell 5 (graph) — run for real, upload stubbed ---
ns = {"__name__": "__main__"}
exec(cell(5), ns)
assert (len(ns["GRAPH"]["sections"]), len(ns["GRAPH"]["nodes"]), len(ns["GRAPH"]["edges"])) == (32, 46, 77)

# --- Cell 6 (test set + GT + LABEL_BY_ID) ---
exec(cell(6), ns)
TEST_SET = ns["TEST_SET"]

# --- Cell 7 pre-loop definitions (up to RESULTS = []) ---
c7 = cell(7)
pre, loop = c7.split("RESULTS = []", 1)
exec(pre, ns)
AUX_PROMPTS = ns["AUX_PROMPTS"]
NODES = ns["NODES"]

# --- fake agent replaying v4r scores ---
v4r = json.load(open(V4R))
runs = {r["id"]: r for r in v4r["raw_live_runs"]}
by_q = {t["question"]: t["id"] for t in TEST_SET}

class FakeAgent:
    def predict(self, meta, payload):
        body = meta["body"]
        keys = list(payload.keys())
        # Dispatch on key prefix FIRST: a sub-choice call can carry the full
        # question as body (argmax clause < 5 words -> body = q), so body
        # alone cannot distinguish the passes.
        if all(k.startswith("issue_") for k in keys):
            qid = by_q.get(body)
            # full-question pass: body is a whole question
            if qid is not None and body == next(t["question"] for t in TEST_SET if t["id"] == qid):
                r = runs[qid]
                raw = r["stage1_raw"]
                ans = {}
                for k in keys:
                    name = k[len("issue_"):]
                    ans[k] = {"noul": str(raw[name])}
                return {"answers": ans}
            # clause pass: body is a clause of some question
            for t in TEST_SET:
                r = runs[t["id"]]
                if body in r["clauses"]:
                    cm = r["stage1_clause_max"]
                    ans = {}
                    for k in keys:
                        name = k[len("issue_"):]
                        ans[k] = {"noul": str(cm[name])}
                    return {"answers": ans}
            raise AssertionError(f"FakeAgent: clause unmatched body={body[:60]!r}")
        # aux pass: body is a whole question, payload keys aux_N
        if all(k.startswith("aux_") for k in keys):
            qid = by_q.get(body)
            assert qid is not None, f"FakeAgent: aux body not a question: {body[:60]!r}"
            r = runs[qid]
            ans = {}
            for k in keys:
                ai = int(k[4:])
                aux = AUX_PROMPTS[ai]
                p = r["aux_scores"].get(aux["issue"], {}).get(aux["phrase"])
                ans[k] = {"noul": str(p)}
            return {"answers": ans}
        # sub-choice pass: payload keys are node ids; replay recorded option
        # text via opt-index (body is the argmax clause / question). The
        # index must be into the SAME option list Cell 7 offers — i.e. with
        # the HMA-25 Layer-A filter applied (maintenance-root, decree False).
        for t in TEST_SET:
            r = runs[t["id"]]
            if body == t["question"] or body in r["clauses"]:
                ans = {}
                for node_id in keys:
                    text = r["sub_choices"].get(node_id)
                    opts = list(NODES[node_id]["options"])
                    if node_id == "maintenance:maintenance-root" and not t["facts"]["decree"]:
                        if "permanent alimony at/after an HMA decree" in opts:
                            opts.remove("permanent alimony at/after an HMA decree")
                    if text is None:
                        raise AssertionError(f"no recorded sub-choice for {node_id} on {t['id']} (v5 fired a v4r-unfired issue!)")
                    ans[node_id] = {"choice": f"opt{opts.index(text)}"}
                return {"answers": ans}
        raise AssertionError(f"FakeAgent: unmatched call body={body[:60]!r} keys={keys}")

ns["agent"] = FakeAgent()
ns["LOAD_INFO"] = {"loader_used": "harness-stub", "load_seconds": 0.0,
                   "errors_before_success": {}}

# --- Cell 7 live loop + Cell 8 scoring ---
exec("RESULTS = []" + loop, ns)
exec(cell(8), ns)

agg = None
# Cell 8 leaves `agg` and `out` in the namespace
agg = ns["agg"]
print()
print("HARNESS RESULT:")
for k in ("notebook_version", "exact_section_set_match", "mean_precision",
          "mean_recall", "micro_precision", "micro_recall", "micro_tp_fp_fn",
          "court_correct", "escalates_correct", "fp_total", "fp_by_issue",
          "fp_by_section", "questions_with_model_error", "residence_fired_count",
          "residence_gated_count"):
    print(f"  {k}: {agg.get(k)}")
print("  non-exact:", [x["id"] for x in ns["rows"] if not x["exact"]])
print("  court wrong:", [x["id"] for x in ns["rows"] if not x["court_correct"]])
print("  escalates wrong:", [x["id"] for x in ns["rows"] if not x["escalates_correct"]])
print("  guard armed:", {r["id"]: r["single_issue_guard"] for r in ns["RESULTS"] if r["single_issue_guard"] and r["single_issue_guard"]["armed"]})
print("  custody_claim:", {r["id"]: (r["custody_claim"], r["custody_gated"], r["custody_final_pre_gate"]) for r in ns["RESULTS"]})
print("  money/gold facts:", {r["id"]: (r["money_fact"], r["gold_fact"]) for r in ns["RESULTS"]})
assert agg["exact_section_set_match"] == "16/16", agg["exact_section_set_match"]
assert agg["micro_tp_fp_fn"] == [57, 0, 0], agg["micro_tp_fp_fn"]
assert agg["court_correct"] == "16/16", agg["court_correct"]
assert agg["escalates_correct"] == "12/16", agg["escalates_correct"]
assert agg["fp_total"] == 0 and agg["fp_by_issue"] == {} and agg["fp_by_section"] == {}
assert agg["questions_with_model_error"] == 0
print("HARNESS: ALL ASSERTIONS PASS — v5 notebook code reproduces 16/16, 57/0/0, court 16/16, escalates 12/16 offline.")
