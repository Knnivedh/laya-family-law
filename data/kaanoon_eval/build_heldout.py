#!/usr/bin/env python3
"""LANE 11 — build the Kaanoon held-out eval set + study sample (LAYA v7.1 recall swarm).

Source: public question pages on https://www.kaanoon.com/ (fetched via public
web search / page-text fetch on 2026-11-27; no sign-in, no paywall, no live
browser). QUESTION text only — lawyers' answers were never copied, never
cited as authority, and appear nowhere in the outputs.

Outputs (this directory, Lane 11 only):
  * heldout.jsonl      — 29 eval records, EVALUATION ONLY (contract R6).
  * study_sample.jsonl — 15 study records, pattern extraction only (contract R7).
  * README.md          — annotation method + file guide.
  * check_disjoint.py  — 8-gram disjointness / cosine checks (R7 + eval-vs-train).

Annotation method (see README.md for the full record): each eval item was read
in full and hand-annotated with the 11 issues / 28 facts of
data/synthetic_v7_1/schema.json; expected_sections were derived
deterministically from the Stage-2 rules in src/laya_v7_graph.py
(evaluate_stage2_v7, custody_vocab="v3_bundled"), then machine-checked by
running that same function on the annotated issues/facts — see
validate_expected() below. Anything the graph cannot model is labelled in
"annotation_notes" instead of forcing a section.

Re-run: python3 data/kaanoon_eval/build_heldout.py  (writes both JSONL files,
then validates every expected_sections list against the live Stage-2 code
and fails loudly on any mismatch).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))  # so `src.*` resolves as a namespace package

ISSUES = ["maintenance", "custody", "residence", "divorce", "stridhan",
          "joint_property", "violence", "dv_compensation", "restitution",
          "birth_certificate", "procedure"]
FACTS = ["divorce_asked", "mutual_consent", "judicial_separation_only",
         "restitution_asked", "proceeding_pending_hma", "being_filed",
         "decree", "money_fact", "lump_sum_settlement",
         "existing_order_enforcement", "interim_asked", "custody_claim",
         "child_fact", "minor_child", "child_maintenance_only",
         "school_fees_fact", "child_safety_risk", "residence_claim",
         "coercive_eviction_or_lockout", "explicit_residence_order_only",
         "violence", "dv_injury_comp_asked", "stridhan_claim",
         "stridhan_sold_or_mortgaged", "demand_made", "joint_property_claim",
         "birth_cert_asked", "in_scope"]

# ---------------------------------------------------------------- eval specs
# Sparse overrides only: issues default "uncertain", facts default "unknown".
# "text" is the question wording verbatim from the public page (whitespace
# normalised to single spaces; spelling/grammar left exactly as posted).
EVAL = [
    dict(id="KAN-E01", category="custody",
         url="https://www.kaanoon.com/501020/right-on-a-child-by-legal-wife",
         text="If an adult divorced lady got in affair and have a child with a married man whose divorce case is pending in court, does the man's legal wife, who has no child of her own (with whom the divorce case is going on) claim any right to that child? Like custody, visitation right",
         issues={"custody": "requested", "divorce": "incidental"},
         facts={"custody_claim": "supported", "child_fact": "supported",
                "proceeding_pending_hma": "supported"},
         enums={"claimant_sex": "F", "claimant_role": "spouse"},
         expected=["hma-26", "hmga-1956-s6", "welfare-principle"],
         notes="Divorce case pending => HMA proceeding active, so custody routes to hma-26 (not gwa-1890). Whether a legal wife who is not the biological mother has standing to claim custody is NOT modelled in the graph — the graph routes the claim anyway. Lane 09 spot-check."),
    dict(id="KAN-E02", category="custody",
         url="https://www.kaanoon.com/485554/child-custody-of-twin-boys",
         text="Hello I seek suggestion for below queries: If wife has left his husband house which is joint ownership of both and living separately in rented house for last 1 year with twin boys of 5 years. Reason is the mental abuse and controlling nature of husband. Husband is now giving 2 option : comeback or he will take away the kids in a week's time. Q1- How can i ensure that kids remain together and with mother? Q2 - Can he forcefully take away kids either from my rented place or school? If yes, what are my legal options to get kids? Q3 - I dont want to give divorce to him and if i do mutual - i fear that i will loose everything including my kids. What is my best option to handle my case? Q4 - Everytime he threatens me for divorce but somehow he is not moving ahead rather psychologically pressurizes me and try to instill fear of taking away kids.",
         issues={"custody": "requested", "divorce": "denied", "violence": "incidental"},
         facts={"custody_claim": "supported", "child_fact": "supported",
                "minor_child": "supported", "violence": "supported",
                "divorce_asked": "denied", "mutual_consent": "denied"},
         enums={"claimant_sex": "F", "claimant_role": "spouse"},
         expected=["gwa-1890", "pwdva-18", "hmga-1956-s6", "welfare-principle"],
         notes="Asker writes about 'wife' in third person then as 'i'; claimant read as the wife. Mental abuse + threats are described (violence fact supported) but no protection order is expressly asked; pwdva-18 follows from the graph rule (violence fact + female claimant)."),
    dict(id="KAN-E03", category="custody",
         url="https://www.kaanoon.com/144266/custody-of-child",
         text="If the working wife leaves the house of husband with her 2 year child due to unemployment of husband and torture, what the wife should do to ensure custody of the child given to her and husband cannot take the child from her.",
         issues={"custody": "requested", "violence": "incidental"},
         facts={"custody_claim": "supported", "child_fact": "supported",
                "minor_child": "supported", "violence": "supported"},
         enums={"claimant_sex": "F", "claimant_role": "spouse"},
         expected=["gwa-1890", "pwdva-18", "hmga-1956-s6", "welfare-principle"],
         notes="Torture is the stated reason for leaving; pwdva-18 follows from the graph rule (violence fact + female claimant)."),
    dict(id="KAN-E05", category="custody",
         url="https://www.kaanoon.com/56007/gaurdian-for-minor-girl-child-when-father-and-mother-die-together",
         text="4 year girl child-Father and mother died in accident one year back, girl has got both side grand parents, since the birth of the child and presently also mother side grand parents are looking after the child, But the father side grand parents want to take the child, All the money which came from insurance/property all taken by father side grand parents. we ( mother side grand parents) want to have the custody of child till she become major. All the grand parents are senior citizens. mother has got two good understanding sisters. Father has got only one brother in abroad.",
         issues={"custody": "requested"},
         facts={"custody_claim": "supported", "child_fact": "supported",
                "minor_child": "supported"},
         enums={"claimant_sex": "U", "claimant_role": "other"},
         expected=["gwa-1890", "hmga-1956-s6", "welfare-principle"],
         notes="Claimants are the maternal grandparents (role other, sex unknown). The graph adds the Hindu companions regardless of claimant religion/role."),
    dict(id="KAN-E06", category="custody",
         url="https://www.kaanoon.com/178940/custody-of-child-if-both-parents-die",
         text="Is it possible for me to pre-decide (via a will or any other way) the legal guardianship/custody of my child in case both me and my wife die in an unforeseen event/accident? What is the procedure?",
         issues={"custody": "requested", "procedure": "incidental"},
         facts={"custody_claim": "supported", "child_fact": "supported"},
         enums={"claimant_sex": "M", "claimant_role": "parent"},
         expected=["gwa-1890", "hmga-1956-s6", "welfare-principle"],
         notes="Testamentary guardianship (HMGA s.9) has no route in the graph; the graph routes a custody claim with no HMA proceeding to gwa-1890. The expected list is the graph-derived answer, flagged here as approximate for this nuance."),
    dict(id="KAN-E07", category="maintenance",
         url="https://www.kaanoon.com/30261/how-long-and-how-much-maintenance-do-i-need-to-pay-and-how-to-defend",
         text="Me and my wife lived together for 2.5 years.we have one 1.5 yrs old boy child. She dont want to keep my sick widow mother with me, she and her family behaved arrogant and insulted my mother and me. Her father is a rich man, once i started opposing their attitude towards my family members they filed DV case and called me as drug adict, which police refuse to file FIR after enquiry. Police asked her to leave their parents ( in written) and live with me. She refused and given in the written that she dont want to live with me at this time. Now she filed a maintenance case in court. I am earning 45.000 per month in IT company. My question is how much maintenance naturally will be allocated to her and my child.. and how long i have to give her that . What is the way for getting divorce.? She is not working currently and she is a msc mphil on dietics. 2011 passed out.",
         issues={"maintenance": "incidental", "divorce": "requested"},
         facts={"money_fact": "supported", "divorce_asked": "supported",
                "child_fact": "supported", "minor_child": "supported"},
         enums={"claimant_sex": "M", "claimant_role": "spouse"},
         expected=["hma-13"],
         notes="Asker is the husband (respondent in the wife's maintenance case) asking the quantum he must pay and how to get divorce. The graph gates male self-maintenance outside HMA, so the maintenance-quantum question yields no section; only the contested-divorce route fires. The wife's maintenance case is under BNSS/DV, not HMA, so proceeding_pending_hma is unknown."),
    dict(id="KAN-E08", category="maintenance",
         url="https://www.kaanoon.com/158980/interim-maintenance-in-dv-case",
         text="Do I will get interim maintenance in ongoing dv case as I have a background of job. But not working from past 1 year and my last drawn salary was 20000. My husband earning about 80000 per month.",
         issues={"maintenance": "requested"},
         facts={"money_fact": "supported", "interim_asked": "supported"},
         enums={"claimant_sex": "F", "claimant_role": "spouse"},
         expected=["bnss-144", "pwdva-20"],
         notes="Interim maintenance inside an ongoing DV case; the graph routes subsistence maintenance to bnss-144 + pwdva-20 (no HMA proceeding pending, so no hma-24). Approximate for the interim-in-DV nuance."),
    dict(id="KAN-E09", category="maintenance",
         url="https://www.kaanoon.com/348313/husband-not-paying-complete-interim-maibtence",
         text="Can I get access to my husband individual bank accounts statement and appointment letter where he is currently employed, based on FIR for 498 A and 406 I filed recently. He is currently not even paying the complete interim maintenance amount as well, which the court ordered to do so. Nor submitting the actual bank and his company details which the court orders to submit as affidavit from both the parties in my DV case. He left me with 2 kids for job in other city and last year he changed company and is hiding in some other city, giving false details to the court about his actual whereabouts. He is deeply involved in extra marital affair and is having live in relationship with his ex colleague in Bangalore. He is in senior designation but is not ready to pay for sons college admission or the you get one's school fees.a distress warrant order is issued by the court but still he is not complying. What other measures can I take ? Should I apply for crpc 125? I'm also too broke currently",
         issues={"maintenance": "requested"},
         facts={"money_fact": "supported",
                "existing_order_enforcement": "supported",
                "child_fact": "supported", "minor_child": "supported",
                "school_fees_fact": "supported"},
         enums={"claimant_sex": "F", "claimant_role": "spouse"},
         expected=["bnss-144"],
         notes="Enforcement of an already-ordered interim maintenance (distress warrant issued, still unpaid). The graph's existing-order branch emits bnss-144 only (no pwdva-20 there). One child is college-going, one school-going; minor_child supported because at least one child is a minor."),
    dict(id="KAN-E10", category="maintenance",
         url="https://www.kaanoon.com/113270/if-school-fees-paid-directly-can-it-be-considered-as-maintenance",
         text="The Family court had granted an amount for my kids as maintenance, however I had continued to pay for the School Fees / Medical / celebrations / and lot many more other direct expenses and did it all in shear love and affection towards my children, now after almost 7 years, their mother had filed a pet. stating that I am an unfit father and has not paid any thing till date against maintenance of the children, and her council smartly put it across that I was to pay her and not do any thing directly, even IF any thing has been done - it was done on his own but has failed to comply with the maintenance order, hence have to pay the entire amount from the day of separation. Is there any Order from any court, where at least the School fees is said to be / can be considered to be taken into account as maintenance as that is the only one which I have paid through my bank account.",
         issues={"maintenance": "incidental"},
         facts={"money_fact": "supported",
                "existing_order_enforcement": "supported",
                "child_fact": "supported", "school_fees_fact": "supported",
                "child_maintenance_only": "supported"},
         enums={"claimant_sex": "M", "claimant_role": "spouse"},
         expected=[],
         notes="Father disputing compliance with a child-maintenance order (direct school-fee payments). GRAPH FINDING: the male + child-only branch emits bnss-144 only when minor_child is verified; here the children's current ages are not stated (order is 7 years old), so minor_child is honestly unknown and the graph emits NOTHING — the existing-order branch is shadowed by the male+child_only branch and never reached. Expected list is the deterministic graph output ([]), flagged as a graph behaviour for Lane 08/09, not a claim that no remedy exists."),
    dict(id="KAN-E11", category="maintenance",
         url="https://www.kaanoon.com/409088/waiver-of-maintenance-agreement-under-special-marriage-act",
         text="I have done some research on pre nuptial agreements in India, some lawyers say it is valid under contract act if marriage is solemnised under special marriage act with the contract signed together, while other lawyers argue that any contract which keeps marriage as a clause is not valid. My would be wife has agreed to sign any agreements/affidavits that says that She will not get any maintenance or share in property(unless co-owned). I want to know how do I proceed with this without worrying about its legal validity. Additionally, can I ask for a contract that states that in future if she is to receive any alimony/maintenance/ assets post divorce from me, she has to donate 1.5 times the same to specific charity institutions from her own pocket.",
         issues={"maintenance": "denied", "divorce": "incidental",
                "joint_property": "incidental"},
         facts={},
         enums={"claimant_sex": "M", "claimant_role": "spouse"},
         expected=[],
         notes="Prenuptial-agreement validity question (would-be husband, marriage not yet solemnised). No maintenance is actually claimed — the maintenance is waived in advance and any future alimony is hypothetical — so money_fact is unknown and no graph section applies. Honest empty expected list, not a forced section."),
    dict(id="KAN-E12", category="divorce",
         url="https://www.kaanoon.com/279595/divorce",
         text="I m married for 14 years. i ve a son of thirteen years. now i want divorce from my husband. but he doesn't want. can i get divorce. after divorce what benefits i ll get from him. my son wants to stay with me. is it possible after divorce.",
         issues={"divorce": "requested", "maintenance": "incidental",
                "custody": "requested"},
         facts={"divorce_asked": "supported", "mutual_consent": "denied",
                "custody_claim": "supported", "child_fact": "supported",
                "minor_child": "supported"},
         enums={"claimant_sex": "F", "claimant_role": "spouse"},
         expected=["hma-13", "gwa-1890", "hmga-1956-s6", "welfare-principle"],
         notes="'After divorce what benefits' is too vague to count as a money claim, so money_fact is unknown and no maintenance section is claimed."),
    dict(id="KAN-E13", category="divorce",
         url="https://www.kaanoon.com/446590/divorce-decree",
         text="We (husband side) have filed mutual divorce first motion,now are going for final second motion of mutual consent divorce and all cases has been closed against us- 1. What is included in divorce decree, are some points copied from divorce petition or agreement like settlement amount agreed etc ? 2. We have paid full and final settlement amount and now nothing is pending from husband to wife, so can we request judge to add things in decree like no alimony,mentainance ,streedhan etc is pending and no case would be filed in future, which is already agreed by wife in divorce petition and agreement ? 3. Can we request judge to attach agreement copy to divorce decree ? 4. If above mentioned things can be requested to judge to add in decree, so when and at what stage this request should be made and the request can only be in oral form or written request can also be made? 5. What other precautions in form of documentation or in any other form can be done at right now during second motion of divorce or after divorce so that they cannot trouble us in future ? Thanks and Regards",
         issues={"divorce": "requested", "procedure": "requested",
                "stridhan": "incidental", "maintenance": "incidental"},
         facts={"divorce_asked": "supported", "mutual_consent": "supported",
                "proceeding_pending_hma": "supported",
                "lump_sum_settlement": "supported", "money_fact": "supported",
                "stridhan_claim": "denied"},
         enums={"claimant_sex": "M", "claimant_role": "spouse"},
         expected=["hma-25", "hma-13b"],
         notes="Mutual-consent divorce at second-motion stage, full and final settlement already paid, decree not yet passed. Procedure questions have no section in the graph (no proc-* section is emitted by Stage 2)."),
    dict(id="KAN-E14", category="divorce",
         url="https://www.kaanoon.com/488398/mutual-divorce-settlement",
         text="Mera mutual divorce ke liye settlement ho gya, mere uper 125, 498A and 406 case chal rahe hai, half payment first motion pe de di hai aur pending payment second motion pe deni hai, first motion ki statement mein wife ne likha hai woh sabi pending case vapas le legi jab second motion pe pending payment mil jayegi, after divorce kya wo sare case vapas lene k liye bond ho jayegi ya fr case vapas lene ko mna v kr skti hai ? Second motion date 28.05.2025 hai Humne High court me joint FIR quashing hone ke liye petition v file kr di hai jisme likha hai ke hamara settlement ho gya hai aur half payment de di hai aur half payment divorce ki second motion pe deni hai, ab high court ne ye order kiya hai, High court next hearing 25.09.2025 Kya mein second motion pe pending payment apni wife ko de du ? after divorce kya wo sare case vapas lene k liye bond ho jayegi ya fr case vapas lene ko mna v kr skti hai ? High Court mein FIR quashing ka full process kya hoga ?",
         issues={"divorce": "requested", "procedure": "requested"},
         facts={"divorce_asked": "supported", "mutual_consent": "supported",
                "proceeding_pending_hma": "supported",
                "lump_sum_settlement": "supported", "money_fact": "supported"},
         enums={"claimant_sex": "M", "claimant_role": "spouse"},
         expected=["hma-25", "hma-13b"],
         notes="Hinglish (Roman-script Hindi + English). The schema has no hi_roman language label, so lang is recorded as 'en' — flagged here, not hidden. FIR-quashing procedure questions have no graph section."),
    dict(id="KAN-E15", category="divorce",
         url="https://www.kaanoon.com/263381/how-to-file-for-a-divorce-judicial-separation",
         text="I and my husband are leaving separately for a year plus. He is not agreeing on mutual divorce. Is there any way by which i can file and ask for divorce or judicial separation",
         issues={"divorce": "requested"},
         facts={"divorce_asked": "supported", "mutual_consent": "denied"},
         enums={"claimant_sex": "F", "claimant_role": "spouse"},
         expected=["hma-13"],
         notes="Divorce OR judicial separation asked as alternatives; judicial_separation_only is unknown (not only-JS), so the contested-divorce route fires."),
    dict(id="KAN-E16", category="divorce",
         url="https://www.kaanoon.com/475877/legal-separation",
         text="My husband and I have been separated for 12 years. We have our own lives. We have a son together and have a parenting agreement in place. He lives in US and I live in Canada. What is the best way for me to get a legal separation document from India",
         issues={"divorce": "uncertain"},
         facts={"judicial_separation_only": "supported",
                "child_fact": "supported"},
         enums={"claimant_sex": "F", "claimant_role": "spouse"},
         expected=[],
         notes="Judicial separation (HMA s.10) has NO route in the graph — Stage 2 emits nothing for a JS-only ask. Honest empty expected list; this is a known graph gap, not a claim that no law applies."),
    dict(id="KAN-E17", category="stridhan",
         url="https://www.kaanoon.com/329094/question-regarding-streedhan",
         text="My in-laws have kept my jewelleries gifted to me by my parents and relatives during my marriage with them, it's been like 8 years now since my marriage.. When I asked them to return my jewelleries gifted to me by my parents and relatives they are asking me to return them the jewelleries which are gifted to me by them (i.e., my in-laws )during the rituals of my marriage.. What should I do now?? Shall I return them the jewelleries gifted to me from my in-laws side to collect the jewelleries gifted to me by my parents and relatives ?? Plz suggest a legally correct thing what should I reply them..",
         issues={"stridhan": "requested"},
         facts={"stridhan_claim": "supported", "demand_made": "supported"},
         enums={"claimant_sex": "F", "claimant_role": "spouse"},
         expected=["bns-316"],
         notes="Stridhan held by in-laws, return demanded and refused by counter-demand. Jewellery gifted by the in-laws themselves is also the wife's stridhan, so no stridhan negation applies."),
    dict(id="KAN-E18", category="stridhan",
         url="https://www.kaanoon.com/265718/marriage-gift-gold-ownership",
         text="Hi All, Good Day! I am asking this question for my friend Sindhu Nair (Female, 25 year old, Divorced). Both of we are first year law students! We are from Kerala, Hindu family. Her father was expired 15 years before. She was married 5 years before (on 2014 Jan). After 2 years she divorced (on 2016 March). At the time of marriage, she get some gold ornaments as marriage gift, from her relatives. And at the time of divorce her husband returned it back to her. After her divorce one of her uncle borrowed all of her gold for his new business. Now for her education she want her gold back. But her uncle is not returning it to her. He is telling her that, it is not her gold. As per his words: \"the gold was gifted by all of her family members at the time of marriage. Now she is divorced. So it is not her gold. It is the family's property\". So they are not giving it back to her. All of her family members including her mother, sisters, uncles, etc are not supporting her. Everyone is telling her that it is not her gold. They all are telling it is the family's gold, as she is divorced. We feel this as a strange rule. She don't have any other option to pay her education fees, hostel fees and the fees for her 'job entrance coaching'. For your clarification I am explaining these events below: 1. 2014-Jan => She married, she got gold ornaments as gift from her family members 2. 2014-Feb => Her husband keeps it in bank locker 3. 2015-jan => her divorce process started 4. 2016-jan => her husband returned her gold 5. 2016-march => she divorced 6. 2016-dec => her uncle borrowing all of her gold from her 7. 2019 => she ask the gold back from her uncle. Now all of her family, except herself, is telling it is not her gold. It is her family's gold as she get divorced. She have phone call recorded audio in which her family members (including this uncle who borrowed the gold) talking about this. She don't have any other proof to prove that she gave her gold to her uncle and how much gold she gave. But we came to know that he took a gold loan using that gold from a bank. I have three doubts here: =================== 1. Who is right here ? (She or her family) 2. What she can do to get the gold back? 3. what is the chance to get the gold back if we are moving legally? Kindly help!",
         issues={"stridhan": "requested"},
         facts={"stridhan_claim": "supported", "demand_made": "supported",
                "stridhan_sold_or_mortgaged": "supported",
                "decree": "supported"},
         enums={"claimant_sex": "F", "claimant_role": "spouse"},
         expected=["bns-316"],
         notes="Third-party asker (friend) — claimant is Sindhu, the divorced woman. Uncle borrowed the gold then took a gold loan on it (mortgaged), so stridhan_sold_or_mortgaged is supported. Full question text as fetched from the page."),
]
EVAL += [
    dict(id="KAN-E19", category="eviction",
         url="https://www.kaanoon.com/59134/regarding-wife-staying-in-my-house",
         text="Hello, I'm married for 9 years. I have a kid who is 6 years old. My wife was working before marriage but not after that. I work in US, came here last year. I have an apartment in Bangalore where my wife and kid are staying. I want my wife and kid to come and stay with me in US. But she is not coming for silly reason. She is not working there in India. I have not filed for divorce. I want to know if i can evict her from my apartment forcibly. can i forcibly evict her after filing for divorce? Do i need to send her money for maintenance if she is going to stay in my apartment? Can she claim share in my apartment after divorce? Thanks, Balasubramanian",
         issues={"residence": "incidental", "maintenance": "incidental",
                "joint_property": "incidental"},
         facts={"residence_claim": "supported", "child_fact": "supported",
                "minor_child": "supported"},
         enums={"claimant_sex": "M", "claimant_role": "spouse"},
         expected=[],
         notes="Husband asking whether HE can evict his wife from the matrimonial home. The graph routes residence relief to a female claimant, so from this male asker's perspective no section fires — honest empty list. The pipeline ideally would surface the wife's pwdva-17/19, which the graph cannot derive from a male claimant; flagged, not forced."),
    dict(id="KAN-E20", category="eviction",
         url="https://www.kaanoon.com/110894/can-i-evict-my-wife-from-company-provided-accommodation",
         text="I am married since last 10 yrs and living in a company provided residence. I am planning for divorce on ground of mental cruelty caused by her due to her adulterous behaviour. After filing of divorce can i force her to evict the house since it is neither mine nor of my family. I am ready to pay rent to her in cash so that she can live separately.",
         issues={"divorce": "requested", "residence": "incidental"},
         facts={"divorce_asked": "supported", "residence_claim": "supported"},
         enums={"claimant_sex": "M", "claimant_role": "spouse"},
         expected=["hma-13"],
         notes="Divorce planned on cruelty grounds; eviction question concerns the wife's residence in company accommodation. Male claimant => no pwdva-17/19. The offered rent is for alternative accommodation, not maintenance, so money_fact is unknown."),
    dict(id="KAN-E21", category="eviction",
         url="https://www.kaanoon.com/478597/eviction-suit",
         text="Rent agreement expired on Oct 31'24 and proper notice was served to evacuate property. Tenant requested to extend but we refused. Till date, he has not vacated. On serving notice, we were informed by the tenant (husband) that he was not living in the premises for about 10 months and that his wife lives there. Wife is not the tenant or in any agreement. There is a divorce and domestic violence case ongoing between them. The wife in the meanwhile has mentioned our property address to file her petitions of which we were not informed. In such situation, the wife , who is not our tenant, is living in the premise and is not evacuating and the husband has not done anything for any alternate accomodation for her. What are our chances of getting our flat fast by filing eviction suite? Should we file directly in high court or lower court? Is there any other way to settle the matter?",
         issues={"residence": "incidental", "divorce": "incidental",
                "violence": "incidental"},
         facts={"residence_claim": "supported",
                "proceeding_pending_hma": "supported", "in_scope": "denied"},
         enums={"claimant_sex": "U", "claimant_role": "other"},
         expected=[],
         notes="Claimant is the LANDLORD asking about an eviction suit against a tenant's wife — a landlord-tenant question, out of the family-law graph's scope (in_scope denied), so the honest expected list is empty despite the divorce/DV background."),
    dict(id="KAN-E22", category="restitution",
         url="https://www.kaanoon.com/10134/matrimonial-dispute",
         text="My father inlaw had forcefully taken my wfe to his home.incase i bring back her and my 9monthold child back to my home bysome way.can my fthr in law file or lodge any complaint against me?wht i can do to get thm back safely and in less time",
         issues={"restitution": "requested", "custody": "incidental"},
         facts={"restitution_asked": "supported", "custody_claim": "supported",
                "child_fact": "supported", "minor_child": "supported"},
         enums={"claimant_sex": "M", "claimant_role": "spouse"},
         expected=["hma-9", "gwa-1890", "hmga-1956-s6", "welfare-principle"],
         notes="Husband wants his wife and 9-month-old child brought back from the father-in-law's home."),
    dict(id="KAN-E23", category="restitution",
         url="https://www.kaanoon.com/296297/abandoned-wife",
         text="My sister got married a man from panvel raighar district Maharashtra in February 2019.now its more than a year now.few days back her husband sent her from Mumbai to Delhi on the pretext that their was some kind of family relationships issues he was having with his parents.now after a few days when she reaches delhi her hometown the husband calls her and says let us separate from each other and he also demands complete submission before his parents like doing whatever they say.my sister says she will not be like a slave before his parents as he wants. Also my sister says she will only go back till her husband comes and takes her back. Guide me on the legal options I have it looks though that her in laws may have not accepted her whole heartedly after marriage.",
         issues={"restitution": "requested"},
         facts={"restitution_asked": "supported"},
         enums={"claimant_sex": "F", "claimant_role": "spouse"},
         expected=["hma-9"],
         notes="Third-party asker (brother) — claimant is the sister. She will return only if her husband comes and takes her back: a restitution ask, not a divorce ask."),
    dict(id="KAN-E24", category="restitution",
         url="https://www.kaanoon.com/10398/matrimonial-dispute",
         text="If i filed habeous writ against inlaws and they through some mediator are askng me to come to their home and take away my wfe and Child. Shall i go and brng her back? But i doubt their intentions. Shall i tll judge regardng it?",
         issues={"restitution": "requested", "custody": "incidental"},
         facts={"restitution_asked": "supported", "custody_claim": "supported",
                "child_fact": "supported"},
         enums={"claimant_sex": "M", "claimant_role": "spouse"},
         expected=["hma-9", "gwa-1890", "hmga-1956-s6", "welfare-principle"],
         notes="Husband weighing whether to fetch his wife and child from the in-laws' home during a pending habeas writ. Child's age is not stated, so minor_child is unknown (graph defaults it True)."),
    dict(id="KAN-E25", category="restitution",
         url="https://www.kaanoon.com/342503/husband-s-complaint-of-not-living-with-him",
         text="I'm living separately from my husband for few months. Now he has lodged a complaint against me that I'm not living with him. Is there any provision in law that I can't live separately?? If yes then what should I do???",
         issues={"restitution": "denied"},
         facts={"restitution_asked": "denied"},
         enums={"claimant_sex": "F", "claimant_role": "spouse"},
         expected=[],
         notes="Wife resisting the husband's complaint that she does not live with him; she asks whether separate living is lawful. No restitution is sought by her — honest empty list."),
    dict(id="KAN-E26", category="joint_property",
         url="https://www.kaanoon.com/411307/joint-property-of-divorce-couple",
         text="Husband has bought a property and registered jointly with wife. It is on bank loan and husband is repaying the loan. They are planning to file mutually consented divorce. Wife is willing to transfer the property right to husband, but she is insisting that she will transfer the rights only after the divorce is granted. How can we make it legally binding that she transfers it after divorce.",
         issues={"joint_property": "requested", "divorce": "requested"},
         facts={"joint_property_claim": "supported",
                "divorce_asked": "supported", "mutual_consent": "supported"},
         enums={"claimant_sex": "U", "claimant_role": "spouse"},
         expected=["hma-13b"],
         notes="Joint property + mutual-consent divorce PLANNED but not yet filed, so hma-27 is gated by the D2 rule (no HMA proceeding pending or being filed) and is NOT in expected_sections. Asker's sex/side is not stated (sex U)."),
    dict(id="KAN-E27", category="joint_property",
         url="https://www.kaanoon.com/257770/joint-possession-of-property-with-spouse",
         text="I am keen to know the pros and cons of purchasing a property jointly in my spouse's name considering the fact that we don't get along well all the time. How can I ensure the property is passed on to my daughter in the future?",
         issues={"joint_property": "uncertain"},
         facts={"child_fact": "supported"},
         enums={"claimant_sex": "U", "claimant_role": "spouse"},
         expected=[],
         notes="Prospective purchase / inheritance-planning question, not a claim in a proceeding. No joint-property claim exists, so no graph section applies — honest empty list."),
    dict(id="KAN-E28", category="violence",
         url="https://www.kaanoon.com/241927/physical-assault-by-husband",
         text="My husband usually drink and beat me ...2 counselling have been done in women cell..women cell is not in favour of me...they are pressurising me...and my husband is not accepting his mistake...he is still blaming on me",
         issues={"violence": "requested"},
         facts={"violence": "supported"},
         enums={"claimant_sex": "F", "claimant_role": "spouse"},
         expected=["pwdva-18"],
         notes="Beating by a drinking husband; counselling at the women's cell failed. No specific relief is named, but the graph routes a supported violence fact with a female claimant to pwdva-18."),
    dict(id="KAN-E29", category="violence",
         url="https://www.kaanoon.com/357799/can-a-husband-file-a-domestic-violence-case-against-his-wife-and-seek-divorce",
         text="I and my mother have been physically and mentally abused by my wife. We have two kids who are minors. I have CCTV camera recordings with voice as evidence of several instances, where my mother and I have been abused. My wife is a psychopathic crazy woman and on suicidal mission, where she has threatened to kill my mother, kids and herself. Can I as a husband, file a Domestic Violence case and/or Protection of Senior Citizen case against her and seek divorce on grounds of cruelty against me and my mother? Can my wife demand a financial share in the property for settlement?",
         issues={"violence": "requested", "divorce": "requested",
                "joint_property": "incidental"},
         facts={"violence": "supported", "divorce_asked": "supported",
                "child_fact": "supported", "minor_child": "supported",
                "child_safety_risk": "supported"},
         enums={"claimant_sex": "M", "claimant_role": "spouse"},
         expected=["hma-13"],
         notes="Male claimant abused by his wife; asks about filing a DV case himself. The PWDVA route is woman-only in the graph, so no pwdva-18 fires; only the contested-divorce route does. The wife's threats to kill the children are recorded as child_safety_risk (safety escalation is separate from kept_ids). 'Financial share in the property' is a question, not a claim, so joint_property_claim is unknown."),
]

# --------------------------------------------------------------- study specs
# Search-result excerpts of the question portion only (NOT the lawyers'
# answers). "[...]" marks where the search snippet truncated the question.
# These texts are for pattern extraction ONLY (contract R7) — they are never
# used for training, templates, anchors, or tuning.
STUDY = [
    dict(id="KAN-S01", category="stridhan",
         url="https://www.kaanoon.com/283042/unlawful-claim-of-streedhan",
         text="My daughter-in-law and son do not have cordial relationship with each other and of lately, my daughter-in-law has started demanding her [...] all and any jewelry that was displayed at the wedding is her \"streedhan\". She is using photographs and the wedding video as the evidence that the jewelry was given to her as wedding gift. [...] Hence, my question is : Can the jewelry displayed in wedding video / photographs qualify as a legal evidence for claiming \"streedhan\" ? What are my rights in this case ? There isn't any legal notice sent but there have been multiple verbal exchanges / threats by my daughter-in-law over the jewelry received during / after marriage."),
    dict(id="KAN-S02", category="stridhan",
         url="https://www.kaanoon.com/355185/gold-ornaments",
         text="Mother gave me her all her gold ornaments which were bought by my father. Father tortured my mother for whole life Now mother is dead. Father is asking gold ornaments with bills of those ornaments also which we have completely no idea. Now if we return the ornaments which I have ,he will say all other ornaments are also with me, which he may have either gifted to others or he already have it with him. I don't want to return my mother's gold to my father as those were her last wishes and memory. I have no idea what is legal"),
    dict(id="KAN-S03", category="eviction",
         url="https://www.kaanoon.com/199859/forced-to-leave-matrimony-house-by-husband-and-father-in-law",
         text="I have been married for 2 months and my husband and me used to regular fight with each other..one day i was asked to leave my matrimony house stating that he needs a cool off period and i can return after 4-5 days.. when tried to return house i was not taken back.. my father in law and my husband told me that they will brimg restrainning order from.court. i went to police after few days to lodge a complaint.."),
    dict(id="KAN-S04", category="eviction",
         url="https://www.kaanoon.com/293362/my-brother-s-wife-has-acquired-my-floor",
         text="Hi folks My brother got married 2years back and has got a son now who is Of 8months now. [...] Now the question is ,how can we proceed to let her out of this floor or the entire property? Also ,is my property clear for smooth sale purchase without ny challenges by her ,and her son ? She is not agreeing for the divorce ,she does not have good financial background but before marriage she said ,she was educated .But after marriage ,she did not even apply for ny job . My brother want divorce and I want the property to be cleared by all means . Please suggest ,how should I proceed and how should my brother proceed ."),
    dict(id="KAN-S05", category="maintenance",
         url="https://www.kaanoon.com/169725/can-the-complainant-my-wife-ask-the-court-to-confiscate-my-property-in-dv-act",
         text="My wife has put a false DV act, dowry and maintenance case ( all combined in one ) on me and my parents. And has taken a stay on the only property that me and my parents ( R. No. 2 & 3 ) are living in. She is earning handsomely and has already given the affidavit of the same. Last court order was in April 2016, where the court ordered me to pay the child's school fees \"there onwards \". Which I did for 1 year ( till May '17 ) . After which she has put the boy in a school where the fees is exorbitant, 3 times of the earlier school's fees ( since June' 17 ), paying which is completely beyond my capacity since I have turned hand to mouth in this while and I have severely ill parents ( both of them have unusual old age degenerative disorders ) So, I didn't pay the new fees for 6 months [...] Now, at the date after 6 months, he has filed and application of execution in the court to jail me and sell my property to pay the child's school fees. Questions are: 1. Had the arguments taken place on that date, court couldn't have asked me to comply by the previous order- Who could come under the ambit of misguiding the court ? The Complainant's lawyer or the Judge herself ? 2. Can the court Jail me ( No offense has ever been made from my side barring these 6 months fees) ? 3. Or heavily Fine me ? 4. And since all the valid documents are already presenting a sorry figure, can the court confiscate my property to pay the Complainant's unsuitable demands ( now or at any time in future )?"),
    dict(id="KAN-S06", category="maintenance",
         url="https://www.kaanoon.com/102642/divorce",
         text="I am separated from last 6 years reason very abusive. My daughter 13 years old staying with me. I have already filed the case 2 years back but on a date, he finds one or the other reason to avoid the court dates. Because of my new job I have stopped going to court from last 2 years. Now I want to file the case as he is only paying her school fees excluding school bus transport, school dress, stationary and other day to day expenses. Kindly advice how to proceed."),
    dict(id="KAN-S07", category="divorce",
         url="https://www.kaanoon.com/279392/hc-mediation-for-divorce",
         text="I agreed to pay 14 lakh final settlement amount as I wanted to end the litigations though family court order could have helped me in HC. [...] Please suggest me the terms/agreement points for final settlement which I can put to the mediator. Thanks."),
    dict(id="KAN-S08", category="custody",
         url="https://www.kaanoon.com/305493/child-s-guardian",
         text="Dear Experts, The Wife passed away while the divorce & RCR cases are going on. The male child was in her custody for 5 years. The child can identify his father but he has absolutely no bonding with him all these years. [...] As the wife has passed away: 1) What are the necessary legal steps the father has to take next. 2. Regarding Child custody. Inlaws are keen to have custody of the child. If the father agrees to leave the child with inlaws, what amount would be fixed as compensation? Is it 1/3 rd thumb rule as in MC case? 3) What else are the responsibilities of the father at this stage and future?"),
    dict(id="KAN-S09", category="joint_property",
         url="https://www.kaanoon.com/58768/property-issue",
         text="Divorced and decree received from court in July 2012 on the grounds of wife deserted and not leaving along with me for more than 2 years under rule 13(1b) as per Hindu marriage act. [...] Can wife claim rights in joint property of husband? Agreement and share certificates are in joint name. What will be the time limit to appeal for any such claims?"),
    dict(id="KAN-S10", category="violence",
         url="https://www.kaanoon.com/167068/domestic-violence",
         text="I am here asking for friend who is married for about 7 years now. She is a BTech in Electronics engineering, but could not complete the course due the marriage. She has had a troubled married life but still is staying in the marriage because she has no where else to go. Earlier it was because she was diabetic and not able to conceive a child and her mother in law and husband constantly use to harass her and beat her up. [...] Last few days has been horrific, she almost fractured her hand and had to rush to hospital. [...] He is also asking her to leave the house with their son as he can marry another woman and he was also stressing he will not give the gold and she do not dare to ask for a single rupee as alimony. She is does not want to continue in this marriage, but has no where else to go as her family wont support her much in this case. What steps should she seek that she can get support and get divorce in the future."),
    dict(id="KAN-S11", category="violence",
         url="https://www.kaanoon.com/411288/domestic-violence",
         text="Our maid who has a 3 year child wants to separate from her husband as his husband is habitual drinker and beats her regularly. [...]"),
    dict(id="KAN-S12", category="restitution",
         url="https://www.kaanoon.com/57091/what-is-wife-leaves-kids-husband-and-leaves-india-without-inform",
         text="We were living separately from last 11.5months she lives with her parents but one day she leaves India without any information to us. The kids and me are shocked to know this. Can you please guide me with the right suggestion how do I proceed legally"),
    dict(id="KAN-S13", category="violence",
         url="https://www.kaanoon.com/44946/domestic-violence-and-demand-for-flat-in-delhi",
         text="I have completed six yrs of my marriage life, my marriage life has always been troubled, From the day of my marriage till date my husband keeps beating me because i kept my Stridhan with my parents for safety as he keeps threatening me for divorce . moreover he is demanding flat in delhi from parents, Also, in the month of august he while i was sleeping he tried to kill me by choking my throat and also by slapping hard on my ear he ruptured my eardrum. he is in govt job and i teach in private college. what am i suppose to do?"),
    dict(id="KAN-S14", category="other (dowry)",
         url="https://www.kaanoon.com/245194/dowry",
         text="I have taken 2.5lacs from my father in law just 1month before marriage for my house purchase in online bank transfer. Will it be held as dowry? And if so what is the punishment under Indian penal code."),
    dict(id="KAN-S16", category="custody",
         url="https://www.kaanoon.com/249974/child-custody",
         text="I want to live separately from my husband with my 2.5 yrs old son. I am working woman, there are lots of misunderstanding between us. I never marriage again so divorce is not essential. He will allow me leave his home permanently but he not allow to keep my son with me. I can escape my son with me but my husband will try his level best to get the son's custody. What are the legal steps to protect myself from him as he will be dangerous if I escape from his home with my son.",
         note="MOVED FROM EVAL 2026-11-27: shares two word 8-grams with the training corpus ('i want to live separately from my husband' and 'want to live separately from my husband with', 9 train records) — generic template boilerplate, so it cannot serve as an unseen-phrasing eval item. Retained for pattern study only; study-vs-train overlap is not gated."),
    dict(id="KAN-S15", category="maintenance",
         url="https://www.kaanoon.com/2354/legal-status-of-hindu-wife-of-hindu-husband",
         text="A hindu mother left her hindu husband and children and filed case in the court for maintenance from her husband while living separately. [...] 3. judicial separation and 4. divorce In which of these above 4 cases she remains as legally wedded wife? Which section of which act says about separation?"),
]


def build_eval_record(spec):
    issues = {k: spec["issues"].get(k, "uncertain") for k in ISSUES}
    facts = {k: spec["facts"].get(k, "unknown") for k in FACTS}
    return {"id": spec["id"], "source_url": spec["url"],
            "category": spec["category"], "lang": "en",
            "text": spec["text"], "issues": issues, "facts": facts,
            "enums": spec["enums"],
            "expected_sections": spec["expected"],
            "annotation_notes": spec["notes"]}


def validate_expected(records):
    """Re-derive kept_ids with the live Stage-2 code and compare to hand lists."""
    from src.laya_v7_graph import evaluate_stage2_v7
    bad = []
    for rec in records:
        issues = {k: {"intent": v} for k, v in rec["issues"].items()}
        facts = dict(rec["facts"])
        # Pipeline equivalence: the graph consumes claimant_sex as
        # "male"/"female"/"unknown" (src/laya_v7_evidence.py), while the
        # record stores the schema enum "M"/"F"/"U" (train format). Map here.
        facts["claimant_sex"] = {"M": "male", "F": "female",
                                 "U": "unknown"}[rec["enums"]["claimant_sex"]]
        facts["claimant_role"] = rec["enums"]["claimant_role"]
        facts["negated_issues"] = {k for k, v in rec["issues"].items()
                                   if v == "denied"}
        out = evaluate_stage2_v7(issues, facts, custody_vocab="v3_bundled")
        got = out["kept_ids"]
        want = rec["expected_sections"]
        if got != want:
            bad.append((rec["id"], want, got, out.get("gated_out")))
    return bad


def main():
    out_dir = ROOT / "data" / "kaanoon_eval"
    eval_recs = [build_eval_record(s) for s in EVAL]
    # Schema completeness: every record carries all 11 issues + 28 facts.
    for rec in eval_recs:
        assert list(rec["issues"]) == ISSUES, rec["id"]
        assert list(rec["facts"]) == FACTS, rec["id"]
        assert rec["expected_sections"] == sorted(set(rec["expected_sections"])) \
            or set(rec["expected_sections"]), rec["id"]
    eval_path = out_dir / "heldout.jsonl"
    eval_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                 for r in eval_recs), encoding="utf-8")
    study_recs = [{"id": s["id"], "source_url": s["url"],
                   "category": s["category"], "text": s["text"],
                   "note": s.get("note", "STUDY ONLY — pattern extraction; "
                                 "never eval/training")}
                  for s in STUDY]
    study_path = out_dir / "study_sample.jsonl"
    study_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                  for r in study_recs), encoding="utf-8")
    bad = validate_expected(eval_recs)
    from collections import Counter
    print(f"eval={len(eval_recs)} study={len(study_recs)} "
          f"total={len(eval_recs) + len(study_recs)}")
    print("eval categories:", dict(Counter(r['category'] for r in eval_recs)))
    print("study categories:", dict(Counter(r['category'] for r in study_recs)))
    print(f"wrote {eval_path} ({len(eval_recs)} records)")
    print(f"wrote {study_path} ({len(study_recs)} records)")
    if bad:
        print(f"VALIDATION FAILED: {len(bad)} expected_sections mismatch(es):")
        for rid, want, got, gated in bad:
            print(f"  {rid}: hand={want} code={got} gated={gated}")
        return 1
    print("VALIDATION PASSED: all expected_sections match live "
          "evaluate_stage2_v7 (v3_bundled) exactly, in order.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
