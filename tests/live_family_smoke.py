"""Live English maintenance smoke cases. These are authored regression cases."""

import argparse
import json
from functools import partial
from statistics import median
from time import perf_counter

from src.laya_family import assess, guided_assessment, QUESTIONS
from src.laya_family_model import extract_facts


def new_support(beneficiary):
    return {"maintenance": True, "new_support": True, beneficiary: True}


CASES = [
    ("wife-new", "Since he moved out, I have had no income and can't meet basic household costs. I am his wife and want a fresh order for him to support me.",
     {"bnss-144"}, new_support("wife")),
    ("child-new", "How do I get a new order for school and living expenses for my 7-year-old child? His mother has a job and does not contribute.",
     {"bnss-144"}, new_support("minor_child")),
    ("parent-new", "I am dependent on my grown son for rent and food, but he has refused to help. I want the court to order maintenance for me as his mother.",
     {"bnss-144"}, new_support("parent")),
    ("husband-new", "I'm a husband asking just for my own living expenses from my wife. No case has been started and there are no children.",
     set(), new_support("husband")),
    ("hma-interim", "Our Hindu Marriage Act petition is still before the court. Can I, as his wife with no independent income, get money to pay for living and the pending case?",
     {"hma-24"}, {"maintenance": True, "interim": True, "hma_pending": True, "wife": True}),
    ("hma-decree", "My divorce decree under the Hindu Marriage Act has been passed. I'm the former wife and want to request ongoing permanent support connected to this decree.",
     {"hma-25"}, {"maintenance": True, "permanent": True, "hma_decree": True, "wife": True}),
    ("bnss-recover", "I have an order under section 144 BNSS and my ex has skipped the last two maintenance instalments. What steps can I take to collect them?",
     {"bnss-144-3"}, {"maintenance": True, "recover": True, "bnss_order": True}),
    ("bnss-vary", "My living costs changed after a BNSS 144 support order. I need to ask the issuing court to increase the monthly amount it fixed.",
     {"bnss-146"}, {"maintenance": True, "vary": True, "bnss_order": True}),
    ("wrong-order", "My older order says CrPC section 125. I want to get the maintenance already owed to me under it.",
     set(), {"maintenance": True, "recover": True, "bnss_order": False}),
    ("hypothetical", "If a Hindu Marriage Act case is filed one day could I get temporary maintenance? There is no case at the moment.",
     set(), {"maintenance": True, "interim": True, "hma_pending": False}),
    ("negated", "I specifically do not want financial support. I'd just like information on visiting my daughter.", set(), {}),
    ("unrelated", "The online store refuses to return the price of a scratched dining table. Where can I file a complaint?", set(), {}),
]


def _guided(question, extract, confirmed):
    def answer(prompt):
        field = next(key for key, text in QUESTIONS.items() if prompt.startswith(text))
        if not confirmed and field != "maintenance":
            return ""
        return "yes" if confirmed.get(field, False) else "no"

    return guided_assessment(question, extract, {}, answer, lambda _: None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    args = parser.parse_args()

    measures = {mode: {"exact": 0, "nonempty_exact": 0, "extra": 0, "unresolved": 0}
                for mode in ("raw", "guided")}
    timings = []
    cases = []
    live_extract = partial(extract_facts, device=args.device)
    for case_id, question, expected, confirmations in CASES:
        started = perf_counter()
        scores = live_extract(question)
        timings.append(perf_counter() - started)

        def extract(_):
            return scores

        case = {"id": case_id, "expected": sorted(expected)}
        for mode, result in (
            ("raw", assess(question, extract)),
            ("guided", _guided(question, extract, confirmations)),
        ):
            actual = {route["id"] for route in result["routes"]}
            exact = actual == expected
            measures[mode]["exact"] += exact
            measures[mode]["nonempty_exact"] += bool(expected) and exact
            measures[mode]["extra"] += bool(actual - expected)
            measures[mode]["unresolved"] += bool(result["questions"])
            case[mode] = {"provisions": sorted(actual), "status": result["status"]}
        cases.append(case)

    print(json.dumps({
        "device": args.device,
        "total": len(CASES),
        "nonempty_expected": sum(bool(expected) for _, _, expected, _ in CASES),
        "first_model_call_s": round(timings[0], 3),
        "warm_model_call_median_s": round(median(timings[1:]), 3),
        "warm_model_call_max_s": round(max(timings[1:]), 3),
        "measures": measures,
        "cases": cases,
    }, indent=2))
    if measures["guided"]["exact"] != len(CASES) or measures["raw"]["extra"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
