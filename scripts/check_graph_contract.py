"""Phase A gate A1 — dead fact keys + graph contract check.

Reads how ``src/laya_v7_graph.py`` consumes issues/facts/enums, compares
against the classifier's ``FACTS`` / ``ISSUES`` / enum heads (from
``src/laya_v7_classifier.py``) plus deterministic derivations, and prints a
coverage table.

Classification of each graph-consumed key (see docs/impl_phaseA_A1_graph_contract.md
for the evidence behind each row):

  FACT        — a head in the classifier's FACTS (28) / ISSUES (11) / ENUMS.
  DERIVED     — assigned inside ``_normalize_legacy_facts`` from a FACT/enum
                key (e.g. ``stridhan_held_or_disposed`` from ``stridhan_claim``),
                or built by the Stage 1 -> Stage 2 bridge
                (``tests/recall_eval.py::predict_sections_from_stage1``:
                ``negated_issues`` / ``denied_issues`` from denied intents).
  DEFAULTED   — assigned a constant default inside ``_normalize_legacy_facts``
                (``domestic_relationship=True``, ``open_fact_markers=set()``).
                The graph treats absence as this value; it is NOT a producer.
  LEGACY      — read ONLY inside ``_normalize_legacy_facts`` as input to a
                derivation whose target is a FACT (``gold_fact``,
                ``magistrate_case_only``, ``proceeding_pending``). The
                classifier never emits these; harmless while the target FACT
                is present, but they are not classifier outputs.
  ALIAS       — ``stridhan_sold``: OR-fallback spelling of the canonical
                ``stridhan_sold_or_mortgaged`` (graph L~``_derive_escalations_v7``).
  UNCOVERED   — no classifier head, no derivation, no default supplies a
                meaningful value. In the classifier path the graph reads
                ``False`` / absent for these on every question.

Exit code: 0 iff 0 UNCOVERED keys (100% of graph input keys covered);
1 otherwise. Reverse-dead outputs (classifier heads the graph never reads:
``school_fees_fact``, ``procedure``, ``modality_time``) are reported as
warnings; they do not change the exit code.

Pure python — no torch needed. Run from the repo root:

    python3 scripts/check_graph_contract.py
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from laya_v7_classifier import ENUMS, FACTS, ISSUES  # noqa: E402
from laya_integrated import BRIDGE_DERIVED_KEYS  # noqa: E402

GRAPH_PATH = REPO_ROOT / "src" / "laya_v7_graph.py"

# Keys whose only reader is _derive_escalations_v7 / layer_a_filter_options
# are escalation/filter-only; keys read in evaluate_stage2_v7's slices can
# change kept_ids. Impact is computed from the source (which function body
# mentions the key), not from this table.
ESCALATION_ONLY_FUNCS = {"_derive_escalations_v7", "layer_a_filter_options"}

# Bridge-derived keys: denied-intent projections + C1 runtime _attach_bridge_facts.
BRIDGE_DERIVED = {"negated_issues", "denied_issues"} | set(BRIDGE_DERIVED_KEYS)

# Legacy-only inputs to _normalize_legacy_facts derivations.
LEGACY_INPUTS = {"gold_fact", "magistrate_case_only", "proceeding_pending"}

# Alias spellings whose canonical key is a FACT.
ALIASES = {"stridhan_sold": "stridhan_sold_or_mortgaged"}


def _function_bodies(src: str) -> dict[str, str]:
    """Split module source into {function_name: body} (top-level defs)."""
    bodies: dict[str, str] = {}
    parts = re.split(r"(?m)^def (\w+)\(", src)
    # parts[0] = module header; then alternating name, body.
    for i in range(1, len(parts) - 1, 2):
        bodies[parts[i]] = parts[i + 1]
    return bodies


def extract_graph_keys(src: str) -> tuple[Counter, dict[str, set[str]]]:
    """All fact/enum keys the graph reads, and which functions read them."""
    keys: Counter = Counter()
    readers: dict[str, set[str]] = defaultdict(set)
    bodies = _function_bodies(src)
    patterns = [
        r"(?:proved_true|fact_value|is_denied)\((?:facts|f),\s*\"([^\"]+)\"",
        r"_as_str\((?:facts|f),\s*\"([^\"]+)\"",
        r"(?:facts|f)\.get\(\"([^\"]+)\"",
        r"(?:facts|f)\[\"([^\"]+)\"\]",
        r"\"([^\"]+)\"\s+in\s+(?:facts|f)\b",
    ]
    for fname, body in bodies.items():
        for pat in patterns:
            for m in re.finditer(pat, body):
                keys[m.group(1)] += 1
                readers[m.group(1)].add(fname)
    # _wanted("issue") calls are issue consumption.
    issue_readers: dict[str, set[str]] = defaultdict(set)
    for fname, body in bodies.items():
        for m in re.finditer(r"_wanted\(\"([^\"]+)\"\)", body):
            issue_readers[m.group(1)].add(fname)
    return keys, readers, issue_readers  # type: ignore[return-value]


def normaliser_assignments(src: str) -> tuple[set[str], set[str]]:
    """Keys assigned in _normalize_legacy_facts, split into derived vs defaulted.

    Derived: assigned from another fact key (``f["a"] = proved_true(f, "b")``
    or a conditional on another key). Defaulted: assigned a constant
    (``True``, ``set()``) when the key is absent.
    """
    start = src.index("def _normalize_legacy_facts")
    end = src.index("def _derive_escalations_v7")
    body = src[start:end]
    assigned = set(re.findall(r"f\[\"([^\"]+)\"\\]\s*=", body))
    derived: set[str] = set()
    defaulted: set[str] = set()
    for key in assigned:
        # The assignment block for this key: text from its first assignment
        # to the next top-level statement is approximated by the lines
        # mentioning the key.
        lines = [ln for ln in body.splitlines() if f'"{key}"' in ln]
        joined = " ".join(lines)
        if "proved_true(f" in joined or "in f" in joined:
            derived.add(key)
        else:
            defaulted.add(key)
    # Hand-verified overrides (the heuristic above is line-local):
    # - proceeding_pending_hma / stridhan_claim / stridhan_held_or_disposed
    #   are conditional derivations from legacy keys.
    # - domestic_relationship / in_scope / negated_issues / open_fact_markers
    #   are constant defaults when absent.
    derived |= {"proceeding_pending_hma", "stridhan_claim",
                "stridhan_held_or_disposed"}
    defaulted |= {"domestic_relationship", "in_scope", "negated_issues",
                  "open_fact_markers"}
    derived -= defaulted
    return derived, defaulted


def classify(key: str, derived: set[str], defaulted: set[str]) -> str:
    if key in FACTS:
        return "FACT"
    if key in ENUMS:
        return "ENUM"
    if key in BRIDGE_DERIVED:
        return "DERIVED (bridge)"
    if key in derived:
        return "DERIVED (graph normaliser)"
    if key in defaulted:
        return "DEFAULTED (graph normaliser)"
    if key in LEGACY_INPUTS:
        return "LEGACY (normaliser input only)"
    if key in ALIASES:
        return f"ALIAS of {ALIASES[key]}"
    return "UNCOVERED"


def main() -> int:
    src = GRAPH_PATH.read_text(encoding="utf-8")
    keys, readers, issue_readers = extract_graph_keys(src)
    derived, defaulted = normaliser_assignments(src)

    print(f"Graph file: {GRAPH_PATH.relative_to(REPO_ROOT)}")
    print(f"Classifier vocab: {len(ISSUES)} issues, {len(FACTS)} facts, "
          f"enums {sorted(ENUMS)}")
    print(f"Distinct graph-consumed fact/enum keys: {len(keys)}")
    print()
    print(f"{'key':<42} {'class':<28} {'impact':<16} readers")
    print("-" * 120)
    uncovered: list[str] = []
    counts: Counter = Counter()
    for key in sorted(keys):
        cls = classify(key, derived, defaulted)
        counts[cls.split(" ")[0]] += 1
        if cls == "UNCOVERED":
            uncovered.append(key)
        funcs = readers[key]
        if "_derive_escalations_v7" in funcs or funcs <= ESCALATION_ONLY_FUNCS:
            impact = "escalation/filter"
        elif "evaluate_stage2_v7" in funcs:
            impact = "kept_ids"
        else:
            impact = "normaliser"
        print(f"{key:<42} {cls:<28} {impact:<16} {', '.join(sorted(funcs))}")
    print()
    print("Issues consumed by the graph via _wanted():")
    for name in sorted(issue_readers):
        print(f"  {name:<20} readers: {', '.join(sorted(issue_readers[name]))}")
    unread_issues = [i for i in ISSUES if i not in issue_readers]
    print(f"Issues NEVER read by the graph (reverse-dead): {unread_issues}")
    unread_facts = [f for f in FACTS if f not in keys]
    print(f"Facts NEVER read by the graph (reverse-dead): {unread_facts}")
    unread_enums = [e for e in ENUMS if e not in keys]
    print(f"Enums NEVER read by the graph (reverse-dead): {unread_enums}")
    print()
    print("Summary by class:")
    for cls, n in sorted(counts.items()):
        print(f"  {cls}: {n}")
    print(f"  UNCOVERED keys: {len(uncovered)}")
    if uncovered:
        print("  UNCOVERED list:")
        for key in uncovered:
            print(f"    - {key}")
        print()
        print("FAIL: graph input keys without a classifier producer / "
              "derivation. A1 gate NOT passed (exit 1).")
        return 1
    print()
    print("PASS: 100% of graph input keys covered, 0 dead keys (exit 0).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
