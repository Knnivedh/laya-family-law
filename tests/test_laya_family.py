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

    def test_explicit_procedure_uses_an_exact_user_text_span(self):
        cases = (
            ("I am the wife. Our HMA petition is still ongoing. Can I get temporary funds?",
             "interim", "hma_pending", "hma-24"),
            ("The judge granted a decree of nullity under the Hindu Marriage Act in my case. Can I claim permanent alimony?",
             "permanent", "hma_decree", "hma-25"),
            ("Our court maintenance order was passed under s. 144 of the BNSS. Can I recover arrears?",
             "recover", "bnss_order", "bnss-144-3"),
        )
        for question, purpose, field, expected in cases:
            with self.subTest(field=field):
                answer = assess(question, lambda _: {purpose: 0.95})
                self.assertEqual(self.ids(answer), {expected})
                fact = answer["facts"][field]
                self.assertEqual(fact["source"], "user_text")
                span = fact["span"]
                self.assertEqual(question[span["start"]:span["end"]], span["text"])

    def test_foreign_procedural_references_do_not_license_a_route(self):
        cases = (
            ("If my HMA petition is pending someday, what about temporary funds?", "interim"),
            ("My friend's divorce petition under HMA is pending, while mine has ended.", "interim"),
            ('The internet says "Our HMA petition is pending". I have not filed.', "interim"),
            ("A draft decree under HMA was prepared but has not been passed. Can I get permanent alimony?", "permanent"),
            ("It is unclear whether my existing maintenance order was made under BNSS section 144.", "recover"),
            ("My CrPC 125 order mentions updated BNSS sections. BNSS 144 is an option for someone else.", "recover"),
            ("My Special Marriage Act petition is pending and I read also that HMA applies to some people. Can I ask for interim costs?", "interim"),
            ("I want the court to order maintenance under BNSS section 144. How could I later recover arrears?", "recover"),
            ("I want a divorce decree granted under the Hindu Marriage Act before I can get permanent alimony.", "permanent"),
        )
        for question, purpose in cases:
            with self.subTest(question=question):
                answer = assess(question, lambda _: {purpose: 0.99})
                self.assertEqual(self.ids(answer), set())

    def test_one_ancillary_request_does_not_create_a_second_application(self):
        answer = assess(
            "Our HMA marriage case is pending. As his wife I need living money and case costs until the case ends.",
            lambda _: {"wife": "yes", "interim": "yes", "new_support": "yes"},
        )
        self.assertEqual(self.ids(answer), {"hma-24"})

    def test_independently_requested_support_is_preserved(self):
        answer = assess(
            "My Hindu Marriage Act divorce petition is still pending. I need my legal fees paid during the case. "
            "Separately I want a new support order for my twelve-year-old.",
            lambda _: {"minor_child": "yes", "interim": "yes", "new_support": "yes"},
        )
        self.assertEqual(self.ids(answer), {"hma-24", "bnss-144"})

    def test_confirmed_separate_claim_overrides_ambiguous_overlap(self):
        answer = assess(
            "I am his wife. My HMA divorce petition is pending. I have questions about support.",
            lambda _: {"wife": "yes", "interim": "yes", "new_support": "yes"},
            {"new_support": True},
        )
        self.assertEqual(self.ids(answer), {"hma-24", "bnss-144"})

    def test_express_order_request_overrides_an_extra_model_intent(self):
        answer = assess(
            "Our BNSS section 144 maintenance order was issued. How can I recover the missing payments?",
            lambda _: {"recover": "yes", "vary": "yes"},
        )
        self.assertEqual(self.ids(answer), {"bnss-144-3"})
        self.assertEqual(answer["facts"]["recover"]["source"], "user_text")

    def test_both_order_actions_are_kept_when_expressly_requested(self):
        answer = assess(
            "The court issued my order under Section 144 BNSS. I want to collect unpaid support and lower the amount going forward.",
            lambda _: {"recover": "yes"},
        )
        self.assertEqual(self.ids(answer), {"bnss-144-3", "bnss-146"})

    def test_recovers_an_express_ancillary_request_without_the_model(self):
        answer = assess(
            "My HMA nullity petition remains pending. I need enough money for my lawyer during the case.",
            lambda _: {"new_support": "yes", "husband": "yes"},
        )
        self.assertEqual(self.ids(answer), {"hma-24"})

    def test_identifies_unknown_act_from_express_litigation_expenses(self):
        answer = assess(
            "My marriage case is still in court but I don't know the Act. How can I get litigation expenses?",
            lambda _: {"maintenance": "unknown"},
        )
        self.assertEqual(self.ids(answer), set())
        self.assertEqual(answer["questions"][0]["field"], "hma_pending")

    def test_beneficiary_label_requires_evidence_for_that_person(self):
        cases = (
            ("My spouse will not contribute. Can I seek support for myself?", "wife"),
            ("Does my daughter get support? I have not said her age.", "minor_child"),
            ("My daughter is 23, but the classifier considers her a child. Can I seek money for her?", "minor_child"),
            ("I am a father seeking money for myself from my own spouse. My child is already supported.", "parent"),
            ("My son is eight. I need money for myself and I am not asking for any payments for the child.", "minor_child"),
        )
        for question, role in cases:
            with self.subTest(role=role):
                answer = assess(question, lambda _: {"new_support": "yes", role: "yes"})
                self.assertEqual(self.ids(answer), set())

    def test_supported_minor_twin_age_comes_from_the_question(self):
        answer = assess(
            "My twins, both nine, need financial help from their other parent. What order can I get?",
            lambda _: {"new_support": "yes", "minor_child": "yes"},
        )
        self.assertEqual(self.ids(answer), {"bnss-144"})
        self.assertEqual(answer["facts"]["minor_child"]["source"], "user_text")

    def test_source_stress_cases_with_wrong_model_assumptions(self):
        cases = (
            ("pending-past", "My divorce under the Hindu Marriage Act was pending last year. I need help with the lawyer's costs.", "interim", []),
            ("pending-closed", "My HMA divorce petition was pending last year. It has since been dismissed. Can I ask for temporary money?", "interim", []),
            ("pending-denied-request", "My HMA petition is still pending. I don't want interim maintenance. I only need visitation.", "interim", []),
            ("pending-other-actor", "My dentist's HMA petition is still pending. My own petition uses a different Act. Could I ask for costs?", "interim", []),
            ("pending-pretend", "Pretend my HMA petition is pending. Can you explain what temporary money could be granted on those assumed facts?", "interim", []),
            ("decree-source-future", "The judge is passing the decree under HMA next month. Could I get permanent maintenance now?", "permanent", []),
            ("decree-person", "The judge granted my colleague a divorce under the HMA. Can I ask for permanent alimony in my own case?", "permanent", []),
            ("decree-own-positive", "The court has granted me a decree of judicial separation under the Hindu Marriage Act. I want to apply for a permanent allowance under the decree.", "permanent", ["hma-25"]),
            ("order-stale-claimed", "In April 2022 my BNSS section 144 maintenance order was issued. Now I want to collect the missed instalments.", "recover", []),
            ("order-wrong-code", "Court issued my order under section 144 of the CrPC. I looked up BNSS. Can I get unpaid money?", "recover", []),
            ("order-free-standing-code", "My civil support order is under a property case. I read about BNSS section 144 and want to recover unpaid money.", "recover", []),
            ("order-future", "I am applying for my maintenance order to be issued under section 144 of the BNSS. What about recovering missed instalments if it is issued?", "recover", []),
            ("order-negated-recovery", "I have an active BNSS section 144 maintenance order. I don't want to recover missing payments. I only need to see my children.", "recover", []),
            ("order-negated-change", "The court issued my maintenance order under BNSS section 144. I do not want to change the amount. I am just concerned about visitation.", "vary", []),
            ("order-window", "My BNSS 144 court order was issued in November 2025. I want to collect the maintenance unpaid this month.", "recover", ["bnss-144-3"]),
            ("order-legal-paper", "The existing court maintenance order cites BNSS section 144. I want it changed after my hours were reduced.", "vary", ["bnss-146"]),
            ("wife-not-recipient", "My husband pays me enough. I want maintenance only for my daughter, whose age I haven't given.", "new_support", []),
            ("child-speaker-age", "I'm a 16-year-old mother. I want to ask if my daughter can get support. Her age is not supplied.", "new_support", []),
            ("child-previous-age", "My son was twelve years old ten years ago. Can I apply for money for him while he studies?", "new_support", []),
            ("parent-speaker-incorrect", "My adult daughter is doing well. The only financial support I want is for myself from my wife, not from my daughter.", "new_support", []),
            ("scope-no-money", "My wife and I separated. I do not want maintenance. Can I see the kids this weekend?", "new_support", []),
        )
        for name, question, purpose, expected in cases:
            with self.subTest(name=name):
                scores = {purpose: "yes"}
                if purpose == "new_support":
                    scores.update(wife="yes", minor_child="yes", parent="yes")
                answer = assess(question, lambda _: scores)
                self.assertEqual(self.ids(answer), set(expected))

    def test_order_citation_has_to_name_the_issuing_act_and_section(self):
        cases = (
            ("case-number", "The court made my maintenance order under the BNSS. The docket lists case number 144. Can I collect overdue amounts?", "recover", []),
            ("case-number-same-clause", "My court maintenance order was made under the BNSS with case number 144. I want to collect unpaid instalments.", "recover", []),
            ("general-law-reference", "I got my civil maintenance order under a different Act and read about BNSS section 144. Can I collect the overdue balance?", "recover", []),
            ("different-provision", "My maintenance order quotes BNSS section 145 and receipt number 144. Can I seek a change in the amount?", "vary", []),
            ("auth-short-form", "The judge granted my maintenance u/s 144 of BNSS, 2023. It is unpaid. Can I recover the balance?", "recover", ["bnss-144-3"]),
            ("auth-named-year", "My support order was made under BNSS 2023, section 144. I'd like to reduce the amount.", "vary", ["bnss-146"]),
            ("auth-section-after", "My maintenance order cites the Bharatiya Nagarik Suraksha Sanhita, s. 144. How can I enforce the unpaid portion?", "recover", ["bnss-144-3"]),
            ("code-as-headline", "BNSS §144 order. I already have it. How can I enforce the unpaid portion?", "recover", ["bnss-144-3"]),
            ("conditional-authority", "If my maintenance order turns out to have been made under BNSS section 144, can I enforce it? I haven't checked which Act.", "recover", []),
        )
        for name, question, action, expected in cases:
            with self.subTest(name=name):
                result = assess(question, lambda _: {action: "yes"})
                self.assertEqual(self.ids(result), set(expected))

    def test_ambiguous_order_intents_do_not_issue_both_provisions(self):
        answer = assess(
            "I have a maintenance order under BNSS section 144. I have a question about its payment.",
            lambda _: {"recover": "yes", "vary": "yes"},
        )
        self.assertEqual(self.ids(answer), set())
        self.assertEqual({"recover", "vary"}, {item["field"] for item in answer["questions"]})

    def test_other_family_members_case_or_support_does_not_transfer(self):
        scenarios = (
            ("My parents' HMA divorce petition is pending. I am their son and want my case costs paid.", "interim", "wife"),
            ("My adult daughter sends money already. I am the husband and want money only from my wife.", "new_support", "parent"),
            ("I have a seven-year-old. Do not assess payments for the child. I want money from my wife.", "new_support", "minor_child"),
        )
        for question, purpose, role in scenarios:
            with self.subTest(question=question):
                answer = assess(question, lambda _: {purpose: "yes", role: "yes"})
                self.assertEqual(self.ids(answer), set())

    def test_distinct_minor_claim_can_be_read_separately_from_matrimonial_case(self):
        answer = assess(
            "My divorce petition under HMA is pending. I am a wife seeking interim maintenance. "
            "Separately I want a new support order for our baby.",
            lambda _: {"interim": "yes", "wife": "yes"},
        )
        self.assertEqual(self.ids(answer), {"bnss-144", "hma-24"})
        self.assertEqual(answer["facts"]["minor_child"]["value"], "yes")

    def test_follow_up_can_correct_a_fact_stated_in_the_question(self):
        result = assess(
            "My HMA divorce petition is still pending. Can I get interim support?",
            lambda _: {"interim": 0.99},
            {"hma_pending": False},
        )
        self.assertEqual(self.ids(result), set())
        self.assertEqual(result["facts"]["hma_pending"]["source"], "user_confirmation")

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
