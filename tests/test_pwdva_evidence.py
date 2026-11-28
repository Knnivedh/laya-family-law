import unittest

from src.laya_v7_evidence import extract_grounded_v7
from src.laya_v7_extractor import extract_v7
from src.laya_v7_graph import evaluate_stage2_v7
from src.laya_runtime import assess_turn


WIFE_MAINTENANCE = (
    "I have been married for two years. My husband lends me money when I ask. "
    "I want a maintenance order because my salary has reduced."
)
UNMARRIED_CHILD_EXPENSES = (
    "My former partner will not pay our child expenses. "
    "We never lived together or married. Can I ask for maintenance?"
)
BASIS_BLOCKER = "pwdva_monetary_basis_blocked"


class PwdvaEvidenceTests(unittest.TestCase):
    def assess(self, text):
        evidence = extract_grounded_v7(text, strict_pwdva=True)
        return evidence, evaluate_stage2_v7(evidence["issues"], evidence["facts"])

    def test_explicit_denial_does_not_trigger_protection_or_urgency(self):
        for denial in (
            "There has been no domestic violence.",
            "My husband has never committed domestic violence.",
            "There is no abuse of any kind.",
        ):
            with self.subTest(denial=denial):
                evidence, outcome = self.assess(f"{WIFE_MAINTENANCE} {denial}")
                self.assertEqual(evidence["issues"]["violence"].intent, "denied")
                self.assertTrue(evidence["facts"][BASIS_BLOCKER].value)
                self.assertIn("bnss-144", outcome["kept_ids"])
                self.assertNotIn("pwdva-18", outcome["kept_ids"])
                self.assertNotIn("pwdva-20", outcome["kept_ids"])
                self.assertNotIn("safety", outcome["escalation_kinds"])

    def test_specific_danger_survives_separate_broad_denial(self):
        text = (
            f"{WIFE_MAINTENANCE} There has been no domestic violence. "
            "My husband threatened to kill me today."
        )
        evidence, outcome = self.assess(text)
        self.assertTrue(evidence["facts"]["violence"].value)
        self.assertFalse(evidence["facts"][BASIS_BLOCKER].value)
        self.assertIn("pwdva-18", outcome["kept_ids"])
        self.assertIn("safety", outcome["escalation_kinds"])

    def test_explicitly_denied_threat_does_not_trigger_urgency(self):
        evidence, outcome = self.assess(
            f"{WIFE_MAINTENANCE} My husband has never threatened to kill me."
        )
        self.assertFalse(evidence["facts"]["urgent_safety_risk"].value)
        self.assertNotIn("safety", outcome["escalation_kinds"])

    def test_never_shared_or_married_keeps_bnss_independent(self):
        evidence, outcome = self.assess(UNMARRIED_CHILD_EXPENSES)
        self.assertTrue(evidence["facts"][BASIS_BLOCKER].value)
        self.assertIn("bnss-144", outcome["kept_ids"])
        self.assertNotIn("pwdva-20", outcome["kept_ids"])

    def test_no_shared_household_followup_updates_a_maintenance_conversation(self):
        opening = "My former partner will not pay our child expenses. Can I ask for maintenance?"
        _, state = assess_turn(None, opening, mode="evidence", device="cpu", strict_pwdva=True)
        result, _ = assess_turn(
            state, "We never lived together or married.", mode="evidence", device="cpu",
            strict_pwdva=True,
        )
        self.assertIn("bnss-144", result["kept_ids"])
        self.assertNotIn("pwdva-20", result["kept_ids"])

    def test_past_shared_household_keeps_evidence_for_monetary_relief(self):
        text = (
            "My former husband has stopped paying the household expenses and I need maintenance. "
            "We do not live together now. We lived together before the divorce. "
            "He took my wages and prevented me from accessing our bank account when we lived together."
        )
        evidence, outcome = self.assess(text)
        self.assertFalse(evidence["facts"][BASIS_BLOCKER].value)
        self.assertIn("pwdva-20", outcome["kept_ids"])

    def test_independent_economic_control_survives_broad_denial(self):
        text = (
            "My husband stopped paying and I need maintenance. There has been no domestic violence. "
            "He takes my wages and prevents me from accessing our bank account."
        )
        evidence, outcome = self.assess(text)
        self.assertFalse(evidence["facts"][BASIS_BLOCKER].value)
        self.assertIn("pwdva-20", outcome["kept_ids"])
        self.assertNotIn("safety", outcome["escalation_kinds"])

    def test_denial_of_physical_violence_is_not_a_monetary_relief_blocker(self):
        evidence, outcome = self.assess(f"{WIFE_MAINTENANCE} There was no physical violence.")
        self.assertNotIn(BASIS_BLOCKER, evidence["facts"])
        self.assertNotIn("safety", outcome["escalation_kinds"])

    def test_current_marital_status_alone_cannot_cancel_past_relationship(self):
        evidence, _ = self.assess(
            "My former partner will not pay our child expenses. "
            "We never lived together. We are not married. Can I ask for maintenance?"
        )
        self.assertNotIn(BASIS_BLOCKER, evidence["facts"])

    def test_right_to_reside_cues_do_not_trigger_never_shared_block(self):
        text = (
            f"{WIFE_MAINTENANCE} My husband and I never lived together. "
            "He refused me entry to the matrimonial home and I want a residence order."
        )
        evidence, outcome = self.assess(text)
        self.assertFalse(evidence["facts"][BASIS_BLOCKER].value)
        self.assertIn("pwdva-19", outcome["kept_ids"])

    def test_unknown_or_absent_harm_has_no_blocker(self):
        evidence = extract_grounded_v7(WIFE_MAINTENANCE, strict_pwdva=True)
        self.assertNotIn(BASIS_BLOCKER, evidence["facts"])

    def test_live_evidence_extractor_opt_in_preserves_legacy_default(self):
        def baseline(strict_pwdva=False):
            return extract_v7(UNMARRIED_CHILD_EXPENSES, mode="evidence", device="cpu",
                              strict_pwdva=strict_pwdva)

        self.assertNotIn(BASIS_BLOCKER, baseline()["facts"])
        self.assertTrue(baseline(True)["facts"][BASIS_BLOCKER].value)

    def test_requested_order_is_not_an_issued_order(self):
        for text in (
            WIFE_MAINTENANCE,
            "My husband is not paying maintenance and I want to apply for a maintenance order.",
        ):
            with self.subTest(text=text):
                evidence, outcome = self.assess(text)
                self.assertFalse(evidence["facts"]["existing_order_enforcement"].value)
                self.assertIn("bnss-144", outcome["kept_ids"])
                self.assertIn("subsistence_maintenance_bnss144",
                              outcome["dispositions"]["bnss-144"]["reason_codes"])

    def test_existing_order_and_distinct_new_request_are_preserved(self):
        issued = "The court ordered my husband to pay me maintenance, but he has not paid it."
        for text in (issued, f"{issued} I am also asking for a new maintenance order."):
            with self.subTest(text=text):
                evidence, _ = self.assess(text)
                self.assertTrue(evidence["facts"]["existing_order_enforcement"].value)

    def test_future_interim_order_does_not_create_a_pending_proceeding(self):
        evidence, _ = self.assess(
            "My husband and I are married. I want an interim maintenance order only till the divorce ends."
        )
        self.assertFalse(evidence["facts"]["existing_order_enforcement"].value)
        self.assertFalse(evidence["facts"]["proceeding_pending_hma"].value)


if __name__ == "__main__":
    unittest.main()
