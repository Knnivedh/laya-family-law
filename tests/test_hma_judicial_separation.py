from __future__ import annotations

import unittest

from src.laya_prose_v2 import prose_forbidden_check
from src.laya_runtime import assess_turn


class JudicialSeparationTests(unittest.TestCase):
    def assess(self, text, *, state=None, act="hma", confirmations=None):
        result, state = assess_turn(
            state, text, mode="evidence", device="cpu",
            judicial_separation_act=act, confirmations=confirmations,
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["prose_fp_hits"], [])
        return result, state

    def test_hma_potential_route_and_grounded_prose(self):
        result, _ = self.assess("I want a judicial separation from my spouse. I do not want a divorce.")
        self.assertEqual(result["kept_statutory_ids"], ["hma-10"])
        self.assertIn("Section 10 of the Hindu Marriage Act", result["prose"])
        self.assertIn("if the court grants", result["prose"].lower())
        self.assertIn("grounds", result["prose"])
        self.assertIn("local jurisdiction", result["court_live"][0])
        self.assertNotIn("You would approach", result["prose"])

    def test_sma_has_separate_source_and_disposition(self):
        result, _ = self.assess("Can I apply for judicial separation?", act="sma")
        self.assertEqual(result["kept_statutory_ids"], ["sma-23"])
        self.assertIn("Section 23 of the Special Marriage Act", result["prose"])
        self.assertNotIn("Hindu Marriage Act", result["prose"])
        self.assertIn("grounds", result["prose"])

    def test_default_runtime_keeps_legacy_coverage(self):
        result, _ = assess_turn(None, "I want judicial separation.", mode="evidence", device="cpu")
        self.assertNotIn("hma-10", result["kept_statutory_ids"])

    def test_lay_first_person_court_order_without_ending_marriage(self):
        for question in (
            "I want to live apart under a court order without ending my marriage.",
            "I want a court order to live apart without ending my marriage.",
        ):
            with self.subTest(question=question):
                result, _ = self.assess(question)
                self.assertIn("hma-10", result["kept_statutory_ids"])

    def test_adjacent_context_does_not_award_new_route(self):
        for question in (
            "My sister wants judicial separation.",
            'My spouse says "I want judicial separation".',
            "My spouse thinks I want judicial separation.",
            "Suppose I ask for judicial separation someday.",
            "I already have a decree for judicial separation.",
            "I do not want judicial separation.",
            "I do not want a court order to live apart without ending my marriage.",
            "We are living apart by agreement.",
        ):
            with self.subTest(question=question):
                result, _ = self.assess(question)
                self.assertNotIn("hma-10", result["kept_statutory_ids"])

    def test_silence_preserves_intent_and_explicit_retraction_retires_route(self):
        _, state = self.assess("I want judicial separation.")
        result, state = self.assess("What documents should I bring?", state=state)
        self.assertIn("hma-10", result["kept_statutory_ids"])

        result, state = self.assess("I no longer want judicial separation.", state=state)
        self.assertNotIn("hma-10", result["kept_statutory_ids"])

        result, _ = self.assess("I want a divorce instead.", state=state)
        self.assertIn("hma-13", result["kept_statutory_ids"])
        self.assertNotIn("hma-10", result["kept_statutory_ids"])

    def test_conflicting_intents_abstain_until_user_clarifies(self):
        result, state = self.assess("I want judicial separation. I want a divorce too.")
        self.assertFalse({"hma-10", "hma-13"} & set(result["kept_statutory_ids"]))
        self.assertIn("judicial_separation_requested",
                      {q["fact_key"] for q in result["pending_clarifications"]})
        result, state = self.assess(
            "Yes, remain married.", state=state,
            confirmations={"judicial_separation_requested": True},
        )
        self.assertEqual(result["kept_statutory_ids"], ["hma-10"])
        result, _ = self.assess("I want a divorce instead.", state=state)
        self.assertEqual(result["kept_statutory_ids"], ["hma-13"])

    def test_confirmation_cannot_add_route_without_a_clarification(self):
        result, _ = self.assess("Yes.", confirmations={"judicial_separation_requested": True})
        self.assertNotIn("hma-10", result["kept_statutory_ids"])

    def test_lay_retraction_retires_existing_route(self):
        _, state = self.assess("I want a court order to live apart without ending my marriage.")
        result, _ = self.assess(
            "I do not want a court order to live apart without ending my marriage.",
            state=state,
        )
        self.assertNotIn("hma-10", result["kept_statutory_ids"])

    def test_uncertain_personal_request_needs_clarification(self):
        result, _ = self.assess("I am not sure if I want judicial separation.")
        self.assertEqual(result["kept_statutory_ids"], [])
        self.assertIn("judicial_separation_requested",
                      {q["fact_key"] for q in result["pending_clarifications"]})

    def test_prose_checker_rejects_unauthorized_separation_citations(self):
        for excerpt in ("Section 10 of the Hindu Marriage Act, 1955",
                        "Section 23 of the Special Marriage Act, 1954"):
            hits, _ = prose_forbidden_check(excerpt, [], [], {})
            self.assertTrue(any(hit["item"] == 7 for hit in hits))


if __name__ == "__main__":
    unittest.main()
