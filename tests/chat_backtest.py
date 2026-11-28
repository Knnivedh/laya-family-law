"""Measure first-turn chatbot responses over the four non-sealed suites."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import median
from threading import Thread
from time import perf_counter
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from src.laya_chat_api import make_server
from tests import integrated_backtest as integrated
from tests import recall_eval, v7_backtest


def _suites() -> dict[str, list[tuple[str, set[str]]]]:
    integrated.verify_validation_sha()
    validation, _, _ = recall_eval.load_split(
        integrated.DEFAULT_MANIFEST, integrated.DEFAULT_VALIDATION,
    )
    kaanoon = recall_eval.load_kaanoon_split(integrated.DEFAULT_KAANOON)
    return {
        "validation": [(r["text"], recall_eval.expected_sections(r)) for r in validation],
        "kaanoon": [(r["text"], recall_eval.expected_sections(r)) for r in kaanoon],
        "16q": [(r["question"], set(r["gt_ids"])) for r in v7_backtest._load_16q()],
        "brutal": [(r["question"], set(r["gt_ids"])) for r in v7_backtest._load_brutal()],
    }


def _measure(endpoint: str, rows: list[tuple[str, set[str]]]) -> dict:
    status_counts: Counter[str] = Counter()
    exact = status_exact = answers_returned = answer_exact = 0
    tp = fp = fn = 0
    latencies = []
    for text, reference in rows:
        request = Request(
            endpoint, json.dumps({"messages": [{"text": text}]}).encode("utf-8"),
            {"Content-Type": "application/json"},
        )
        start = perf_counter()
        try:
            with urlopen(request, timeout=15) as response:
                result = json.load(response)
        except HTTPError as exc:
            with exc:
                status_counts[f"http_{exc.code}"] += 1
            continue
        latencies.append((perf_counter() - start) * 1000)
        status_counts[result["status"]] += 1
        expected = set(reference) - v7_backtest.CUSTODY_COMPANIONS
        actual = {p["id"] for p in result["provisions"]}
        exact += actual == expected
        has_answer = isinstance(result["answer"], str) and bool(result["answer"])
        status_exact += actual == expected and result["status"] in {"assessment", "urgent"}
        answers_returned += has_answer
        answer_exact += actual == expected and has_answer
        tp += len(actual & expected)
        fp += len(actual - expected)
        fn += len(expected - actual)

    latencies.sort()
    return {
        "questions": len(rows),
        "exact_provision_set": exact,
        "exact_with_assessment_or_urgent_status": status_exact,
        "answers_returned": answers_returned,
        "exact_with_answer": answer_exact,
        "micro_tp_fp_fn": [tp, fp, fn],
        "status_counts": dict(status_counts),
        "p50_ms": round(median(latencies), 2) if latencies else None,
        "p95_ms": round(latencies[(95 * len(latencies) - 1) // 100], 2) if latencies else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--mode", choices=("auto", "evidence"), default="auto")
    args = parser.parse_args()
    suites = _suites()
    with make_server(port=0, extractor_mode=args.mode) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = f"http://127.0.0.1:{server.server_port}/v1/assess"
            report = {name: _measure(endpoint, rows) for name, rows in suites.items()}
        finally:
            server.shutdown()
            thread.join()
    output = json.dumps(report, indent=2) + "\n"
    print(output, end="")
    if args.json_out:
        args.json_out.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
