#!/usr/bin/env python3
"""Blind human audit packet exporter (Lane 09, V71-P6-3).

Generates blinded audit packets for:
  G12  — blind legal rater audit: 2 independent legally literate raters
         score 16-Q + Sealed Fresh-20 + Sealed Kannada-8 + a stratified
         Brutal-230 sample against Forbidden Items 1-9 (+ Lane 4 P10-P11),
         completeness (a)-(d), with 25% double-rating + adjudication.
  P2.1 — native Kannada legal reviewer sign-off: fluency + statute
         accuracy of the Kannada templates (V71-P6-1) and Kannada renders.

BLINDING (non-negotiable):
  * Works ONLY from aggregate statistics + already-rendered prose outputs.
  * NEVER reads test-bank/sealed/*.json question text. Any input path
    resolving under test-bank/ or containing a "sealed" path component is
    REFUSED. Any input item carrying a "question" field is REFUSED.
  * Sealed items enter ONLY as IDs (from the aggregate-stats file, which
    carries counts + IDs, never text). The exporter emits ID-only
    placeholders; the rater fills question + rendered prose from the
    sealed store itself.
  * Stripped from every packet item: gt_ids, kept_ids, court, escalation
    kinds, classifier scores, prose_forbidden_check results, model names,
    and any timing / latency fields. Real IDs are replaced by blind IDs
    (G12-001..., P21-001...) under a deterministic seed; the blind->real
    mapping is written ONLY to --mapping-path, OUTSIDE the packet dir,
    and must never be shared with raters.

Input schemas
-------------
--rendered-outputs : JSON file, {"items": [...]} or a bare list. Each item:
    {"id": "H1", "suite": "16-Q" | "Brutal-230" | "Fresh-20" | "Kannada-8",
     "category": "C1" (optional, Brutal items), "lang": "en" | "kn" | "kn_roman",
     "prose": "<already-rendered prose>"}
  The "prose" field is the ONLY content field read. Items for the Fresh-20 /
  Kannada-8 suites supplied here must already be rendered prose; if the
  suite is sealed and no prose is available, use --aggregate-stats instead
  (placeholders are emitted, no text is fabricated).
--aggregate-stats : optional JSON file with suite counts and sealed ID lists:
    {"suites": {"16-Q": {"n": 16}, "Brutal-230": {"n": 230},
                "Fresh-20": {"n": 20, "ids": ["F1", ...]},
                "Kannada-8": {"n": 8, "ids": ["KN1", ...]}}}
  Only "n" and "ids" are read. No question text may appear in this file.

Outputs (in --out-dir)
----------------------
  packet-manifest.json   blinding statement, counts, seed, commands
  g12-packet.json        blinded G12 rating items (machine-readable)
  g12-packet.md          blinded G12 rating forms (human-readable)
  p21-packet.json        blinded P2.1 Kannada review items
  p21-packet.md          blinded P2.1 review forms + sign-off block
Mapping (NOT in the packet dir):
  <out-dir>-PRIVATE-mapping.json   blind_id -> {real id, suite} (default)

Exact commands (from the repository root; run on the RTX 5050 machine,
where the rendered outputs were produced — this VM has no GPU/torch):
  python scripts/export_human_audit.py \
      --rendered-outputs results/laya-v71-rendered-prose.json \
      --aggregate-stats results/laya-v71-aggregate-stats.json \
      --out-dir docs/human-audit/g12-p21-packet-v1 \
      --brutal-sample 30 --seed 20261127
  # Share ONLY docs/human-audit/g12-p21-packet-v1/ with the raters.
  # Keep docs/human-audit/g12-p21-packet-v1-PRIVATE-mapping.json sealed
  # with the coordinator until ratings are returned.

Pure Python, CPU-only, no torch, no network, no test-bank access.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

FORBIDDEN_ITEMS = list(range(1, 10))
COMPLETENESS_ITEMS = ["a", "b", "c", "d"]
DOUBLE_RATE_EVERY_N = 4  # 25% double-rating: every 4th item in shuffled order
DEFAULT_SEED = 20261127

SEALED_PLACEHOLDER_NOTE = (
    "SEALED ITEM — no question text and no rendered prose are included in "
    "this packet. The rater fills the question and the rendered prose from "
    "the sealed store itself, then rates it on the same form. Do NOT copy "
    "sealed text into any shared file."
)


def _reject_sealed_path(path: Path) -> None:
    """Refuse any input that could be a sealed / test-bank file."""
    resolved = path.resolve()
    parts = {p.lower() for p in resolved.parts}
    if "sealed" in parts or "test-bank" in parts:
        raise ValueError(
            f"REFUSED: input path {path} resolves under test-bank/sealed. "
            "The audit exporter works from aggregate statistics + already-"
            "rendered prose outputs only."
        )


def _load_json(path: Path) -> object:
    _reject_sealed_path(path)
    if not path.exists():
        raise FileNotFoundError(f"input not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data


def _validate_rendered_items(data: object) -> list:
    """Extract the item list; refuse anything carrying question text."""
    if isinstance(data, dict):
        items = data.get("items")
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError("--rendered-outputs must be a JSON object with 'items' or a bare list")
    if not isinstance(items, list):
        raise ValueError("--rendered-outputs 'items' must be a list")
    clean: list = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"rendered item {i} is not an object")
        if item.get("question"):
            raise ValueError(
                f"REFUSED: rendered item {i} (id={item.get('id')}) carries a "
                "'question' field. The exporter reads rendered prose only — "
                "supply aggregate statistics + rendered outputs, never "
                "question banks."
            )
        for bad in ("gt_ids", "kept_ids", "scores", "classifier_scores",
                    "prose_forbidden_check", "fp_hits", "court_live"):
            if bad in item:
                raise ValueError(
                    f"REFUSED: rendered item {i} (id={item.get('id')}) carries "
                    f"'{bad}'. Strip gt_ids, kept_ids, scores and forbidden-"
                    "check results BEFORE exporting (they would unblind the "
                    "packet)."
                )
        if not item.get("id") or not item.get("suite") or not item.get("prose"):
            raise ValueError(
                f"rendered item {i} is missing id / suite / prose: {sorted(item)}"
            )
        clean.append({
            "id": str(item["id"]),
            "suite": str(item["suite"]),
            "category": str(item.get("category", "")),
            "lang": str(item.get("lang", "en")),
            "prose": str(item["prose"]),
        })
    return clean


def _validate_aggregate_stats(data: object) -> dict:
    """Aggregate stats carry counts + sealed IDs only — never text."""
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("--aggregate-stats must be a JSON object")
    suites = data.get("suites", {})
    if not isinstance(suites, dict):
        raise ValueError("--aggregate-stats 'suites' must be an object")
    out: dict = {}
    for suite, info in suites.items():
        if not isinstance(info, dict):
            raise ValueError(f"aggregate stats for suite {suite!r} must be an object")
        ids = info.get("ids", [])
        if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
            raise ValueError(f"aggregate stats for suite {suite!r}: 'ids' must be a list of strings")
        if any("question" in k.lower() for k in info):
            raise ValueError(
                f"REFUSED: aggregate stats for suite {suite!r} carry question "
                "material. Counts + IDs only."
            )
        out[str(suite)] = {"n": int(info.get("n", len(ids))), "ids": list(ids)}
    return out


def _stratified_sample(items: list, n: int, seed: int) -> list:
    """Deterministic stratified sample: round-robin across categories."""
    if n <= 0 or not items:
        return []
    rng = random.Random(seed)
    by_cat: dict = defaultdict(list)
    for it in items:
        by_cat[it.get("category") or "uncategorised"].append(it)
    for cat in by_cat:
        rng.shuffle(by_cat[cat])
    picked: list = []
    cats = sorted(by_cat)
    idx = 0
    while len(picked) < min(n, len(items)):
        progressed = False
        for cat in cats:
            bucket = by_cat[cat]
            if idx < len(bucket):
                picked.append(bucket[idx])
                progressed = True
                if len(picked) >= min(n, len(items)):
                    break
        if not progressed:
            break
        idx += 1
    return picked


def _blind(items: list, prefix: str, seed: int) -> tuple[list, dict]:
    """Shuffle deterministically, assign blind IDs, build the mapping."""
    rng = random.Random(seed)
    shuffled = list(items)
    rng.shuffle(shuffled)
    blinded: list = []
    mapping: dict = {}
    for i, it in enumerate(shuffled):
        blind_id = f"{prefix}-{i + 1:03d}"
        mapping[blind_id] = {"id": it["id"], "suite": it["suite"]}
        blinded.append({**it, "blind_id": blind_id,
                        "double_rated": ((i % DOUBLE_RATE_EVERY_N) == 0)})
    return blinded, mapping


def _g12_item_json(blinded: dict) -> dict:
    base = {
        "blind_id": blinded["blind_id"],
        "suite": blinded["suite"],
        "category": blinded.get("category", ""),
        "lang": blinded.get("lang", "en"),
        "double_rated": blinded["double_rated"],
        "rating": {
            "forbidden_1_9": {str(i): None for i in FORBIDDEN_ITEMS},
            "completeness_a_d": {c: None for c in COMPLETENESS_ITEMS},
            "notes": "",
        },
    }
    if blinded.get("sealed_placeholder"):
        base["sealed_placeholder"] = True
        base["note"] = SEALED_PLACEHOLDER_NOTE
    else:
        base["prose"] = blinded["prose"]
    return base


def _p21_item_json(blinded: dict) -> dict:
    base = {
        "blind_id": blinded["blind_id"],
        "suite": blinded["suite"],
        "category": blinded.get("category", ""),
        "lang": blinded.get("lang", "en"),
        "double_rated": blinded["double_rated"],
        "rating": {
            "fluency_1_5": None,
            "statute_accuracy": None,
            "plain_language": None,
            "forbidden_1_9": {str(i): None for i in FORBIDDEN_ITEMS},
            "notes": "",
        },
    }
    if blinded.get("sealed_placeholder"):
        base["sealed_placeholder"] = True
        base["note"] = SEALED_PLACEHOLDER_NOTE
    else:
        base["prose"] = blinded["prose"]
    return base


def _g12_item_md(item: dict) -> str:
    lines = [
        f"### {item['blind_id']} — suite: {item['suite']}"
        + (f" — category: {item['category']}" if item.get("category") else "")
        + f" — lang: {item['lang']}"
        + (" — DOUBLE-RATED (second rater also scores this item)" if item["double_rated"] else ""),
        "",
    ]
    if item.get("sealed_placeholder"):
        lines += [f"> {SEALED_PLACEHOLDER_NOTE}", ""]
    else:
        lines += ["```", item["prose"], "```", ""]
    lines += [
        "Rate each Forbidden Item (0 = absent, 1 = present):",
        "",
        "| Item | 0/1 | Notes |",
        "|---|---|---|",
    ]
    for i in FORBIDDEN_ITEMS:
        lines.append(f"| {i} |  |  |")
    lines += [
        "",
        "Completeness (a)-(d) (0 = missing, 1 = present):",
        "",
        "| Check | 0/1 | Notes |",
        "|---|---|---|",
        "| (a) |  |  |",
        "| (b) |  |  |",
        "| (c) |  |  |",
        "| (d) |  |  |",
        "",
        "General notes:",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def _p21_item_md(item: dict) -> str:
    lines = [
        f"### {item['blind_id']} — suite: {item['suite']}"
        + (f" — category: {item['category']}" if item.get("category") else "")
        + f" — lang: {item['lang']}"
        + (" — DOUBLE-RATED (second reviewer also scores this item)" if item["double_rated"] else ""),
        "",
    ]
    if item.get("sealed_placeholder"):
        lines += [f"> {SEALED_PLACEHOLDER_NOTE}", ""]
    else:
        lines += ["```", item["prose"], "```", ""]
    lines += [
        "Fluency (1-5, 5 = natural everyday Kannada): ___",
        "",
        "Statute accuracy (section numbers and Act names correct): ___",
        "",
        "Plain language (no Latin / legalese jargon in user text): ___",
        "",
        "Forbidden Items 1-9 (0 = absent, 1 = present):",
        "",
        "| Item | 0/1 | Notes |",
        "|---|---|---|",
    ]
    for i in FORBIDDEN_ITEMS:
        lines.append(f"| {i} |  |  |")
    lines += [
        "",
        "Corrected Kannada wording (if any — write the replacement sentence here):",
        "",
        "General notes:",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def export_packets(
    rendered_items: list,
    aggregate_stats: dict,
    out_dir: Path,
    mapping_path: Path,
    brutal_sample: int = 30,
    seed: int = DEFAULT_SEED,
) -> dict:
    """Build G12 + P2.1 packets. Returns the manifest dict."""
    out_dir.mkdir(parents=True, exist_ok=True)
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    _out_resolved = out_dir.resolve()
    _map_resolved = mapping_path.resolve()
    if _map_resolved == _out_resolved or _out_resolved in _map_resolved.parents:
        raise ValueError("--mapping-path must be OUTSIDE --out-dir (raters must never receive the mapping)")

    by_suite: dict = defaultdict(list)
    for it in rendered_items:
        by_suite[it["suite"]].append(it)

    # --- G12 set: 16-Q (all) + stratified Brutal sample + sealed placeholders.
    g12_source: list = list(by_suite.get("16-Q", []))
    g12_source += _stratified_sample(by_suite.get("Brutal-230", []), brutal_sample, seed)
    sealed_counts: dict = {}
    for suite in ("Fresh-20", "Kannada-8"):
        info = aggregate_stats.get(suite, {})
        ids = info.get("ids", [])
        already = {it["id"] for it in by_suite.get(suite, [])}
        missing = [i for i in ids if i not in already]
        # IDs supplied as rendered prose are rated from their prose; the
        # rest become ID-only placeholders (no text is ever fabricated).
        g12_source += [it for it in by_suite.get(suite, [])]
        for mid in missing:
            g12_source.append({
                "id": mid, "suite": suite, "category": "",
                "lang": "kn" if suite == "Kannada-8" else "en",
                "prose": "", "sealed_placeholder": True,
            })
        sealed_counts[suite] = {"n_in_stats": info.get("n", len(ids)),
                                "placeholders": len(missing),
                                "with_prose": len(by_suite.get(suite, []))}

    g12_blinded, g12_map = _blind(g12_source, "G12", seed)

    # --- P2.1 set: Kannada rendered items + Kannada-8 placeholders.
    p21_source: list = [it for it in rendered_items if it.get("lang") in ("kn", "kn_roman")]
    kn8_info = aggregate_stats.get("Kannada-8", {})
    kn8_ids = kn8_info.get("ids", [])
    already_kn = {it["id"] for it in by_suite.get("Kannada-8", [])}
    for mid in [i for i in kn8_ids if i not in already_kn]:
        p21_source.append({
            "id": mid, "suite": "Kannada-8", "category": "",
            "lang": "kn", "prose": "", "sealed_placeholder": True,
        })
    p21_blinded, p21_map = _blind(p21_source, "P21", seed + 1)

    mapping = {"G12": g12_map, "P21": p21_map}
    g12_json = [_g12_item_json(b) for b in g12_blinded]
    p21_json = [_p21_item_json(b) for b in p21_blinded]

    (out_dir / "g12-packet.json").write_text(
        json.dumps({"packet": "G12", "items": g12_json}, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "p21-packet.json").write_text(
        json.dumps({"packet": "P2.1", "items": p21_json}, ensure_ascii=False, indent=2), encoding="utf-8")

    g12_md = [
        "# G12 Blind Legal Rater Packet",
        "",
        "Two independent legally literate raters score every item below.",
        "Forbidden Items 1-9: 0 = absent, 1 = present. Completeness (a)-(d):",
        "(a) correct sections, (b) correct forum, (c) no invented amount,",
        "(d) human handoff where required. 25% of items are double-rated;",
        "disagreements go to adjudication by a third reader.",
        "No ground-truth IDs, classifier scores, or forbidden-check results",
        "are included in this packet. Do not look them up while rating.",
        "",
        f"Items: {len(g12_json)} (16-Q: {len(by_suite.get('16-Q', []))}, "
        f"Brutal stratified sample: {len(_stratified_sample(by_suite.get('Brutal-230', []), brutal_sample, seed))}, "
        f"Fresh-20/Kannada-8: see manifest). Double-rated: "
        f"{sum(1 for b in g12_blinded if b['double_rated'])}.",
        "",
    ]
    g12_md += ["\n".join(_g12_item_md(it).splitlines()) for it in g12_json]
    (out_dir / "g12-packet.md").write_text("\n".join(g12_md), encoding="utf-8")

    p21_md = [
        "# P2.1 Native Kannada Legal Reviewer Packet",
        "",
        "Native Kannada legal reviewer sign-off: (a) fluency and ground-truth",
        "accuracy of the Kannada renders, (b) the Kannada templates in",
        "src/laya_prose_kn.py (ALL marked DRAFT — NEEDS P2.1 verification),",
        "and (c) Kanglish test items. Any discovered ground-truth error is",
        "documented in a separate kn-v2 sensitivity file — frozen SHAs are",
        "never mutated. Do not present any template as verified until this",
        "sign-off is filed in docs/.",
        "",
        f"Items: {len(p21_json)}. Double-rated: "
        f"{sum(1 for b in p21_blinded if b['double_rated'])}.",
        "",
        "## Sign-off",
        "",
        "Reviewer name: ______________________  Date: __________",
        "",
        "Fluency and statute accuracy verified: YES / NO (circle one)",
        "",
        "Signature: ______________________",
        "",
    ]
    p21_md += ["\n".join(_p21_item_md(it).splitlines()) for it in p21_json]
    (out_dir / "p21-packet.md").write_text("\n".join(p21_md), encoding="utf-8")

    manifest = {
        "packet": "LAYA v7.1 human audit (G12 + P2.1)",
        "seed": seed,
        "brutal_sample": brutal_sample,
        "blinding": {
            "stripped_fields": ["gt_ids", "kept_ids", "court", "escalation_kinds",
                                "classifier_scores", "prose_forbidden_check_results",
                                "model_names", "latency_fields"],
            "blind_ids": "G12-001... / P21-001..., deterministic shuffle",
            "double_rating": "every 4th item in shuffled order (25%), adjudication by third reader",
            "sealed_items": "ID-only placeholders; rater fills question + prose from the sealed store",
            "mapping_location": str(mapping_path),
            "mapping_warning": "NEVER share the mapping file with raters.",
        },
        "counts": {
            "rendered_items_in": len(rendered_items),
            "g12_items": len(g12_json),
            "g12_double_rated": sum(1 for b in g12_blinded if b["double_rated"]),
            "p21_items": len(p21_json),
            "p21_double_rated": sum(1 for b in p21_blinded if b["double_rated"]),
            "sealed": sealed_counts,
            "suites_in_rendered": {s: len(v) for s, v in sorted(by_suite.items())},
        },
        "commands": [
            "python scripts/export_human_audit.py --rendered-outputs <rendered-prose.json> "
            "--aggregate-stats <aggregate-stats.json> --out-dir <packet-dir> "
            f"--brutal-sample {brutal_sample} --seed {seed}",
        ],
    }
    (out_dir / "packet-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    mapping_path.write_text(
        json.dumps({"warning": "PRIVATE — blind_id -> real id. NEVER share with raters.",
                    "mapping": mapping}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return manifest


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description="Export blind G12 + P2.1 human audit packets.")
    ap.add_argument("--rendered-outputs", required=True,
                    help="JSON of already-rendered prose outputs (id/suite/category/lang/prose). "
                         "Must NOT contain question text, gt_ids, kept_ids, or scores.")
    ap.add_argument("--aggregate-stats", default=None,
                    help="Optional JSON with suite counts + sealed ID lists (no text).")
    ap.add_argument("--out-dir", required=True, help="Packet directory (shared with raters).")
    ap.add_argument("--mapping-path", default=None,
                    help="Private blind->real mapping file. MUST be outside --out-dir. "
                         "Default: <out-dir>-PRIVATE-mapping.json next to --out-dir.")
    ap.add_argument("--brutal-sample", type=int, default=30,
                    help="Stratified Brutal-230 sample size for G12 (default 30).")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED,
                    help="Deterministic shuffle seed (default 20261127).")
    args = ap.parse_args(argv)

    rendered_path = Path(args.rendered_outputs)
    items = _validate_rendered_items(_load_json(rendered_path))
    stats: dict = {}
    if args.aggregate_stats:
        stats = _validate_aggregate_stats(_load_json(Path(args.aggregate_stats)))

    out_dir = Path(args.out_dir)
    mapping_path = Path(args.mapping_path) if args.mapping_path else (
        out_dir.parent / (out_dir.name + "-PRIVATE-mapping.json"))

    manifest = export_packets(items, stats, out_dir, mapping_path,
                              brutal_sample=args.brutal_sample, seed=args.seed)
    print(f"AUDIT PACKETS EXPORTED: {manifest['counts']['g12_items']} G12 items "
          f"({manifest['counts']['g12_double_rated']} double-rated), "
          f"{manifest['counts']['p21_items']} P2.1 items "
          f"({manifest['counts']['p21_double_rated']} double-rated) -> {out_dir}")
    print(f"PRIVATE mapping (do NOT share with raters): {mapping_path}")
    print("Sealed placeholders: "
          + json.dumps(manifest["counts"]["sealed"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
