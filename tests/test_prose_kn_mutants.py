"""Kannada adversarial mutant suite for src/laya_prose_kn.py (Lane 09, V71-P6-1).

Covers:
  1. All 20 Kannada section templates + all 9 escalation kinds render clean
     (0 Fp hits, 0 quality flags, 0 question marks, readability avg <= 22).
  2. >= 15 Kannada adversarial mutants for the 9 Frozen Forbidden Items
     (Kannada parity traps) + Additions A-E — 23 mutants in this file.
  3. DRAFT marking: every template and every render result is marked
     DRAFT — NEEDS P2.1 native Kannada speaker verification.

Pure Python, CPU-only, no test-bank / sealed access of any kind.
Run:  python -m unittest tests.test_prose_kn_mutants -v
   or python tests/test_prose_kn_mutants.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from laya_prose_kn import (  # noqa: E402
    DRAFT_STATUS,
    KNOWN_ESCALATION_KINDS_KN,
    KNOWN_SECTIONS_KN,
    TEMPLATE_COVERAGE_KN,
    document_checklist_kn,
    prose_forbidden_check_kn,
    readability_check_kn,
    render_prose_kn,
    render_prose_localized,
    run_self_test,
)

# (name, text, kept, dropped, facts, expected_fp_item, expected_flag)
# expected_fp_item None => no Fp hit expected for that mutant's target item.
MUTANTS = [
    ("kn_item1_rajnesh_kn", "ರಾಜನೇಶ್ ವಿರುದ್ಧ ನೇಹಾ ಪ್ರಕರಣದ ಪ್ರಕಾರ ಬಂಗಾರ ಹಿಂದಿರುಗಿಸಿ.", ["bns-316"], [], {}, 1, None),
    ("kn_item1_rajnesh_latin", "Per Rajnesh v. Neha, return the gold.", ["bns-316"], [], {}, 1, None),
    ("kn_item2_satish_kn", "ಸತೀಶ್ ಚಂದರ್ ಅಹುಜಾ ಪ್ರಕರಣದ ಪ್ರಕಾರ ಪಾಲನೆ ನಿರ್ಧರಿಸಲಾಗುತ್ತದೆ.", ["gwa-1890"], [], {}, 2, None),
    ("kn_item3_13_unasked", "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಸೆಕ್ಷನ್ 13 ರ ಅಡಿಯಲ್ಲಿ ವಿಚ್ಛೇದನ ಕೇಳಬಹುದು.", ["bnss-144"], [], {"divorce_asked": False}, 3, None),
    ("kn_item3_13b_nomutual", "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಸೆಕ್ಷನ್ 13ಬಿ ರ ಅಡಿಯಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ.", ["hma-13b"], [], {"divorce_asked": True, "mutual_consent": False}, 3, None),
    ("kn_item4_tenancy_kn", "ಮನೆಯಲ್ಲಿ ನಿಮಗೆ ಬಾಡಿಗೆ ಹಕ್ಕು ಇದೆ.", ["pwdva-17"], [], {}, 4, None),
    ("kn_item4_tenancy_latin", "ನಿಮಗೆ ಟೆನೆನ್ಸಿ ಹಕ್ಕು ಇದೆ.", ["pwdva-17"], [], {}, 4, None),
    ("kn_item5_question_mark", "ಯಾವ ನ್ಯಾಯಾಲಯಕ್ಕೆ ಹೋಗಬೇಕು?", ["bnss-144"], [], {}, 5, None),
    ("kn_item5_pick_court", "ನ್ಯಾಯಾಲಯವನ್ನು ಆಯ್ಕೆ ಮಾಡಿ.", ["bnss-144"], [], {}, 5, None),
    ("kn_item6_birth_hma", "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಅಡಿಯಲ್ಲಿ ಜನನ ಪ್ರಮಾಣಪತ್ರ ಪಡೆಯಿರಿ.", ["births-deaths-act-1969"], [], {}, 6, None),
    ("kn_item6_birth_no1969", "ಜನನ ಪ್ರಮಾಣಪತ್ರವನ್ನು ರಿಜಿಸ್ಟ್ರಾರ್ ಅವರಿಂದ ಪಡೆಯಿರಿ.", ["births-deaths-act-1969"], [], {}, 6, None),
    ("kn_item7_dropped_hma25", "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಸೆಕ್ಷನ್ 25 ರ ಅಡಿಯಲ್ಲಿ ಶಾಶ್ವತ ಜೀವನಾಂಶ.", ["bnss-144"], [["hma-25", "no decree"]], {}, 7, None),
    ("kn_item7_cited_not_kept", "ಭಾರತೀಯ ನ್ಯಾಯ ಸಂಹಿತೆ, 2023 ರ ಸೆಕ್ಷನ್ 316 ರ ಅಡಿಯಲ್ಲಿ ದೂರು ನೀಡಿ.", ["hma-27"], [], {}, 7, None),
    ("kn_item8_rupee_symbol", "ನಿಮಗೆ ₹15,000 ಸಿಗುತ್ತದೆ.", ["bnss-144"], [], {}, 8, None),
    ("kn_item8_monthly_rupees", "ನಿಮಗೆ ತಿಂಗಳಿಗೆ 15000 ರೂಪಾಯಿ ಸಿಗುತ್ತದೆ.", ["bnss-144"], [], {}, 8, None),
    ("kn_item8_lakh_monthly", "ತಿಂಗಳಿಗೆ 2 ಲಕ್ಷ ರೂಪಾಯಿ ಜೀವನಾಂಶ ಸಿಗುತ್ತದೆ.", ["bnss-144"], [], {}, 8, None),
    ("kn_item8_rupee_abbr", "ನಿಮಗೆ ರೂ. 20000 ಸಿಗುತ್ತದೆ.", ["bnss-144"], [], {}, 8, None),
    ("kn_item9_payslip_kn", "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಸಂಬಳದ ಚೀಟಿ ಕೊಡಿ.", ["bnss-144"], [], {}, 9, None),
    ("kn_item9_payslip_latin", "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪೇ ಸ್ಲಿಪ್ ಕೊಡಿ.", ["bnss-144"], [], {}, 9, None),
    ("kn_item9_income_proof_demand", "ಆದಾಯದ ಪುರಾವೆ ತರಬೇಕು.", ["bnss-144"], [], {}, 9, None),
    ("kn_addA_res_base", "ಹಂಚಿದ ಮನೆಯಲ್ಲಿ ವಾಸಿಸುವ ಹಕ್ಕು ನಿಮಗಿದೆ.", ["pwdva-18"], [], {}, None, "A-residence-base-without-section"),
    ("kn_addB_child", "ನಿಮಗಾಗಿ ಮತ್ತು ನಿಮ್ಮ ಮಗುವಿಗಾಗಿ ಜೀವನಾಂಶ.", ["bnss-144"], [], {"child_fact": False}, None, "B-child-without-fact"),
    ("kn_addB_fees", "ಮತ್ತು ನಿಮ್ಮ ಮಗುವಿನ ಶಾಲಾ ಶುಲ್ಕ.", ["bnss-144"], [], {"school_fees_fact": False}, None, "B-school-fees-without-fact"),
    ("kn_addC_hma27_leak", "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಸೆಕ್ಷನ್ 27 ರ ಅಡಿಯಲ್ಲಿ ಸಿವಿಲ್ ವಸೂಲಿ.", ["bns-316"], [["hma-27", "no proceeding"]], {}, 7, "C-pre-d1a-hma27-leak"),
    ("kn_addE_male", "ಪತ್ನಿಯಾಗಿ ನಿಮ್ಮ ಗಂಡನಿಂದ ಜೀವನಾಂಶ ಕೇಳಬಹುದು.", ["hma-24"], [], {"claimant_sex": "male"}, None, "E-claimant-sex-mismatch"),
]

BASE_FACTS = {
    "divorce_asked": True,
    "mutual_consent": True,
    "proceeding_pending_hma": True,
    "proceeding_pending": True,
    "being_filed": False,
    "decree": True,
    "demand_made": True,
    "violence": True,
    "residence_claim": True,
    "child_fact": True,
    "school_fees_fact": True,
    "stridhan_sold": True,
    "stridhan_sold_or_mortgaged": True,
    "joint_property_claim": True,
    "claimant_sex": "female",
    "claimant_role": "spouse",
    "no_dispute_empty": False,
}


class TestKannadaCoverage(unittest.TestCase):
    def test_20_sections_9_kinds(self):
        self.assertEqual(len(KNOWN_SECTIONS_KN), 20)
        self.assertEqual(len(KNOWN_ESCALATION_KINDS_KN), 9)
        self.assertEqual(len(TEMPLATE_COVERAGE_KN), 20)
        self.assertTrue(all("DRAFT" in v and "P2.1" in v for v in TEMPLATE_COVERAGE_KN.values()))
        self.assertIn("DRAFT", DRAFT_STATUS)
        self.assertIn("P2.1", DRAFT_STATUS)

    def test_each_section_renders_clean(self):
        all_kinds = sorted(KNOWN_ESCALATION_KINDS_KN)
        for sid in sorted(KNOWN_SECTIONS_KN):
            with self.subTest(section=sid):
                rec = {
                    "kept_ids": [sid],
                    "court_live": ["Family Court"],
                    "court_source": "kept",
                    "escalation_kinds": all_kinds,
                    "in_scope": True,
                    "facts": dict(BASE_FACTS),
                    "lang": "kn",
                }
                res = render_prose_kn(rec, dict(BASE_FACTS), include_forum_note=True, include_checklist=True)
                self.assertEqual(res["status"], "ok")
                self.assertTrue(res["draft"])
                self.assertFalse(res["p2_1_verified"])
                self.assertNotIn("?", res["prose"])
                hits, flags = prose_forbidden_check_kn(res["prose"], [sid], [], BASE_FACTS)
                self.assertEqual(hits, [], f"{sid}: {hits}")
                self.assertEqual(flags, [], f"{sid}: {flags}")
                read = readability_check_kn(res["prose"])
                self.assertTrue(read["passes"], f"{sid}: {read}")

    def test_dispatcher_routes_kn_and_en(self):
        rec_kn = {"kept_ids": ["bnss-144"], "in_scope": True,
                  "facts": dict(BASE_FACTS), "lang": "kn"}
        res = render_prose_localized(rec_kn, dict(BASE_FACTS))
        self.assertEqual(res.get("lang"), "kn")
        self.assertEqual(res["status"], "ok")

    def test_checklist_never_names_payslips(self):
        text = document_checklist_kn(
            ["bnss-144", "bns-316", "pwdva-18"],
            {"child_fact": True, "school_fees_fact": True},
        )
        self.assertIn("ಮದುವೆ ಪುರಾವೆ", text)
        self.assertNotIn("ಸಂಬಳದ ಚೀಟಿ", text)
        self.assertNotIn("ಪೇ ಸ್ಲಿಪ್", text)
        hits, flags = prose_forbidden_check_kn(
            text, ["bnss-144", "bns-316", "pwdva-18"], [], {"child_fact": True, "school_fees_fact": True}
        )
        self.assertEqual(hits, [])
        self.assertEqual(flags, [])


class TestKannadaMutants(unittest.TestCase):
    def test_mutant_count(self):
        self.assertGreaterEqual(len(MUTANTS), 15, "plan requires >= 15 Kannada mutants")

    def test_each_mutant_caught(self):
        for name, text, kept, dropped, facts, exp_item, exp_flag in MUTANTS:
            with self.subTest(mutant=name):
                hits, flags = prose_forbidden_check_kn(text, kept, dropped, facts)
                if exp_item is not None:
                    self.assertTrue(
                        any(h["item"] == exp_item for h in hits),
                        f"Mutant {name} missed Fp item {exp_item}: {hits}",
                    )
                if exp_flag is not None:
                    self.assertTrue(
                        any(f["check"] == exp_flag for f in flags),
                        f"Mutant {name} missed flag {exp_flag}: {flags}",
                    )


class TestKannadaSelfTest(unittest.TestCase):
    def test_module_self_test(self):
        summary = run_self_test()
        self.assertEqual(summary["fp_total"], 0)
        self.assertEqual(summary["quality_flags_total"], 0)
        self.assertEqual(summary["question_marks_total"], 0)
        self.assertEqual(summary["sections_rendered"], 20)


if __name__ == "__main__":
    unittest.main(verbosity=2)
