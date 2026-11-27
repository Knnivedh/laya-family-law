"""Declarative Graph v4.1 interpreter for LAYA v7.1 (10x plan §2, V71-P2-2).

This module actually loads ``graph/laya-crpc-bns-section-decision-tree-v4.1.json``
and executes it — unlike ``laya_v7_graph.evaluate_stage2_v7``, which never
loads the graph JSON and never calls ``layer_a_filter_options()``.

What it does
------------
1. Structural traversal from the single root ``root:issue-classification``,
   running Layer A (``layer_a_filter_options``) on every choice node visited
   and recording what Layer A removes.
2. Legal disposition via the existing ``evaluate_stage2_v7`` (the graph's
   edge ``condition`` strings are human-readable prose, not executable
   predicates, so full declarative legal execution is NOT claimed here —
   see the honesty note in ``execute``). The engine's contribution is that
   the pre-gate candidate set is now genuine: ``candidates_before_gate`` is
   every section Stage 2 actually considered (all disposition keys:
   eligible + conditional + inapplicable), fixing the ``laya_v7.py:100,168``
   clone where ``candidates_before_stage2`` was just a copy of ``kept_ids``
   and ``prose_forbidden_check`` was passed ``[]`` instead of ``gated_out``.
3. Validation of the v4.1 graph: 100% single-root reachability, zero
   dangling edges, non-empty options on every choice node, welfare-principle
   scoring metadata, bnss-144-3 / bnss-146 nodes under
   ``maintenance:post-order-enforcement``.

Vocabulary profiles (plan §2.3 V71-P2-1) map onto the Stage 2 custody
vocabulary; the section-level folding for ``v4_legacy_18`` is applied in
``apply_vocab_profile`` so the mapping is explicit and testable even though
today's Stage 2 never emits bnss-144-3 / bnss-146 (Lane 01 owns Stage 2).
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
GRAPH_V41_PATH = REPO_ROOT / "graph" / "laya-crpc-bns-section-decision-tree-v4.1.json"
GRAPH_V4_PATH = REPO_ROOT / "graph" / "laya-crpc-bns-section-decision-tree-v4.json"

ROOT_NODE = "root:issue-classification"

VOCAB_PROFILES: tuple[str, ...] = (
    "v4_legacy_18",
    "brutal_primary",
    "maintenance_sub_routes",
)

#: Profile -> custody_vocab passed to evaluate_stage2_v7.
PROFILE_CUSTODY_VOCAB: dict[str, str] = {
    "v4_legacy_18": "v3_bundled",
    "brutal_primary": "statutory_primary",
    "maintenance_sub_routes": "v3_bundled",
}

#: Sections folded into bnss-144 under the legacy 18-section vocabulary.
LEGACY_FOLD: dict[str, str] = {
    "bnss-144-3": "bnss-144",
    "bnss-146": "bnss-144",
}


def load_graph_v41(path: str | Path | None = None) -> dict[str, Any]:
    """Load the Graph v4.1 JSON. Raises FileNotFoundError if it is absent."""
    p = Path(path) if path is not None else GRAPH_V41_PATH
    if not p.exists():
        raise FileNotFoundError(
            f"Graph v4.1 not found at {p}. Run: python3 src/build_graph_v4.py --v41"
        )
    return json.loads(p.read_text(encoding="utf-8"))


def load_graph(path: str | Path | None = None) -> dict[str, Any]:
    """Load v4.1 by default; explicit path override for tests."""
    return load_graph_v41(path)


def audit_reachability_single_root(graph: dict[str, Any]) -> dict[str, Any]:
    """BFS reachability from the SINGLE root node (plan §2.4 exit criterion).

    NOTE: this differs deliberately from
    ``laya_v7_graph.audit_graph_reachability``, which seeds four declared
    entry nodes and therefore reports 66/66 on v4. The v7.1 bar is stricter:
    100% reachable from ``root:issue-classification`` alone.
    """
    node_ids = {n["node_id"] for n in graph["nodes"]}
    adj: dict[str, list[str]] = {}
    for edge in graph["edges"]:
        adj.setdefault(edge["from"], []).append(edge["to"])
    visited: set[str] = set()
    queue: deque[str] = deque([ROOT_NODE])
    while queue:
        cur = queue.popleft()
        if cur in visited:
            continue
        visited.add(cur)
        queue.extend(adj.get(cur, ()))
    return {
        "root": ROOT_NODE,
        "total_nodes": len(node_ids),
        "reachable_nodes": len(visited & node_ids),
        "unreachable_nodes": sorted(node_ids - visited),
        "reachable": node_ids <= visited,
    }


def validate_graph_v41(graph: dict[str, Any]) -> dict[str, Any]:
    """Structural validation of a v4.1 graph dict. Returns a report dict."""
    node_ids = {n["node_id"] for n in graph["nodes"]}
    section_ids = {s["id"] for s in graph["sections"]}
    problems: list[str] = []

    reach = audit_reachability_single_root(graph)
    if not reach["reachable"]:
        problems.append(f"unreachable from root: {reach['unreachable_nodes']}")

    for i, e in enumerate(graph["edges"]):
        if e["from"] not in node_ids:
            problems.append(f"edge[{i}] dangling from={e['from']}")
        if e["to"] not in node_ids:
            problems.append(f"edge[{i}] dangling to={e['to']}")

    for n in graph["nodes"]:
        if n.get("type") == "choice" and not n.get("options"):
            problems.append(f"choice node {n['node_id']} has empty options")
        for sid in n.get("section_set", []):
            if sid not in section_ids:
                problems.append(f"node {n['node_id']} unknown section {sid}")

    for s in graph["sections"]:
        for rs in s.get("related_sections", []):
            if isinstance(rs, dict) and rs.get("section_id") not in section_ids:
                problems.append(f"section {s['id']} unresolved related {rs.get('section_id')}")

    welfare = next((s for s in graph["sections"] if s["id"] == "welfare-principle"), None)
    if welfare is None:
        problems.append("missing welfare-principle section")
    else:
        lq = welfare.get("laya_question") or {}
        if lq.get("type") != "score":
            problems.append("welfare-principle.laya_question type is not 'score'")
        if "scoring_semantics" not in lq:
            problems.append("welfare-principle.laya_question lacks scoring_semantics")

    for sid in ("bnss-144-3", "bnss-146"):
        if sid not in section_ids:
            problems.append(f"missing section {sid}")
    poe = next((n for n in graph["nodes"] if n["node_id"] == "maintenance:post-order-enforcement"), None)
    if poe is None:
        problems.append("missing maintenance:post-order-enforcement node")
    else:
        poe_set = set(poe.get("section_set", []))
        if not {"bnss-144-3", "bnss-146"} <= poe_set:
            problems.append("post-order-enforcement section_set lacks bnss-144-3/bnss-146")
    for nid in ("stage2:bnss-144-3-leaf", "stage2:bnss-146-leaf"):
        if nid not in node_ids:
            problems.append(f"missing node {nid}")

    return {
        "valid": not problems,
        "problems": problems,
        "sections": len(section_ids),
        "nodes": len(node_ids),
        "edges": len(graph["edges"]),
        "reachability": reach,
    }


def apply_vocab_profile(kept_ids: list[str], vocab_profile: str) -> list[str]:
    """Map kept sections through a vocabulary profile.

    ``v4_legacy_18`` folds bnss-144-3 / bnss-146 into bnss-144 (16-Q /
    Sealed / v7 backward comparability). The other profiles keep the
    sub-routes distinct. Unknown profiles raise ValueError — silently
    defaulting would hide a caller bug.
    """
    if vocab_profile not in VOCAB_PROFILES:
        raise ValueError(f"Unknown vocab_profile {vocab_profile!r}; expected one of {VOCAB_PROFILES}")
    if vocab_profile == "v4_legacy_18":
        folded: list[str] = []
        for sid in kept_ids:
            mapped = LEGACY_FOLD.get(sid, sid)
            if mapped not in folded:
                folded.append(mapped)
        return folded
    return list(kept_ids)


def traverse_with_layer_a(
    graph: dict[str, Any], facts: dict[str, Any]
) -> dict[str, Any]:
    """Walk the graph from the root, applying Layer A at each choice node.

    Returns visited nodes in BFS order, the per-node Layer A outcome, and
    the genuine ``gated_out_layer_a`` list (``"node :: option [reason]"``).
    Edge conditions are prose, not predicates, so traversal follows the
    graph structure (all outgoing edges) rather than pretending to evaluate
    conditions — the legal disposition itself is computed by Stage 2 in
    ``execute``.
    """
    from .laya_v7_graph import layer_a_filter_options

    nodes = {n["node_id"]: n for n in graph["nodes"]}
    adj: dict[str, list[str]] = {}
    for edge in graph["edges"]:
        adj.setdefault(edge["from"], []).append(edge["to"])

    visited: list[str] = []
    seen: set[str] = set()
    layer_a: dict[str, dict[str, Any]] = {}
    gated_out_layer_a: list[str] = []
    queue: deque[str] = deque([ROOT_NODE])
    while queue:
        cur = queue.popleft()
        if cur in seen or cur not in nodes:
            continue
        seen.add(cur)
        visited.append(cur)
        node = nodes[cur]
        options = node.get("options") or []
        # Root options are structured dicts ({value, next, section_set});
        # Layer A filters plain-string option lists only.
        if node.get("type") == "choice" and options and isinstance(options[0], str):
            kept_opts, removed_opts = layer_a_filter_options(cur, list(options), facts)
            layer_a[cur] = {"kept_options": kept_opts, "removed_options": removed_opts}
            gated_out_layer_a.extend(f"{cur} :: {r}" for r in removed_opts)
        queue.extend(adj.get(cur, ()))
    return {
        "visited_nodes": visited,
        "visited_count": len(visited),
        "layer_a": layer_a,
        "gated_out_layer_a": gated_out_layer_a,
    }


def execute(
    graph: dict[str, Any],
    issues: dict[str, Any],
    facts: dict[str, Any],
    *,
    vocab_profile: str = "v4_legacy_18",
) -> dict[str, Any]:
    """Execute Graph v4.1: Layer A traversal + Stage 2 disposition.

    Honesty note: the *legal* routing (which sections are eligible /
    conditional / inapplicable) is still computed by
    ``laya_v7_graph.evaluate_stage2_v7`` — the graph JSON's edge conditions
    are English prose, not an executable predicate language, so a fully
    declarative legal execution is not possible from this JSON alone and is
    not faked here. What this engine guarantees, and what v7 did not, is:

    * the graph file is actually loaded and traversed (not bypassed);
    * Layer A runs on every visited choice node and its removals are recorded;
    * ``candidates_before_gate`` is the genuine pre-gate set: every section
      Stage 2 considered (all disposition keys), NOT a clone of kept_ids;
    * ``gated_out`` passed onward is the real union of Layer A removals and
      Stage 2 gated_out — never ``[]`` by construction — so Fb is measurable
      (Lane 10 scorer contract C1).
    """
    if vocab_profile not in VOCAB_PROFILES:
        raise ValueError(f"Unknown vocab_profile {vocab_profile!r}; expected one of {VOCAB_PROFILES}")
    from .laya_v7_graph import evaluate_stage2_v7

    traversal = traverse_with_layer_a(graph, facts)
    decision = evaluate_stage2_v7(
        issues,
        facts,
        custody_vocab=PROFILE_CUSTODY_VOCAB[vocab_profile],
    )
    dispositions = decision.get("dispositions", {}) or {}
    # Genuine pre-gate candidates: everything Stage 2 considered, including
    # conditional and inapplicable dispositions (the v7 clone only had kept).
    candidates_before_gate = sorted(dispositions.keys())
    gated_out_stage2 = list(decision.get("gated_out", []) or [])
    gated_out = list(traversal["gated_out_layer_a"]) + gated_out_stage2
    kept_raw = list(decision.get("kept_ids", []) or [])
    kept_ids = apply_vocab_profile(kept_raw, vocab_profile)

    return {
        **{k: v for k, v in decision.items() if k not in ("kept_ids",)},
        "kept_ids": kept_ids,
        "kept_ids_before_vocab_profile": kept_raw,
        "vocab_profile": vocab_profile,
        "visited_nodes": traversal["visited_nodes"],
        "visited_count": traversal["visited_count"],
        "layer_a": traversal["layer_a"],
        "candidates_before_gate": candidates_before_gate,
        "gated_out_layer_a": traversal["gated_out_layer_a"],
        "gated_out_stage2": gated_out_stage2,
        "gated_out": gated_out,
        # Fb inputs for the Lane 10 scorer: the pre-gate candidate set plus
        # everything gated out before prose. Fb itself is scored by Lane 10
        # (candidates_before_gate entries that violate statutory prerequisites).
        "fb_inputs": {
            "candidates_before_gate": candidates_before_gate,
            "gated_out_layer_a": traversal["gated_out_layer_a"],
            "gated_out_stage2": gated_out_stage2,
        },
    }
