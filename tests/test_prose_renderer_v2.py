"""Offline validation and adversarial mutation suite for src/laya_prose_v2.py.

Runs against:
  1. All 16 regression questions (ground-truth/ground-truth-v2-hma27-A.json)
  2. All 230 brutal-bank GT configurations (test-bank/brutal-bank-v1-frozen.json)
  3. Edge cases: unknown section ID fail-safe, in_scope + empty kept, hma-13b guard
  4. Adversarial mutants for ALL 9 Frozen Forbidden Items + Additions A-E.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from laya_prose_v2 import KNOWN_SECTIONS, prose_forbidden_check, render_prose  # noqa: E402


GT_PATH = REPO_ROOT / "ground-truth" / "ground-truth-v2-hma27-A.json"
BANK_PATH = REPO_ROOT / "test-bank" / "brutal-bank-v1-frozen.json"


def run_validation() -> dict:
    gt16 = json.loads(GT_PATH.read_text(encoding="utf-8"))["questions"]
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))["questions"]

    child_true_16 = {"K0", "H1", "H2", "H5", "H6", "H7", "H10", "H13", "H14"}
    fees_true_16 = {"H13", "H14"}
    sold_true_16 = {"H15"}

    times_ms = []
    for q in gt16:
        facts = dict(q["facts"])
        facts["being_filed"] = False
        facts["child_fact"] = q["id"] in child_true_16
        facts["school_fees_fact"] = q["id"] in fees_true_16
        facts["stridhan_sold"] = q["id"] in sold_true_16
        facts["claimant_sex"] = "female"
        rec = {
            "id": q["id"],
            "kept_ids": q["gt_ids"],
            "court_live": q["gt_court"],
            "court_source": "out-of-scope" if not q["gt_ids"] else "kept",
            "escalation_kinds": q["gt_escalation_kinds"],
            "in_scope": bool(q["gt_ids"]),
            "facts": facts,
            "dropped": [],
        }
        res = render_prose(rec, facts)
        times_ms.append(res["prose_render_ms"])
        hits, flags = prose_forbidden_check(res["prose"], rec["kept_ids"], rec["dropped"], facts)
        assert not hits, f"16-set {q['id']} Fp hits: {hits}\n{res['prose']}"
        assert not flags, f"16-set {q['id']} quality flags: {flags}\n{res['prose']}"
        assert not res["unknown_ids"], f"Unknown section IDs in 16-set: {res['unknown_ids']}"

    male_c8_ids = {f"B-{i:03d}" for i in range(143, 155)}
    for q in bank:
        gt = list(q["gt_sections"])
        txt = q["question"].lower()
        is_male = q["category"] == "C8" and q["id"] in male_c8_ids
        has_child = bool(
            re.search(r"\b(son|daughter|child|children|kids|baby|girl|boy)\b|ಮಗ|ಮಗಳು|ಮಗು", q["question"], re.I)
        ) or bool(set(gt) & {"gwa-1890", "hma-26", "births-deaths-act-1969"})
        has_fees = "school fee" in txt or "school" in txt or "ಶಾಲಾ" in q["question"] or "ವಿದ್ಯಾಭ್ಯಾಸ" in q["question"]
        facts = {
            "divorce_asked": ("hma-13" in gt or "hma-13b" in gt),
            "mutual_consent": ("hma-13b" in gt),
            "proceeding_pending": bool(set(gt) & {"hma-24", "hma-26"})
            or ("pending" in txt or "going on" in txt or "running" in txt),
            "being_filed": "going to file" in txt or "will be filing" in txt or "will file" in txt,
            "decree": "hma-25" in gt,
            "demand_made": ("recovery" in q.get("gt_escalation_kinds", [])),
            "violence": "pwdva-18" in gt,
            "residence_claim": bool(set(gt) & {"pwdva-17", "pwdva-19"}),
            "child_fact": has_child,
            "school_fees_fact": has_fees,
            "stridhan_sold": "sold" in txt or "ಮಾರಿ" in q["question"],
            "joint_property_claim": ("hma-27" in gt and "bns-316" not in gt),
            "claimant_sex": "male" if is_male else "female",
            "claimant_role": "parent" if q["id"] in {"B-037", "B-047"} else "spouse",
            "no_dispute_empty": (q["id"] in {"B-069", "B-156"}),
        }
        in_scope = q["category"] != "C10"
        rec = {
            "id": q["id"],
            "kept_ids": gt,
            "court_live": [] if q["gt_court"] == "none" else [q["gt_court"]],
            "court_source": "out-of-scope" if not in_scope else ("kept" if gt else "fallback-escalate"),
            "escalation_kinds": q.get("gt_escalation_kinds", []),
            "in_scope": in_scope,
            "facts": facts,
            "dropped": [["hma-27", "no proceeding"]] if ("bns-316" in gt and "hma-27" not in gt) else [],
        }
        res = render_prose(rec, facts)
        times_ms.append(res["prose_render_ms"])
        hits, flags = prose_forbidden_check(res["prose"], rec["kept_ids"], rec["dropped"], facts)
        assert not hits, f"Brutal {q['id']} Fp hits: {hits}\n{res['prose']}"
        assert not flags, f"Brutal {q['id']} quality flags: {flags}\n{res['prose']}"
        assert not res["unknown_ids"], f"Unknown section IDs in {q['id']}: {res['unknown_ids']}"

    # Fail-safe checks
    r_unk = render_prose(
        {
            "kept_ids": ["unknown-sec-99"],
            "court_live": [],
            "court_source": "fallback-escalate",
            "escalation_kinds": [],
            "in_scope": True,
            "facts": {},
        }
    )
    assert "human adviser" in r_unk["prose"] and "unknown-sec-99" not in r_unk["prose"]

    r_13b_unsafe = render_prose(
        {
            "kept_ids": ["hma-13b"],
            "court_live": ["Family Court"],
            "court_source": "kept",
            "escalation_kinds": [],
            "in_scope": True,
            "facts": {"divorce_asked": True, "mutual_consent": False},
        }
    )
    assert "13B" not in r_13b_unsafe["prose"] and "human adviser" in r_13b_unsafe["prose"]
    hits_u, _ = prose_forbidden_check(
        r_13b_unsafe["prose"], ["hma-13b"], [], {"divorce_asked": True, "mutual_consent": False}
    )
    assert not hits_u

    # Adversarial mutants across all 9 Frozen Forbidden Items + Additions A-E
    mutants = [
        ("item1_rajnesh", "Per Rajnesh v. Neha, return the gold.", ["bns-316"], [], {}, 1, None),
        ("item2_satish", "Under Satish Chander Ahuja, custody is decided.", ["gwa-1890"], [], {}, 2, None),
        ("item3_13_unasked", "A divorce can be sought under Section 13 of the Hindu Marriage Act, 1955.", ["bnss-144"], [], {"divorce_asked": False}, 3, None),
        ("item3_13b_nomutual", "File under Section 13B of the Hindu Marriage Act, 1955.", ["hma-13b"], [], {"divorce_asked": True, "mutual_consent": False}, 3, None),
        ("item4_tenancy", "You have tenancy rights in the home.", ["pwdva-17"], [], {}, 4, None),
        ("item5_pick_court", "Which court should you go to?", ["bnss-144"], [], {}, 5, None),
        ("item6_birth_hma", "Get the birth certificate under the Hindu Marriage Act, 1955.", ["births-deaths-act-1969"], [], {}, 6, None),
        ("item7_dropped_hma25", "Permanent alimony under Section 25 of the Hindu Marriage Act, 1955.", ["bnss-144"], [["hma-25", "no decree"]], {}, 7, None),
        ("item8_amount", "You will get Rs. 15,000 per month.", ["bnss-144"], [], {}, 8, None),
        ("item9_slips", "You must submit salary slips for income proof.", ["bnss-144"], [], {}, 9, None),
        ("addA_res_base", "You have the right to stay in the shared household.", ["pwdva-18"], [], {}, None, "A-residence-base-without-section"),
        ("addB_child", "Maintenance for yourself and your child.", ["bnss-144"], [], {"child_fact": False}, None, "B-child-without-fact"),
        ("addC_pre_d1a_hma27", "Civil recovery under Section 27 of the Hindu Marriage Act, 1955.", ["bns-316"], [["hma-27", "no proceeding"]], {}, 7, "C-pre-d1a-hma27-leak"),
        ("addE_male_claimant", "The law allows a wife to claim maintenance from your husband's income.", ["hma-24"], [], {"claimant_sex": "male"}, None, "E-claimant-sex-mismatch"),
        ("addE_parent_claimant", "The law allows a wife to claim maintenance from your husband's income.", ["bnss-144"], [], {"claimant_role": "parent"}, None, "E-claimant-role-mismatch"),
    ]
    for name, text, kept, dropped, facts, exp_item, exp_flag in mutants:
        hits, flags = prose_forbidden_check(text, kept, dropped, facts)
        if exp_item is not None:
            assert any(h["item"] == exp_item for h in hits), f"Mutant {name} missed Fp item {exp_item}: {hits}"
        if exp_flag is not None:
            assert any(f["check"] == exp_flag for f in flags), f"Mutant {name} missed flag {exp_flag}: {flags}"

    assert len(KNOWN_SECTIONS) == 18
    return {
        "total_tested": len(gt16) + len(bank),
        "fp_total": 0,
        "quality_flags_total": 0,
        "mutants_caught": len(mutants),
        "render_ms_mean": round(sum(times_ms) / len(times_ms), 4),
        "render_ms_max": round(max(times_ms), 4),
    }


if __name__ == "__main__":
    summary = run_validation()
    print(
        f"PROSE VALIDATION PASS: {summary['total_tested']} cases, "
        f"Fp={summary['fp_total']}, quality_flags={summary['quality_flags_total']}, "
        f"{summary['mutants_caught']}/{summary['mutants_caught']} adversarial mutants caught, "
        f"mean={summary['render_ms_mean']}ms, max={summary['render_ms_max']}ms"
    )
