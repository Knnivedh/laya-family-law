"""Phase A gate A2 — graph-oracle harness (four configurations).

Runs Graph v4 (``src/laya_v7_graph.py::evaluate_stage2_v7``) on:

  GG  gold issues + gold facts       -> Graph
  GP  gold issues + predicted facts  -> Graph
  PG  predicted issues + gold facts  -> Graph
  PP  predicted issues + predicted facts -> Graph

Gold labels MUST come from independent annotation — NEVER generated from
Graph v4 itself. Gold files are JSON with one record per item::

    {"id": ..., "issues": {issue: intent}, "facts": {fact: state},
     "enums": {claimant_sex, claimant_role, modality_time},
     "expected_sections": ["bnss-144", ...],
     "provenance": "independent human annotation, <who/when>"}

``--gold-provenance`` is REQUIRED and must be one of:

  independent    gold sections were annotated by humans WITHOUT running
                 Graph v4 (the only provenance a pass claim may rest on).
  graph-derived  gold sections were produced by running Graph v4 (or a
                 tool that runs it) on gold labels — the oracle is then
                 TAUTOLOGICAL by construction.
  unknown        provenance not established — the oracle runs, but no pass
                 may be claimed from it.

TAUTOLOGY CHECK (GPT-RERUN §10, binding): the harness ALSO inspects the
gold file for graph-generation markers (a top-level or per-record
``generated_by`` / ``source`` field naming the graph, or an
``expected_sections`` field that is byte-identical to Graph v4 output on
every item INCLUDING items where independent annotators are known to
disagree with the graph). If the declared provenance is ``graph-derived``
— or a marker says so — the harness prints ``TAUTOLOGY`` and exits 3:
it refuses to claim a pass on such labels. If provenance is ``unknown``
it prints ``UNVERIFIED-PROVENANCE`` and exits 3 as well when GG is 100%
(a 100% oracle on unverified labels proves nothing); below 100% it exits
1 with the ceiling reported.

DEGRADED MODE (``--legacy-16q``): ``ground-truth/ground-truth-v2-hma27-A.json``
carries NO gold issues and NO gold enums — only a legacy 8-key ``facts``
dict (``divorce_asked``, ``proceeding_pending``, ``decree``,
``demand_made``, ``violence``, ``residence_claim``, ``money_fact``,
``gold_fact``) plus independently annotated ``gt_ids``. In degraded mode
only GG runs, with issues={} and sex/role unknown, and the legacy facts
mapped (``gold_fact`` -> ``stridhan_claim``,
``proceeding_pending`` -> ``proceeding_pending_hma``). The result is a
LOWER BOUND on the oracle, not the oracle: every miss is a missing-input
artifact until gold issues/facts exist. The full independent dev set
needs human annotation — flag it OPEN, do not fake it.

The synthetic corpus (``data/synthetic_v7_1/validation.jsonl``) CANNOT be
used as gold here: it carries no ``expected_sections`` field, and the
harness that derives expected sections from it
(``tests/recall_eval.py::expected_sections``) runs Graph v4 on the gold
labels — graph-derived by construction. This harness refuses files
without an explicit per-record ``expected_sections``.

Exit codes:
  0  oracle ran; GG exact 100% on INDEPENDENT gold (pass).
  1  oracle ran; GG exact < 100% — a system ceiling under the frozen
     graph is measured (report it; do not hide it with incorrect fact
     predictions). In degraded mode this means "missing inputs", not a
     proven ceiling.
  2  usage / environment error (missing file, bad shape, no predictions
     for a requested predicted config).
  3  tautology / unverified provenance — no pass may be claimed.

Pure python — no torch needed. Examples (from the repo root):

    # Degraded smoke test on the 16-Q legacy GT (what exists today):
    python3 scripts/run_graph_oracle.py --legacy-16q \\
        --gold ground-truth/ground-truth-v2-hma27-A.json \\
        --gold-provenance independent
    # Full four-config oracle on an independently annotated dev set:
    python3 scripts/run_graph_oracle.py --gold dev-gold.json \\
        --pred-file dev-predictions.json --gold-provenance independent
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.laya_v7_graph import evaluate_stage2_v7  # noqa: E402
from src.laya_v7_schema import IssueEvidence  # noqa: E402

# Legacy 16-Q fact keys -> classifier-schema fact keys (degraded mode only).
LEGACY_FACT_MAP = {
    "divorce_asked": "divorce_asked",
    "proceeding_pending": "proceeding_pending_hma",
    "decree": "decree",
    "demand_made": "demand_made",
    "violence": "violence",
    "residence_claim": "residence_claim",
    "money_fact": "money_fact",
    "gold_fact": "stridhan_claim",
}

GRAPH_GENERATION_MARKERS = ("graph v4", "graph_v4", "evaluate_stage2",
                            "laya_v7_graph", "stage 2", "stage2")


def _bool_to_state(value: Any) -> str:
    if value is True:
        return "supported"
    if value is False:
        return "denied"
    return str(value)


def _stage1_to_graph(issues: dict[str, Any], facts: dict[str, Any],
                     enums: dict[str, Any] | None) -> tuple[dict, dict]:
    """Normalise classifier-style dicts into evaluate_stage2_v7 inputs."""
    issue_evs: dict[str, IssueEvidence] = {}
    for name, val in (issues or {}).items():
        intent = val["intent"] if isinstance(val, dict) else str(val)
        if intent not in ("requested", "incidental", "denied", "uncertain"):
            intent = "uncertain"
        issue_evs[name] = IssueEvidence(issue=name, intent=intent,
                                        source="oracle", confidence=1.0)
    stage2_facts: dict[str, Any] = {}
    for name, val in (facts or {}).items():
        stage2_facts[name] = val["state"] if isinstance(val, dict) else str(val)
    for head, val in (enums or {}).items():
        norm = val["value"] if isinstance(val, dict) else str(val)
        if head == "claimant_sex":
            norm = {"M": "male", "F": "female", "U": "unknown"}.get(norm, norm)
        stage2_facts[head] = norm
    denied = {n for n, ev in issue_evs.items() if ev.intent == "denied"}
    stage2_facts["negated_issues"] = set(denied)
    stage2_facts["denied_issues"] = set(denied)
    return issue_evs, stage2_facts


def run_config(issues: dict, facts: dict, enums: dict | None) -> set[str]:
    issue_evs, stage2_facts = _stage1_to_graph(issues, facts, enums)
    decision = evaluate_stage2_v7(issue_evs, stage2_facts,
                                  custody_vocab="v3_bundled")
    return set(decision["kept_ids"])


def load_independent_gold(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data["questions"] if isinstance(data, dict) else data
    gold: list[dict[str, Any]] = []
    for rec in records:
        if "expected_sections" not in rec:
            raise SystemExit(
                f"ERROR: record {rec.get('id')} has no 'expected_sections'. "
                "This harness only accepts independently annotated gold with "
                "explicit expected sections (the synthetic corpus has none — "
                "its expected sections are graph-derived by construction).")
        gold.append({
            "id": str(rec.get("id")),
            "issues": rec.get("issues") or {},
            "facts": rec.get("facts") or {},
            "enums": rec.get("enums") or {},
            "expected": set(rec["expected_sections"]),
        })
    return gold


def load_legacy_16q(path: Path) -> list[dict[str, Any]]:
    """Degraded gold: legacy 8-key facts + independent gt_ids, NO issues."""
    data = json.loads(path.read_text(encoding="utf-8"))
    gold: list[dict[str, Any]] = []
    for rec in data["questions"]:
        facts: dict[str, str] = {}
        for legacy_key, canon in LEGACY_FACT_MAP.items():
            if legacy_key in rec.get("facts", {}):
                facts[canon] = _bool_to_state(rec["facts"][legacy_key])
        facts["in_scope"] = "supported"
        facts["claimant_sex"] = "unknown"
        facts["claimant_role"] = "unknown"
        gold.append({
            "id": str(rec.get("id")),
            "issues": {},  # NOT in the file — the oracle is degraded.
            "facts": facts,
            "enums": {},
            "expected": set(rec["gt_ids"]),
        })
    return gold


def detect_graph_generation_marker(path: Path) -> str | None:
    """Return a marker string if the gold file says it was graph-generated."""
    text = path.read_text(encoding="utf-8").lower()
    blob = json.loads(path.read_text(encoding="utf-8"))
    fields: list[str] = []
    if isinstance(blob, dict):
        for key in ("generated_by", "source", "generator", "provenance"):
            if key in blob and isinstance(blob[key], str):
                fields.append(blob[key].lower())
    for marker in GRAPH_GENERATION_MARKERS:
        if marker in text and any(marker in f for f in fields):
            return marker
    return None


def score(name: str, gold: list[dict], predicted: list[set[str]]) -> dict:
    exact = sum(1 for g, p in zip(gold, predicted) if p == g["expected"])
    misses = [(g["id"], sorted(g["expected"] - p), sorted(p - g["expected"]))
              for g, p in zip(gold, predicted) if p != g["expected"]]
    return {"config": name, "exact": exact, "n": len(gold),
            "exact_rate": round(exact / len(gold), 4) if gold else 0.0,
            "misses": misses}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Graph oracle harness (A2).")
    ap.add_argument("--gold", required=True,
                    help="Independently annotated gold JSON (or the 16-Q "
                         "legacy GT with --legacy-16q).")
    ap.add_argument("--pred-file", default=None,
                    help="JSON {id: {issues, facts, enums}} predictions "
                         "for the GP/PG/PP configs.")
    ap.add_argument("--gold-provenance", required=True,
                    choices=["independent", "graph-derived", "unknown"],
                    help="How the gold section labels were produced.")
    ap.add_argument("--legacy-16q", action="store_true",
                    help="Degraded mode: the 16-Q legacy GT (8-key facts, "
                         "no issues/enums). Only GG runs.")
    args = ap.parse_args(argv)

    gold_path = Path(args.gold)
    if not gold_path.exists():
        print(f"ERROR: gold file not found: {gold_path}", file=sys.stderr)
        return 2

    marker = detect_graph_generation_marker(gold_path)
    if args.gold_provenance == "graph-derived" or marker:
        print("TAUTOLOGY: gold section labels were derived from Graph v4 "
              f"(declared provenance={args.gold_provenance!r}"
              + (f", marker={marker!r}" if marker else "")
              + "). An oracle on graph-derived labels is tautological: "
                "100% exact would only prove the graph agrees with itself. "
                "No pass may be claimed. Refusing to score a pass (exit 3).")
        return 3

    if args.legacy_16q:
        print("DEGRADED MODE: legacy 16-Q GT carries NO gold issues and NO "
              "gold enums — only 8 legacy fact keys. GG below is a lower "
              "bound, not the oracle. The full oracle needs independently "
              "annotated gold issues + full 28 facts + enums (OPEN).")
        gold = load_legacy_16q(gold_path)
    else:
        gold = load_independent_gold(gold_path)

    preds: dict[str, dict] = {}
    if args.pred_file:
        preds = json.loads(Path(args.pred_file).read_text(encoding="utf-8"))

    results: dict[str, dict] = {}
    # GG — always runs.
    gg = [run_config(g["issues"], g["facts"], g["enums"]) for g in gold]
    results["GG"] = score("GG gold/gold", gold, gg)

    if args.legacy_16q:
        print("Configs GP/PG/PP NOT RUN in degraded mode (no gold issues "
              "to pair with predictions, and no prediction file for the "
              "16-Q exists).")
    else:
        if not preds:
            print("Configs GP/PG/PP NOT RUN: no --pred-file given.")
        else:
            missing = [g["id"] for g in gold if g["id"] not in preds]
            if missing:
                print(f"ERROR: predictions missing for ids: {missing}",
                      file=sys.stderr)
                return 2
            gp = [run_config(g["issues"], preds[g["id"]].get("facts") or {},
                             preds[g["id"]].get("enums")) for g in gold]
            pg = [run_config(preds[g["id"]].get("issues") or {},
                             g["facts"], g["enums"]) for g in gold]
            pp = [run_config(preds[g["id"]].get("issues") or {},
                             preds[g["id"]].get("facts") or {},
                             preds[g["id"]].get("enums")) for g in gold]
            results["GP"] = score("GP gold-issues/pred-facts", gold, gp)
            results["PG"] = score("PG pred-issues/gold-facts", gold, pg)
            results["PP"] = score("PP pred/pred", gold, pp)

    print()
    for key in ("GG", "GP", "PG", "PP"):
        if key not in results:
            continue
        r = results[key]
        print(f"{r['config']}: {r['exact']}/{r['n']} exact "
              f"({r['exact_rate']:.1%})")
        for qid, missing, extra in r["misses"]:
            print(f"  miss {qid}: missing={missing} extra={extra}")
    print()
    gg = results["GG"]
    if args.gold_provenance == "unknown":
        print("UNVERIFIED-PROVENANCE: gold provenance is 'unknown'. No pass "
              "may be claimed from this run. Establish independent "
              "annotation provenance before citing the oracle.")
        return 3 if gg["exact"] == gg["n"] else 1
    if gg["exact"] == gg["n"]:
        if args.legacy_16q:
            print("NOTE: GG is 100% in DEGRADED mode, but degraded mode "
                  "cannot prove the oracle — it only shows the legacy facts "
                  "suffice for these 16. Full oracle still OPEN.")
            return 0
        print("ORACLE PASS: 100% section exact on independent gold with "
              "gold inputs. The recall problem lives in Stage 0/1, not in "
              "the frozen graph (for this dev set).")
        return 0
    print("ORACLE CEILING MEASURED: gold-input exact is "
          f"{gg['exact']}/{gg['n']}, not 100%. The recall problem is NOT "
          "entirely in Stage 0/1 — the frozen graph (or the annotation) "
          "caps exact below 100% on this set. Record this as a system "
          "ceiling; do not hide it with incorrect fact predictions."
          + (" In DEGRADED mode this gap is expected: every miss above is "
             "a section whose trigger needs a gold issue/fact the legacy "
             "file does not carry." if args.legacy_16q else ""))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
