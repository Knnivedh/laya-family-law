import unittest

from src.laya_family import assess, guided_assessment, parse_confirmations


def resolve(**facts):
    return assess("A layperson's family support question", lambda _: {}, facts)


class FamilyLawTests(unittest.TestCase):
    def ids(self, response):
        return {route["id"] for route in response["routes"]}

    def test_bnss_role_does_not_depend_on_speaker(self):
        for beneficiary in ("wife", "minor_child", "parent"):
            with self.subTest(beneficiary=beneficiary):
                result = resolve(maintenance=True, new_support=True, **{beneficiary: True})
                self.assertEqual(self.ids(result), {"bnss-144"})
                self.assertTrue(result["routes"][0]["requirements"])
                self.assertIn("Family Court", result["routes"][0]["forum"])

    def test_husband_self_claim_does_not_get_bnss_144(self):
        result = resolve(maintenance=True, new_support=True, husband=True)
        self.assertEqual(self.ids(result), set())

    def test_hma_requires_its_own_proceeding_stage(self):
        for purpose, stage, code in (
            ("interim", "hma_pending", "hma-24"),
            ("permanent", "hma_decree", "hma-25"),
        ):
            with self.subTest(code=code):
                facts = {"maintenance": True, "wife": True, purpose: True}
                missing = resolve(**facts)
                self.assertEqual(self.ids(missing), set())
                self.assertIn(stage, [q["field"] for q in missing["questions"]])
                present = resolve(**facts, **{stage: True})
                self.assertEqual(self.ids(present), {code})

    def test_order_action_uses_issuing_law(self):
        for action, route in (("recover", "bnss-144-3"), ("vary", "bnss-146")):
            with self.subTest(action=action):
                unknown = resolve(maintenance=True, **{action: True})
                self.assertEqual(self.ids(unknown), set())
                self.assertEqual(unknown["questions"][0]["field"], "bnss_order")
                known = resolve(maintenance=True, bnss_order=True, **{action: True})
                self.assertEqual(self.ids(known), {route})
                other = resolve(maintenance=True, bnss_order=False, **{action: True})
                self.assertEqual(self.ids(other), set())

    def test_confirmation_overrides_prediction_and_sources_do_not_echo_text(self):
        result = assess("Unique synthetic wording", lambda _: {"maintenance": 0.99}, {"maintenance": False})
        self.assertEqual(result["status"], "outside_maintenance")
        self.assertEqual(result["facts"]["maintenance"]["source"], "user_confirmation")
        self.assertNotIn("Unique synthetic wording", repr(result))

    def test_uncertainty_does_not_create_statutory_routes(self):
        result = assess("Something happened", lambda _: {"maintenance": 0.50})
        self.assertEqual(self.ids(result), set())
        self.assertEqual(result["questions"][0]["field"], "maintenance")

    def test_unsupported_script_cannot_issue_english_model_answer(self):
        def unexpected(_):
            self.fail("Unsupported script invoked the English model")
        result = assess("ನನಗೆ ಜೀವನಾಂಶ ಬೇಕು", unexpected)
        self.assertEqual(result["status"], "unsupported_language")
        self.assertEqual(self.ids(result), set())

    def test_scoped_order_intent_can_establish_maintenance_without_an_extra_question(self):
        result = assess("What about those unpaid instalments?", lambda _: {"maintenance": 0.10, "recover": 0.99})
        self.assertEqual(result["questions"][0]["field"], "bnss_order")
        self.assertEqual(self.ids(result), set())

    def test_procedure_requires_confirmation_even_for_high_model_score(self):
        result = assess(
            "If I file someday can I get interim money?",
            lambda _: {"maintenance": 0.90, "interim": 0.95, "hma_pending": 0.98},
        )
        self.assertEqual(self.ids(result), set())
        self.assertEqual(result["questions"][0]["field"], "hma_pending")

    def test_guided_path_reuses_one_model_call_and_resolves_a_clarification(self):
        questions = []
        reads = iter(["bad", "yes"])

        def extract(text):
            questions.append(text)
            return {"maintenance": 0.90, "new_support": 0.88, "wife": 0.60}

        messages = []
        result = guided_assessment("I need financial help", extract, {}, lambda _: next(reads), messages.append)
        self.assertEqual(len(questions), 1)
        self.assertEqual(self.ids(result), {"bnss-144"})
        self.assertEqual(result["facts"]["wife"]["source"], "user_confirmation")
        self.assertEqual(messages, ["Answer yes or no, or press Enter if you are unsure."])

    def test_invalid_model_scores_never_emit_routes(self):
        for score in (float("nan"), 1.1, True):
            with self.subTest(score=score):
                with self.assertRaises(ValueError):
                    assess("Please help", lambda _: {"maintenance": score})

    def test_rejects_invalid_confirmation_fields_and_conflicts(self):
        for values in (["dataset_id=yes"], ["maintenance=x"], ["maintenance=yes", "maintenance=no"]):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    parse_confirmations(values)


if __name__ == "__main__":
    unittest.main()
