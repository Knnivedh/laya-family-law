"""Full-system LAYA v7 Decision Graph runtime and scorer-isolated entrypoint."""

from __future__ import annotations

import argparse
import json
from time import perf_counter
from typing import Any

from .laya_prose_v2 import prose_forbidden_check, render_prose
from .laya_v7_extractor import extract_v7, extract_v7_batch
from .laya_v7_graph import evaluate_stage2_v7
from .laya_v7_schema import FactEvidence, IssueEvidence


def apply_confirmations_v7(extracted: dict[str, Any], confirmations: dict[str, Any] | None) -> dict[str, Any]:
    """Apply explicit user confirmations cleanly, superseding extracted/prior facts without stale retention."""
    if not confirmations:
        return extracted
    facts = dict(extracted["facts"])
    issues = dict(extracted["issues"])
    negated = set(extracted.get("negated_issues") or set())
    for k, v in confirmations.items():
        if isinstance(v, bool):
            facts[k] = FactEvidence(
                key=k,
                status="supported" if v else "denied",
                value=v,
                source="user_confirmation",
                confidence=1.0,
                turn=1,
            )
            if k == "divorce_asked":
                if v:
                    negated.discard("divorce")
                    issues["divorce"] = IssueEvidence(issue="divorce", intent="requested", source="user_confirmation", confidence=1.0, turn=1)
                else:
                    negated.add("divorce")
                    issues["divorce"] = IssueEvidence(issue="divorce", intent="denied", source="user_confirmation", confidence=1.0, turn=1)
        else:
            facts[k] = FactEvidence(
                key=k,
                status="supported",
                value=v,
                source="user_confirmation",
                confidence=1.0,
                turn=1,
            )
    facts["negated_issues"] = negated
    out = dict(extracted)
    out["facts"] = facts
    out["issues"] = issues
    out["negated_issues"] = negated
    return out


def assess_v7(
    question: str,
    *,
    locale: str | None = None,
    confirmations: dict[str, Any] | None = None,
    mode: str = "auto",
    device: str = "cuda",
    custody_vocab: str = "v3_bundled",
    kannada_strategy: str = "nllb_then_en",
    with_prose: bool = True,
) -> dict[str, Any]:
    """Run LAYA v7 end-to-end strictly from production inputs (question, locale, confirmations)."""
    t0 = perf_counter()
    extracted = extract_v7(
        question,
        locale=locale,
        mode=mode,
        device=device,
        kannada_strategy=kannada_strategy,
    )
    if confirmations:
        extracted = apply_confirmations_v7(extracted, confirmations)

    decision = evaluate_stage2_v7(
        extracted["issues"],
        extracted["facts"],
        custody_vocab=custody_vocab,
    )
    result: dict[str, Any] = {
        "lang": extracted["lang"],
        "script": extracted["script"],
        "extractor_mode": extracted["extractor_mode"],
        "in_scope": decision["in_scope"],
        "kept_ids": decision["kept_ids"],
        "kept_statutory_ids": decision["kept_statutory_ids"],
        "applied_principles": decision["applied_principles"],
        "custody_companions": decision["custody_companions"],
        "court_live": decision["court_live"],
        "court_source": decision["court_source"],
        "escalations_typed": decision["escalations_typed"],
        "escalation_kinds": decision["escalation_kinds"],
        "gated_out": decision["gated_out"],
        "dispositions": decision["dispositions"],
        "candidates_before_stage2": list(decision["kept_ids"]),
        "error": None,
    }
    if with_prose:
        prose_out = render_prose(result, decision["facts"])
        fp_hits, q_flags = prose_forbidden_check(prose_out["prose"], result["kept_ids"], [], decision["facts"])
        result["prose"] = prose_out["prose"]
        result["prose_fp_hits"] = fp_hits
        result["prose_quality_flags"] = q_flags
        result["prose_render_ms"] = prose_out["prose_render_ms"]
        if prose_out.get("status") == "error":
            result["error"] = "prose_validation_error"
    result["latency_s"] = round(perf_counter() - t0, 4)
    return result


def assess_v7_batch(
    questions: list[str],
    *,
    locales: list[str | None] | None = None,
    confirmations_list: list[dict[str, Any] | None] | None = None,
    mode: str = "auto",
    device: str = "cuda",
    custody_vocab: str = "v3_bundled",
    kannada_strategy: str = "nllb_then_en",
    with_prose: bool = True,
    batch_size: int = 16,
) -> tuple[list[dict[str, Any]], float]:
    """Run batched LAYA v7 strictly from production inputs; returns (records, total_wall_s)."""
    t0 = perf_counter()
    extracted_list = extract_v7_batch(
        questions,
        locales=locales,
        mode=mode,
        device=device,
        kannada_strategy=kannada_strategy,
        batch_size=batch_size,
    )
    t_ext = perf_counter() - t0
    per_q_s = round(t_ext / max(len(questions), 1), 4)
    records: list[dict[str, Any]] = []
    for idx, extracted in enumerate(extracted_list):
        t_item = perf_counter()
        confs = confirmations_list[idx] if confirmations_list else None
        if confs:
            extracted = apply_confirmations_v7(extracted, confs)
        decision = evaluate_stage2_v7(
            extracted["issues"],
            extracted["facts"],
            custody_vocab=custody_vocab,
        )
        rec: dict[str, Any] = {
            "lang": extracted["lang"],
            "script": extracted["script"],
            "extractor_mode": extracted["extractor_mode"],
            "model_slots": extracted.get("model_slots", {}),
            "translated_text": extracted.get("translated_text"),
            "in_scope": decision["in_scope"],
            "kept_ids": decision["kept_ids"],
            "kept_statutory_ids": decision["kept_statutory_ids"],
            "applied_principles": decision["applied_principles"],
            "custody_companions": decision["custody_companions"],
            "court_live": decision["court_live"],
            "court_source": decision["court_source"],
            "escalations_typed": decision["escalations_typed"],
            "escalation_kinds": decision["escalation_kinds"],
            "gated_out": decision["gated_out"],
            "dispositions": decision["dispositions"],
            "candidates_before_stage2": list(decision["kept_ids"]),
            "error": None,
        }
        if with_prose:
            prose_out = render_prose(rec, decision["facts"])
            fp_hits, q_flags = prose_forbidden_check(prose_out["prose"], rec["kept_ids"], [], decision["facts"])
            rec["prose"] = prose_out["prose"]
            rec["prose_fp_hits"] = fp_hits
            rec["prose_quality_flags"] = q_flags
            rec["prose_render_ms"] = prose_out["prose_render_ms"]
            if prose_out.get("status") == "error":
                rec["error"] = "prose_validation_error"
        rec["latency_s"] = round(per_q_s + (perf_counter() - t_item), 4)
        records.append(rec)
    return records, round(perf_counter() - t0, 3)


def main() -> None:
    parser = argparse.ArgumentParser(description="Assess an Indian family-law question with LAYA v7.")
    parser.add_argument("--question", required=True)
    parser.add_argument("--locale", default=None)
    parser.add_argument("--mode", choices=("auto", "laya", "structured", "evidence"), default="auto")
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--custody-vocab", choices=("v3_bundled", "statutory_primary"), default="v3_bundled")
    args = parser.parse_args()
    out = assess_v7(
        args.question,
        locale=args.locale,
        mode=args.mode,
        device=args.device,
        custody_vocab=args.custody_vocab,
    )
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
