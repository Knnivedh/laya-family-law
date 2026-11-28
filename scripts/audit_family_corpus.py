"""Audit LAYA corpus balance and split overlap from existing labels and metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
SYNTHETIC = REPO_ROOT / "data" / "synthetic_v7_1"
KAANOON = REPO_ROOT / "data" / "kaanoon_eval" / "heldout.jsonl"
EXPECTED_LANGUAGES = {"en", "kn", "kn_roman"}
GROUP_FIELDS = ("template_family_id", "grammar_rule_id", "scenario_family", "scenario_id")


def _count_labels(
    rows: list[dict[str, Any]],
    column: str,
    labels: dict[str, list[str]],
    *,
    kind: str | None = None,
) -> dict[str, dict[str, int]]:
    counts = {key: dict.fromkeys(values, 0) for key, values in labels.items()}
    for row in rows:
        supplied = row.get(column) or {}
        if kind is not None:
            spanned = {span.get("key") for span in row.get("spans", []) or [] if span.get("kind") == kind}
        for key, options in counts.items():
            if kind is not None and key not in spanned:
                continue
            value = supplied.get(key)
            if value is None:
                value = "_missing"
            elif not isinstance(value, str) or value not in labels[key]:
                value = "_invalid"
            options[value] = options.get(value, 0) + 1
    return counts


def _summarize_slice(rows: list[dict[str, Any]], schema: dict[str, Any]) -> dict[str, Any]:
    issues = dict.fromkeys(schema["issues"], schema["intents"])
    facts = dict.fromkeys(schema["facts"], schema["fact_states"])
    scenario_counts = Counter(
        (row.get("meta") or {}).get("cluster") or row.get("category") or "_unlabeled"
        for row in rows
    )
    explicit_sections = [row["expected_sections"] for row in rows if "expected_sections" in row]
    return {
        "rows": len(rows),
        "scenario_counts": dict(scenario_counts),
        "issues": _count_labels(rows, "issues", issues),
        "facts": _count_labels(rows, "facts", facts),
        "enums": _count_labels(rows, "enums", schema["enums"]),
        "spanned_issues": _count_labels(rows, "issues", issues, kind="issue"),
        "spanned_facts": _count_labels(rows, "facts", facts, kind="fact"),
        "rows_with_explicit_sections": len(explicit_sections),
        "rows_with_empty_annotated_section_set": sum(not section_set for section_set in explicit_sections),
        "expected_section_counts": dict(Counter(
            section for section_set in explicit_sections for section in set(section_set)
        )),
    }


def summarize_rows(rows: list[dict[str, Any]], schema: dict[str, Any]) -> dict[str, Any]:
    by_language: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_language[row.get("lang") or "_unlabeled"].append(row)
    return {
        **_summarize_slice(rows, schema),
        "language_counts": {
            lang: len(by_language.get(lang, [])) for lang in sorted(by_language.keys() | EXPECTED_LANGUAGES)
        },
        "by_language": {lang: _summarize_slice(group, schema) for lang, group in by_language.items()},
    }


def _blocks(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple((row.get("meta") or {}).get("blocks") or ())


def _labels(row: dict[str, Any]) -> str:
    return json.dumps({name: row.get(name) for name in ("issues", "facts", "enums")}, sort_keys=True)


def _group_id(row: dict[str, Any], field: str) -> str | None:
    value = row.get(field) or (row.get("meta") or {}).get(field)
    return value if isinstance(value, str) and value else None


def synthetic_split_overlap(
    train: list[dict[str, Any]], validation: list[dict[str, Any]],
) -> dict[str, Any]:
    train_signatures: set[tuple[str, ...]] = set()
    train_languages: dict[tuple[tuple[str, ...], str], set[str]] = defaultdict(set)
    for row in train:
        blocks = _blocks(row)
        if blocks:
            train_signatures.add(blocks)
        if blocks and row.get("lang"):
            train_languages[(blocks, _labels(row))].add(row["lang"])

    validation_signatures: set[tuple[str, ...]] = set()
    per_language: dict[str, Counter] = defaultdict(Counter)
    for row in validation:
        blocks = _blocks(row)
        if blocks:
            validation_signatures.add(blocks)
        lang = row.get("lang") or "_unlabeled"
        matching_languages = train_languages.get((blocks, _labels(row)), set())
        counts = per_language[lang]
        counts["validation_rows"] += 1
        counts["rows_with_seen_block_signature"] += int(blocks in train_signatures)
        counts["rows_with_label_block_match"] += int(bool(matching_languages))
        counts["rows_with_different_language_label_block_match"] += int(
            lang != "_unlabeled" and bool(matching_languages - {lang})
        )

    explicit_groups = {}
    for field in GROUP_FIELDS:
        training = [group for row in train if (group := _group_id(row, field)) is not None]
        validating = [group for row in validation if (group := _group_id(row, field)) is not None]
        training_set = set(training)
        explicit_groups[field] = {
            "train_rows_tagged": len(training),
            "validation_rows_tagged": len(validating),
            "validation_unique_groups": len(set(validating)),
            "validation_unique_groups_seen_in_train": len(set(validating) & training_set),
            "validation_rows_seen_in_train": sum(group in training_set for group in validating),
        }

    train_blocks = {block for signature in train_signatures for block in signature}
    validation_blocks = {block for signature in validation_signatures for block in signature}
    return {
        "validation_rows": len(validation),
        "train_unique_block_signatures": len(train_signatures),
        "validation_unique_block_signatures": len(validation_signatures),
        "validation_unique_block_signatures_seen_in_train": len(train_signatures & validation_signatures),
        "validation_blocks": len(validation_blocks),
        "validation_blocks_seen_in_train": len(train_blocks & validation_blocks),
        "validation_rows_with_seen_block_signature": sum(
            counts["rows_with_seen_block_signature"] for counts in per_language.values()
        ),
        "validation_rows_with_label_block_match": sum(
            counts["rows_with_label_block_match"] for counts in per_language.values()
        ),
        "validation_rows_with_different_language_label_block_match": sum(
            counts["rows_with_different_language_label_block_match"] for counts in per_language.values()
        ),
        "by_validation_language": {lang: dict(counts) for lang, counts in per_language.items()},
        "explicit_groups": explicit_groups,
    }


def _read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as records:
        return [json.loads(line) for line in records if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Write the aggregate report to a JSON file.")
    args = parser.parse_args()
    if args.out is not None:
        output = args.out.resolve()
        protected = ("data", "ground-truth", "test-bank")
        if any(output.is_relative_to(REPO_ROOT / directory) for directory in protected):
            parser.error("Choose an output path outside the input corpora and benchmark directories.")

    schema = json.loads((SYNTHETIC / "schema.json").read_text(encoding="utf-8"))
    manifest = json.loads((SYNTHETIC / "manifest.json").read_text(encoding="utf-8"))
    validation_path = SYNTHETIC / "validation.jsonl"
    validation_sha = hashlib.sha256(validation_path.read_bytes()).hexdigest()
    if validation_sha != manifest["frozen_validation_sha256"]:
        parser.error("Frozen synthetic validation hash differs from the manifest.")

    train = _read_rows(SYNTHETIC / "train.jsonl")
    validation = _read_rows(validation_path)
    kaanoon = _read_rows(KAANOON)
    report = {
        "method": {
            "counts": "Each row has one state per annotated issue, fact or enum. A row can request multiple issues.",
            "spanned_labels": "Rows with at least one matching annotated span, without judging span correctness.",
            "scenario_counts": "Synthetic template clusters or Kaanoon issue categories.",
            "split_overlap": "Ordered template blocks and full-label matches are proxies. A different-language match does not establish an exact translated sibling.",
            "kaanoon": "Real user wording with graph-derived expected sections. Evaluation use only.",
            "frozen_validation_sha256": validation_sha,
        },
        "synthetic_train": summarize_rows(train, schema),
        "frozen_synthetic_validation": summarize_rows(validation, schema),
        "kaanoon_heldout": summarize_rows(kaanoon, schema),
        "synthetic_train_validation_overlap": synthetic_split_overlap(train, validation),
    }
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(payload, end="")
    else:
        output.write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
