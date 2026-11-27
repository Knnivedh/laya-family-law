"""Integrity tests for Decision Graph v4 and frozen repository artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FROZEN_SHA256 = {
    "graph/laya-crpc-bns-section-decision-tree-v2.json": "c7e095ad185242e9360d8b9f180fefff894f5677b52d188174413a32a2704255",
    "graph/laya-crpc-bns-section-decision-tree-v3.json": "67bf2b04ca946f7c7fa3062068e01ce051fbce8f4d740c281afe6fff841c34a5",
    "ground-truth/ground-truth-v2-hma27-A.json": "87818b1b659583bf06a25280a6b53dabedf65f29cab99058f02b8ed31c9ac97e",
    "test-bank/brutal-bank-v1-frozen.json": "934a2b2265ac137c96939e1fbeca3682a037010e42f972bfd459c2fcac4ec717",
    "test-bank/sealed/sealed-fresh-20.json": "1d8b5dc376e711c3ac6ead4424bb2d8ce52b07552b9a533ad86e0616dbcf8837",
    "test-bank/sealed/sealed-kannada-8.json": "2f652af1123a22441cc4158ddf480ef0981aa923858bbcb9dc3622f5e5c25853",
    "notebooks/live-laya-colab-test-v6-brutal.ipynb": "d6ee579534b5f2ac0b836f834954afe73fd5480d0da7a7a9fc5bec6e2461ff98",
}


def lf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_frozen_files_untouched() -> None:
    for rel, expected in FROZEN_SHA256.items():
        actual = lf_sha256(REPO_ROOT / rel)
        assert actual == expected, f"FROZEN FILE MODIFIED: {rel} ({actual} != {expected})"


def test_graph_v4_integrity() -> None:
    v4_path = REPO_ROOT / "graph" / "laya-crpc-bns-section-decision-tree-v4.json"
    g = json.loads(v4_path.read_text(encoding="utf-8"))

    assert (len(g["sections"]), len(g["nodes"]), len(g["edges"])) == (34, 66, 99), (
        f"Unexpected v4 counts: {len(g['sections'])}/{len(g['nodes'])}/{len(g['edges'])}"
    )
    section_ids = {s["id"] for s in g["sections"]}
    node_ids = {n["node_id"] for n in g["nodes"]}
    assert len(section_ids) == 34
    assert len(node_ids) == 66

    # Zero dangling edges
    for i, e in enumerate(g["edges"]):
        assert e["from"] in node_ids, f"Edge [{i}] dangling from={e['from']}"
        assert e["to"] in node_ids, f"Edge [{i}] dangling to={e['to']}"

    # Zero unresolved related_sections
    for s in g["sections"]:
        assert isinstance(s.get("laya_question"), dict), f"{s['id']} laya_question not dict"
        for idx, rs in enumerate(s.get("related_sections", [])):
            assert isinstance(rs, dict), f"{s['id']}.related_sections[{idx}] not dict"
            assert rs.get("section_id") in section_ids, (
                f"{s['id']}.related_sections[{idx}] unresolved: {rs!r}"
            )

    # All node section_set entries exist in SECTION_IDS
    for n in g["nodes"]:
        assert set(n.get("section_set", [])) <= section_ids, f"{n['node_id']} bad section_set"

    # Specific v3 defects resolved
    bnss_rels = [r["section_id"] for r in next(s for s in g["sections"] if s["id"] == "bnss-144")["related_sections"]]
    assert "hmga-6" not in bnss_rels and "hmga-1956-s6" in bnss_rels
    for target in ("stage1:escalate-clarify", "stage2:escalate-demand-first", "stage2:hma-13b-leaf", "stage2:hma-27-leaf", "stage2:pwdva-17-19-residence-leaf", "stage2:pwdva-18-protection-leaf"):
        assert target in node_ids, f"Missing expected v4 node {target}"


if __name__ == "__main__":
    test_frozen_files_untouched()
    test_graph_v4_integrity()
    print("GRAPH V4 + FROZEN SHA TEST PASS: 34 sections / 66 nodes / 99 edges, 0 dangling edges, 7/7 frozen hashes intact.")
