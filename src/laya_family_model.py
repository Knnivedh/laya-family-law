"""Pinned, local LAYA fact suggestions for English maintenance intake."""

from functools import lru_cache
import math


MODEL = "PIXMELT/laya"
REVISION = "29a1a48862bf4a92935c5a7162e1f88a05fc7440"

PROMPTS = {
    "maintenance": {
        "type": "noul",
        "instructions": (
            "Is someone asking for family maintenance or alimony, help paying a spouse's, child's or parent's "
            "expenses, or how to recover or change support ordered by a court? Exclude deposits, other civil debts, "
            "incidental references and explicitly declined financial support."
        ),
    },
    "purpose": {
        "type": "choice",
        "instructions": "What financial remedy is the person actually asking for?",
        "criteria": {
            "new_support": "First or separate maintenance application for living expenses, child support or support for a parent.",
            "interim": "Temporary support or costs of legal proceedings during a matrimonial case.",
            "permanent": "Permanent alimony or continuing financial support linked to a decree of divorce, separation or nullity.",
            "recover": "Collect unpaid amounts already due under a court support order.",
            "vary": "Increase, reduce or otherwise change an existing court maintenance order.",
            "other": "No such request, incidental or negated request, or a different legal issue.",
            "unclear": "The requested remedy is materially ambiguous.",
        },
    },
    "beneficiary": {
        "type": "choice",
        "instructions": "Who would receive or benefit from the financial maintenance requested? Choose based on the request, regardless of who is asking.",
        "criteria": {
            "wife": "A wife or divorced wife herself, seeking support from her husband or former husband.",
            "minor_child": "A child clearly younger than eighteen, seeking support from a parent, directly or through another person.",
            "parent": "A parent seeking support from their adult son or daughter.",
            "husband": "A husband seeking support for himself from his wife.",
            "unclear": "The role is unspecified, multiple, outside these choices or no maintenance is requested.",
        },
    },
}


@lru_cache(maxsize=2)
def _load(device: str | None):
    from huggingface_hub import snapshot_download
    import laya

    path = snapshot_download(MODEL, revision=REVISION, local_files_only=True)
    return laya.load(path, device=device)


def _score(value) -> float:
    if type(value) not in {int, float} or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Invalid probability in the LAYA model response.")
    return float(value)


def extract_facts(question: str, *, device: str | None = None) -> dict[str, float]:
    result = _load(device).predict({"body": question}, PROMPTS)
    try:
        answers = result["answers"]
        purpose = {key: _score(answers["purpose"]["probabilities"][key])
                   for key in PROMPTS["purpose"]["criteria"]}
        beneficiary = {key: _score(answers["beneficiary"]["probabilities"][key])
                       for key in PROMPTS["beneficiary"]["criteria"]}
        support = _score(answers["maintenance"]["noul"])
    except (KeyError, TypeError) as error:
        raise ValueError("The local model did not return the expected fields.") from error

    return {
        "maintenance": support,
        **{key: value for key, value in purpose.items() if key not in {"other", "unclear"}},
        **{key: value for key, value in beneficiary.items() if key != "unclear"},
    }
