"""Deterministic Indian family-law maintenance intake with cited rule explanations."""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from functools import lru_cache
import json
import math
import sys
import unicodedata
from collections.abc import Callable, Mapping, Sequence


BNSS = "https://www.indiacode.nic.in/bitstream/123456789/20340/1/bnss%2C_2023.pdf"
HMA = "https://www.indiacode.nic.in/bitstream/123456789/1560/1/A1955-25Eng.pdf"
FAMILY_COURTS = "https://www.indiacode.nic.in/bitstream/123456789/1844/1/A1984__66.pdf"
RAJNESH = "https://api.sci.gov.in/supremecourt/2018/37875/37875_2018_39_1501_24602_Judgement_04-Nov-2020.pdf"

QUESTIONS = {
    "maintenance": "Are you asking for financial support for a spouse, child or parent, or about an existing maintenance order?",
    "new_support": "Are you seeking a fresh maintenance order separate from any existing case or order?",
    "wife": "Is support sought for a wife or divorced wife herself from her husband or former husband?",
    "minor_child": "Is support sought for a child under 18 from their parent?",
    "parent": "Is a parent seeking financial support from their adult child?",
    "husband": "Is the husband seeking financial support for himself?",
    "interim": "Do you want temporary support or help with case expenses while a marriage case is in court?",
    "permanent": "Do you want permanent maintenance linked to a marriage decree?",
    "recover": "Are you trying to collect payments already due under a court maintenance order?",
    "vary": "Are you trying to change the amount in an existing court order?",
    "hma_pending": "Do the papers say a case about your marriage under the Hindu Marriage Act is currently pending in court?",
    "hma_decree": "Do the papers show a decree for your marriage being passed or already passed under the Hindu Marriage Act?",
    "bnss_order": "Does the existing order cite section 144 of the BNSS, 2023?",
}

REASONS = {
    "new_support": "you are seeking a fresh maintenance order",
    "wife": "the requested support is for a wife or divorced wife",
    "minor_child": "the requested support is for a child under 18",
    "parent": "a parent is seeking support from their adult child",
    "interim": "you need temporary support or case expenses during a marriage case",
    "permanent": "you are seeking permanent maintenance connected to a marriage decree",
    "recover": "you are trying to collect payments already due under a maintenance order",
    "vary": "you are asking the court to change an existing maintenance order",
    "hma_pending": "a Hindu Marriage Act case about your marriage is pending",
    "hma_decree": "there is a Hindu Marriage Act decree for your marriage",
    "bnss_order": "your existing order cites section 144 of the BNSS",
}

PURPOSES = ("new_support", "interim", "permanent", "recover", "vary")
PROCEDURAL_FACTS = {"hma_pending", "hma_decree", "bnss_order"}
BENEFICIARIES = {"wife": "wife or divorced wife", "minor_child": "minor child", "parent": "parent"}


def parse_confirmations(values: Sequence[str]) -> dict[str, bool]:
    facts = {}
    for item in values:
        field, _, answer = item.partition("=")
        if field not in QUESTIONS or answer not in {"yes", "no"} or field in facts:
            raise ValueError("Confirm a listed field once with field=yes or field=no.")
        facts[field] = answer == "yes"
    return facts


def _interpret(scores: Mapping[str, float], confirmed: Mapping[str, bool]) -> dict:
    if set(scores) - QUESTIONS.keys():
        raise ValueError("The extractor returned an unknown field.")
    if set(confirmed) - QUESTIONS.keys() or any(type(value) is not bool for value in confirmed.values()):
        raise ValueError("User confirmations must contain only known fields with Boolean values.")

    facts = {}
    for field in QUESTIONS:
        score = scores.get(field)
        if field in scores and (
            type(score) not in {float, int} or not math.isfinite(score) or not 0 <= score <= 1
        ):
            raise ValueError(f"Invalid extractor score for {field}.")
        if field in confirmed:
            facts[field] = {"value": "yes" if confirmed[field] else "no", "source": "user_confirmation"}
        elif score is None:
            facts[field] = {"value": "unknown", "source": "unresolved"}
        else:
            value = "unknown"
            if field not in PROCEDURAL_FACTS:
                if score >= 0.70:
                    value = "yes"
                elif score <= 0.20:
                    value = "no"
            facts[field] = {"value": value, "source": "model_suggestion", "score": round(score, 4)}
    if "maintenance" not in confirmed and facts["maintenance"]["value"] != "yes":
        purpose = next((field for field in PURPOSES if facts[field]["value"] == "yes"), None)
        if purpose:
            facts["maintenance"] = {"value": "yes", "source": "derived_from_intent", "basis": purpose}
    return facts


def _route(rule_id: str, provision: str, url: str, facts: list[str], requirements: list[str], forum: str) -> dict:
    return {"id": rule_id, "provision": provision, "url": url, "because": facts,
            "requirements": requirements, "forum": forum}


def assess(
    question: str,
    extract: Callable[[str], Mapping[str, float]],
    confirmed: Mapping[str, bool] | None = None,
) -> dict:
    question = question.strip()
    if not question:
        raise ValueError("Enter a family-law question.")
    result = {"status": "needs_clarification", "routes": [], "questions": [], "notes": [], "facts": {}}
    if any(char.isalpha() and "LATIN" not in unicodedata.name(char, "") for char in question):
        result["status"] = "unsupported_language"
        result["notes"].append("This maintenance intake can assess English text. Seek help in a language you can use.")
        return result
    if len(question) > 3000:
        result["notes"].append("Share one maintenance issue at a time, including the relevant order or case details.")
        return result

    facts = _interpret(extract(question), {} if confirmed is None else confirmed)
    result["facts"] = facts

    def is_yes(field: str) -> bool:
        return facts[field]["value"] == "yes"

    def ask(*fields: str) -> None:
        for field in fields:
            if facts[field]["value"] == "unknown" and all(q["field"] != field for q in result["questions"]):
                result["questions"].append({"field": field, "question": QUESTIONS[field]})

    maintenance = facts["maintenance"]["value"]
    if maintenance == "no":
        result["status"] = "outside_maintenance"
        result["notes"].append("This release handles maintenance. Other family matters need a separate review.")
        return result
    if maintenance == "unknown":
        ask("maintenance")
        return result

    routes = result["routes"]
    if is_yes("recover") or is_yes("vary"):
        if is_yes("bnss_order"):
            forum = "Start with the court that issued the maintenance order and confirm the available procedure."
            if is_yes("recover"):
                routes.append(_route(
                    "bnss-144-3", "BNSS, 2023, section 144(3)", BNSS, ["recover", "bnss_order"],
                    ["Bring the order and a list of unpaid instalments and due dates.",
                     "Have the recovery application timing checked promptly. The warrant provision has a one-year condition for each amount due."],
                    forum,
                ))
            if is_yes("vary"):
                routes.append(_route(
                    "bnss-146", "BNSS, 2023, section 146", BNSS, ["vary", "bnss_order"],
                    ["Bring the existing order and evidence of the change in circumstances."], forum,
                ))
        else:
            ask("bnss_order")
            result["notes"].append("Check the statute and court named on the order. Older or differently governed orders need their own procedure.")

    for purpose, stage, rule_id, name, requirement in (
        ("interim", "hma_pending", "hma-24", "Hindu Marriage Act, 1955, section 24",
         "Show that your independent income is insufficient for support and necessary expenses of the proceeding."),
        ("permanent", "hma_decree", "hma-25", "Hindu Marriage Act, 1955, section 25",
         "Bring the decree and information about both spouses' income, property and relevant circumstances."),
    ):
        if not is_yes(purpose):
            continue
        if not is_yes(stage):
            ask(stage)
            continue
        routes.append(_route(rule_id, name, HMA, [purpose, stage], [requirement],
                             "Start with the court handling the Hindu Marriage Act proceeding or decree."))

    roles = [field for field in BENEFICIARIES if is_yes(field)]
    if is_yes("new_support"):
        if roles:
            routes.append(_route(
                "bnss-144", "BNSS, 2023, section 144", BNSS, ["new_support", *roles],
                [
                    "Show the relationship for the claimed beneficiary: " + ", ".join(BENEFICIARIES[role] for role in roles) + ".",
                    "Explain the beneficiary's inability to maintain themself and the other person's means and alleged neglect or refusal to support.",
                    "Check the beneficiary-specific conditions and statutory exceptions for your situation.",
                ],
                "Check territorial jurisdiction. The relevant Family Court may exercise maintenance jurisdiction where established. Otherwise the Act provides for a first-class Magistrate.",
            ))
            result["forum_sources"] = [
                {"provision": "BNSS, 2023, section 145", "url": BNSS},
                {"provision": "Family Courts Act, 1984, sections 7–8", "url": FAMILY_COURTS},
            ]
        else:
            ask("wife", "minor_child", "parent")

    if routes:
        result["status"] = "partial_route" if result["questions"] else "potential_route"
        result["practice_authorities"] = [{
            "provision": "Rajnesh v. Neha, Supreme Court, final directions on overlapping maintenance proceedings",
            "url": RAJNESH,
            "relevance": "Disclose earlier maintenance proceedings and orders so the court can consider adjustments.",
        }]
    elif not result["questions"]:
        ask(*PURPOSES)
        if not result["questions"]:
            result["status"] = "review_needed"
    result["notes"].append("The court decides eligibility, venue and relief. This assessment covers the maintenance issue.")
    return result


def guided_assessment(
    question: str,
    extract: Callable[[str], Mapping[str, float]],
    confirmed: Mapping[str, bool],
    prompt: Callable[[str], str],
    tell: Callable[[str], None],
) -> dict:
    cached_extract = lru_cache(maxsize=1)(extract)
    answers = dict(confirmed)
    result = assess(question, cached_extract, answers)
    while result["questions"]:
        pending = result["questions"][0]
        try:
            answer = prompt(f"{pending['question']} (yes/no, Enter if unsure) ").strip().lower()
        except EOFError:
            return result
        if not answer:
            return result
        if answer not in {"yes", "no", "y", "n"}:
            tell("Answer yes or no, or press Enter if you are unsure.")
            continue
        answers[pending["field"]] = answer in {"yes", "y"}
        result = assess(question, cached_extract, answers)
    return result


def _show(result: dict) -> None:
    if result["routes"]:
        print("\nPotential legal routes")
    for route in result["routes"]:
        print(f"- {route['provision']}")
        for field in route["because"]:
            fact = result["facts"][field]
            evidence = "You confirmed" if fact["source"] == "user_confirmation" else "Your question suggests"
            print(f"  {evidence} that {REASONS[field]}.")
        for requirement in route["requirements"]:
            print(f"  {requirement}")
        print(f"  {route['forum']}")
        print(f"  {route['url']}")
    for source in result.get("forum_sources", []):
        print(f"{source['provision']}  {source['url']}")
    for source in result.get("practice_authorities", []):
        print(f"{source['relevance']}  {source['url']}")
    for note in result["notes"]:
        print(note)
    if result["questions"]:
        print("\nA fact still needed")
        print(result["questions"][0]["question"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", help="Read the English question from this argument. Standard input is the default.")
    parser.add_argument("--confirm", action="append", default=[], metavar="FIELD=YES_OR_NO")
    parser.add_argument("--device", choices=("cuda", "cpu"), help="Use this device for the local model.")
    parser.add_argument("--interactive", action="store_true", help="Ask follow-up questions and show the answer in plain text.")
    args = parser.parse_args()
    try:
        from .laya_family_model import extract_facts
        confirmed = parse_confirmations(args.confirm)
        question = args.question
        if question is None:
            question = input("Describe your maintenance question in your own words. ") if args.interactive else sys.stdin.read()

        def extract(text: str) -> Mapping[str, float]:
            with redirect_stdout(sys.stderr):
                return extract_facts(text, device=args.device)

        if args.interactive:
            _show(guided_assessment(question, extract, confirmed, input, print))
        else:
            print(json.dumps(assess(question, extract, confirmed), ensure_ascii=True, indent=2))
    except (EOFError, ImportError, OSError, RuntimeError, ValueError) as error:
        parser.exit(2, f"Family-law assessment unavailable. {error}\n")


if __name__ == "__main__":
    main()
