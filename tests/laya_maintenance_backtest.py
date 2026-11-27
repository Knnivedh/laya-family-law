"""Raw-text maintenance backtest with frozen case files and isolated labels."""

import argparse
from collections import Counter
from functools import partial
from hashlib import sha256
import json
from pathlib import Path
from statistics import median
from time import perf_counter

from src.laya_family import HMA, BNSS, assess
from src.laya_family_model import extract_facts


ROOT = Path(__file__).resolve().parent
FROZEN = {
    "development": "7f7afea4d390567610df8b8b1c47a3c2e097c32ff515b44fe15197c89ca7b505",
    "verification": "e80b0e90cea8e5d3d0b56ee67a185771a9b50b814777be595193628d3e718817",
    "challenge": "7c8476d211f777c5cdc492a5bfb69092f680349d71d5cc2e195c58c6dd2cffcb",
    "final_check": "5d8ffe1eb42cc7af41ae9f90af64cc0ed803c3bfd1fb993d76fe8d4dddb75cbe",
}
RULE_SOURCES = {
    "bnss-144": ("BNSS, 2023, section 144", BNSS),
    "bnss-144-3": ("BNSS, 2023, section 144(3)", BNSS),
    "bnss-146": ("BNSS, 2023, section 146", BNSS),
    "hma-24": ("Hindu Marriage Act, 1955, section 24", HMA),
    "hma-25": ("Hindu Marriage Act, 1955, section 25", HMA),
}


def load_cases(split):
    data = (ROOT / "fixtures" / f"laya_maintenance_{split}.json").read_bytes().replace(b"\r\n", b"\n")
    digest = sha256(data).hexdigest()
    if digest != FROZEN[split]:
        raise ValueError(f"Frozen {split} case bytes did not match: {digest}")
    rows = json.loads(data)
    for row in rows:
        row.setdefault("kind", "positive" if row["expected"] else "boundary")
    return rows, digest


def audit_routes(result, question):
    problem = False
    for route in result["routes"]:
        key = route["id"]
        if RULE_SOURCES.get(key) != (route["provision"], route["url"]):
            problem = True
        if not route["requirements"] or not route["forum"] or not route["because"]:
            problem = True
        for fact in route["because"]:
            record = result["facts"][fact]
            if record["value"] != "yes":
                problem = True
            if "span" in record:
                span = record["span"]
                if question[span["start"]:span["end"]] != span["text"]:
                    problem = True
    return problem


def evaluate(split, extract, details):
    cases, digest = load_cases(split)
    measures = Counter()
    by_kind = {key: Counter() for key in sorted({row["kind"] for row in cases})}
    expected_labels, true_labels = Counter(), Counter()
    rows = []
    elapsed = []
    outcomes = []
    for row in cases:
        expected = set(row["expected"])
        expected_labels.update(expected)
        required = set(row.get("must_ask", []))
        counters = by_kind[row["kind"]]
        for counter in (measures, counters):
            counter["total"] += 1
            counter["positive"] += bool(expected)
            counter["required_clarification_rows"] += bool(required)
        start = perf_counter()
        try:
            result = assess(row["question"], extract)
        except (ImportError, RuntimeError, ValueError, OSError) as error:
            measures["runtime_errors"] += 1
            counters["runtime_errors"] += 1
            outcomes.append((row["id"], "error", (), ()))
            if details:
                rows.append({"id": row["id"], "family": row["family"], "runtime_error": str(error)})
            continue
        elapsed.append(perf_counter() - start)
        output = result["routes"]
        actual = {route["id"] for route in output}
        questions = {item["field"] for item in result["questions"]}
        true_labels.update(expected & actual)
        exact = expected == actual and len(output) == len(actual)
        unsafe = bool(actual - expected)
        bad_citation = audit_routes(result, row["question"].strip())
        asked = required <= questions
        outcomes.append((row["id"], result["status"], sorted(actual), sorted(questions)))
        for counter in (measures, counters):
            counter["exact"] += exact
            counter["positive_exact"] += bool(expected) and exact
            counter["extra_provision_rows"] += unsafe
            counter["provision_tp"] += len(expected & actual)
            counter["provision_fp"] += len(actual - expected)
            counter["invalid_citation_rows"] += bad_citation
            counter["correct_required_clarifications"] += bool(required) and asked
        if details and (not exact or not asked or unsafe or bad_citation):
            rows.append({
                "id": row["id"], "family": row["family"], "expected": sorted(expected),
                "actual": sorted(actual), "required": sorted(required), "asked": sorted(questions),
                "status": result["status"],
                "facts": {key: value for key, value in result["facts"].items()
                          if "score" in value or value["value"] == "yes"},
            })

    measures["total"] = len(cases)
    measures["runtime_errors"] += 0
    measures["provision_fn"] = sum(expected_labels.values()) - measures["provision_tp"]
    outcome_bytes = json.dumps(outcomes, ensure_ascii=True, separators=(",", ":")).encode()
    report = {
        "split": split, "fixture_sha256": digest, "outcome_sha256": sha256(outcome_bytes).hexdigest(),
        "measures": dict(measures),
        "per_kind": {key: dict(val) for key, val in by_kind.items()},
        "expected_labels": dict(expected_labels), "matched_labels": dict(true_labels),
        "warm_median_s": round(median(elapsed[1:]), 4) if elapsed[1:] else None,
        "warm_max_s": round(max(elapsed[1:]), 4) if elapsed[1:] else None,
    }
    if details:
        report["differences"] = rows
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=tuple(FROZEN), required=True)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--detail", action="store_true")
    parser.add_argument("--extractor", choices=("laya", "structured"), default="laya")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--strict", action="store_true", help="Fail if any measured engineering gate does not pass.")
    args = parser.parse_args()
    if args.split in {"verification", "final_check"} and args.detail:
        parser.error("Case-level detail is available for the development and challenge banks.")
    extractor = extract_facts
    if args.extractor == "structured":
        from src.laya_family_structured import extract_facts as extractor
    report = evaluate(args.split, partial(extractor, device=args.device), args.detail)
    report["extractor"] = args.extractor
    report["device"] = args.device
    modules = ["laya_family.py", "laya_family_evidence.py", "laya_family_model.py", "laya_family_structured.py"]
    report["runtime_sha256"] = {
        name: sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        for name in modules if (path := ROOT.parent / "src" / name).is_file()
    }
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: val for key, val in report.items() if key != "differences"}, indent=2))
    metrics = report["measures"]
    if args.strict and (
        metrics["exact"] != metrics["total"]
        or metrics["invalid_citation_rows"]
        or metrics["runtime_errors"]
        or metrics["required_clarification_rows"] != metrics["correct_required_clarifications"]
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
