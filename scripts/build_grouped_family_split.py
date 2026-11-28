"""Build a recorded-template-block-disjoint development split from LAYA TRAIN-7500."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import tempfile
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "synthetic_v7_1"
SOURCE = CORPUS / "train.jsonl"
SEARCH_ATTEMPTS = 4096

Row = dict[str, Any]
Label = tuple[str, ...]


def _normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _components(rows: list[Row]) -> list[list[int]]:
    # A combo links all its block IDs transitively. Duplicate text links even
    # rows whose recorded blocks do not overlap.
    parents = list(range(len(rows)))
    first_seen: dict[tuple[str, str], int] = {}

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for index, row in enumerate(rows):
        keys = [("text", _normalize(row["text"]))]
        keys.extend(("block", block) for block in row["meta"]["blocks"])
        for key in keys:
            neighbor = first_seen.setdefault(key, index)
            parents[root(index)] = root(neighbor)

    components: dict[int, list[int]] = defaultdict(list)
    for index in range(len(rows)):
        components[root(index)].append(index)
    return list(components.values())


def _profile(rows: Iterable[Row]) -> Counter[Label]:
    counts: Counter[Label] = Counter()
    for row in rows:
        language = row["lang"]
        counts["language", language] += 1
        for issue, state in row["issues"].items():
            if state == "requested":
                counts["issue", issue] += 1
                counts["language_issue", language, issue] += 1
    return counts


def _select_dev(
    profiles: list[Counter[Label]], sizes: list[int], totals: Counter[Label],
    required: set[Label], target: int, tolerance: int, seed: int,
) -> tuple[int, ...]:
    lower, upper = target - tolerance, target + tolerance
    eligible = [index for index, size in enumerate(sizes) if size <= upper]
    total_rows = sum(sizes)
    rng = random.Random(seed)
    best: tuple[int, ...] = ()
    best_score = float("inf")

    groups_by_label = {
        key: tuple(index for index in eligible if 0 < profiles[index][key] < totals[key])
        for key in required
    }
    rare_first = sorted(required, key=lambda key: (len(groups_by_label[key]), key))
    for _ in range(SEARCH_ATTEMPTS):
        selected: list[int] = []
        counts: Counter[Label] = Counter()
        rows = 0

        # Reserve whole components for rare requests before filling the size
        # window. Each attempted seed picks a different eligible combination.
        for key in rare_first:
            if counts[key]:
                continue
            choices = [index for index in groups_by_label[key] if rows + sizes[index] <= upper]
            if not choices:
                break
            weights = [1 / sizes[index] for index in choices]
            index = rng.choices(choices, weights=weights)[0]
            selected.append(index)
            counts.update(profiles[index])
            rows += sizes[index]
        else:
            filler = [index for index in eligible if index not in selected]
            rng.shuffle(filler)
            candidates = [tuple(selected)] if rows >= lower else []
            for index in filler:
                if rows + sizes[index] > upper:
                    continue
                selected.append(index)
                rows += sizes[index]
                if rows >= lower:
                    candidates.append(tuple(selected))
            for candidate in candidates:
                candidate_rows = sum(sizes[index] for index in candidate)
                candidate_counts: Counter[Label] = Counter()
                for index in candidate:
                    candidate_counts.update(profiles[index])
                if not all(0 < candidate_counts[key] < totals[key] for key in required):
                    continue
                # Relative differences give rare requests a voice alongside
                # common classes while leaving size and coverage explicit.
                distribution_error = sum(
                    abs((candidate_counts[key] * total_rows) / (candidate_rows * count) - 1)
                    for key, count in totals.items()
                ) / len(totals)
                score = abs(candidate_rows - target) / target + distribution_error
                if score < best_score:
                    best_score = score
                    best = candidate
    if not best:
        raise ValueError(
            "No grouped split was found within the target size window with all required "
            "language and issue labels represented in both partitions. Try a wider size window."
        )
    return best


def _check_rows(rows: list[Row]) -> None:
    ids: set[str] = set()
    for row in rows:
        row_id = row.get("id")
        meta = row.get("meta") or {}
        blocks = meta.get("blocks")
        if (
            not isinstance(row_id, str) or not row_id or row_id in ids
            or meta.get("split") != "train"
            or not isinstance(blocks, list) or not blocks
            or not all(isinstance(block, str) and block for block in blocks)
            or not isinstance(row.get("text"), str) or not _normalize(row["text"])
            or not isinstance(row.get("lang"), str) or not row["lang"]
            or not isinstance(row.get("issues"), dict)
        ):
            raise ValueError("Expected train rows with unique IDs, text, language, issues and recorded blocks.")
        ids.add(row_id)


def grouped_split(
    rows: list[Row], issues: list[str], *,
    dev_size: int = 500, tolerance: int = 25, seed: int = 7102,
) -> tuple[list[Row], list[Row]]:
    _check_rows(rows)
    if tolerance < 0 or dev_size - tolerance < 1 or dev_size + tolerance >= len(rows):
        raise ValueError("The grouped split size window must fit entirely within the source corpus.")
    components = _components(rows)
    totals = _profile(rows)
    required = {("language", row["lang"]) for row in rows}
    required.update(("issue", issue) for issue in issues)
    if any(totals[key] < 2 for key in required):
        raise ValueError("No grouped split can put a language or topic with fewer than two rows on both sides.")
    selected = _select_dev(
        [_profile(rows[index] for index in component) for component in components],
        [len(component) for component in components],
        totals, required, dev_size, tolerance, seed,
    )
    development_indices = {index for component in selected for index in components[component]}
    train, dev = [], []
    for index, row in enumerate(rows):
        (dev if index in development_indices else train).append(row)
    verify_split(train, dev)
    return train, dev


def verify_split(train: list[Row], dev: list[Row]) -> dict[str, int]:
    metrics = {
        "shared_recorded_blocks": len(
            {block for row in train for block in row["meta"]["blocks"]}
            & {block for row in dev for block in row["meta"]["blocks"]}
        ),
        "shared_normalized_texts": len(
            {_normalize(row["text"]) for row in train} & {_normalize(row["text"]) for row in dev}
        ),
        "shared_ids": len({row["id"] for row in train} & {row["id"] for row in dev}),
    }
    if any(metrics.values()):
        raise ValueError(f"Grouped train/development overlap detected: {metrics}")
    return metrics


def _write_partition(path: Path, rows: list[Row], split: str) -> dict[str, Any]:
    digest = hashlib.sha256()
    with path.open("wb") as output:
        for row in rows:
            annotated = dict(row, meta=dict(row["meta"], split=split, source_split="train"))
            encoded = (json.dumps(annotated, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
            output.write(encoded)
            digest.update(encoded)
    profile = _profile(rows)
    return {
        "rows": len(rows),
        "sha256": digest.hexdigest(),
        "languages": {label[1]: count for label, count in profile.items() if label[0] == "language"},
        "issues_requested": {label[1]: count for label, count in profile.items() if label[0] == "issue"},
        "issues_requested_by_language": {
            language: {
                label[2]: count for label, count in profile.items()
                if label[0] == "language_issue" and label[1] == language
            }
            for language in {row["lang"] for row in rows}
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True, help="New directory for the grouped split.")
    parser.add_argument("--dev-size", type=int, default=500)
    parser.add_argument("--tolerance", type=int, default=25, help="Maximum allowed deviation from dev-size.")
    parser.add_argument("--seed", type=int, default=7102)
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    if destination.exists():
        parser.error("The output directory already exists. Choose a new directory.")
    if destination.is_relative_to(ROOT / "test-bank") or destination.is_relative_to(ROOT / "ground-truth"):
        parser.error("Choose an output directory outside frozen benchmark directories.")
    source_bytes = SOURCE.read_bytes()
    corpus_manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    schema = json.loads((CORPUS / "schema.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in source_bytes.splitlines() if line.strip()]
    if len(rows) != corpus_manifest["n_train"]:
        parser.error("The source training row count differs from the corpus manifest.")
    try:
        train, dev = grouped_split(
            rows, schema["issues"], dev_size=args.dev_size, tolerance=args.tolerance, seed=args.seed,
        )
    except ValueError as exc:
        parser.error(str(exc))

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".laya-grouped-", dir=destination.parent) as staging:
        staged = Path(staging)
        sizes = sorted((len(group) for group in _components(rows)), reverse=True)
        report = {
            "seed": args.seed,
            "n_train": len(train),
            "n_validation": len(dev),
            "purpose": "Synthetic development proxy derived only from the existing training corpus.",
            "limitation": "The source carries recorded block names but lacks explicit scenario-family and translation-sibling IDs. Zero recorded-block overlap does not establish independent authorship or disjoint latent scenario families.",
            "grouping": "Transitive connected components of shared recorded block IDs or exact Unicode NFKC/casefold/whitespace-normalized text. Related block names remain separate unless linked by these signals.",
            "method": {
                "search_attempts": SEARCH_ATTEMPTS,
                "target_dev_rows": args.dev_size,
                "tolerance_rows": args.tolerance,
                "components": len(sizes),
                "largest_component_rows": sizes[0],
            },
            "source": {"path": SOURCE.relative_to(ROOT).as_posix(), "rows": len(rows),
                       "sha256": hashlib.sha256(source_bytes).hexdigest()},
            "overlap_checks": verify_split(train, dev),
            "partitions": {
                "grouped_train.jsonl": _write_partition(staged / "grouped_train.jsonl", train, "grouped_train"),
                "grouped_dev.jsonl": _write_partition(staged / "grouped_dev.jsonl", dev, "grouped_dev"),
            },
        }
        payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
        (staged / "manifest.json").write_bytes(payload.encode("utf-8"))
        if destination.exists():
            parser.error("The output directory was created during generation. Choose a new directory.")
        staged.rename(destination)
    print(payload, end="")


if __name__ == "__main__":
    main()
