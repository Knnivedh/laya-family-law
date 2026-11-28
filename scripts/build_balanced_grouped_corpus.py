#!/usr/bin/env python3
"""Build a balanced, block-disjoint trilingual training set over LAYA grouped split.

Preserves:
- ``data/synthetic_v7_1/validation.jsonl`` (FROZEN, untouched)
- ``grouped_dev.jsonl`` (498 block-disjoint rows from build_grouped_family_split.py)

Generates clean synthetic balanced blocks ONLY in the training partition
(``data/synthetic_v7_1_balanced/balanced_train.jsonl``) to remediate the corpus
imbalances identified in ``docs/family-law-data-audit.md``:
1. Zero-denied issues: ``violence``, ``birth_certificate``, ``procedure``.
2. Eleven zero-denied facts: ``judicial_separation_only``, ``lump_sum_settlement``,
   ``interim_asked``, ``child_fact``, ``minor_child``, ``child_maintenance_only``,
   ``school_fees_fact``, ``child_safety_risk``, ``explicit_residence_order_only``,
   ``stridhan_sold_or_mortgaged``, ``birth_cert_asked``.
3. Zero-conflict facts across key family-law disputes.
4. Sparse span density (all added records carry ``[[key:phrase]]`` spans).
5. Minority issues (``restitution``, ``dv_compensation``, ``procedure``,
   ``birth_certificate``, ``joint_property``, ``judicial_separation``),
   demographics (``M``, ``parent``, ``child``), prospective-vs-existing order
   contrasts, and colloquial Kannada / Kanglish paraphrases.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from build_grouped_family_split import CORPUS, SOURCE, grouped_split, verify_split  # noqa: E402
from laya_v7_classifier import FACTS, ISSUES  # noqa: E402

SPAN_RE = re.compile(r"\[\[([A-Za-z_0-9]+):([^\]]+)\]\]")


def _normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _render(template: str, rng: random.Random, lang: str) -> tuple[str, list[dict[str, Any]]]:
    slots = {
        "en": {
            "age": rng.choice(["4", "5", "7", "9", "11", "14"]),
            "adult_age": rng.choice(["21", "24", "27", "30"]),
            "months": rng.choice(["four months", "seven months", "eleven months", "two years"]),
            "amt": rng.choice(["18,000 rupees", "35,000 rupees", "45,000 rupees"]),
            "city": rng.choice(["Mysuru", "Hubballi", "Mangaluru", "Belagavi", "Bengaluru"]),
        },
        "kn": {
            "age": rng.choice(["4", "5", "7", "9", "11", "14"]),
            "adult_age": rng.choice(["21", "24", "27", "30"]),
            "months": rng.choice(["ನಾಲ್ಕು ತಿಂಗಳಿಂದ", "ಏಳು ತಿಂಗಳಿಂದ", "ಒಂದು ವರ್ಷದಿಂದ", "ಎರಡು ವರ್ಷಗಳಿಂದ"]),
            "amt": rng.choice(["18,000 ರೂಪಾಯಿ", "35,000 ರೂಪಾಯಿ", "45,000 ರೂಪಾಯಿ"]),
            "city": rng.choice(["ಮೈಸೂರು", "ಹುಬ್ಬಳ್ಳಿ", "ಮಂಗಳೂರು", "ಬೆಳಗಾವಿ", "ಬೆಂಗಳೂರು"]),
        },
        "kn_roman": {
            "age": rng.choice(["4", "5", "7", "9", "11", "14"]),
            "adult_age": rng.choice(["21", "24", "27", "30"]),
            "months": rng.choice(["naalku tingalinda", "elu tingalinda", "ondu varshada", "eradu varshadinda"]),
            "amt": rng.choice(["18,000 rupees", "35,000 rupees", "45,000 rupees"]),
            "city": rng.choice(["Mysuru", "Hubballi", "Mangaluru", "Belagavi", "Bengaluru"]),
        },
    }[lang]
    filled = template.format(**slots)
    out: list[str] = []
    spans: list[dict[str, Any]] = []
    pos = 0
    for match in SPAN_RE.finditer(filled):
        out.append(filled[pos:match.start()])
        start = sum(len(chunk) for chunk in out)
        phrase = match.group(2)
        out.append(phrase)
        key = match.group(1)
        spans.append({
            "key": key,
            "kind": "fact" if key in FACTS else "issue",
            "text": phrase,
            "start": start,
            "end": start + len(phrase),
        })
        pos = match.end()
    out.append(filled[pos:])
    return "".join(out), spans


def _make_record(
    idx: int,
    spec: dict[str, Any],
    lang: str,
    rng: random.Random,
) -> dict[str, Any]:
    template = rng.choice(spec["templates"][lang])
    text, spans = _render(template, rng, lang)
    issues = {name: "uncertain" for name in ISSUES}
    for name, val in spec.get("issues", {}).items():
        issues[name] = val
    facts = {name: "unknown" for name in FACTS}
    facts["in_scope"] = spec.get("in_scope", "supported")
    for name, val in spec.get("facts", {}).items():
        facts[name] = val
    enums = {
        "claimant_sex": spec.get("sex", "F"),
        "claimant_role": spec.get("role", "spouse"),
        "modality_time": spec.get("modality", "present"),
    }
    return {
        "id": f"BAL-TR-{idx:05d}",
        "lang": lang,
        "text": text,
        "issues": issues,
        "facts": facts,
        "enums": enums,
        "spans": spans,
        "meta": {
            "cluster": spec["cluster"],
            "blocks": [spec["id"]],
            "split": "train",
        },
    }


BALANCED_SPECS: list[dict[str, Any]] = [
    # 1. Explicit denials of previously zero-denied issues (violence, birth_certificate, procedure)
    {
        "id": "bal_deny_violence_maint",
        "cluster": "bal_neg",
        "issues": {"violence": "denied", "maintenance": "requested"},
        "facts": {"violence": "denied", "money_fact": "supported", "child_safety_risk": "denied"},
        "templates": {
            "en": [
                "There is [[violence:no physical cruelty or threat anywhere at home]], and our home is safe. I only ask for [[maintenance:monthly maintenance]] because my husband [[money_fact:stopped sending living money]] since {months}.",
                "My spouse has [[violence:never assaulted or intimidated me]]. I need [[maintenance:regular financial allowance]] for rent and groceries as he [[money_fact:withholds monthly expenses]].",
            ],
            "kn": [
                "ಮನೆಯಲ್ಲಿ [[violence:ಯಾವುದೇ ಹಲ್ಲೆ ಅಥವಾ ಬೆದರಿಕೆ ಇಲ್ಲ]], ನಮ್ಮ ವಾತಾವರಣ ಸುರಕ್ಷಿತವಾಗಿದೆ. ನನ್ನ ಗಂಡ {months} [[money_fact:ಮನೆ ಖರ್ಚಿಗೆ ಹಣ ಕೊಡುವುದನ್ನು ನಿಲ್ಲಿಸಿದ್ದಾರೆ]], ನನಗೆ [[maintenance:ಮಾಸಿಕ ಜೀವನಾಂಶ]] ಬೇಕು.",
                "ನನ್ನ ಪತಿ ನನ್ನ ಮೇಲೆ [[violence:ಎಂದಿಗೂ ದೌರ್ಜನ್ಯ ಅಥವಾ ಹೊಡೆತ ಮಾಡಿಲ್ಲ]]. ಅವರು [[money_fact:ಖರ್ಚಿಗೆ ದುಡ್ಡು ಕೊಡುತ್ತಿಲ್ಲವಾದ್ದರಿಂದ]] ನನಗೆ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕಾಗಿದೆ.",
            ],
            "kn_roman": [
                "Maneyalli [[violence:yavude halle athava bedarike illa]]. Nanna ganda {months} inda [[money_fact:kharchige hana koduttilla]], nange [[maintenance:monthly jivanaamsha]] beku.",
                "Nanna pati [[violence:yavattu hodetavu maadilla]]. Avaru [[money_fact:maneya kharchige duddu kodutta illa]], nange [[maintenance:maintenance]] bekagide.",
            ],
        },
    },
    {
        "id": "bal_deny_birth_cert_custody",
        "cluster": "bal_neg",
        "issues": {"birth_certificate": "denied", "custody": "requested"},
        "facts": {"birth_cert_asked": "denied", "custody_claim": "supported", "child_fact": "supported", "minor_child": "supported", "child_safety_risk": "denied"},
        "templates": {
            "en": [
                "We already possess the municipal [[birth_cert_asked:birth record and do not ask for any birth certificate correction]]. My husband took our {age}-year-old child to {city}; I ask for [[custody:care and guardianship of my minor child]].",
                "No [[birth_certificate:birth registration application is needed]] because the certificate is ready. I want [[custody_claim:our {age}-year-old child to live with me]] safely.",
            ],
            "kn": [
                "ನಮ್ಮ ಮಗುವಿನ [[birth_cert_asked:ಜನನ ಪ್ರಮಾಣಪತ್ರ ಈಗಾಗಲೇ ಸರಿಯಾಗಿದೆ, ಅದಕ್ಕಾಗಿ ಯಾವುದೇ ಅರ್ಜಿ ಬೇಡ]]. ನನ್ನ {age} ವರ್ಷದ ಮಗುವನ್ನು [[custody:ನನ್ನ ವಶದಲ್ಲಿ ಇರಿಸಿಕೊಳ್ಳಲು]] ಕಾನೂನು ಪರಿಹಾರ ಬೇಕು.",
                "ನಮಗೆ [[birth_certificate:ಹೊಸ ಜನನ ನೋಂದಣಿ ಬೇಡವೇ ಬೇಡ]]. {age} ವರ್ಷದ ಮಗುವಿನ [[custody_claim:ಪೋಷಣೆ ಮತ್ತು ವಶವನ್ನು]] ನನಗೆ ಕೊಡಬೇಕು.",
            ],
            "kn_roman": [
                "Maguvina [[birth_cert_asked:janana pramaanapatra sariyagide, adakke arji beda]]. Nanna {age} varshada maguvina [[custody:custody mattu rakshane]] nange beku.",
                "Namage [[birth_certificate:birth certificate tiddapadi beda]]. Aa {age} varshada [[custody_claim:maguvannu nanna jothe iralu]] court order beku.",
            ],
        },
    },
    {
        "id": "bal_deny_procedure_ask",
        "cluster": "bal_neg",
        "issues": {"procedure": "denied", "residence": "requested"},
        "facts": {"residence_claim": "supported", "explicit_residence_order_only": "supported", "coercive_eviction_or_lockout": "denied", "violence": "denied"},
        "templates": {
            "en": [
                "I am [[procedure:not asking about filing fees or general court steps]]. Although there has been [[coercive_eviction_or_lockout:no forcible lockout or violence]], I want an [[explicit_residence_order_only:explicit court order securing my right to stay]] in the [[residence:shared family house]] in {city}.",
                "Please [[procedure:do not list document checklists or appeals timelines]]. Nobody beat me, yet I seek a [[residence_claim:clear order allowing me to remain in the matrimonial house]].",
            ],
            "kn": [
                "ನನಗೆ [[procedure:ಕೋರ್ಟ್ ಶುಲ್ಕ ಅಥವಾ ದಾಖಲೆ ಪಟ್ಟಿಯ ಮಾಹಿತಿ ಬೇಡ]]. ಮನೆಯಲ್ಲಿ [[coercive_eviction_or_lockout:ಯಾರೂ ಬೀಗ ಹಾಕಿಲ್ಲ ಮತ್ತು ಹೊಡೆದಿಲ್ಲ]], ಆದರೆ ನಾನು {city} [[residence:ಸಂಸಾರದ ಮನೆಯಲ್ಲಿ ವಾಸಿಸುವ ಹಕ್ಕನ್ನು]] [[explicit_residence_order_only:ಸ್ಪಷ್ಟ ವಾಸದ ಆದೇಶದ ಮೂಲಕ]] ಉಳಿಸಿಕೊಳ್ಳಬೇಕು.",
                "ದಯವಿಟ್ಟು [[procedure:ಪ್ರಕ್ರಿಯೆ ಮತ್ತು ಮೇಲ್ಮನವಿ ವಿವರ ಬೇಡ]]. ನನಗೆ [[residence_claim:ಗಂಡನ ಮನೆಯಲ್ಲಿ ಉಳಿದುಕೊಳ್ಳಲು]] ವಾಸದ ರಕ್ಷಣಾ ಆದೇಶ ಬೇಕು.",
            ],
            "kn_roman": [
                "Nange [[procedure:court procedure athava fee bagge mahiti beda]]. Yaaru [[coercive_eviction_or_lockout:lock haakilla]], aadre {city} [[residence:maneyalli vaasa maaduva hakku]] ulsikolloke [[explicit_residence_order_only:spashta residence order]] beku.",
                "Dayavittu [[procedure:document steps helabedi]]. Nange [[residence_claim:gandana maneyalli iralu court order]] maatra beku.",
            ],
        },
    },
    # 2. Denied fact coverage for formerly zero-denied facts
    {
        "id": "bal_deny_js_and_divorce_for_restitution",
        "cluster": "bal_neg",
        "issues": {"restitution": "requested", "divorce": "denied"},
        "facts": {"restitution_asked": "supported", "divorce_asked": "denied", "judicial_separation_only": "denied", "mutual_consent": "denied"},
        "templates": {
            "en": [
                "My wife moved to {city} {months} ago without reason. I want [[restitution_asked:her to resume living with me as my spouse]] — I refuse [[divorce:divorce]] and I do [[judicial_separation_only:not want judicial separation or living apart]].",
                "I do [[judicial_separation_only:not seek judicial separation]] nor [[mutual_consent:mutual divorce]]. Please help me invite [[restitution:my spouse back to our matrimonial home]].",
            ],
            "kn": [
                "ನನ್ನ ಹೆಂಡತಿ {months} {city} ನಲ್ಲಿ ಪ್ರತ್ಯೇಕವಾಗಿದ್ದಾರೆ. ನನಗೆ [[divorce:ವಿಚ್ಛೇದನ]] ಬೇಡ, [[judicial_separation_only:ನ್ಯಾಯಾಂಗ ಬೇರ್ಪಡಿಸುವಿಕೆಯೂ ಬೇಡ]]; ನನ್ನ ಪತ್ನಿ [[restitution_asked:ಮರಳಿ ನನ್ನೊಂದಿಗೆ ಬಂದು ಸಂಸಾರ ಮಾಡುವಂತೆ]] ಬಯಸುತ್ತೇನೆ.",
                "ನಾನು [[judicial_separation_only:ಬೇರ್ಪಡಿಸುವಿಕೆ]] ಅಥವಾ [[mutual_consent:ಪರಸ್ಪರ ವಿಚ್ಛೇದನ]] ಕೇಳುತ್ತಿಲ್ಲ. ನನ್ನ ಸಂಗಾತಿ [[restitution:ಮನೆಗೆ ವಾಪಸು ಬರಲು]] ಪರಿಹಾರ ಕೇಳುತ್ತಿದ್ದೇನೆ.",
            ],
            "kn_roman": [
                "Nanna hendati {months} {city} alli bere iddare. Nange [[divorce:divorce beda]], [[judicial_separation_only:judicial separation kuda beda]]; avaru [[restitution_asked:manege vaapasu bandu jothe iralu]] keluttiddene.",
                "Naanu [[judicial_separation_only:bere iruva court order]] athava [[mutual_consent:mutual divorce]] keluttilla. [[restitution:Nanna spouse vaapasu barbeku]] aste.",
            ],
        },
    },
    {
        "id": "bal_deny_lump_interim_existing_prospective",
        "cluster": "bal_neg",
        "issues": {"maintenance": "requested"},
        "facts": {
            "money_fact": "supported",
            "lump_sum_settlement": "denied",
            "interim_asked": "denied",
            "existing_order_enforcement": "denied",
            "proceeding_pending_hma": "denied",
            "decree": "denied",
            "child_fact": "denied",
            "minor_child": "denied",
            "child_maintenance_only": "denied",
            "school_fees_fact": "denied",
        },
        "templates": {
            "en": [
                "I have [[existing_order_enforcement:no earlier court order yet]] and [[child_fact:no children at all]], nor am I paying [[school_fees_fact:any school fees]]. I reject a [[lump_sum_settlement:one-time lump sum settlement]] and [[interim_asked:do not seek interim alimony during any divorce case]]; I need a [[money_fact:fresh monthly maintenance order]] from scratch because we have [[proceeding_pending_hma:no matrimonial suit pending]].",
                "We are [[child_maintenance_only:not asking only for child expenses]] because [[minor_child:we do not have any minor child]]. There is [[existing_order_enforcement:zero prior order to enforce]] and [[lump_sum_settlement:no lump-sum deal]]; I want a [[maintenance:brand new monthly allowance order]] of {amt}.",
            ],
            "kn": [
                "ನಮ್ಮಲ್ಲಿ [[existing_order_enforcement:ಇದುವರೆಗೆ ಯಾವುದೇ ಹಿಂದಿನ ಆದೇಶ ಇಲ್ಲ]] ಮತ್ತು [[child_fact:ನಮಗೆ ಮಕ್ಕಳೂ ಇಲ್ಲ]], [[school_fees_fact:ಶಾಲಾ ಶುಲ್ಕದ ಪ್ರಶ್ನೆಯೂ ಇಲ್ಲ]]. ನನಗೆ [[lump_sum_settlement:ಒಂದೇ ಬಾರಿಯ ಇತ್ಯರ್ಥ ಹಣ ಬೇಡ]] ಮತ್ತು [[interim_asked:ಮಧ್ಯಂತರ ಹಣವೂ ಬೇಡ]]; [[proceeding_pending_hma:ಯಾವುದೇ ವಿಚ್ಛೇದನ ಕೇಸ್ ನಡೆಯುತ್ತಿಲ್ಲ]], ನನಗೆ [[maintenance:ಹೊಸದಾಗಿ ಮಾಸಿಕ ಜೀವನಾಂಶ ಆದೇಶ]] ಬೇಕು.",
                "ನನಗೆ [[minor_child:ಚಿಕ್ಕ ಮಗು ಇಲ್ಲ]], ಹೀಗಾಗಿ [[child_maintenance_only:ಮಗುವಿಗೆ ಮಾತ್ರವಲ್ಲ]]. [[existing_order_enforcement:ಹಿಂದಿನ ಆದೇಶ ಜಾರಿ ಮಾಡುವುದಲ್ಲ]]; [[money_fact:ತಿಂಗಳಿಗೆ {amt} ಹೊಸ ಜೀವನಾಂಶ ಆದೇಶ]] ಬೇಕಾಗಿದೆ.",
            ],
            "kn_roman": [
                "Namma hatra [[existing_order_enforcement:yavude hinde court order illa]], [[child_fact:makkalu kuda illa]], [[school_fees_fact:school fees prashne illa]]. [[lump_sum_settlement:One-time settlement beda]], [[interim_asked:interim support kuda beda]]; [[proceeding_pending_hma:divorce case pending illa]], nange [[maintenance:hosa monthly maintenance order]] beku.",
                "[[minor_child:Minor child illa]], [[child_maintenance_only:makkalige maatra keluttilla]]. [[existing_order_enforcement:Hinde order enforce alla]]; [[money_fact:{amt} hosa maintenance order]] bekagide.",
            ],
        },
    },
    {
        "id": "bal_deny_stridhan_sold_and_demand",
        "cluster": "bal_neg",
        "issues": {"stridhan": "requested"},
        "facts": {
            "stridhan_claim": "supported",
            "stridhan_sold_or_mortgaged": "denied",
            "demand_made": "denied",
            "joint_property_claim": "denied",
        },
        "templates": {
            "en": [
                "My wedding gold ornaments are locked in my husband's {city} cupboard; [[stridhan_sold_or_mortgaged:none of the jewellery has been sold or mortgaged]] and there is [[joint_property_claim:no jointly purchased apartment]]. I [[demand_made:have never formally demanded them back yet]], so how do I protect my [[stridhan_claim:wedding gold]]?",
                "My parents gifted me jewellery still kept intact by my husband — [[stridhan_sold_or_mortgaged:it is neither sold nor pledged]] and I [[demand_made:haven't asked for its return yet]]. Can I reclaim my [[stridhan:stridhan]]?",
            ],
            "kn": [
                "ಮದುವೆಯಲ್ಲಿ ತಂದೆಯವರು ಕೊಟ್ಟ ಚಿನ್ನಾಭರಣಗಳು {city} ಗಂಡನ ಮನೆಯಲ್ಲಿವೆ; [[stridhan_sold_or_mortgaged:ಅವುಗಳನ್ನು ಮಾರಿಲ್ಲ ಅಥವಾ ಅಡವಿಟ್ಟಿಲ್ಲ]] ಮತ್ತು [[joint_property_claim:ಜಂಟಿ ಆಸ್ತಿ ಇಲ್ಲ]]. ನಾನು [[demand_made:ಇನ್ನೂ ವಾಪಸು ಕೇಳಿಲ್ಲ]], ನನ್ನ [[stridhan_claim:ಸ್ತ್ರೀಧನ ಚಿನ್ನ]] ಹೇಗೆ ರಕ್ಷಿಸಲಿ?",
                "ನನ್ನ ಒಡವೆಗಳು ಇನ್ನೂ ಗಂಡನ ಮನೆಯಲ್ಲೇ ಇವೆ — [[stridhan_sold_or_mortgaged:ಮಾರಾಟವಾಗಿಲ್ಲ]]. ನಾನು [[demand_made:ಇದುವರೆಗೆ ವಾಪಸು ಕೊಡಲು ಕೇಳಿಲ್ಲ]], ನನ್ನ [[stridhan:ಸ್ತ್ರೀಧನ]] ಪಡೆಯುವುದು ಹೇಗೆ?",
            ],
            "kn_roman": [
                "Maduveyalli kotta bangaara {city} gandana maneyallide; [[stridhan_sold_or_mortgaged:adannu maarilla athava adavu ittilla]], [[joint_property_claim:joint property illa]]. Naanu [[demand_made:innu vaapasu kelilla]], nanna [[stridhan_claim:stridhan bangaara]] hege tagobeku?",
                "Nanna odavegalu gandana maneyalle ive — [[stridhan_sold_or_mortgaged:sell maadilla]]. Naanu [[demand_made:innu vapasu kelilla]], [[stridhan:stridhan]] wapasu tagoloke enu maadbeku?",
            ],
        },
    },
    # 3. Minority roles (Male self HMA 24, Father child-only BNSS 144, Elderly parent BNSS 144, Minor child speaking)
    {
        "id": "bal_male_pending_hma_interim",
        "cluster": "bal_role_m",
        "sex": "M",
        "role": "spouse",
        "issues": {"maintenance": "requested", "divorce": "incidental", "procedure": "requested"},
        "facts": {"proceeding_pending_hma": "supported", "money_fact": "supported", "interim_asked": "supported", "divorce_asked": "denied", "child_maintenance_only": "denied"},
        "templates": {
            "en": [
                "I am the husband; my wife earns {amt} while I am unemployed after surgery. Her [[proceeding_pending_hma:HMA divorce petition is already pending]] in {city}. Can I request [[interim_asked:interim maintenance and litigation expenses]] while the suit continues?",
                "As a husband facing a [[proceeding_pending_hma:pending Hindu Marriage Act case]], I seek [[interim_asked:temporary support and legal fees]] from my earning wife. [[procedure:Which court hears this interim plea?]]",
            ],
            "kn": [
                "ನಾನು ಪತಿ; ನನ್ನ ಪತ್ನಿ {amt} ದುಡಿಯುತ್ತಾರೆ ಮತ್ತು ಶಸ್ತ್ರಚಿಕಿತ್ಸೆ ನಂತರ ನನಗೆ ಆದಾಯವಿಲ್ಲ. {city} ನ್ಯಾಯಾಲಯದಲ್ಲಿ [[proceeding_pending_hma:HMA ವಿಚ್ಛೇದನ ಅರ್ಜಿ ಬಾಕಿ ಇದೆ]]. ನಾನು [[interim_asked:ಮಧ್ಯಂತರ ಜೀವನಾಂಶ ಮತ್ತು ಕೇಸ್ ಖರ್ಚು]] ಕೇಳಬಹುದೇ?",
                "ಗಂಡನಾಗಿ, [[proceeding_pending_hma:ನಡೆಯುತ್ತಿರುವ ವಿಚ್ಛೇದನ ಪ್ರಕರಣದಲ್ಲಿ]] ಸಂಪಾದಿಸುವ ಹೆಂಡತಿಯಿಂದ [[interim_asked:ತಾತ್ಕಾಲಿಕ ಜೀವನಾಂಶ]] ಬೇಕು. [[procedure:ಯಾವ ನ್ಯಾಯಾಲಯದಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಬೇಕು?]]",
            ],
            "kn_roman": [
                "Naanu husband; nanna wife {amt} earn maadtare. {city} court alli [[proceeding_pending_hma:HMA divorce case pending ide]]. Case mugiyuvaregu [[interim_asked:interim maintenance mattu lawyer fees]] kelabahuda?",
                "Husband aagi [[proceeding_pending_hma:pending divorce case]] nalli earning wife inda [[interim_asked:temporary support]] beku. [[procedure:Yaava court ge hogbeku?]]",
            ],
        },
    },
    {
        "id": "bal_father_child_only_bnss",
        "cluster": "bal_role_m",
        "sex": "M",
        "role": "spouse",
        "issues": {"maintenance": "requested"},
        "facts": {"money_fact": "supported", "child_maintenance_only": "supported", "child_fact": "supported", "minor_child": "supported", "school_fees_fact": "supported", "violence": "denied"},
        "templates": {
            "en": [
                "I am a father raising our {age}-year-old child alone; [[violence:there is no domestic violence]]. My wife earns {amt} and refuses to contribute. I need [[child_maintenance_only:monthly support solely for our minor child's]] [[school_fees_fact:school fees and living costs]], not for myself.",
                "Father here — I ask for [[child_maintenance_only:support strictly for our {age}-year-old child]] and [[school_fees_fact:school tuition]], not for me, from my employed wife.",
            ],
            "kn": [
                "ನಾನು ತಂದೆ, ನಮ್ಮ {age} ವರ್ಷದ ಮಗುವನ್ನು ಒಬ್ಬನೇ ಸಾಕುತ್ತಿದ್ದೇನೆ; [[violence:ಯಾವುದೇ ದೌರ್ಜನ್ಯ ಇಲ್ಲ]]. ಪತ್ನಿ {amt} ಗಳಿಸುತ್ತಾರೆ. ನನಗಾಗಿ ಅಲ್ಲ, [[child_maintenance_only:ಮಗುವಿನ]] [[school_fees_fact:ಶಾಲಾ ಶುಲ್ಕ ಮತ್ತು ಖರ್ಚಿಗೆ ಮಾತ್ರ]] [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು.",
                "ತಂದೆಯಾಗಿ ನಾನು [[child_maintenance_only:ನನ್ನ {age} ವರ್ಷದ ಮಗುವಿಗೆ ಮಾತ್ರ]] [[school_fees_fact:ಶಿಕ್ಷಣ ಮತ್ತು ಖರ್ಚಿನ]] [[money_fact:ಮಾಸಿಕ ಸಹಾಯ]] ಕೇಳುತ್ತಿದ್ದೇನೆ.",
            ],
            "kn_roman": [
                "Naanu father, {age} varshada maguvannu nodikolluttiddene; [[violence:yavude violence illa]]. Wife {amt} salary ide. Nange alla, [[child_maintenance_only:maguvige maatra]] [[school_fees_fact:school fees mattu kharchige]] [[maintenance:maintenance]] beku.",
                "Father here — [[child_maintenance_only:namma {age} varshada maguvige maatra]] [[school_fees_fact:education expenses]] koodalu [[money_fact:monthly money]] keluttiddene.",
            ],
        },
    },
    {
        "id": "bal_elderly_parent_bnss",
        "cluster": "bal_role_p",
        "sex": "U",
        "role": "parent",
        "issues": {"maintenance": "requested", "procedure": "requested"},
        "facts": {"money_fact": "supported", "child_fact": "denied", "minor_child": "denied", "child_maintenance_only": "denied"},
        "templates": {
            "en": [
                "I am a 71-year-old retired parent with medical bills and no pension. My {adult_age}-year-old employed son earns {amt} in {city} but refuses care. [[procedure:Where do I file]] for [[maintenance:monthly parent maintenance]]?",
                "As an infirm elderly mother whose grown {adult_age}-year-old daughter will not assist me, can I seek [[money_fact:monthly subsistence from my earning adult child]]?",
            ],
            "kn": [
                "ನಾನು 71 ವರ್ಷದ ವೃದ್ಧ ತಂದೆ/ತಾಯಿ, ವೈದ್ಯಕೀಯ ಖರ್ಚಿಗೆ ಆದಾಯವಿಲ್ಲ. {city} ಯಲ್ಲಿ {amt} ದುಡಿಯುವ {adult_age} ವರ್ಷದ ಮಗ ನೋಡಿಕೊಳ್ಳುತ್ತಿಲ್ಲ. [[maintenance:ತಂದೆ-ತಾಯಿ ಜೀವನಾಂಶಕ್ಕಾಗಿ]] [[procedure:ಎಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಲಿ?]]",
                "ನಾನು ಅಶಕ್ತ ವೃದ್ಧ ತಾಯಿ, ದುಡಿಯುವ {adult_age} ವರ್ಷದ ಮಗಳು ನನ್ನನ್ನು ನೋಡಿಕೊಳ್ಳುತ್ತಿಲ್ಲ. [[money_fact:ಮಾಸಿಕ ಜೀವನಾಂಶ]] ಪಡೆಯಬಹುದೇ?",
            ],
            "kn_roman": [
                "Naanu 71 varshada vruddha parent, medicine ge hana illa. {city} alli {amt} earn maaduva {adult_age} varshada maga nodikolluttilla. [[maintenance:Parent maintenance]] ge [[procedure:elli case haakbeku?]]",
                "Naanu aged mother, kelasa maaduva {adult_age} varshada magalu help maaduttilla. [[money_fact:Monthly support]] tagobahuda?",
            ],
        },
    },
    # 4. DV compensation, child safety risk, explicit residence order denied (violent lockout), existing order
    {
        "id": "bal_dv_comp_and_child_risk",
        "cluster": "bal_minor",
        "issues": {"dv_compensation": "requested", "violence": "requested", "custody": "requested", "residence": "requested"},
        "facts": {
            "violence": "supported",
            "dv_injury_comp_asked": "supported",
            "custody_claim": "supported",
            "child_fact": "supported",
            "minor_child": "supported",
            "child_safety_risk": "supported",
            "residence_claim": "supported",
            "coercive_eviction_or_lockout": "supported",
            "explicit_residence_order_only": "denied",
        },
        "templates": {
            "en": [
                "My husband [[violence:fractured my wrist during an assault]] in {city}, [[coercive_eviction_or_lockout:changed the door lock to keep me out]], and [[child_safety_risk:leaves our {age}-year-old child locked outside at night while drunk]]. [[explicit_residence_order_only:This is violent abuse, not a peaceful residence-only matter]]. I want [[dv_injury_comp_asked:monetary compensation for the injuries and trauma]], [[residence:re-entry to the shared house]], and [[custody:urgent custody of my child]].",
                "He [[violence:beats me regularly]] and [[coercive_eviction_or_lockout:threw me and our {age}-year-old child onto the street]] after {months} of threats; [[explicit_residence_order_only:it is not merely an unviolent residence order request]]. [[child_safety_risk:He threatens to harm our child]]. I seek [[dv_compensation:compensation for domestic violence injuries]] and [[custody_claim:safe child custody]].",
            ],
            "kn": [
                "{city} ನಲ್ಲಿ ನನ್ನ ಗಂಡ [[violence:ಹೊಡೆದು ನನ್ನ ಕೈ ಮುರಿದಿದ್ದಾರೆ]], [[coercive_eviction_or_lockout:ಮನೆಯ ಬೀಗ ಬದಲಿಸಿ ಹೊರಹಾಕಿದ್ದಾರೆ]] ಮತ್ತು [[child_safety_risk:{age} ವರ್ಷದ ಮಗುವನ್ನು ರಾತ್ರಿ ಹೊರಗೆ ಬಿಟ್ಟು ಹಿಂಸಿಸುತ್ತಾರೆ]]. [[explicit_residence_order_only:ಇದು ಶಾಂತಿಯುತ ಕೇವಲ ವಾಸದ ಆದೇಶವಲ್ಲ, ಹಿಂಸಾತ್ಮಕ ದೌರ್ಜನ್ಯ]]. ನನಗೆ [[dv_injury_comp_asked:ಗಾಯಕ್ಕೆ ಪರಿಹಾರ ಹಣ]], [[residence:ಮನೆಯ ರಕ್ಷಣೆ]], ಹಾಗೂ [[custody:ಮಗುವಿನ ಸುರಕ್ಷಿತ ವಶ]] ಬೇಕು.",
                "ಅವರು [[violence:ಪ್ರತಿದಿನ ದೈಹಿಕ ಹಿಂಸೆ ನೀಡುತ್ತಾರೆ]] ಮತ್ತು {months} [[coercive_eviction_or_lockout:ಮನೆಯಿಂದ ಹೊರದಬ್ಬಿದ್ದಾರೆ]]. [[explicit_residence_order_only:ಹಿಂಸೆಯಿಲ್ಲದ ಕೇವಲ ವಾಸದ ಪ್ರಶ್ನೆಯಲ್ಲ]]; [[child_safety_risk:{age} ವರ್ಷದ ಮಗುವಿಗೆ ಅಪಾಯವಿದೆ]]. [[dv_compensation:ದೌರ್ಜನ್ಯ ಪರಿಹಾರ ಧನ]] ಮತ್ತು [[custody_claim:ಮಗುವಿನ ಕಸ್ಟಡಿ]] ಬೇಕು.",
            ],
            "kn_roman": [
                "{city} alli nanna ganda [[violence:hodedu kai muriddare]], [[coercive_eviction_or_lockout:mane lock maadi horage haakiddare]], mattu kudidu [[child_safety_risk:{age} varshada maguvannu night horage bidtare]]. [[explicit_residence_order_only:Idu kevala shantiyuta residence order alla, himsaatmaka dv]]. Nange [[dv_injury_comp_asked:injury compensation]], [[residence:mane entry order]], mattu [[custody:maguvina safe custody]] beku.",
                "Avaru [[violence:dina hit maadtare]] mattu {months} inda [[coercive_eviction_or_lockout:mane inda horage dabbiddare]]. [[explicit_residence_order_only:Bari residence order maatra alla]]; [[child_safety_risk:{age} varshada maguvige safety threat ide]]. [[dv_compensation:DV compensation]] mattu [[custody_claim:child custody]] beku.",
            ],
        },
    },
    {
        "id": "bal_existing_order_enforce_vary",
        "cluster": "bal_order",
        "issues": {"maintenance": "requested", "procedure": "requested"},
        "facts": {"existing_order_enforcement": "supported", "money_fact": "supported", "lump_sum_settlement": "denied"},
        "templates": {
            "en": [
                "I already hold a [[existing_order_enforcement:Magistrate maintenance order passed under BNSS section 144]], but my former spouse skipped {months} of payments. [[procedure:How do I recover the unpaid arrears]]?",
                "My [[existing_order_enforcement:existing BNSS 144 maintenance order]] fixed a low amount two years ago, and costs doubled in {city}. Can I [[money_fact:apply to increase the ordered monthly allowance]]?",
            ],
            "kn": [
                "ನನ್ನ ಬಳಿ ಈಗಾಗಲೇ [[existing_order_enforcement:BNSS ಕಲಂ 144 ರ ಅಡಿಯಲ್ಲಿ ನ್ಯಾಯಾಧೀಶರು ನೀಡಿದ ಜೀವನಾಂಶ ಆದೇಶ ಇದೆ]], ಆದರೆ {months} ಹಣ ಪಾವತಿಸಿಲ್ಲ. [[procedure:ಬಾಕಿ ಹಣವನ್ನು ವಸೂಲಿ ಮಾಡುವುದು ಹೇಗೆ?]]",
                "ಎರಡು ವರ್ಷಗಳ ಹಿಂದೆ [[existing_order_enforcement:ನ್ಯಾಯಾಲಯ ನೀಡಿದ ಜೀವನಾಂಶ ಆದೇಶದ]] ಮೊತ್ತ ಈಗ ಸಾಲುತ್ತಿಲ್ಲ. [[money_fact:ಮಾಸಿಕ ಮೊತ್ತವನ್ನು ಹೆಚ್ಚಿಸಲು ಬದಲಾವಣೆ ಕೋರಬಹುದೇ?]]",
            ],
            "kn_roman": [
                "Nanna hatra already [[existing_order_enforcement:BNSS section 144 maintenance order ide]], aadre {months} inda arrears kottilla. [[procedure:Unpaid amount hege recover maadodu?]]",
                "Hinde kotta [[existing_order_enforcement:BNSS 144 maintenance order]] kammi ide. {city} kharchige [[money_fact:monthly amount increase maadoke]] apply maadabahuda?",
            ],
        },
    },
    {
        "id": "bal_joint_prop_with_pending_hma",
        "cluster": "bal_prop",
        "issues": {"joint_property": "requested", "divorce": "requested"},
        "facts": {"joint_property_claim": "supported", "divorce_asked": "supported", "proceeding_pending_hma": "supported", "stridhan_claim": "denied", "stridhan_sold_or_mortgaged": "denied"},
        "templates": {
            "en": [
                "Our [[proceeding_pending_hma:Hindu Marriage Act divorce petition is pending]] in {city} and I seek [[divorce:dissolution of marriage]]. We bought a car and an apartment jointly at our wedding — [[stridhan_claim:no separate gold dispute exists]], only [[joint_property_claim:division of our joint matrimonial property]].",
                "While our [[proceeding_pending_hma:contested divorce suit is running]], please explain how to divide [[joint_property:jointly held wedding property]] and flat ownership.",
            ],
            "kn": [
                "{city} ಕೌಟುಂಬಿಕ ನ್ಯಾಯಾಲಯದಲ್ಲಿ [[proceeding_pending_hma:HMA ವಿಚ್ಛೇದನ ಪ್ರಕರಣ ನಡೆಯುತ್ತಿದೆ]] ಮತ್ತು ನಾನು [[divorce:ವಿಚ್ಛೇದನ]] ಕೇಳುತ್ತಿದ್ದೇನೆ. [[stridhan_claim:ಚಿನ್ನಾಭರಣದ ವಿವಾದ ಇಲ್ಲ]], ಮದುವೆ ಸಮಯದಲ್ಲಿ ಖರೀದಿಸಿದ [[joint_property_claim:ಜಂಟಿ ಫ್ಲಾಟ್ ಮತ್ತು ಆಸ್ತಿ ಹಂಚಿಕೆ]] ಬೇಕಾಗಿದೆ.",
                "ನಮ್ಮ [[proceeding_pending_hma:ವಿಚ್ಛೇದನ ಕೇಸ್ ಬಾಕಿ ಇರುವಾಗಲೇ]] ಮದುವೆಯಲ್ಲಿ ಬಂದ [[joint_property:ಜಂಟಿ ಆಸ್ತಿ ವಿಭಾಗ]] ಹೇಗೆ ಪಡೆಯಬಹುದು?",
            ],
            "kn_roman": [
                "{city} court alli [[proceeding_pending_hma:HMA divorce case pending ide]] mattu [[divorce:divorce]] keluttiddene. [[stridhan_claim:Gold dispute illa]], maduveyalli tagedukonda [[joint_property_claim:joint flat mattu property divide]] aagbeku.",
                "Namma [[proceeding_pending_hma:divorce suit nadeyuttiruvaaga]] [[joint_property:joint wedding property share]] hege tagobeku?",
            ],
        },
    },
    {
        "id": "bal_late_birth_cert_req",
        "cluster": "bal_bc",
        "issues": {"birth_certificate": "requested", "procedure": "requested"},
        "facts": {"birth_cert_asked": "supported", "child_fact": "supported", "minor_child": "supported", "divorce_asked": "denied"},
        "templates": {
            "en": [
                "Our {age}-year-old child was born at home in {city} and never registered. Now school admission requires a [[birth_cert_asked:delayed birth certificate registration]]. [[procedure:Which Magistrate or Registrar office handles late entry]]?",
                "There is a spelling mistake on my {age}-year-old child's municipal [[birth_certificate:birth certificate]] — how do we apply for correction?",
            ],
            "kn": [
                "ನಮ್ಮ {age} ವರ್ಷದ ಮಗುವಿನ ಜನನ {city} ಮನೆಯಲ್ಲಿ ಆಗಿದ್ದು ನೋಂದಣಿ ಆಗಿಲ್ಲ. ಶಾಲೆಗೆ [[birth_cert_asked:ತಡವಾದ ಜನನ ಪ್ರಮಾಣಪತ್ರ]] ಬೇಕು; [[procedure:ಯಾವ ಕಚೇರಿ ಅಥವಾ ನ್ಯಾಯಾಲಯಕ್ಕೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಬೇಕು?]]",
                "ನನ್ನ {age} ವರ್ಷದ ಮಗುವಿನ [[birth_certificate:ಜನನ ಪ್ರಮಾಣಪತ್ರದಲ್ಲಿ]] ಹೆಸರು ತಪ್ಪಾಗಿದೆ, ಸರಿಪಡಿಸುವುದು ಹೇಗೆ?",
            ],
            "kn_roman": [
                "Namma {age} varshada maguvina birth {city} maneyalli aagi register aagilla. School ge [[birth_cert_asked:late birth certificate]] beku; [[procedure:yaava office ge hogbeku?]]",
                "Nanna {age} varshada maguvina [[birth_certificate:birth certificate]] nalli hesaru wrong ide, correct maadodu hege?",
            ],
        },
    },
    # 5. Conflicting facts (explicit contradictions within the same turn)
    {
        "id": "bal_conflict_facts_suite",
        "cluster": "bal_conflict",
        "modality": "present",
        "issues": {"maintenance": "uncertain", "custody": "uncertain", "residence": "uncertain", "violence": "uncertain", "stridhan": "uncertain"},
        "facts": {
            "money_fact": "conflicting",
            "custody_claim": "conflicting",
            "residence_claim": "conflicting",
            "violence": "conflicting",
            "stridhan_claim": "conflicting",
        },
        "templates": {
            "en": [
                "After {months} in {city}, I first asked for [[money_fact:{amt} monthly support]] and [[custody_claim:custody of our {age}-year-old child]], then withdrew saying no [[money_fact:maintenance]] or [[custody_claim:custody]] is wanted. Half my draft alleges [[violence:cruelty]] while the next denies [[violence:any cruelty]], and we keep shifting on [[residence_claim:house rights]] or [[stridhan_claim:claiming jewellery]].",
                "During our {months} dispute in {city}, my note requests [[money_fact:maintenance]] and [[residence_claim:living in the shared house]] yet later says I reject [[money_fact:any money]], reject [[residence_claim:staying in the house]], contradict myself on [[custody_claim:our {age}-year-old child]], hesitate on [[stridhan_claim:wedding ornaments]], and give opposing statements about [[violence:domestic violence]].",
            ],
            "kn": [
                "{city} ನಲ್ಲಿ {months} ಕಳೆದ ನಂತರ, ಮೊದಲು ನಾನು [[money_fact:{amt} ಜೀವನಾಂಶ]] ಮತ್ತು [[custody_claim:{age} ವರ್ಷದ ಮಗುವಿನ ವಶ]] ಕೇಳಬೇಕೆಂದುಕೊಂಡೆ, ನಂತರ [[money_fact:ಹಣ ಬೇಡ]] ಮತ್ತು [[custody_claim:ವಶ ಬೇಡ]] ಎಂದೆ. ಒಂದು ಕಡೆ [[violence:ಹಿಂಸೆ ಇದೆ]] ಮತ್ತೊಂದೆಡೆ [[violence:ಹಿಂಸೆ ಇಲ್ಲ]] ಎಂದಿದೆ; [[residence_claim:ಮನೆ]] ಹಾಗೂ [[stridhan_claim:ಒಡವೆ]] ಬಗ್ಗೆ ವಿರುದ್ಧ ಹೇಳಿಕೆಗಳಿವೆ.",
                "{months} ರಿಂದ {city} ಪ್ರಕರಣದಲ್ಲಿ ನಾನು ಒಮ್ಮೆ [[residence_claim:ಮನೆಯಲ್ಲಿ ಉಳಿಯಬೇಕು]] ಮತ್ತು [[stridhan_claim:ಚಿನ್ನ ಬೇಕು]] ಎನ್ನುತ್ತೇನೆ, ಮತ್ತೊಮ್ಮೆ [[residence_claim:ಮನೆ ಬೇಡ]] ಮತ್ತು [[stridhan_claim:ಚಿನ್ನ ಬೇಡ]] ಎನ್ನುತ್ತೇನೆ; [[money_fact:ಜೀವನಾಂಶ]], [[custody_claim:{age} ವರ್ಷದ ಮಗು]] ಮತ್ತು [[violence:ದೌರ್ಜನ್ಯ]] ಕುರಿತು ವಿರೋಧಾಭಾಸವಿದೆ.",
            ],
            "kn_roman": [
                "{city} alli {months} aadmele, modalu [[money_fact:{amt} jivanaamsha]] mattu [[custody_claim:{age} varshada maguvina custody]] kelbeku ande, aamele [[money_fact:hana beda]] mattu [[custody_claim:custody beda]] ande. Ondu kade [[violence:violence ide]] innondu kade [[violence:violence illa]] anta ide; [[residence_claim:mane]] mattu [[stridhan_claim:gold]] bagge confuse aagide.",
                "{months} inda {city} vishayadalli omme [[residence_claim:maneyalli irbeku]] mattu [[stridhan_claim:bangaara beku]] antini, aamele [[residence_claim:mane beda]] mattu [[stridhan_claim:bangaara beda]] antini; [[money_fact:maintenance]], [[custody_claim:{age} varshada magu]], [[violence:dourjanya]] bagge conflict ide.",
            ],
        },
    },
    # 6. Out-of-scope domains (strictly excluded from family law)
    {
        "id": "bal_oos_domains",
        "cluster": "bal_oos",
        "sex": "U",
        "role": "other",
        "in_scope": "denied",
        "issues": {},
        "facts": {"in_scope": "denied"},
        "templates": {
            "en": [
                "A commercial tenant in my {city} shop stopped paying rent for {months} and broke the shutter lock.",
                "My former software employer withheld my final bonus and laptop deposit after resignation.",
                "The traffic police issued an incorrect challan against my scooter near {city}.",
            ],
            "kn": [
                "{city} ನಲ್ಲಿ ನನ್ನ ವಾಣಿಜ್ಯ ಅಂಗಡಿಯ ಬಾಡಿಗೆದಾರರು {months} ಬಾಡಿಗೆ ಕೊಡುತ್ತಿಲ್ಲ ಮತ್ತು ಶಟರ್ ಬೀಗ ಮುರಿದಿದ್ದಾರೆ.",
                "ನನ್ನ ಹಿಂದಿನ ಕಂಪನಿಯು ರಾಜೀನಾಮೆ ನಂತರ ಅಂತಿಮ ಬೋನಸ್ ಮತ್ತು ಭದ್ರತಾ ಠೇವಣಿ ತಡೆಹಿಡಿದಿದೆ.",
                "{city} ಬಳಿ ಟ್ರಾಫಿಕ್ ಪೊಲೀಸರು ನನ್ನ ಸ್ಕೂಟರ್ ಮೇಲೆ ತಪ್ಪಾದ ಚಲನ್ ಹಾಕಿದ್ದಾರೆ.",
            ],
            "kn_roman": [
                "{city} alli nanna shop tenant {months} inda rent koduttilla mattu lock break maadiddare.",
                "Nanna old IT company resignation aadmele salary bonus mattu deposit tadediddare.",
                "{city} hatra traffic police nanna bike mele wrong fine challan haakiddare.",
            ],
        },
    },
]


def build_balanced_corpus(output_dir: Path, *, seed: int = 7102, repeats_per_lang: int = 65) -> dict[str, Any]:
    """Generate grouped_train/grouped_dev + balanced_train in ``output_dir``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    schema = json.loads((CORPUS / "schema.json").read_text(encoding="utf-8"))
    source_rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]
    grouped_train, grouped_dev = grouped_split(
        source_rows,
        schema["issues"],
        dev_size=500,
        tolerance=25,
        seed=seed,
    )
    dev_norm_texts = {_normalize(row["text"]) for row in grouped_dev}
    train_norm_texts = {_normalize(row["text"]) for row in grouped_train}

    rng = random.Random(seed + 11)
    added: list[dict[str, Any]] = []
    seen = set(dev_norm_texts) | set(train_norm_texts)
    idx = 1
    for spec in BALANCED_SPECS:
        for lang in ("en", "kn", "kn_roman"):
            added_lang = 0
            attempts = 0
            while added_lang < repeats_per_lang and attempts < repeats_per_lang * 20:
                attempts += 1
                rec = _make_record(idx, spec, lang, rng)
                norm = _normalize(rec["text"])
                if norm in seen:
                    continue
                seen.add(norm)
                added.append(rec)
                added_lang += 1
                idx += 1

    balanced_train = list(grouped_train) + added
    rng.shuffle(balanced_train)

    def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
        payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
        path.write_text(payload, encoding="utf-8")
        return hashlib.sha256(path.read_bytes()).hexdigest()

    gt_sha = _write_jsonl(output_dir / "grouped_train.jsonl", grouped_train)
    gd_sha = _write_jsonl(output_dir / "grouped_dev.jsonl", grouped_dev)
    bt_sha = _write_jsonl(output_dir / "balanced_train.jsonl", balanced_train)

    assert not (dev_norm_texts & {_normalize(r["text"]) for r in balanced_train})
    dev_blocks = {b for r in grouped_dev for b in r["meta"]["blocks"]}
    bt_blocks = {b for r in balanced_train for b in r["meta"]["blocks"]}
    assert not (dev_blocks & bt_blocks)

    manifest = {
        "seed": seed,
        "grouped_train_rows": len(grouped_train),
        "grouped_dev_rows": len(grouped_dev),
        "added_balanced_rows": len(added),
        "balanced_train_rows": len(balanced_train),
        "overlap_vs_grouped_dev": {
            "shared_ids": len({r["id"] for r in grouped_dev} & {r["id"] for r in balanced_train}),
            "shared_blocks": len(dev_blocks & bt_blocks),
            "shared_normalized_texts": len(dev_norm_texts & {_normalize(r["text"]) for r in balanced_train}),
        },
        "sha256": {
            "grouped_train.jsonl": gt_sha,
            "grouped_dev.jsonl": gd_sha,
            "balanced_train.jsonl": bt_sha,
        },
        "added_by_lang": dict(Counter(r["lang"] for r in added)),
        "balanced_train_by_lang": dict(Counter(r["lang"] for r in balanced_train)),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "synthetic_v7_1_balanced",
    )
    parser.add_argument("--seed", type=int, default=7102)
    parser.add_argument("--repeats-per-lang", type=int, default=65)
    args = parser.parse_args()
    manifest = build_balanced_corpus(
        args.output_dir, seed=args.seed, repeats_per_lang=args.repeats_per_lang
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
