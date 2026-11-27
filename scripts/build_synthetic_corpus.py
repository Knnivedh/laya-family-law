#!/usr/bin/env python3
"""LAYA v7.1 V71-P1-2 — clean synthetic + hard-negative corpus builder.

Generates a deterministic, seeded 5,000-example bilingual (EN + KN + Kanglish)
training/validation corpus PURELY from statutory grammars, paraphrase templates
and hard-negative perturbations. NEVER from test banks: no test-bank, ground-truth
or fixture question text is read, copied or paraphrased by this builder. Every
sentence below was written fresh from the statutory concepts (BNSS s.144 / s.144(3)
/ s.146, HMA ss.9/13/13B/24/25/26/27, PWDVA ss.17/18/19/20/22, GWA 1890, HMGA
s.6, BNS s.316, Births & Deaths Act 1969) and the hard-negative clusters in
docs/10x_plane.md §1.2 (V71-P1-2). Leakage is verified afterwards by
scripts/check_ngram_leakage.py (0 word 8-grams, cosine < 0.90).

Record schema (contract C2, docs/10x_swarm_state.md):
    {id, lang, text,
     issues: {issue: intent},          # all 11 issues, 4-class intent
     facts:  {fact: state},            # all 28 facts, 4-state
     enums:  {claimant_sex, claimant_role, modality_time},
     spans:  [{key, kind, text, start, end}],
     meta:   {cluster, blocks, split}}  # extra bookkeeping; Lane 03 may ignore

ISSUES (11): maintenance, custody, residence, divorce, stridhan, joint_property,
    violence, dv_compensation, restitution, birth_certificate, procedure.
    Intent: requested | incidental | denied | uncertain.
    - requested: the user asks for that remedy now.
    - incidental: mentioned as background/context, not asked now
      (e.g. "my divorce case is pending" while asking for maintenance).
    - denied: explicitly not wanted / negated ("I do not want a divorce").
    - uncertain: not mentioned / cannot be determined from the text.
    OOS (out-of-scope) records use "uncertain" for every issue and carry the
    signal in facts.in_scope = "denied".

FACTS (28): divorce_asked, mutual_consent, judicial_separation_only,
    restitution_asked, proceeding_pending_hma, being_filed, decree, money_fact,
    lump_sum_settlement, existing_order_enforcement, interim_asked,
    custody_claim, child_fact, minor_child, child_maintenance_only,
    school_fees_fact, child_safety_risk, residence_claim,
    coercive_eviction_or_lockout, explicit_residence_order_only, violence,
    dv_injury_comp_asked, stridhan_claim, stridhan_sold_or_mortgaged,
    demand_made, joint_property_claim, birth_cert_asked, in_scope.
    State: supported | denied | unknown | conflicting.
    Mapping notes for Lane 03 / Lane 01 (evidence.py names in brackets):
    - interim_asked == evidence interim_only_asked (interim relief while an
      HMA proceeding is pending); interim_asked "supported" also implies
      proceeding_pending_hma "supported" in these templates.
    - stridhan "safe in my own possession" is encoded as stridhan_claim
      "denied" (no claim), NOT as a separate fact.
    - urgent_safety_risk (graph dead key) is NOT a corpus fact; it is
      derivable as violence "supported" OR child_safety_risk "supported".
    - domestic_relationship, forum_question_asked, procedure_how_to_asked,
      first_demand_never_made, no_dispute_empty are NOT corpus facts; the
      procedure issue + in_scope + role/sex enums carry that signal.
    - school_fees_fact covers "school fees / tuition" mentions; a record may
      mention school fees only as the reason for a child-only maintenance ask.

ENUMS:
    claimant_sex:  "F" | "M" | "U"  (U = unknown/unstated)
    claimant_role: "spouse" | "parent" | "child" | "other"
                   ("other" also covers genuinely unstated role; "child" is
                   used only when the claimant speaks as the child.)
    modality_time: "present" | "past" | "future" | "hypothetical" | "quoted"

Span markup inside templates: [[key:phrase]] where key is a fact or issue
name; the builder strips the markup and records exact char offsets.

Languages: "en" (English), "kn" (Kannada script), "kn_roman" (Kanglish:
Romanised Kannada, often code-mixed with English legal words).
Kannada templates are plain, everyday Kannada written for this corpus; they
have NOT had a native-speaker audit yet — P2.1 should audit them before any
training run treats the KN split as gold (see lane status file).

Determinism: random.Random(SEED); same seed + same code => byte-identical
JSONL. No network, no GPU, no torch, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

SEED = 7102
N_TOTAL = 5000
N_VAL = 500

ISSUES = [
    "maintenance", "custody", "residence", "divorce", "stridhan",
    "joint_property", "violence", "dv_compensation", "restitution",
    "birth_certificate", "procedure",
]
FACTS = [
    "divorce_asked", "mutual_consent", "judicial_separation_only",
    "restitution_asked", "proceeding_pending_hma", "being_filed", "decree",
    "money_fact", "lump_sum_settlement", "existing_order_enforcement",
    "interim_asked", "custody_claim", "child_fact", "minor_child",
    "child_maintenance_only", "school_fees_fact", "child_safety_risk",
    "residence_claim", "coercive_eviction_or_lockout",
    "explicit_residence_order_only", "violence", "dv_injury_comp_asked",
    "stridhan_claim", "stridhan_sold_or_mortgaged", "demand_made",
    "joint_property_claim", "birth_cert_asked", "in_scope",
]
INTENTS = ("requested", "incidental", "denied", "uncertain")
FACT_STATES = ("supported", "denied", "unknown", "conflicting")

# ---------------------------------------------------------------- slots
# {child_age} digit, {child_word} son/daughter/child, {amount} monthly income
# phrase, {duration} "for X" phrase, {gold_value} stridhan value phrase.
SLOTS = {
    "en": {
        "child_age": ["3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
                    "13", "14", "15", "16"],
        "child_word": ["daughter", "son", "child"],
        "amount": ["twenty thousand rupees", "forty thousand rupees",
                   "fifty thousand rupees", "thirty thousand rupees",
                   "sixty thousand rupees", "twenty-five thousand rupees"],
        "duration": ["two years", "three years", "four years", "five years",
                     "six months", "one year", "eight months", "two months",
                     "nine months"],
        "gold_value": ["five lakh rupees", "two lakh rupees",
                       "three lakh rupees", "one lakh rupees",
                       "four lakh rupees"],
    },
    "kn": {
        "child_age": ["3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
                    "13", "14", "15", "16"],
        "child_word": ["ಮಗಳು", "ಮಗ", "ಮಗು"],
        "amount": ["ಇಪ್ಪತ್ತು ಸಾವಿರ ರೂಪಾಯಿ", "ನಲವತ್ತು ಸಾವಿರ ರೂಪಾಯಿ",
                   "ಐವತ್ತು ಸಾವಿರ ರೂಪಾಯಿ", "ಮೂವತ್ತು ಸಾವಿರ ರೂಪಾಯಿ",
                   "ಅರವತ್ತು ಸಾವಿರ ರೂಪಾಯಿ", "ಇಪ್ಪತ್ತೈದು ಸಾವಿರ ರೂಪಾಯಿ"],
        "duration": ["ಎರಡು ವರ್ಷಗಳಿಂದ", "ಮೂರು ವರ್ಷಗಳಿಂದ",
                     "ನಾಲ್ಕು ವರ್ಷಗಳಿಂದ", "ಐದು ವರ್ಷಗಳಿಂದ",
                     "ಆರು ತಿಂಗಳಿಂದ", "ಒಂದು ವರ್ಷದಿಂದ",
                     "ಎಂಟು ತಿಂಗಳಿಂದ", "ಎರಡು ತಿಂಗಳಿಂದ"],
        "gold_value": ["ಐದು ಲಕ್ಷ ರೂಪಾಯಿ", "ಎರಡು ಲಕ್ಷ ರೂಪಾಯಿ",
                       "ಮೂರು ಲಕ್ಷ ರೂಪಾಯಿ", "ಒಂದು ಲಕ್ಷ ರೂಪಾಯಿ",
                       "ನಾಲ್ಕು ಲಕ್ಷ ರೂಪಾಯಿ"],
    },
    "kn_roman": {
        "child_age": ["3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
                    "13", "14", "15", "16"],
        "child_word": ["magalu", "maga", "magu"],
        "amount": ["twenty thousand rupees", "forty thousand rupees",
                   "fifty thousand rupees", "thirty thousand rupees",
                   "sixty thousand rupees", "twenty-five thousand rupees"],
        "duration": ["two years inda", "three years inda", "four years inda",
                     "five years inda", "six months inda", "one year inda",
                     "eight months inda", "two months inda"],
        "gold_value": ["five lakh rupees", "two lakh rupees",
                       "three lakh rupees", "one lakh rupees",
                       "four lakh rupees"],
    },
}

# ---------------------------------------------------------------- blocks
# B(id, cluster, en=[...], kn=[...], ro=[...], issues={...}, facts={...},
#   enums={...})
# cluster: core | combo | hn_a | hn_b | hn_c | hn_d | hn_e | hn_f | neg | conflict


def B(bid, cluster, en, kn, ro, issues=None, facts=None, enums=None):
    return {"id": bid, "cluster": cluster, "en": en, "kn": kn, "ro": ro,
            "issues": issues or {}, "facts": facts or {},
            "enums": enums or {}}


F = "F"
M = "M"
SPOUSE = {"claimant_sex": F, "claimant_role": "spouse"}
SPOUSE_M = {"claimant_sex": M, "claimant_role": "spouse"}

BLOCKS = {}
def _reg(b):
    BLOCKS[b["id"]] = b
    return b

# --- core: maintenance -------------------------------------------------
_reg(B("maint_wife", "core",
    en=["My husband [[money_fact:has stopped giving me any money]] to run the home. I need [[maintenance:maintenance]] from him.",
        "My husband earns {amount} a month but [[money_fact:sends me nothing]] for food and rent."],
    kn=["ನನ್ನ ಗಂಡ [[money_fact:ಮನೆಗೆ ಹಣ ಕೊಡುತ್ತಿಲ್ಲ]]. ನನಗೆ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು.",
        "ನನ್ನ ಗಂಡ ತಿಂಗಳಿಗೆ {amount} ಸಂಪಾದಿಸುತ್ತಾನೆ, ಆದರೆ [[money_fact:ನನಗೆ ಏನೂ ಕೊಡುವುದಿಲ್ಲ]]."],
    ro=["Nanna ganda [[money_fact:mane nadisalu hana koduvudannu nillisidanu]]. Nanage [[maintenance:jeevanamsha]] beku.",
        "Nanna ganda tingalige {amount} sampadistane, adare [[money_fact:nanage enu koduvudilla]]."],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_child_only", "core",
    en=["I want [[maintenance:maintenance]] only for my {child_age}-year-old {child_word}, for [[school_fees_fact:school fees]] and food.",
        "My husband gives nothing for our {child_word}. I need money only for the [[school_fees_fact:child's school fees]]."],
    kn=["ನನಗೆ {child_age} ವರ್ಷದ {child_word}ಗಾಗಿ ಮಾತ್ರ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು, [[school_fees_fact:ಶಾಲಾ ಶುಲ್ಕ]] ಮತ್ತು ಊಟಕ್ಕಾಗಿ.",
        "ನನ್ನ ಗಂಡ ನಮ್ಮ {child_word}ಗೆ ಏನೂ ಕೊಡುವುದಿಲ್ಲ. [[school_fees_fact:ಮಗುವಿನ ಶಾಲಾ ಶುಲ್ಕ]]ಕ್ಕಾಗಿ ಮಾತ್ರ ಹಣ ಬೇಕು."],
    ro=["Nanage {child_age} varshada {child_word}gagi matra [[maintenance:jeevanamsha]] beku, [[school_fees_fact:shala shulka]] mattu utakkagi.",
        "Nanna ganda namma {child_word}ge enu koduvudilla. [[school_fees_fact:maguvina shala shulka]]kkagi matra hana beku."],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "child_maintenance_only": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "school_fees_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_lump_sum", "core",
    en=["I want a [[lump_sum_settlement:lump sum]] payment instead of monthly [[maintenance:maintenance]] from my husband.",
        "Can I ask for a [[lump_sum_settlement:one-time lump sum settlement]] rather than monthly support?"],
    kn=["ತಿಂಗಳ [[maintenance:ಜೀವನಾಂಶ]] ಬದಲು ನನಗೆ [[lump_sum_settlement:ಒಟ್ಟು ಹಣ]] ಬೇಕು.",
        "ತಿಂಗಳ ಬೆಂಬಲದ ಬದಲು [[lump_sum_settlement:ಒಂದೇ ಬಾರಿಗೆ ಒಟ್ಟು ಹಣ]] ಕೇಳಬಹುದೇ?"],
    ro=["Tingala [[maintenance:jeevanamsha]] badalu nanage [[lump_sum_settlement:ottu hana]] beku.",
        "Tingala bembalada badalu [[lump_sum_settlement:onde barige ottu hana]] kelabahude?"],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "lump_sum_settlement": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_interim_pending", "core",
    en=["My divorce case is pending in court. I need [[interim_asked:interim maintenance]] until the case ends.",
        "While our divorce case is going on, I want [[interim_asked:maintenance for now]], till the final order."],
    kn=["ನಮ್ಮ ವಿಚ್ಛೇದನ ಕೇಸ್ ಕೋರ್ಟ್‌ನಲ್ಲಿ ನಡೆಯುತ್ತಿದೆ. ಕೇಸ್ ಮುಗಿಯುವವರೆಗೆ ನನಗೆ [[interim_asked:ಮಧ್ಯಂತರ ಜೀವನಾಂಶ]] ಬೇಕು.",
        "ವಿಚ್ಛೇದನ ಕೇಸ್ ನಡೆಯುವಾಗ ನನಗೆ [[interim_asked:ಈಗ ಜೀವನಾಂಶ]] ಬೇಕು."],
    ro=["Namma divorce case court nalli nadeyuttide. Case mugiyuvarage nanage [[interim_asked:madhyantara jeevanamsha]] beku.",
        "Divorce case nadeyuvaga nanage [[interim_asked:ega jeevanamsha]] beku."],
    issues={"maintenance": "requested", "divorce": "incidental"},
    facts={"money_fact": "supported", "interim_asked": "supported",
           "proceeding_pending_hma": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_post_decree", "core",
    en=["Our divorce is already decided by the court. I still need monthly [[maintenance:maintenance]] from my ex-husband.",
        "The court gave the divorce decree last year. I want [[maintenance:maintenance]] after the decree."],
    kn=["ನಮ್ಮ ವಿಚ್ಛೇದನವನ್ನು ಕೋರ್ಟ್ ಈಗಾಗಲೇ ತೀರ್ಮಾನಿಸಿದೆ. ನನ್ನ ಮಾಜಿ ಗಂಡನಿಂದ ಇನ್ನೂ ತಿಂಗಳ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು.",
        "ಕೋರ್ಟ್ ಕಳೆದ ವರ್ಷ ವಿಚ್ಛೇದನ ತೀರ್ಪು ನೀಡಿತು. ತೀರ್ಪಿನ ನಂತರ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು."],
    ro=["Namma divorce court egagale teermaniside. Nanna maji gandana inda innu tingala [[maintenance:jeevanamsha]] beku.",
        "Court kaleda varsha divorce teerpu needitu. Teerpina nantara [[maintenance:jeevanamsha]] beku."],
    issues={"maintenance": "requested", "divorce": "incidental"},
    facts={"money_fact": "supported", "decree": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_arrears", "hn_e",
    en=["The court already ordered my husband to pay [[maintenance:maintenance]], but he has not paid for {duration}. I want the unpaid amount.",
        "My husband was ordered to pay monthly support, and he has missed payments for {duration}. How do I recover the arrears?"],
    kn=["ಕೋರ್ಟ್ ಈಗಾಗಲೇ ನನ್ನ ಗಂಡ ಜೀವನಾಂಶ ಕೊಡಬೇಕು ಎಂದು ಆದೇಶಿಸಿದೆ, ಆದರೆ ಅವನು {duration} ಕೊಟ್ಟಿಲ್ಲ. ಬಾಕಿ ಹಣ ಬೇಕು.",
        "ನನ್ನ ಗಂಡ ತಿಂಗಳ ಬೆಂಬಲ ಕೊಡಬೇಕು ಎಂದು ಆದೇಶವಿದೆ, {duration} ಕೊಟ್ಟಿಲ್ಲ. ಬಾಕಿ ಹಣವನ್ನು ಹೇಗೆ ಪಡೆಯುವುದು?"],
    ro=["Court egagale nanna ganda jeevanamsha kodabeku anta adeshiside, adare avanu {duration} kottilla. Baki hana beku.",
        "Nanna ganda tingala bembala kodabeku anta adeshavide, {duration} kottilla. Baki hanavannu hege padeyuvudu?"],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "existing_order_enforcement": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_vary", "hn_e",
    en=["My husband's salary has gone up since the maintenance order. I want the [[maintenance:maintenance]] amount increased.",
        "The maintenance was fixed two years ago, but my husband now earns much more. Can the amount be revised upwards?"],
    kn=["ಜೀವನಾಂಶ ಆದೇಶವಾದ ನಂತರ ನನ್ನ ಗಂಡನ ಸಂಬಳ ಹೆಚ್ಚಾಗಿದೆ. [[maintenance:ಜೀವನಾಂಶ]] ಮೊತ್ತ ಹೆಚ್ಚಿಸಬೇಕು.",
        "ಜೀವನಾಂಶವನ್ನು ಎರಡು ವರ್ಷಗಳ ಹಿಂದೆ ನಿಗದಿಪಡಿಸಲಾಗಿತ್ತು, ಆದರೆ ನನ್ನ ಗಂಡ ಈಗ ಹೆಚ್ಚು ಸಂಪಾದಿಸುತ್ತಾನೆ. ಮೊತ್ತ ಹೆಚ್ಚಿಸಬಹುದೇ?"],
    ro=["Jeevanamsha adeshavada nantara nanna gandana sambala hechagide. [[maintenance:jeevanamsha]] motta hechisabeku.",
        "Jeevanamsha vannu eradu varshagala hinde nigadipadisalagittu, adare nanna ganda ega hechu sampadistane. Motta hechisabahude?"],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "existing_order_enforcement": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_elder_parent", "hn_e",
    en=["I am a 70-year-old mother. My son earns well but [[money_fact:gives me nothing]] for food and medicines. I need [[maintenance:maintenance]] from him.",
        "I am 68 years old and my son does not support me at all. Can a parent ask for [[maintenance:maintenance]] from a son?"],
    kn=["ನನಗೆ 70 ವರ್ಷ. ನನ್ನ ಮಗ ಚೆನ್ನಾಗಿ ಸಂಪಾದಿಸುತ್ತಾನೆ, ಆದರೆ [[money_fact:ಊಟ ಮತ್ತು ಔಷಧಿಗೆ ಏನೂ ಕೊಡುವುದಿಲ್ಲ]]. ಅವನಿಂದ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು.",
        "ನನಗೆ 68 ವರ್ಷ, ನನ್ನ ಮಗ ನನ್ನನ್ನು ನೋಡಿಕೊಳ್ಳುವುದೇ ಇಲ್ಲ. ತಂದೆ-ತಾಯಿ ಮಗನಿಂದ [[maintenance:ಜೀವನಾಂಶ]] ಕೇಳಬಹುದೇ?"],
    ro=["Nanage 70 varsha. Nanna maga chennagi sampadistane, adare [[money_fact:uta mattu aushadhige enu koduvudilla]]. Avaninda [[maintenance:jeevanamsha]] beku.",
        "Nanage 68 varsha, nanna maga nannannu nodikolluvude illa. Tande-tayi maganinda [[maintenance:jeevanamsha]] kelabahude?"],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "in_scope": "supported"},
    enums={"claimant_sex": F, "claimant_role": "parent"}))
_reg(B("maint_male_self", "hn_e",
    en=["I am the husband. My wife earns {amount} a month and [[money_fact:gives me nothing]] for my living costs. I need [[maintenance:maintenance]] for myself.",
        "I am a husband with no income, and my wife refuses to support me. Can I ask for [[maintenance:maintenance]]?"],
    kn=["ನಾನು ಗಂಡ. ನನ್ನ ಹೆಂಡತಿ ತಿಂಗಳಿಗೆ {amount} ಸಂಪಾದಿಸುತ್ತಾಳೆ, ಆದರೆ [[money_fact:ನನ್ನ ಜೀವನ ವೆಚ್ಚಕ್ಕೆ ಏನೂ ಕೊಡುವುದಿಲ್ಲ]]. ನನಗೆ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು.",
        "ನನಗೆ ಆದಾಯವಿಲ್ಲದ ಗಂಡ, ನನ್ನ ಹೆಂಡತಿ ನನ್ನನ್ನು ನೋಡಿಕೊಳ್ಳಲು ನಿರಾಕರಿಸುತ್ತಾಳೆ. ನಾನು [[maintenance:ಜೀವನಾಂಶ]] ಕೇಳಬಹುದೇ?"],
    ro=["Nanu ganda. Nanna hendati tingalige {amount} sampadistale, adare [[money_fact:nanna jeevana vechchakke enu koduvudilla]]. Nanage [[maintenance:jeevanamsha]] beku.",
        "Nanage adayavilla ganda, nanna hendati nannannu nodikollalu nirakaristale. Nanu [[maintenance:jeevanamsha]] kelabahude?"],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE_M)))
_reg(B("maint_father_child_only", "hn_e",
    en=["I am the father. I want money only for my {child_age}-year-old {child_word}'s [[school_fees_fact:school fees]] and books, nothing for myself.",
        "I am a father asking only for my {child_word}'s expenses. My wife gives nothing for the {child_word}'s schooling."],
    kn=["ನಾನು ತಂದೆ. ನನಗೆ {child_age} ವರ್ಷದ {child_word}ನ [[school_fees_fact:ಶಾಲಾ ಶುಲ್ಕ]] ಮತ್ತು ಪುಸ್ತಕಗಳಿಗಾಗಿ ಮಾತ್ರ ಹಣ ಬೇಕು, ನನಗಾಗಿ ಏನೂ ಬೇಡ.",
        "ನಾನು ತಂದೆ, ನನ್ನ {child_word}ನ ಖರ್ಚಿಗಾಗಿ ಮಾತ್ರ ಕೇಳುತ್ತಿದ್ದೇನೆ. ನನ್ನ ಹೆಂಡತಿ {child_word}ನ ಶಾಲೆಗೆ ಏನೂ ಕೊಡುವುದಿಲ್ಲ."],
    ro=["Nanu tande. Nanage {child_age} varshada {child_word}na [[school_fees_fact:shala shulka]] mattu pustakagaligagi matra hana beku, nanagagi enu beda.",
        "Nanu tande, nanna {child_word}na kharchigagi matra keluttiddene. Nanna hendati {child_word}na shalege enu koduvudilla."],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "child_maintenance_only": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "school_fees_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE_M)))
_reg(B("maint_child_self", "core",
    en=["I am {child_age} years old. My father [[money_fact:does not pay for my school]] or my food. Can I ask for support for myself?",
        "I am a {child_age}-year-old {child_word}, and my father gives nothing for my studies. I need [[maintenance:maintenance]] for my education."],
    kn=["ನನಗೆ {child_age} ವರ್ಷ. ನನ್ನ ತಂದೆ [[money_fact:ನನ್ನ ಶಾಲೆಗೆ ಅಥವಾ ಊಟಕ್ಕೆ ಹಣ ಕೊಡುವುದಿಲ್ಲ]]. ನನಗಾಗಿ ಬೆಂಬಲ ಕೇಳಬಹುದೇ?",
        "ನಾನು {child_age} ವರ್ಷದ {child_word}, ನನ್ನ ತಂದೆ ನನ್ನ ಓದಿಗೆ ಏನೂ ಕೊಡುವುದಿಲ್ಲ. ನನ್ನ ಶಿಕ್ಷಣಕ್ಕಾಗಿ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು."],
    ro=["Nanage {child_age} varsha. Nanna tande [[money_fact:nanna shalege athava utakke hana koduvudilla]]. Nanagagi bembala kelabahude?",
        "Nanu {child_age} varshada {child_word}, nanna tande nanna odige enu koduvudilla. Nanna shikshanakagi [[maintenance:jeevanamsha]] beku."],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "child_maintenance_only": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "school_fees_fact": "supported", "in_scope": "supported"},
    enums={"claimant_sex": "U", "claimant_role": "child"}))

# --- core: custody ------------------------------------------------------
_reg(B("custody_mother", "core",
    en=["I want [[custody:custody]] of my {child_age}-year-old {child_word}. My {child_word} should live with me.",
        "Who will get my {child_age}-year-old {child_word}? I am asking that my {child_word} remain in my care."],
    kn=["ನನ್ನ {child_age} ವರ್ಷದ {child_word}ನ [[custody:ಪಾಲನೆ]] ನನಗೆ ಬೇಕು. ನನ್ನ {child_word} ನನ್ನ ಜೊತೆ ಇರಬೇಕು.",
        "ನನ್ನ {child_age} ವರ್ಷದ {child_word} ಯಾರಿಗೆ ಸಿಗುತ್ತಾರೆ? ನನ್ನ {child_word} ನನ್ನ ಆರೈಕೆಯಲ್ಲಿ ಇರಬೇಕು ಎಂದು ಕೇಳುತ್ತಿದ್ದೇನೆ."],
    ro=["Nanna {child_age} varshada {child_word}na [[custody:paalane]] nanage beku. Nanna {child_word} nanna jothe irabeku.",
        "Nanna {child_age} varshada {child_word} yarige siguttare? Nanna {child_word} nanna aaraikeyalli irabekendu keluttiddene."],
    issues={"custody": "requested"},
    facts={"custody_claim": "supported", "child_fact": "supported",
           "minor_child": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("custody_father", "core",
    en=["I am the father, and I want [[custody:custody]] of my {child_age}-year-old {child_word}.",
        "My wife left with our {child_word}. I want my {child_word} back with me, and I am asking for [[custody:custody]]."],
    kn=["ನಾನು ತಂದೆ, ನನ್ನ {child_age} ವರ್ಷದ {child_word}ನ [[custody:ಪಾಲನೆ]] ನನಗೆ ಬೇಕು.",
        "ನನ್ನ ಹೆಂಡತಿ ನಮ್ಮ {child_word}ನೊಂದಿಗೆ ಹೋಗಿದ್ದಾಳೆ. ನನ್ನ {child_word} ನನ್ನ ಬಳಿ ಬೇಕು, [[custody:ಪಾಲನೆ]] ಕೇಳುತ್ತಿದ್ದೇನೆ."],
    ro=["Nanu tande, nanna {child_age} varshada {child_word}na [[custody:paalane]] nanage beku.",
        "Nanna hendati namma {child_word}nodige hogiddale. Nanna {child_word} nanna bali beku, [[custody:paalane]] keluttiddene."],
    issues={"custody": "requested"},
    facts={"custody_claim": "supported", "child_fact": "supported",
           "minor_child": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE_M)))

# --- core: residence / violence -----------------------------------------
_reg(B("residence_thrown_out", "core",
    en=["My husband is [[residence_claim:throwing me out of the house]]. I have nowhere to go and I want to stay in my home.",
        "My in-laws are forcing me to leave the house. I want the right to keep living in our home."],
    kn=["ನನ್ನ ಗಂಡ [[residence_claim:ನನ್ನನ್ನು ಮನೆಯಿಂದ ಹೊರಹಾಕುತ್ತಿದ್ದಾನೆ]]. ನನಗೆ ಹೋಗಲು ಎಲ್ಲೂ ಇಲ್ಲ, ನನ್ನ ಮನೆಯಲ್ಲೇ ಇರಬೇಕು.",
        "ನನ್ನ ಅತ್ತೆ-ಮಾವ ನನ್ನನ್ನು ಮನೆ ಬಿಟ್ಟು ಹೋಗುವಂತೆ ಒತ್ತಾಯಿಸುತ್ತಿದ್ದಾರೆ. ನಮ್ಮ ಮನೆಯಲ್ಲೇ ಇರುವ ಹಕ್ಕು ಬೇಕು."],
    ro=["Nanna ganda [[residence_claim:nannannu maneyinda horahakuttiddane]]. Nanage hogalu ellu illa, nanna maneyalle irabeku.",
        "Nanna atte-mava nannannu mane bittu hoguvante ottayisuttiddare. Namma maneyalle iruva hakku beku."],
    issues={"residence": "requested"},
    facts={"residence_claim": "supported",
           "coercive_eviction_or_lockout": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("residence_live_in_house", "core",
    en=["I want to keep living in our shared house with my {child_word}. This is the home we have lived in for years.",
        "I only want to continue staying in the house where I have lived since my marriage."],
    kn=["ನನ್ನ {child_word}ನೊಂದಿಗೆ ನಮ್ಮ ಮನೆಯಲ್ಲೇ ಇರಲು ಬಯಸುತ್ತೇನೆ. ಇದು ನಾವು ವರ್ಷಗಳಿಂದ ವಾಸಿಸುತ್ತಿರುವ ಮನೆ.",
        "ಮದುವೆಯಾದಾಗಿನಿಂದ ವಾಸಿಸುತ್ತಿರುವ ಮನೆಯಲ್ಲೇ ಮುಂದುವರಿಯಲು ಬಯಸುತ್ತೇನೆ."],
    ro=["Nanna {child_word}nodige namma maneyalle iralu bayasuttene. Idu navu varshagalinda vaasisuttiruva mane.",
        "Maduveadaginda vaasisuttiruva maneyalle munduvariyalu bayasuttene."],
    issues={"residence": "requested"},
    facts={"residence_claim": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("residence_explicit_only", "hn_b",
    en=["I only want an order that I can live in our shared house. Nobody has hit me and nobody has locked me out.",
        "I am not asking for anything else. I just want a court order saying I may stay in the house I live in."],
    kn=["ನಮ್ಮ ಮನೆಯಲ್ಲಿ ನಾನು ಇರಬಹುದು ಎಂಬ ಆದೇಶ ಮಾತ್ರ ಬೇಕು. ಯಾರೂ ನನ್ನನ್ನು ಹೊಡೆದಿಲ್ಲ, ಯಾರೂ ನನ್ನನ್ನು ಹೊರಗೆ ಹಾಕಿಲ್ಲ.",
        "ನನಗೆ ಬೇರೆ ಏನೂ ಬೇಡ. ನಾನು ವಾಸಿಸುವ ಮನೆಯಲ್ಲಿ ಇರಬಹುದು ಎಂಬ ಕೋರ್ಟ್ ಆದೇಶ ಮಾತ್ರ ಬೇಕು."],
    ro=["Namma maneyalli nanu irabahudu emba adesha matra beku. Yaru nannannu hodedilla, yaru nannannu horage hakilla.",
        "Nanage bere enu beda. Nanu vaasisuva maneyalli irabahudu emba court adesha matra beku."],
    issues={"residence": "requested"},
    facts={"residence_claim": "supported",
           "explicit_residence_order_only": "supported",
           "coercive_eviction_or_lockout": "denied",
           "violence": "denied", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("lockout", "hn_b",
    en=["My husband [[coercive_eviction_or_lockout:locked me out of the house]] and threw my things outside. I cannot enter my own home.",
        "When I came back, the door was locked and my husband refused to let me in. I need to get back into the house."],
    kn=["ನನ್ನ ಗಂಡ [[coercive_eviction_or_lockout:ನನ್ನನ್ನು ಮನೆಯಿಂದ ಹೊರಗೆ ಬೀಗ ಹಾಕಿದನು]] ಮತ್ತು ನನ್ನ ವಸ್ತುಗಳನ್ನು ಹೊರಗೆ ಎಸೆದನು. ನಾನು ನನ್ನ ಮನೆಗೆ ಪ್ರವೇಶಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ.",
        "ನಾನು ಹಿಂತಿರುಗಿದಾಗ ಬಾಗಿಲು ಬೀಗ ಹಾಕಿತ್ತು, ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ಒಳಗೆ ಬಿಡಲಿಲ್ಲ. ಮನೆಗೆ ಮರಳಬೇಕು."],
    ro=["Nanna ganda [[coercive_eviction_or_lockout:nannannu maneyinda horage beega hakidanu]] mattu nanna vastugalannu horage esedanu. Nanu nanna manege praveshisalu sadhyavilla.",
        "Nanu hintirugidaga bagilu beega hakittu, nanna ganda nannannu olage bidalilla. Manege maralabeku."],
    issues={"residence": "requested"},
    facts={"residence_claim": "supported",
           "coercive_eviction_or_lockout": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("violence_beats", "core",
    en=["My husband [[violence:beats me]] at home. I am afraid for my safety and I need protection.",
        "My husband hits me whenever he drinks. I need help to stop the [[violence:violence]] at home."],
    kn=["ನನ್ನ ಗಂಡ ಮನೆಯಲ್ಲಿ [[violence:ನನ್ನನ್ನು ಹೊಡೆಯುತ್ತಾನೆ]]. ನನ್ನ ಸುರಕ್ಷತೆಗಾಗಿ ನನಗೆ ರಕ್ಷಣೆ ಬೇಕು.",
        "ನನ್ನ ಗಂಡ ಕುಡಿದಾಗಲೆಲ್ಲ ನನ್ನನ್ನು ಹೊಡೆಯುತ್ತಾನೆ. ಮನೆಯಲ್ಲಿ [[violence:ಹಿಂಸೆ]] ನಿಲ್ಲಿಸಲು ಸಹಾಯ ಬೇಕು."],
    ro=["Nanna ganda maneyalli [[violence:nannannu hodeyuttane]]. Nanna surakshategagi nanage rakshane beku.",
        "Nanna ganda kudidagale nannannu hodeyuttane. Maneyalli [[violence:himse]] nillisalu sahaya beku."],
    issues={"violence": "requested"},
    facts={"violence": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("violence_threats", "core",
    en=["My husband [[violence:says he will kill me]] if I tell anyone about it. I live in fear every day.",
        "My in-laws abuse me with bad words and threaten to throw me out. I need protection from this harassment."],
    kn=["ನಾನು ಯಾರಿಗಾದರೂ ಹೇಳಿದರೆ ನನ್ನ ಗಂಡ [[violence:ನನ್ನ ಪ್ರಾಣ ತೆಗೆಯುತ್ತೇನೆ ಎಂದು ಹೇಳುತ್ತಾನೆ]]. ಪ್ರತಿದಿನ ಭಯದಲ್ಲಿ ಬದುಕುತ್ತಿದ್ದೇನೆ.",
        "ನನ್ನ ಅತ್ತೆ-ಮಾವ ಕೆಟ್ಟ ಮಾತುಗಳಿಂದ ನನ್ನನ್ನು ನಿಂದಿಸುತ್ತಾರೆ ಮತ್ತು ಹೊರಹಾಕುವುದಾಗಿ ಬೆದರಿಸುತ್ತಾರೆ. ಈ ಕಿರುಕುಳದಿಂದ ರಕ್ಷಣೆ ಬೇಕು."],
    ro=["Nanu yarigadaroo helidare nanna ganda [[violence:nanna prana tegeyuttene anta heluttane]]. Pratidina bhayadalli badukuttiddene.",
        "Nanna atte-mava ketta matugalinda nannannu nindisuttare mattu horahakuvudagi bedarisuttare. Ee kirukula inda rakshane beku."],
    issues={"violence": "requested"},
    facts={"violence": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("violence_dv_comp", "hn_b",
    en=["My husband beat me badly and I had to go to hospital. I want [[dv_compensation:compensation for my injuries]] and medical costs.",
        "I was injured by my husband's beating and spent money on treatment. I want the court to order payment for my injuries."],
    kn=["ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ತೀವ್ರವಾಗಿ ಹೊಡೆದನು, ನಾನು ಆಸ್ಪತ್ರೆಗೆ ಹೋಗಬೇಕಾಯಿತು. ನನ್ನ ಗಾಯಗಳು ಮತ್ತು ಚಿಕಿತ್ಸೆಗಾಗಿ [[dv_compensation:ಪರಿಹಾರ]] ಬೇಕು.",
        "ನನ್ನ ಗಂಡನ ಹೊಡೆತದಿಂದ ಗಾಯಗೊಂಡೆ, ಚಿಕಿತ್ಸೆಗಾಗಿ ಹಣ ಖರ್ಚು ಮಾಡಿದೆ. ನನ್ನ ಗಾಯಗಳಿಗಾಗಿ ಹಣ ನೀಡುವಂತೆ ಕೋರ್ಟ್ ಆದೇಶಿಸಬೇಕು."],
    ro=["Nanna ganda nannannu teevravagi hodedanu, nanu aspatrege hogabekayitu. Nanna gayagalu mattu chikitsegagi [[dv_compensation:parihara]] beku.",
        "Nanna gandana hodetinda gayagondedu, chikitsegagi hana kharchu madide. Nanna gayagaligagi hana needuvante court adeshisabeku."],
    issues={"violence": "requested", "dv_compensation": "requested"},
    facts={"violence": "supported", "dv_injury_comp_asked": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("violence_child_risk", "core",
    en=["My husband drinks and beats our {child_word} too. I fear for my {child_word}'s safety at home.",
        "My husband is violent at home and my {child_age}-year-old {child_word} is not safe with him."],
    kn=["ನನ್ನ ಗಂಡ ಕುಡಿದು ನಮ್ಮ {child_word}ನನ್ನೂ ಹೊಡೆಯುತ್ತಾನೆ. ಮನೆಯಲ್ಲಿ ನನ್ನ {child_word}ನ ಸುರಕ್ಷತೆಯ ಬಗ್ಗೆ ಭಯವಿದೆ.",
        "ನನ್ನ ಗಂಡ ಮನೆಯಲ್ಲಿ ಹಿಂಸಾತ್ಮಕವಾಗಿ ವರ್ತಿಸುತ್ತಾನೆ, ನನ್ನ {child_age} ವರ್ಷದ {child_word} ಅವನ ಜೊತೆ ಸುರಕ್ಷಿತವಾಗಿಲ್ಲ."],
    ro=["Nanna ganda kudidu namma {child_word}nannu hodeyuttane. Maneyalli nanna {child_word}na surakshateya bagge bhayavide.",
        "Nanna ganda maneyalli himsatmakavagi vartistane, nanna {child_age} varshada {child_word} avana jothe surakshitavagilla."],
    issues={"violence": "requested"},
    facts={"violence": "supported", "child_safety_risk": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- core: divorce / restitution / judicial separation -------------------
_reg(B("divorce_want", "core",
    en=["My marriage has broken down completely. I want a [[divorce:divorce]] from my husband.",
        "I no longer want to stay married. I want to end my marriage legally through [[divorce:divorce]]."],
    kn=["ನನ್ನ ಮದುವೆ ಸಂಪೂರ್ಣವಾಗಿ ಮುರಿದುಬಿದ್ದಿದೆ. ನನ್ನ ಗಂಡನಿಂದ [[divorce:ವಿಚ್ಛೇದನ]] ಬೇಕು.",
        "ನಾನು ಇನ್ನು ಮದುವೆಯಲ್ಲಿರಲು ಬಯಸುವುದಿಲ್ಲ. [[divorce:ವಿಚ್ಛೇದನ]] ಮೂಲಕ ನನ್ನ ಮದುವೆಯನ್ನು ಕಾನೂನುಬದ್ಧವಾಗಿ ಕೊನೆಗೊಳಿಸಲು ಬಯಸುತ್ತೇನೆ."],
    ro=["Nanna maduve sampurnavagi muridubiddide. Nanna gandana inda [[divorce:vichchhedana]] beku.",
        "Nanu innu maduveyalliralu bayasuvudilla. [[divorce:vichchhedana]] moolaka nanna maduveyannu kanunubaddhavagi konegolisalu bayasuttene."],
    issues={"divorce": "requested"},
    facts={"divorce_asked": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("divorce_mutual", "core",
    en=["My husband and I both agree to end the marriage. We want a [[divorce:divorce]] by [[mutual_consent:mutual consent]].",
        "We have decided together to separate. We want a [[mutual_consent:mutual consent divorce]]."],
    kn=["ನನ್ನ ಗಂಡ ಮತ್ತು ನಾನು ಮದುವೆ ಕೊನೆಗೊಳಿಸಲು ಒಪ್ಪಿದ್ದೇವೆ. [[mutual_consent:ಪರಸ್ಪರ ಒಪ್ಪಿಗೆ]]ಯಿಂದ [[divorce:ವಿಚ್ಛೇದನ]] ಬೇಕು.",
        "ನಾವು ಒಟ್ಟಿಗೆ ಬೇರೆಯಾಗಲು ನಿರ್ಧರಿಸಿದ್ದೇವೆ. [[mutual_consent:ಪರಸ್ಪರ ಒಪ್ಪಿಗೆಯ ವಿಚ್ಛೇದನ]] ಬೇಕು."],
    ro=["Nanna ganda mattu nanu maduve konegolisalu oppideve. [[mutual_consent:paraspara oppige]]yinda [[divorce:vichchhedana]] beku.",
        "Navu ottige bereyagalu nirdharisiddeve. [[mutual_consent:paraspara oppigeya vichchhedana]] beku."],
    issues={"divorce": "requested"},
    facts={"divorce_asked": "supported", "mutual_consent": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("divorce_pending", "hn_c",
    en=["My divorce case is already pending in the Family Court. I need money to live on while the case goes on.",
        "Our divorce petition is pending before the court. I want to know what support I can get during the case."],
    kn=["ನನ್ನ ವಿಚ್ಛೇದನ ಕೇಸ್ ಈಗಾಗಲೇ ಕೌಟುಂಬಿಕ ನ್ಯಾಯಾಲಯದಲ್ಲಿ ನಡೆಯುತ್ತಿದೆ. ಕೇಸ್ ನಡೆಯುವಾಗ ಬದುಕಲು ಹಣ ಬೇಕು.",
        "ನಮ್ಮ ವಿಚ್ಛೇದನ ಅರ್ಜಿ ಕೋರ್ಟ್‌ನಲ್ಲಿ ನಡೆಯುತ್ತಿದೆ. ಕೇಸ್ ನಡೆಯುವಾಗ ಏನು ಬೆಂಬಲ ಸಿಗುತ್ತದೆ ಎಂದು ತಿಳಿಯಬೇಕು."],
    ro=["Nanna divorce case egagale koutumbika nyayalayadalli nadeyuttide. Case nadeyuvaga badukalu hana beku.",
        "Namma divorce arji court nalli nadeyuttide. Case nadeyuvaga enu bembala siguttade anta tiliyabeku."],
    issues={"divorce": "incidental", "maintenance": "requested"},
    facts={"proceeding_pending_hma": "supported", "divorce_asked": "unknown",
           "money_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("divorce_being_filed", "hn_c",
    en=["I am [[being_filed:filing for divorce]] next week. I have already spoken to a lawyer about the petition.",
        "I will file a divorce petition next month. I want to know what I should do first."],
    kn=["ನಾನು ಮುಂದಿನ ವಾರ [[being_filed:ವಿಚ್ಛೇದನಕ್ಕಾಗಿ ಅರ್ಜಿ ಹಾಕುತ್ತಿದ್ದೇನೆ]]. ಅರ್ಜಿಯ ಬಗ್ಗೆ ವಕೀಲರೊಂದಿಗೆ ಈಗಾಗಲೇ ಮಾತನಾಡಿದ್ದೇನೆ.",
        "ನಾನು ಮುಂದಿನ ತಿಂಗಳು ವಿಚ್ಛೇದನ ಅರ್ಜಿ ಹಾಕುತ್ತೇನೆ. ಮೊದಲು ಏನು ಮಾಡಬೇಕು ಎಂದು ತಿಳಿಯಬೇಕು."],
    ro=["Nanu mundina vara [[being_filed:vichchhedanakagi arji hakuttiddene]]. Arjiya bagge vakilarondige egagale matanadiddene.",
        "Nanu mundina tingalu divorce arji hakuttene. Modalu enu madabeku anta tiliyabeku."],
    issues={"divorce": "requested"},
    facts={"being_filed": "supported", "divorce_asked": "supported",
           "in_scope": "supported"},
    enums={"claimant_sex": F, "claimant_role": "spouse",
           "modality_time": "future"}))
_reg(B("divorce_js_only", "hn_c",
    en=["I want [[judicial_separation_only:judicial separation]] only. I do not want a [[divorce:divorce]].",
        "I want to live separately from my husband with a court order, but I do not want to end the marriage."],
    kn=["ನನಗೆ [[judicial_separation_only:ನ್ಯಾಯಾಂಗ ಬೇರ್ಪಡಿಕೆ]] ಮಾತ್ರ ಬೇಕು. ನನಗೆ [[divorce:ವಿಚ್ಛೇದನ]] ಬೇಡ.",
        "ಕೋರ್ಟ್ ಆದೇಶದೊಂದಿಗೆ ನನ್ನ ಗಂಡನಿಂದ ಬೇರೆಯಾಗಿ ವಾಸಿಸಲು ಬಯಸುತ್ತೇನೆ, ಆದರೆ ಮದುವೆ ಕೊನೆಗೊಳಿಸಲು ಬಯಸುವುದಿಲ್ಲ."],
    ro=["Nanage [[judicial_separation_only:nyayanga berpadike]] matra beku. Nanage [[divorce:vichchhedana]] beda.",
        "Court adeshadondige nanna gandana inda bereyagi vaasisalu bayasuttene, adare maduve konegolisalu bayasuvudilla."],
    issues={"divorce": "denied"},
    facts={"judicial_separation_only": "supported",
           "divorce_asked": "denied", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("divorce_restitution", "hn_c",
    en=["I do not want a divorce. I want my husband to [[restitution:come back and live with me]] as husband and wife.",
        "My husband left the house. I want the court to ask him to return home and live with me again."],
    kn=["ನನಗೆ ವಿಚ್ಛೇದನ ಬೇಡ. ನನ್ನ ಗಂಡ [[restitution:ಮರಳಿ ಬಂದು ನನ್ನ ಜೊತೆ ಗಂಡ-ಹೆಂಡತಿಯಾಗಿ ಬದುಕಬೇಕು]] ಎಂದು ಬಯಸುತ್ತೇನೆ.",
        "ನನ್ನ ಗಂಡ ಮನೆ ಬಿಟ್ಟು ಹೋಗಿದ್ದಾನೆ. ಅವನು ಮನೆಗೆ ಮರಳಿ ನನ್ನ ಜೊತೆ ವಾಸಿಸಬೇಕು ಎಂದು ಕೋರ್ಟ್ ಕೇಳಬೇಕು."],
    ro=["Nanage divorce beda. Nanna ganda [[restitution:marali bandu nanna jothe ganda-hendatiyagi badukabeku]] anta bayasuttene.",
        "Nanna ganda mane bittu hogiddane. Avanu manege marali nanna jothe vaasisabeku anta court kelabeku."],
    issues={"restitution": "requested", "divorce": "denied"},
    facts={"restitution_asked": "supported", "divorce_asked": "denied",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("divorce_decree_done", "hn_c",
    en=["The court already passed our divorce decree last year. I only want to know about maintenance after the decree.",
        "Our divorce was decided by the court six months ago. What support can I get now?"],
    kn=["ಕೋರ್ಟ್ ಕಳೆದ ವರ್ಷ ನಮ್ಮ ವಿಚ್ಛೇದನ ತೀರ್ಪು ನೀಡಿತು. ತೀರ್ಪಿನ ನಂತರದ ಜೀವನಾಂಶದ ಬಗ್ಗೆ ಮಾತ್ರ ತಿಳಿಯಬೇಕು.",
        "ನಮ್ಮ ವಿಚ್ಛೇದನವನ್ನು ಕೋರ್ಟ್ ಆರು ತಿಂಗಳ ಹಿಂದೆ ತೀರ್ಮಾನಿಸಿತು. ಈಗ ನನಗೆ ಏನು ಬೆಂಬಲ ಸಿಗುತ್ತದೆ?"],
    ro=["Court kaleda varsha namma divorce teerpu needitu. Teerpina nantarada jeevanamshada bagge matra tiliyabeku.",
        "Namma divorce vannu court aaru tingala hinde teermanisitu. Eega nanage enu bembala siguttade?"],
    issues={"divorce": "incidental", "maintenance": "requested"},
    facts={"decree": "supported", "divorce_asked": "unknown",
           "money_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- core: stridhan / joint property / birth certificate -----------------
_reg(B("stridhan_held", "core",
    en=["My [[stridhan_claim:gold worth {gold_value}]] given by my parents is held by my husband's family. I have asked for it back several times and they [[demand_made:refuse to give it back]].",
        "My wedding jewellery is kept by my in-laws. I asked for it back and they refused to give it."],
    kn=["ನನ್ನ ಪೋಷಕರು ಕೊಟ್ಟ [[stridhan_claim:{gold_value} ಮೌಲ್ಯದ ಚಿನ್ನ]]ವನ್ನು ನನ್ನ ಗಂಡನ ಮನೆಯವರು ಇಟ್ಟುಕೊಂಡಿದ್ದಾರೆ. ಹಲವು ಬಾರಿ ಕೇಳಿದರೂ ಅದನ್ನು [[demand_made:ಹಿಂದಿರುಗಿಸಲು ನಿರಾಕರಿಸುತ್ತಿದ್ದಾರೆ]].",
        "ನನ್ನ ಮದುವೆಯ ಆಭರಣಗಳನ್ನು ನನ್ನ ಅತ್ತೆ-ಮಾವ ಇಟ್ಟುಕೊಂಡಿದ್ದಾರೆ. ವಾಪಸ್ ಕೇಳಿದೆ, ಅವರು ಕೊಡಲು ನಿರಾಕರಿಸಿದರು."],
    ro=["Nanna poshakaru kotta [[stridhan_claim:{gold_value} maulyada chinnavannu]] nanna gandana maneyavaru ittukondiddare. Halavu bari kelidaru adannu [[demand_made:hindirugisalu nirakarisuttiddare]].",
        "Nanna maduveya abharanagalannu nanna atte-mava ittukondiddare. Vapas kelide, avaru kodalu nirakarisidaru."],
    issues={"stridhan": "requested"},
    facts={"stridhan_claim": "supported", "demand_made": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("stridhan_sold", "hn_d",
    en=["My husband [[stridhan_sold_or_mortgaged:sold my gold jewellery]] without asking me. I want my [[stridhan_claim:gold]] back or its value.",
        "My in-laws pawned my wedding gold. I want to recover the money for my [[stridhan_claim:stridhan]]."],
    kn=["ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ಕೇಳದೆ [[stridhan_sold_or_mortgaged:ನನ್ನ ಚಿನ್ನಾಭರಣವನ್ನು ಮಾರಿಬಿಟ್ಟನು]]. ನನ್ನ [[stridhan_claim:ಚಿನ್ನ]] ಅಥವಾ ಅದರ ಮೌಲ್ಯ ವಾಪಸ್ ಬೇಕು.",
        "ನನ್ನ ಅತ್ತೆ-ಮಾವ ನನ್ನ ಮದುವೆಯ ಚಿನ್ನವನ್ನು ಅಡವಿಟ್ಟರು. ನನ್ನ [[stridhan_claim:ಚಿನ್ನ]]ಕ್ಕಾಗಿ ಹಣ ವಾಪಸ್ ಪಡೆಯಬೇಕು."],
    ro=["Nanna ganda nannannu kelade [[stridhan_sold_or_mortgaged:nanna chinnabharanavannu maribittanu]]. Nanna [[stridhan_claim:chinna]] athava adara maulya vapas beku.",
        "Nanna atte-mava nanna maduveya chinnavannu adavittaru. Nanna [[stridhan_claim:chinna]]kkagi hana vapas padeyabeku."],
    issues={"stridhan": "requested"},
    facts={"stridhan_claim": "supported",
           "stridhan_sold_or_mortgaged": "supported",
           "demand_made": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("stridhan_safe", "hn_d",
    en=["My gold is [[stridhan_claim:safe in my own locker]] and nobody has taken it. I only want to know about maintenance.",
        "My jewellery is with me and there is no dispute about it. My question is only about monthly support."],
    kn=["ನನ್ನ ಚಿನ್ನ [[stridhan_claim:ನನ್ನ ಸ್ವಂತ ಲಾಕರ್‌ನಲ್ಲಿ ಸುರಕ್ಷಿತವಾಗಿದೆ]], ಯಾರೂ ತೆಗೆದುಕೊಂಡಿಲ್ಲ. ನನಗೆ ಜೀವನಾಂಶದ ಬಗ್ಗೆ ಮಾತ್ರ ತಿಳಿಯಬೇಕು.",
        "ನನ್ನ ಆಭರಣಗಳು ನನ್ನ ಬಳಿಯೇ ಇವೆ, ಅವುಗಳ ಬಗ್ಗೆ ಯಾವುದೇ ವಿವಾದವಿಲ್ಲ. ನನ್ನ ಪ್ರಶ್ನೆ ತಿಂಗಳ ಬೆಂಬಲದ ಬಗ್ಗೆ ಮಾತ್ರ."],
    ro=["Nanna chinna [[stridhan_claim:nanna swanta locker nalli surakshitavagide]], yaru tegedukondilla. Nanage jeevanamshada bagge matra tiliyabeku.",
        "Nanna abharanagalu nanna baliye ive, avugala bagge yavude vivadavilla. Nanna prashne tingala bembalada bagge matra."],
    issues={"stridhan": "denied", "maintenance": "requested"},
    facts={"stridhan_claim": "denied", "money_fact": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("stridhan_never_asked", "hn_d",
    en=["I have [[demand_made:never asked]] my in-laws for my gold back. Can I ask for my [[stridhan_claim:stridhan]] now?",
        "My wedding gold is still with my husband's family, but I have not demanded it yet. How do I ask for it?"],
    kn=["ನಾನು ನನ್ನ ಅತ್ತೆ-ಮಾವನನ್ನು ಚಿನ್ನ ವಾಪಸ್ ಕೇಳಿಯೇ ಇಲ್ಲ. ಈಗ ನನ್ನ [[stridhan_claim:ಚಿನ್ನ]] ಕೇಳಬಹುದೇ?",
        "ನನ್ನ ಮದುವೆಯ ಚಿನ್ನ ಇನ್ನೂ ನನ್ನ ಗಂಡನ ಮನೆಯಲ್ಲಿದೆ, ಆದರೆ ನಾನು ಇನ್ನೂ ಕೇಳಿಲ್ಲ. ಅದನ್ನು ಹೇಗೆ ಕೇಳುವುದು?"],
    ro=["Nanu nanna atte-mavanannu chinna vapas keliye illa. Eega nanna [[stridhan_claim:chinna]] kelabahude?",
        "Nanna maduveya chinna innu nanna gandana maneyallide, adare nanu innu kelilla. Adannu hege keluvudu?"],
    issues={"stridhan": "requested"},
    facts={"stridhan_claim": "supported", "demand_made": "denied",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("joint_property", "core",
    en=["My husband and I bought a flat together in both our names. I want my share of this [[joint_property_claim:joint property]].",
        "We own a house jointly, and I want the court to divide our [[joint_property_claim:joint property]] fairly."],
    kn=["ನನ್ನ ಗಂಡ ಮತ್ತು ನಾನು ಇಬ್ಬರ ಹೆಸರಿನಲ್ಲಿ ಒಂದು ಫ್ಲ್ಯಾಟ್ ಖರೀದಿಸಿದೆವು. ಈ [[joint_property_claim:ಜಂಟಿ ಆಸ್ತಿ]]ಯಲ್ಲಿ ನನ್ನ ಪಾಲು ಬೇಕು.",
        "ನಾವು ಜಂಟಿಯಾಗಿ ಮನೆ ಹೊಂದಿದ್ದೇವೆ, ನಮ್ಮ [[joint_property_claim:ಜಂಟಿ ಆಸ್ತಿ]]ಯನ್ನು ನ್ಯಾಯಯುತವಾಗಿ ವಿಭಜಿಸಲು ಕೋರ್ಟ್‌ಗೆ ಕೇಳಬೇಕು."],
    ro=["Nanna ganda mattu nanu ibbara hesarinalli ondu flat khareedisidevu. Ee [[joint_property_claim:janti asti]]yalli nanna palu beku.",
        "Navu jantiyagi mane hondiddeve, namma [[joint_property_claim:janti asti]]yannu nyayayutavagi vibhajisalu court ge kelabeku."],
    issues={"joint_property": "requested"},
    facts={"joint_property_claim": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("joint_property_hma_pending", "hn_d",
    en=["My divorce case is pending, and we also have a house in both our names. I want my share of the [[joint_property_claim:joint property]] along with the divorce case.",
        "While our divorce case goes on, I want the court to decide about our jointly owned flat as well."],
    kn=["ನನ್ನ ವಿಚ್ಛೇದನ ಕೇಸ್ ನಡೆಯುತ್ತಿದೆ, ನಮ್ಮಿಬ್ಬರ ಹೆಸರಿನಲ್ಲಿ ಮನೆಯೂ ಇದೆ. ವಿಚ್ಛೇದನ ಕೇಸ್ ಜೊತೆಗೆ [[joint_property_claim:ಜಂಟಿ ಆಸ್ತಿ]]ಯಲ್ಲಿ ನನ್ನ ಪಾಲು ಬೇಕು.",
        "ನಮ್ಮ ವಿಚ್ಛೇದನ ಕೇಸ್ ನಡೆಯುವಾಗ, ನಮ್ಮ ಜಂಟಿ ಫ್ಲ್ಯಾಟ್ ಬಗ್ಗೆಯೂ ಕೋರ್ಟ್ ತೀರ್ಮಾನಿಸಬೇಕು."],
    ro=["Nanna divorce case nadeyuttide, nammibbara hesarinalli maneyu ide. Divorce case jotege [[joint_property_claim:janti asti]]yalli nanna palu beku.",
        "Namma divorce case nadeyuvaga, namma janti flat baggeyu court teermanisabeku."],
    issues={"joint_property": "requested", "divorce": "incidental"},
    facts={"joint_property_claim": "supported",
           "proceeding_pending_hma": "supported",
           "divorce_asked": "unknown", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("joint_property_no_hma", "hn_d",
    en=["There is no divorce case between us. I only want my share of the house we bought together in both names.",
        "We are still married and there is no case in court, but I want to know about my share in our joint house."],
    kn=["ನಮ್ಮ ನಡುವೆ ಯಾವುದೇ ವಿಚ್ಛೇದನ ಕೇಸ್ ಇಲ್ಲ. ನಾವು ಇಬ್ಬರ ಹೆಸರಿನಲ್ಲಿ ಖರೀದಿಸಿದ ಮನೆಯಲ್ಲಿ ನನ್ನ ಪಾಲು ಮಾತ್ರ ಬೇಕು.",
        "ನಾವು ಇನ್ನೂ ಮದುವೆಯಲ್ಲಿದ್ದೇವೆ, ಕೋರ್ಟ್‌ನಲ್ಲಿ ಯಾವುದೇ ಕೇಸ್ ಇಲ್ಲ, ಆದರೆ ನಮ್ಮ ಜಂಟಿ ಮನೆಯಲ್ಲಿ ನನ್ನ ಪಾಲಿನ ಬಗ್ಗೆ ತಿಳಿಯಬೇಕು."],
    ro=["Namma naduve yavude divorce case illa. Navu ibbara hesarinalli khareedisa maneyalli nanna palu matra beku.",
        "Navu innu maduveyalliddeve, court nalli yavude case illa, adare namma janti maneyalli nanna palina bagge tiliyabeku."],
    issues={"joint_property": "requested"},
    facts={"joint_property_claim": "supported",
           "proceeding_pending_hma": "denied", "being_filed": "denied",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("birth_cert", "core",
    en=["I need a [[birth_certificate:birth certificate]] for my {child_age}-year-old {child_word} for school admission. How do I get one?",
        "My {child_word} was born at home and has no [[birth_certificate:birth certificate]]. Where do I apply for it?"],
    kn=["ಶಾಲಾ ಪ್ರವೇಶಕ್ಕಾಗಿ ನನ್ನ {child_age} ವರ್ಷದ {child_word}ನ [[birth_certificate:ಜನನ ಪ್ರಮಾಣಪತ್ರ]] ಬೇಕು. ಅದನ್ನು ಹೇಗೆ ಪಡೆಯುವುದು?",
        "ನನ್ನ {child_word} ಮನೆಯಲ್ಲಿ ಹುಟ್ಟಿದನು, [[birth_certificate:ಜನನ ಪ್ರಮಾಣಪತ್ರ]] ಇಲ್ಲ. ಎಲ್ಲಿ ಅರ್ಜಿ ಹಾಕಬೇಕು?"],
    ro=["Shala praveshakagi nanna {child_age} varshada {child_word}na [[birth_certificate:janana pramanapatra]] beku. Adannu hege padeyuvudu?",
        "Nanna {child_word} maneyalli huttidanu, [[birth_certificate:janana pramanapatra]] illa. Elli arji hakabeku?"],
    issues={"birth_certificate": "requested"},
    facts={"birth_cert_asked": "supported", "child_fact": "supported",
           "minor_child": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- core: procedure ------------------------------------------------------
_reg(B("procedure_court", "core",
    en=["Which court should I go to for [[procedure:maintenance]] and my child's custody?",
        "I do not know which court handles family cases. Where should I file my case?"],
    kn=["[[procedure:ಜೀವನಾಂಶ]] ಮತ್ತು ನನ್ನ ಮಗುವಿನ ಪಾಲನೆಗಾಗಿ ನಾನು ಯಾವ ಕೋರ್ಟ್‌ಗೆ ಹೋಗಬೇಕು?",
        "ಕೌಟುಂಬಿಕ ಪ್ರಕರಣಗಳನ್ನು ಯಾವ ಕೋರ್ಟ್ ನೋಡುತ್ತದೆ ಎಂದು ನನಗೆ ಗೊತ್ತಿಲ್ಲ. ನಾನು ಎಲ್ಲಿ ಕೇಸ್ ಹಾಕಬೇಕು?"],
    ro=["[[procedure:Jeevanamsha]] mattu nanna maguvina paalanegagi nanu yava court ge hogabeku?",
        "Koutumbika prakaranagalannu yava court noduttade anta nanage gottilla. Nanu elli case hakabeku?"],
    issues={"procedure": "requested"},
    facts={"in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("procedure_how_file", "core",
    en=["How do I file a case for [[procedure:maintenance]]? What papers do I need to start?",
        "What is the first step to ask the court for help with my husband not paying me?"],
    kn=["[[procedure:ಜೀವನಾಂಶ]]ಕ್ಕಾಗಿ ಕೇಸ್ ಹೇಗೆ ಹಾಕುವುದು? ಪ್ರಾರಂಭಿಸಲು ಯಾವ ಕಾಗದಗಳು ಬೇಕು?",
        "ನನ್ನ ಗಂಡ ಹಣ ಕೊಡದಿದ್ದಾಗ ಕೋರ್ಟ್ ಸಹಾಯ ಕೇಳಲು ಮೊದಲ ಹೆಜ್ಜೆ ಏನು?"],
    ro=["[[procedure:Jeevanamsha]]kkagi case hege hakuvudu? Prarambhisalu yava kagadagalu beku?",
        "Nanna ganda hana kodadiddaga court sahaya kelalu modala hejje enu?"],
    issues={"procedure": "requested"},
    facts={"in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- hard negative A: custody vs residence co-location --------------------
_reg(B("coloc_stay_with_child", "hn_a",
    en=["I want my {child_age}-year-old {child_word} to keep living at home with me. This is about living together at home.",
        "My {child_word} and I live in our house. I want us to keep staying in this house together."],
    kn=["ನನ್ನ {child_age} ವರ್ಷದ {child_word} ಮನೆಯಲ್ಲಿ ನನ್ನ ಜೊತೆಯೇ ವಾಸ ಮುಂದುವರಿಸಬೇಕೆಂದು ಬಯಸುತ್ತೇನೆ. ಇದು ಮನೆಯಲ್ಲಿ ಒಟ್ಟಿಗೆ ವಾಸಿಸುವ ಬಗ್ಗೆ.",
        "ನನ್ನ {child_word} ಮತ್ತು ನಾನು ನಮ್ಮ ಮನೆಯಲ್ಲಿ ವಾಸಿಸುತ್ತೇವೆ. ನಾವು ಈ ಮನೆಯಲ್ಲಿ ಒಟ್ಟಿಗೆ ಇರುವುದನ್ನು ಮುಂದುವರಿಸಬೇಕು."],
    ro=["Nanna {child_age} varshada {child_word} maneyalli nanna joteye vaasa munduvarisabekendu bayasuttene. Idu maneyalli ottige vaasisuva bagge.",
        "Nanna {child_word} mattu nanu namma maneyalli vaasistevu. Navu ee maneyalli ottige iruvudannu munduvarisabeku."],
    issues={"residence": "requested", "custody": "incidental"},
    facts={"residence_claim": "supported", "custody_claim": "denied",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("coloc_custody_word", "hn_a",
    en=["My {child_word} should remain in my care, not go to my husband. I am asking for [[custody:custody]] of my {child_word}.",
        "My husband wants to take our {child_word} away. I want the court to give me [[custody:custody]]."],
    kn=["ನನ್ನ {child_word} ನನ್ನ ಆರೈಕೆಯಲ್ಲಿ ಇರಬೇಕು, ನನ್ನ ಗಂಡನ ಬಳಿ ಅಲ್ಲ. ನನ್ನ {child_word}ನ [[custody:ಪಾಲನೆ]] ಕೇಳುತ್ತಿದ್ದೇನೆ.",
        "ನನ್ನ ಗಂಡ ನಮ್ಮ {child_word}ನನ್ನು ಕರೆದುಕೊಂಡು ಹೋಗಲು ಬಯಸುತ್ತಾನೆ. ಕೋರ್ಟ್ ನನಗೆ [[custody:ಪಾಲನೆ]] ನೀಡಬೇಕು."],
    ro=["Nanna {child_word} nanna aaraikeyalli irabeku, nanna gandana bali alla. Nanna {child_word}na [[custody:paalane]] keluttiddene.",
        "Nanna ganda namma {child_word}nannu karedukondu hogalu bayasuttane. Court nanage [[custody:paalane]] needabeku."],
    issues={"custody": "requested", "residence": "incidental"},
    facts={"custody_claim": "supported", "residence_claim": "denied",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- hard negative F: hypothetical / third-party / quoted / pre-BNSS -------
_reg(B("hypothetical", "hn_f",
    en=["Suppose a woman's husband stops giving her any money. Could she ask the court for [[maintenance:maintenance]]?",
        "If a husband throws his wife out of their house, what rights would she have to stay there?",
        "Imagine a mother whose son earns well but gives her nothing. Would she be able to ask for support?"],
    kn=["ಒಂದು ವೇಳೆ ಒಬ್ಬ ಮಹಿಳೆಯ ಗಂಡ ಅವಳಿಗೆ ಹಣ ಕೊಡುವುದನ್ನು ನಿಲ್ಲಿಸಿದರೆ, ಅವಳು ಕೋರ್ಟ್‌ನಲ್ಲಿ [[maintenance:ಜೀವನಾಂಶ]] ಕೇಳಬಹುದೇ?",
        "ಒಂದು ವೇಳೆ ಗಂಡ ಹೆಂಡತಿಯನ್ನು ಮನೆಯಿಂದ ಹೊರಹಾಕಿದರೆ, ಅಲ್ಲಿ ಇರಲು ಅವಳಿಗೆ ಏನು ಹಕ್ಕುಗಳಿರುತ್ತವೆ?",
        "ಒಬ್ಬ ತಾಯಿಯ ಮಗ ಚೆನ್ನಾಗಿ ಸಂಪಾದಿಸಿದರೂ ಅವಳಿಗೆ ಏನೂ ಕೊಡದಿದ್ದರೆ, ಅವಳು ಬೆಂಬಲ ಕೇಳಬಹುದೇ ಎಂದು ಊಹಿಸಿ."],
    ro=["Ondu vele obba mahileyaga ganda avalige hana koduvudannu nillisidare, avalu court nalli [[maintenance:jeevanamsha]] kelabahude?",
        "Ondu vele ganda hendatiyannu maneyinda horahakidare, alli iralu avalige enu hakkugaliruttave?",
        "Obba tayiya maga chennagi sampadisidaru avalige enu kodadiddare, avalu bembala kelabahude anta uuhisi."],
    issues={},
    facts={"in_scope": "supported"},
    enums={"claimant_sex": "U", "claimant_role": "other",
           "modality_time": "hypothetical"}))
_reg(B("third_party", "hn_f",
    en=["My friend's husband beats her at home. What can she do to get protection and support?",
        "My neighbour's daughter was thrown out of her house by her in-laws. What help can she get?",
        "My sister's husband gives her no money for the house. Can she ask for [[maintenance:maintenance]]?"],
    kn=["ನನ್ನ ಗೆಳತಿಯ ಗಂಡ ಮನೆಯಲ್ಲಿ ಅವಳನ್ನು ಹೊಡೆಯುತ್ತಾನೆ. ರಕ್ಷಣೆ ಮತ್ತು ಬೆಂಬಲ ಪಡೆಯಲು ಅವಳು ಏನು ಮಾಡಬಹುದು?",
        "ನನ್ನ ನೆರೆಯವರ ಮಗಳನ್ನು ಅತ್ತೆ-ಮಾವ ಮನೆಯಿಂದ ಹೊರಹಾಕಿದರು. ಅವಳಿಗೆ ಏನು ಸಹಾಯ ಸಿಗುತ್ತದೆ?",
        "ನನ್ನ ತಂಗಿಯ ಗಂಡ ಮನೆಗೆ ಹಣ ಕೊಡುವುದಿಲ್ಲ. ಅವಳು [[maintenance:ಜೀವನಾಂಶ]] ಕೇಳಬಹುದೇ?"],
    ro=["Nanna gelatiya ganda maneyalli avalannu hodeyuttane. Rakshane mattu bembala padeyalu avalu enu madabahudu?",
        "Nanna nereyavara magalannu atte-mava maneyinda horahakidaru. Avalige enu sahaya siguttade?",
        "Nanna tangiya ganda manege hana koduvudilla. Avalu [[maintenance:jeevanamsha]] kelabahude?"],
    issues={},
    facts={"in_scope": "supported"},
    enums={"claimant_sex": "U", "claimant_role": "other"}))
_reg(B("quoted", "hn_f",
    en=["My sister told me, \"My husband beats me and gives me no money.\" She wants to know what she can do.",
        "A woman at work said, \"My in-laws took my gold and will not return it.\" She asked me what the law says."],
    kn=["ನನ್ನ ತಂಗಿ ನನಗೆ ಹೇಳಿದಳು, \"ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ಹೊಡೆಯುತ್ತಾನೆ ಮತ್ತು ಹಣ ಕೊಡುವುದಿಲ್ಲ.\" ಅವಳು ಏನು ಮಾಡಬಹುದು ಎಂದು ತಿಳಿಯಲು ಬಯಸುತ್ತಾಳೆ.",
        "ಕೆಲಸದಲ್ಲಿ ಒಬ್ಬ ಮಹಿಳೆ ಹೇಳಿದಳು, \"ನನ್ನ ಅತ್ತೆ-ಮಾವ ನನ್ನ ಚಿನ್ನ ತೆಗೆದುಕೊಂಡು ವಾಪಸ್ ಕೊಡುವುದಿಲ್ಲ.\" ಕಾನೂನು ಏನು ಹೇಳುತ್ತದೆ ಎಂದು ಅವಳು ಕೇಳಿದಳು."],
    ro=["Nanna tangi nanage helidalu, \"Nanna ganda nannannu hodeyuttane mattu hana koduvudilla.\" Avalu enu madabahudu anta tiliyalu bayasutale.",
        "Kelasadalli obba mahile helidalu, \"Nanna atte-mava nanna chinna tegedukondu vapas koduvudilla.\" Kanoonu enu heluttade anta avalu kelidalu."],
    issues={},
    facts={"in_scope": "supported"},
    enums={"claimant_sex": "U", "claimant_role": "other",
           "modality_time": "quoted"}))
_reg(B("pre_bnss", "hn_f",
    en=["In 2023, before the new criminal law came in, the court ordered my husband to pay me under the old maintenance law. He has not paid since then.",
        "My husband was ordered to pay support under the old CrPC 125 law in 2022. He stopped paying last year. What can I do now?"],
    kn=["2023ರಲ್ಲಿ, ಹೊಸ ಕ್ರಿಮಿನಲ್ ಕಾನೂನು ಬರುವ ಮೊದಲು, ಕೋರ್ಟ್ ನನ್ನ ಗಂಡ ಹಳೆಯ ಜೀವನಾಂಶ ಕಾನೂನಿನಡಿ ಹಣ ಕೊಡಬೇಕು ಎಂದು ಆದೇಶಿಸಿತ್ತು. ಅಂದಿನಿಂದ ಅವನು ಕೊಟ್ಟಿಲ್ಲ.",
        "2022ರಲ್ಲಿ ಹಳೆಯ CrPC 125 ಕಾನೂನಿನಡಿ ನನ್ನ ಗಂಡ ಬೆಂಬಲ ಕೊಡಬೇಕು ಎಂದು ಆದೇಶಿಸಲಾಗಿತ್ತು. ಕಳೆದ ವರ್ಷ ಅವನು ಕೊಡುವುದನ್ನು ನಿಲ್ಲಿಸಿದನು. ಈಗ ನಾನು ಏನು ಮಾಡಬಹುದು?"],
    ro=["2023 ralli, hosa criminal kanoonu baruva modalu, court nanna ganda haleya jeevanamsha kanoonina adi hana kodabeku anta adeshisittu. Andininda avanu kottilla.",
        "2022 ralli haleya CrPC 125 kanoonina adi nanna ganda bembala kodabeku anta adeshisalagittu. Kaleda varsha avanu koduvudannu nillisidanu. Eega nanu enu madabahudu?"],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported",
           "existing_order_enforcement": "supported",
           "in_scope": "supported"},
    enums={"claimant_sex": F, "claimant_role": "spouse",
           "modality_time": "past"}))
_reg(B("past_event", "hn_f",
    en=["My husband left our home five years ago and never sent any money after that. I managed alone all these years.",
        "Three years ago my husband stopped paying for our {child_word}'s school. I have been paying everything myself since then."],
    kn=["ನನ್ನ ಗಂಡ ಐದು ವರ್ಷಗಳ ಹಿಂದೆ ನಮ್ಮ ಮನೆ ಬಿಟ್ಟು ಹೋದನು, ಆ ನಂತರ ಎಂದೂ ಹಣ ಕಳುಹಿಸಲಿಲ್ಲ. ಈ ಎಲ್ಲಾ ವರ್ಷಗಳೂ ನಾನೊಬ್ಬಳೇ ನಿಭಾಯಿಸಿದೆ.",
        "ಮೂರು ವರ್ಷಗಳ ಹಿಂದೆ ನನ್ನ ಗಂಡ ನಮ್ಮ {child_word}ನ ಶಾಲೆಗೆ ಹಣ ಕೊಡುವುದನ್ನು ನಿಲ್ಲಿಸಿದನು. ಅಂದಿನಿಂದ ಎಲ್ಲವನ್ನೂ ನಾನೇ ಕೊಡುತ್ತಿದ್ದೇನೆ."],
    ro=["Nanna ganda aidu varshagala hinde namma mane bittu hodanu, aa nantara endu hana kaluhisalilla. Ee ella varshagalu nanobbale nibhayiside.",
        "Mooru varshagala hinde nanna ganda namma {child_word}na shalege hana koduvudannu nillisidanu. Andininda ellavannu nane koduttiddene."],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "in_scope": "supported"},
    enums={"claimant_sex": F, "claimant_role": "spouse",
           "modality_time": "past"}))

# --- negation primaries ----------------------------------------------------
_reg(B("neg_maintenance", "neg",
    en=["I do not want any [[maintenance:maintenance]] from my husband. I only want [[custody:custody]] of my {child_word}.",
        "I am not asking for money. I only want my {child_age}-year-old {child_word} to remain in my care."],
    kn=["ನನ್ನ ಗಂಡನಿಂದ ಯಾವುದೇ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಡ. ನನ್ನ {child_word}ನ [[custody:ಪಾಲನೆ]] ಮಾತ್ರ ಬೇಕು.",
        "ನಾನು ಹಣ ಕೇಳುತ್ತಿಲ್ಲ. ನನ್ನ {child_age} ವರ್ಷದ {child_word} ನನ್ನ ಆರೈಕೆಯಲ್ಲಿ ಇರಬೇಕು ಅಷ್ಟೇ."],
    ro=["Nanna gandana inda yavude [[maintenance:jeevanamsha]] beda. Nanna {child_word}na [[custody:paalane]] matra beku.",
        "Nanu hana keluttilla. Nanna {child_age} varshada {child_word} nanna aaraikeyalli irabeku ashte."],
    issues={"maintenance": "denied", "custody": "requested"},
    facts={"money_fact": "denied", "custody_claim": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("neg_divorce", "neg",
    en=["I do not want a [[divorce:divorce]] at all. I only want my husband to start paying [[maintenance:maintenance]] again.",
        "Ending the marriage is not what I want. I just need monthly support from my husband."],
    kn=["ನನಗೆ [[divorce:ವಿಚ್ಛೇದನ]] ಖಂಡಿತ ಬೇಡ. ನನ್ನ ಗಂಡ ಮತ್ತೆ [[maintenance:ಜೀವನಾಂಶ]] ಕೊಡಲು ಪ್ರಾರಂಭಿಸಬೇಕು ಅಷ್ಟೇ.",
        "ಮದುವೆ ಕೊನೆಗೊಳಿಸುವುದು ನನಗೆ ಬೇಡ. ನನ್ನ ಗಂಡನಿಂದ ತಿಂಗಳ ಬೆಂಬಲ ಬೇಕು ಅಷ್ಟೇ."],
    ro=["Nanage [[divorce:vichchhedana]] khandita beda. Nanna ganda matte [[maintenance:jeevanamsha]] kodalu prarambhisabeku ashte.",
        "Maduve konegolisuvudu nanage beda. Nanna gandana inda tingala bembala beku ashte."],
    issues={"divorce": "denied", "maintenance": "requested"},
    facts={"divorce_asked": "denied", "money_fact": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("neg_custody", "neg",
    en=["I am not asking for the children's [[custody:custody]]. I only want monthly support for myself and my {child_word}.",
        "Custody is already settled between us. I only need help with monthly support."],
    kn=["ಮಕ್ಕಳ [[custody:ಪಾಲನೆ]] ಕೇಳುತ್ತಿಲ್ಲ. ನನಗಾಗಿ ಮತ್ತು ನನ್ನ {child_word}ಗಾಗಿ ತಿಂಗಳ ಬೆಂಬಲ ಮಾತ್ರ ಬೇಕು.",
        "ಪಾಲನೆ ನಮ್ಮ ನಡುವೆ ಈಗಾಗಲೇ ತೀರ್ಮಾನವಾಗಿದೆ. ತಿಂಗಳ ಬೆಂಬಲಕ್ಕಾಗಿ ಮಾತ್ರ ಸಹಾಯ ಬೇಕು."],
    ro=["Makkala [[custody:paalane]] keluttilla. Nanagagi mattu nanna {child_word}gagi tingala bembala matra beku.",
        "Paalane namma naduve egagale teermanavagide. Tingala bembalakkagi matra sahaya beku."],
    issues={"custody": "denied", "maintenance": "requested"},
    facts={"custody_claim": "denied", "money_fact": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))

_reg(B("neg_decree_mutual", "neg",
    en=["We do not want a [[mutual_consent:mutual consent divorce]], and there is no decree yet. I only want [[maintenance:maintenance]].",
        "There is no court decree between us, and we have not agreed to a mutual divorce."],
    kn=["ನಮಗೆ [[mutual_consent:ಪರಸ್ಪರ ಒಪ್ಪಿಗೆಯ ವಿಚ್ಛೇದನ]] ಬೇಡ, ಇನ್ನೂ ಯಾವುದೇ ತೀರ್ಪು ಇಲ್ಲ. ನನಗೆ [[maintenance:ಜೀವನಾಂಶ]] ಮಾತ್ರ ಬೇಕು.",
        "ನಮ್ಮ ನಡುವೆ ಕೋರ್ಟ್ ತೀರ್ಪು ಇಲ್ಲ, ಪರಸ್ಪರ ಒಪ್ಪಿಗೆಯ ವಿಚ್ಛೇದನಕ್ಕೂ ಒಪ್ಪಿಲ್ಲ."],
    ro=["Namage [[mutual_consent:paraspara oppigeya divorce]] beda, innu yavude teerpu illa. Nanage [[maintenance:jeevanamsha]] matra beku.",
        "Namma naduve court teerpu illa, paraspara oppigeya divorce kku oppilla."],
    issues={"divorce": "denied", "maintenance": "requested"},
    facts={"mutual_consent": "denied", "decree": "denied",
           "divorce_asked": "denied", "money_fact": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("neg_no_order", "neg",
    en=["No court has ordered [[maintenance:maintenance]] for me yet. I want to ask for it for the first time.",
        "There is no maintenance order in my favour so far. Can I ask the court to make one?"],
    kn=["ಕೋರ್ಟ್ ಇನ್ನೂ ನನಗೆ [[maintenance:ಜೀವನಾಂಶ]] ಆದೇಶಿಸಿಲ್ಲ. ಮೊದಲ ಬಾರಿಗೆ ಕೇಳಲು ಬಯಸುತ್ತೇನೆ.",
        "ನನ್ನ ಪರವಾಗಿ ಇಲ್ಲಿಯವರೆಗೆ ಯಾವುದೇ ಜೀವನಾಂಶ ಆದೇಶವಿಲ್ಲ. ಕೋರ್ಟ್ ಆದೇಶ ಮಾಡುವಂತೆ ಕೇಳಬಹುದೇ?"],
    ro=["Court innu nanage [[maintenance:jeevanamsha]] adeshisilla. Modala barige kelalu bayasuttene.",
        "Nanna paravagi illiyavarage yavude jeevanamsha adeshavilla. Court adesha maduvante kelabahude?"],
    issues={"maintenance": "requested"},
    facts={"existing_order_enforcement": "denied",
           "money_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- conflicting ------------------------------------------------------------
_reg(B("conflict_divorce", "conflict",
    en=["I want a [[divorce:divorce]] from my husband. Actually, no, I do not want a divorce, I want him to come back home and live with me.",
        "One moment I want to end the marriage, the next moment I want my husband back. I am confused about what to ask for."],
    kn=["ನನ್ನ ಗಂಡನಿಂದ [[divorce:ವಿಚ್ಛೇದನ]] ಬೇಕು. ಇಲ್ಲ, ವಿಚ್ಛೇದನ ಬೇಡ, ಅವನು ಮನೆಗೆ ಮರಳಿ ನನ್ನ ಜೊತೆ ಬದುಕಬೇಕು.",
        "ಒಂದು ಕ್ಷಣ ಮದುವೆ ಕೊನೆಗೊಳಿಸಲು ಬಯಸುತ್ತೇನೆ, ಮರುಕ್ಷಣ ನನ್ನ ಗಂಡ ವಾಪಸ್ ಬೇಕು. ಏನು ಕೇಳಬೇಕೆಂದು ಗೊಂದಲವಿದೆ."],
    ro=["Nanna gandana inda [[divorce:vichchhedana]] beku. Illa, divorce beda, avanu manege marali nanna jothe badukabeku.",
        "Ondu kshana maduve konegolisalu bayasuttene, marukshana nanna ganda vapas beku. Enu kelabekendu gondalavide."],
    issues={"divorce": "uncertain", "restitution": "requested"},
    facts={"divorce_asked": "conflicting", "restitution_asked": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- hard negative F: 12 out-of-scope domains ------------------------------
# Each OOS block: in_scope denied, every issue uncertain, every other fact
# unknown. The family-law trigger word (husband/wife/friend's divorce etc.)
# is present only as noise, never as a claim.
OOS_DOMAINS = [
    ("oos_rent", "rent / landlord-tenant",
     ["My landlord has increased my house rent again and will not repair the leaking roof. What can a tenant do?",
      "My husband's landlord is asking for three months' rent in advance. Is that allowed under tenancy law?"],
     ["ನನ್ನ ಮನೆಯ ಮಾಲೀಕರು ಮತ್ತೆ ಬಾಡಿಗೆ ಹೆಚ್ಚಿಸಿದ್ದಾರೆ, ಸೋರುವ ಛಾವಣಿಯನ್ನು ಸರಿಪಡಿಸುವುದಿಲ್ಲ. ಬಾಡಿಗೆದಾರ ಏನು ಮಾಡಬಹುದು?",
      "ನನ್ನ ಗಂಡನ ಮನೆಯ ಮಾಲೀಕರು ಮೂರು ತಿಂಗಳ ಬಾಡಿಗೆ ಮುಂಗಡ ಕೇಳುತ್ತಿದ್ದಾರೆ. ಬಾಡಿಗೆ ಕಾನೂನಿನಲ್ಲಿ ಅದು ಸರಿಯೇ?"],
     ["Nanna maneya malikaru matte badige hechisiddare, soruva chavaniyannu saripadisuvudilla. Badigedara enu madabahudu?",
      "Nanna gandana maneya malikaru mooru tingala badige mungada keluttiddare. Badige kanoonina alli adu sariye?"]),
    ("oos_employment", "employment / salary from employer",
     ["My employer has held back my pay for the last two months. How do I claim my pending salary from my employer?",
      "My boss cut my pay without notice. Where do I complain about unpaid wages?"],
     ["ನನ್ನ ಉದ್ಯೋಗದಾತರು ಕಳೆದ ಎರಡು ತಿಂಗಳಿನಿಂದ ನನ್ನ ಸಂಬಳ ತಡೆಹಿಡಿದಿದ್ದಾರೆ. ನನ್ನ ಉದ್ಯೋಗದಾತರಿಂದ ಬಾಕಿ ಸಂಬಳವನ್ನು ಹೇಗೆ ಕೇಳುವುದು?",
      "ನನ್ನ ಬಾಸ್ ಸೂಚನೆ ಇಲ್ಲದೆ ನನ್ನ ಸಂಬಳ ಕಡಿತ ಮಾಡಿದರು. ಪಾವತಿಯಾಗದ ವೇತನದ ಬಗ್ಗೆ ಎಲ್ಲಿ ದೂರು ನೀಡುವುದು?"],
     ["Nanna udyogadataru kaleda eradu tingalinda nanna sambala tadehididdare. Nanna udyogadatarinda baki sambalavannu hege keluvudu?",
      "Nanna boss soochane illade nanna sambala kadita madidaru. Pavatiyagada vetanada bagge elli duru needuvudu?"]),
    ("oos_consumer", "consumer refund",
     ["I bought a washing machine online and it stopped working in a week. The shop refuses a refund. What can I do?",
      "The store sold me a damaged phone and will not replace it. How do I get my money back?"],
     ["ನಾನು ಆನ್‌ಲೈನ್‌ನಲ್ಲಿ ವಾಷಿಂಗ್ ಮಷೀನ್ ಖರೀದಿಸಿದೆ, ಒಂದು ವಾರದಲ್ಲಿ ಅದು ಕೆಲಸ ಮಾಡುವುದನ್ನು ನಿಲ್ಲಿಸಿತು. ಅಂಗಡಿ ಹಣ ವಾಪಸ್ ಕೊಡಲು ನಿರಾಕರಿಸುತ್ತಿದೆ. ನಾನು ಏನು ಮಾಡಬಹುದು?",
      "ಅಂಗಡಿ ನನಗೆ ಹಾನಿಗೊಳಗಾದ ಫೋನ್ ಮಾರಿತು, ಬದಲಿಸಲು ನಿರಾಕರಿಸುತ್ತಿದೆ. ನನ್ನ ಹಣವನ್ನು ಹೇಗೆ ವಾಪಸ್ ಪಡೆಯುವುದು?"],
     ["Nanu online nalli washing machine khareedide, ondu varadalli adu kelasa maduvudannu nillisitu. Angadi hana vapas kodalu nirakarisuttide. Nanu enu madabahudu?",
      "Angadi nanage hanigolagada phone maritu, badalisalu nirakarisuttide. Nanna hanavannu hege vapas padeyuvudu?"]),
    ("oos_cheque", "cheque bounce",
     ["A man gave me a cheque for fifty thousand rupees and it bounced. How do I recover the cheque amount?",
      "My friend borrowed money from me and his cheque was returned unpaid. What is the process for a bounced cheque?"],
     ["ಒಬ್ಬ ವ್ಯಕ್ತಿ ನನಗೆ ಐವತ್ತು ಸಾವಿರ ರೂಪಾಯಿ ಚೆಕ್ ಕೊಟ್ಟನು, ಅದು ಬೌನ್ಸ್ ಆಯಿತು. ಚೆಕ್ ಮೊತ್ತವನ್ನು ಹೇಗೆ ವಾಪಸ್ ಪಡೆಯುವುದು?",
      "ನನ್ನ ಗೆಳೆಯ ನನ್ನಿಂದ ಹಣ ಎರವಲು ಪಡೆದನು, ಅವನ ಚೆಕ್ ಪಾವತಿಯಾಗದೆ ವಾಪಸ್ ಬಂತು. ಬೌನ್ಸ್ ಚೆಕ್‌ಗೆ ಪ್ರಕ್ರಿಯೆ ಏನು?"],
     ["Obba vyakti nanage aivattu savira rupayi cheque kottanu, adu bounce ayitu. Cheque mottavannu hege vapas padeyuvudu?",
      "Nanna geleya nanninda hana eravalu padedanu, avana cheque pavati agade vapas bantu. Bounce cheque ge prakriye enu?"]),
    ("oos_tax", "income tax",
     ["I received an income tax notice for the last financial year. How do I reply to the tax department?",
      "My tax refund has not come for eight months. Where do I check the status of my refund?"],
     ["ಕಳೆದ ಆರ್ಥಿಕ ವರ್ಷಕ್ಕೆ ನನಗೆ ಆದಾಯ ತೆರಿಗೆ ನೋಟಿಸ್ ಬಂದಿದೆ. ತೆರಿಗೆ ಇಲಾಖೆಗೆ ಹೇಗೆ ಉತ್ತರಿಸುವುದು?",
      "ನನ್ನ ತೆರಿಗೆ ಮರುಪಾವತಿ ಎಂಟು ತಿಂಗಳಿಂದ ಬಂದಿಲ್ಲ. ನನ್ನ ಮರುಪಾವತಿಯ ಸ್ಥಿತಿಯನ್ನು ಎಲ್ಲಿ ಪರಿಶೀಲಿಸುವುದು?"],
     ["Kaleda arthika varshakke nanage adaya terige notice bandide. Terige ilakhege hege uttarisuvudu?",
      "Nanna terige marupavati entu tingalinda bandilla. Nanna marupavatiya sthitiyannu elli parishilisuvudu?"]),
    ("oos_theft", "criminal theft by a stranger",
     ["A thief stole my scooter from outside my house last night. How do I file a police complaint?",
      "Someone broke into my shop and stole cash from the drawer. What should I do first?"],
     ["ಕಳ್ಳನೊಬ್ಬ ಕಳೆದ ರಾತ್ರಿ ನನ್ನ ಮನೆಯ ಹೊರಗಿನಿಂದ ನನ್ನ ಸ್ಕೂಟರ್ ಕದ್ದನು. ಪೊಲೀಸ್ ದೂರು ಹೇಗೆ ನೀಡುವುದು?",
      "ಯಾರೋ ನನ್ನ ಅಂಗಡಿಗೆ ನುಗ್ಗಿ ಡ್ರಾಯರ್‌ನಿಂದ ಹಣ ಕದ್ದರು. ಮೊದಲು ನಾನು ಏನು ಮಾಡಬೇಕು?"],
     ["Kallanobba kaleda ratri nanna maneya horaginda nanna scooter kaddanu. Police duru hege needuvudu?",
      "Yaro nanna angadige nuggi drawer inda hana kaddaru. Modalu nanu enu madabeku?"]),
    ("oos_neighbour", "neighbour property dispute",
     ["My neighbour built a wall on my land without permission. How do I stop this encroachment?",
      "The people next door play loud music all night. Where do I complain about the noise?"],
     ["ನನ್ನ ನೆರೆಯವರು ಅನುಮತಿ ಇಲ್ಲದೆ ನನ್ನ ಜಮೀನಿನಲ್ಲಿ ಗೋಡೆ ಕಟ್ಟಿದ್ದಾರೆ. ಈ ಒತ್ತುವರಿಯನ್ನು ಹೇಗೆ ನಿಲ್ಲಿಸುವುದು?",
      "ಪಕ್ಕದ ಮನೆಯವರು ರಾತ್ರಿಯೆಲ್ಲ ಜೋರಾಗಿ ಸಂಗೀತ ಕೇಳುತ್ತಾರೆ. ಶಬ್ದದ ಬಗ್ಗೆ ಎಲ್ಲಿ ದೂರು ನೀಡುವುದು?"],
     ["Nanna nereyavaru anumati illade nanna jameeninalli gode kattiddare. Ee ottuvariyannu hege nillisuvudu?",
      "Pakkada maneyavaru ratriyella joragi sangeeta keluttare. Shabdada bagge elli duru needuvudu?"]),
    ("oos_traffic", "traffic challan",
     ["I got a traffic challan for jumping a signal. How do I pay the fine online?",
      "My driving licence was taken by the traffic police. How do I get it back?"],
     ["ಸಿಗ್ನಲ್ ಜಂಪ್ ಮಾಡಿದ್ದಕ್ಕಾಗಿ ನನಗೆ ಟ್ರಾಫಿಕ್ ಚಲನ್ ಬಂದಿದೆ. ದಂಡವನ್ನು ಆನ್‌ಲೈನ್‌ನಲ್ಲಿ ಹೇಗೆ ಪಾವತಿಸುವುದು?",
      "ಟ್ರಾಫಿಕ್ ಪೊಲೀಸರು ನನ್ನ ಡ್ರೈವಿಂಗ್ ಲೈಸೆನ್ಸ್ ತೆಗೆದುಕೊಂಡರು. ಅದನ್ನು ಹೇಗೆ ವಾಪಸ್ ಪಡೆಯುವುದು?"],
     ["Signal jump madiddakkagi nanage traffic challan bandide. Dandavannu online nalli hege pavatisuvudu?",
      "Traffic policesu nanna driving licence tegedukondaru. Adannu hege vapas padeyuvudu?"]),
    ("oos_bank_loan", "bank loan",
     ["The bank is asking me to repay a personal loan I took three years ago. Can I ask for more time to repay?",
      "My home loan interest rate went up and my monthly payment increased. Can I change to another bank?"],
     ["ಬ್ಯಾಂಕ್ ಮೂರು ವರ್ಷಗಳ ಹಿಂದೆ ನಾನು ತೆಗೆದುಕೊಂಡ ವೈಯಕ್ತಿಕ ಸಾಲವನ್ನು ಮರುಪಾವತಿಸಲು ಕೇಳುತ್ತಿದೆ. ಮರುಪಾವತಿಸಲು ಹೆಚ್ಚು ಸಮಯ ಕೇಳಬಹುದೇ?",
      "ನನ್ನ ಗೃಹ ಸಾಲದ ಬಡ್ಡಿ ದರ ಹೆಚ್ಚಾಯಿತು, ನನ್ನ ತಿಂಗಳ ಪಾವತಿ ಹೆಚ್ಚಾಯಿತು. ಬೇರೆ ಬ್ಯಾಂಕ್‌ಗೆ ಬದಲಾಯಿಸಬಹುದೇ?"],
     ["Bank mooru varshagala hinde nanu tegedukonda vaiyaktika salavannu marupavatisalu keluttide. Marupavatisalu hechu samaya kelabahude?",
      "Nanna gruha salada baddi dara hechayitu, nanna tingala pavati hechayitu. Bere bank ge badalayisabahude?"]),
    ("oos_visa", "visa / immigration",
     ["My work visa expires next month and my company has not renewed it. How do I extend my visa?",
      "I want to travel abroad for a job. What documents do I need for a work permit?"],
     ["ನನ್ನ ಕೆಲಸದ ವೀಸಾ ಮುಂದಿನ ತಿಂಗಳು ಮುಕ್ತಾಯಗೊಳ್ಳುತ್ತದೆ, ನನ್ನ ಕಂಪನಿ ಅದನ್ನು ನವೀಕರಿಸಿಲ್ಲ. ನನ್ನ ವೀಸಾವನ್ನು ಹೇಗೆ ವಿಸ್ತರಿಸುವುದು?",
      "ನಾನು ಕೆಲಸಕ್ಕಾಗಿ ವಿದೇಶಕ್ಕೆ ಪ್ರಯಾಣಿಸಲು ಬಯಸುತ್ತೇನೆ. ವರ್ಕ್ ಪರ್ಮಿಟ್‌ಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?"],
     ["Nanna kelasa visa mundina tingalu muktayagolluttade, nanna company adannu navikarisilla. Nanna visavannu hege vistarisuvudu?",
      "Nanu kelasakkagi videshakke prayanisalu bayasuttene. Work permit ge yava dakhalegalu beku?"]),
    ("oos_school_admin", "school admission (non-maintenance)",
     ["The school near my house is not giving admission to my child. Where do I complain about school admissions?",
      "My child's school increased the fees suddenly. Is there a limit on how much a school can charge?"],
     ["ನನ್ನ ಮನೆಯ ಹತ್ತಿರದ ಶಾಲೆ ನನ್ನ ಮಗುವಿಗೆ ಪ್ರವೇಶ ನೀಡುತ್ತಿಲ್ಲ. ಶಾಲಾ ಪ್ರವೇಶದ ಬಗ್ಗೆ ಎಲ್ಲಿ ದೂರು ನೀಡುವುದು?",
      "ನನ್ನ ಮಗುವಿನ ಶಾಲೆ ಇದ್ದಕ್ಕಿದ್ದಂತೆ ಶುಲ್ಕ ಹೆಚ್ಚಿಸಿದೆ. ಶಾಲೆ ಎಷ್ಟು ವಿಧಿಸಬಹುದು ಎಂಬುದಕ್ಕೆ ಮಿತಿ ಇದೆಯೇ?"],
     ["Nanna maneya hattirada shale nanna maguvige pravesha needuttilla. Shala praveshada bagge elli duru needuvudu?",
      "Nanna maguvina shale iddakkidante shulka hechiside. Shale eshtu vidhisabahudu embudakke miti ideye?"]),
    ("oos_business", "business partnership",
     ["My business partner took money from our company account without telling me. How do I settle a partnership dispute?",
      "I want to close my partnership firm. What is the process to dissolve a business partnership?"],
     ["ನನ್ನ ವ್ಯಾಪಾರ ಪಾಲುದಾರ ನನಗೆ ಹೇಳದೆ ನಮ್ಮ ಕಂಪನಿ ಖಾತೆಯಿಂದ ಹಣ ತೆಗೆದುಕೊಂಡನು. ಪಾಲುದಾರಿಕೆ ವಿವಾದವನ್ನು ಹೇಗೆ ಬಗೆಹರಿಸುವುದು?",
      "ನನ್ನ ಪಾಲುದಾರಿಕೆ ಸಂಸ್ಥೆಯನ್ನು ಮುಚ್ಚಲು ಬಯಸುತ್ತೇನೆ. ವ್ಯಾಪಾರ ಪಾಲುದಾರಿಕೆಯನ್ನು ವಿಸರ್ಜಿಸಲು ಪ್ರಕ್ರಿಯೆ ಏನು?"],
     ["Nanna vyapara paludara nanage helade namma company khateyinda hana tegedukondanu. Paludarike vivadavannu hege bageharisuvudu?",
      "Nanna paludarike samstheyannu mucchalu bayasuttene. Vyapara paludarikeyannu visarjisalu prakriye enu?"]),
]

for _bid, _domain, _en, _kn, _ro in OOS_DOMAINS:
    _reg(B(_bid, "hn_f", en=_en, kn=_kn, ro=_ro,
           issues={}, facts={"in_scope": "denied"},
           enums={"claimant_sex": "U", "claimant_role": "other"}))

# --- forum add-on (appended as a second sentence) --------------------------
FORUM_ADDON = {
    "en": ["Where should I file my case?",
           "Where do I file a case for this?"],
    "kn": ["ನಾನು ಎಲ್ಲಿ ಕೇಸ್ ಹಾಕಬೇಕು?",
           "ಇದಕ್ಕಾಗಿ ಎಲ್ಲಿ ಅರ್ಜಿ ಹಾಕಬೇಕು?"],
    "kn_roman": ["Nanu elli case hakabeku?",
                 "Idakkagi elli arji hakabeku?"],
}

# --- neutral framing (label-neutral; only multiplies surface variety) -----
# Prefixes/suffixes carry no new issue or fact: they are emotional/neutral
# openers and closers. Span offsets are shifted by the prefix length.
FRAMING = {
    "en": {
        "prefix": ["Please help me. ", "I need some advice. ",
                   "I am writing to ask for help. "],
        "suffix": [" I am very worried about this.",
                   " I feel lost about all of this.",
                   " This has been happening for a long time."],
    },
    "kn": {
        "prefix": ["ದಯವಿಟ್ಟು ನನಗೆ ಸಹಾಯ ಮಾಡಿ. ", "ನನಗೆ ಸ್ವಲ್ಪ ಸಲಹೆ ಬೇಕು. ",
                   "ಸಹಾಯ ಕೇಳಲು ಬರೆಯುತ್ತಿದ್ದೇನೆ. "],
        "suffix": [" ಇದರ ಬಗ್ಗೆ ನನಗೆ ತುಂಬಾ ಚಿಂತೆಯಾಗಿದೆ.",
                   " ಇದರ ಬಗ್ಗೆ ನನಗೆ ತುಂಬಾ ಗೊಂದಲವಿದೆ.",
                   " ಇದು ಬಹಳ ಸಮಯದಿಂದ ನಡೆಯುತ್ತಿದೆ."],
    },
    "kn_roman": {
        "prefix": ["Dayavittu nanage sahaya madi. ",
                   "Nanage swalpa salahe beku. ",
                   "Sahaya kelalu bareyuttiddene. "],
        "suffix": [" Idara bagge nanage tumba chinteyagide.",
                   " Idara bagge nanage tumba gondalavide.",
                   " Idu bahala samayadinda nadeyuttide."],
    },
}

# --- preset multi-issue combos (block ids) ---------------------------------
COMBOS = [
    ["divorce_want", "maint_wife"],
    ["divorce_want", "maint_wife", "custody_mother"],
    ["maint_wife", "custody_mother"],
    ["custody_mother", "maint_child_only"],
    ["residence_thrown_out", "violence_beats"],
    ["violence_beats", "maint_wife", "residence_thrown_out"],
    ["stridhan_held", "maint_wife"],
    ["stridhan_held", "residence_thrown_out"],
    ["stridhan_sold", "maint_wife"],
    ["divorce_want", "custody_mother"],
    ["divorce_pending", "maint_interim_pending"],
    ["divorce_decree_done", "maint_lump_sum"],
    ["joint_property_hma_pending", "maint_wife"],
    ["maint_arrears", "joint_property_no_hma"],
    ["birth_cert", "maint_child_only"],
    ["violence_dv_comp", "lockout"],
    ["violence_child_risk", "custody_mother"],
    ["maint_wife", "residence_live_in_house"],
    ["custody_father", "maint_wife"],
    ["stridhan_held", "custody_mother", "maint_wife"],
    ["residence_explicit_only", "maint_wife"],
    ["lockout", "maint_wife"],
    ["divorce_mutual", "maint_lump_sum"],
    ["neg_maintenance", "custody_mother"],
    ["maint_elder_parent", "procedure_court"],
    ["coloc_stay_with_child", "maint_wife"],
    ["coloc_custody_word", "maint_wife"],
    ["pre_bnss", "maint_arrears"],
]

CORE_SINGLE = ["maint_wife", "maint_child_only", "maint_lump_sum",
               "maint_interim_pending", "maint_post_decree", "custody_mother",
               "custody_father", "residence_thrown_out",
               "residence_live_in_house", "violence_beats", "violence_threats",
               "divorce_want", "divorce_mutual", "stridhan_held",
               "joint_property", "birth_cert", "procedure_court",
               "procedure_how_file", "maint_child_self"]

# Allocation: (kind, count). Sums to N_TOTAL = 5000.
PLAN = [
    ("single", 1400),
    ("combo", 1300),
    ("hn_a", 250),
    ("hn_b", 300),
    ("hn_c", 350),
    ("hn_d", 300),
    ("hn_e", 300),
    ("hn_f", 600),
    ("neg", 150),
    ("conflict", 50),
]
assert sum(c for _, c in PLAN) == N_TOTAL

HN_BLOCKS = {
    "hn_a": ["coloc_stay_with_child", "coloc_custody_word"],
    "hn_b": ["residence_explicit_only", "lockout", "violence_dv_comp"],
    "hn_c": ["divorce_pending", "divorce_being_filed", "divorce_js_only",
             "divorce_restitution", "divorce_decree_done"],
    "hn_d": ["stridhan_sold", "stridhan_safe", "stridhan_never_asked",
             "joint_property_hma_pending", "joint_property_no_hma"],
    "hn_e": ["maint_arrears", "maint_vary", "maint_elder_parent",
             "maint_male_self", "maint_father_child_only"],
    "hn_f": ["hypothetical", "third_party", "quoted", "pre_bnss",
             "past_event"],
    "hn_f_oos": [b for b, _, _, _, _ in OOS_DOMAINS],
    "neg": ["neg_maintenance", "neg_divorce", "neg_custody",
            "neg_decree_mutual", "neg_no_order"],
    "conflict": ["conflict_divorce"],
}

# ---------------------------------------------------------------- generation
SPAN_RE = re.compile(r"\[\[([A-Za-z_0-9]+):([^\]]+)\]\]")

_INTENT_RANK = {"uncertain": 0, "denied": 1, "incidental": 2, "requested": 3}
_MODALITY_RANK = {"present": 0, "past": 1, "future": 2,
                  "hypothetical": 3, "quoted": 4}


def _render_block(block, lang, rng):
    """Render one block template in `lang`; return (clean_text, spans)."""
    key = {"en": "en", "kn": "kn", "kn_roman": "ro"}[lang]
    template = rng.choice(block[key])
    slots = {k: rng.choice(v) for k, v in SLOTS[lang].items()}
    text = template.format(**slots)
    spans = []
    out = []
    pos = 0
    for m in SPAN_RE.finditer(text):
        out.append(text[pos:m.start()])
        start = sum(len(s) for s in out)
        phrase = m.group(2)
        out.append(phrase)
        spans.append({"key": m.group(1),
                      "kind": "fact" if m.group(1) in FACTS else "issue",
                      "text": phrase, "start": start,
                      "end": start + len(phrase)})
        pos = m.end()
    out.append(text[pos:])
    return "".join(out), spans


def _merge_issues(base, extra, warnings):
    for k, v in extra.items():
        if k not in base:
            base[k] = v
            continue
        old = base[k]
        if old == v:
            continue
        if {old, v} == {"requested", "denied"}:
            base[k] = "uncertain"
            warnings.append(f"issue-conflict:{k}")
        elif _INTENT_RANK[v] > _INTENT_RANK[old]:
            base[k] = v


def _merge_facts(base, extra, warnings):
    for k, v in extra.items():
        old = base.get(k, "unknown")
        if old == v:
            continue
        if old == "unknown":
            base[k] = v
        elif v == "unknown":
            continue
        else:
            base[k] = "conflicting"
            warnings.append(f"fact-conflict:{k}:{old}/{v}")


def _merge_enums(base, extra):
    for k, v in extra.items():
        if k == "modality_time":
            if _MODALITY_RANK[v] > _MODALITY_RANK[base.get(k, "present")]:
                base[k] = v
        elif base.get(k) in (None, "U", "other"):
            base[k] = v
        elif base.get(k) != v:
            pass  # keep primary block's sex/role on conflict


def build_record(block_ids, lang, rng):
    """Compose one record from 1+ blocks. Returns (record-dict, warnings)."""
    warnings = []
    issues = {i: "uncertain" for i in ISSUES}
    facts = {f: "unknown" for f in FACTS}  # every block must set in_scope
    enums = {"claimant_sex": "U", "claimant_role": "other",
             "modality_time": "present"}
    texts, spans = [], []
    for bid in block_ids:
        block = BLOCKS[bid]
        text, bspans = _render_block(block, lang, rng)
        offset = sum(len(t) + 1 for t in texts)  # +1 for the joining space
        for s in bspans:
            spans.append({"key": s["key"], "kind": s["kind"],
                          "text": s["text"], "start": s["start"] + offset,
                          "end": s["end"] + offset})
        texts.append(text)
        _merge_issues(issues, block["issues"], warnings)
        _merge_facts(facts, block["facts"], warnings)
        _merge_enums(enums, block["enums"])
    # Forum add-on: 25% of non-procedure, in-scope records ask which court.
    if rng.random() < 0.25 and issues.get("procedure") != "requested" \
            and facts["in_scope"] == "supported" \
            and "hypothetical" not in block_ids \
            and "quoted" not in block_ids:
        key = {"en": "en", "kn": "kn", "kn_roman": "kn_roman"}[lang]
        texts.append(rng.choice(FORUM_ADDON[key]))
        if issues["procedure"] == "uncertain":
            issues["procedure"] = "incidental"
    text = " ".join(texts)
    # Neutral framing: prefix shifts span offsets; suffix does not.
    if rng.random() < 0.45:
        prefix = rng.choice(FRAMING[lang]["prefix"])
        for s in spans:
            s["start"] += len(prefix)
            s["end"] += len(prefix)
        text = prefix + text
    if rng.random() < 0.35:
        text = text + rng.choice(FRAMING[lang]["suffix"])
    # OOS convention: every issue stays uncertain; facts stay unknown except
    # in_scope denied (already merged). Re-assert after merges.
    if facts["in_scope"] == "denied":
        issues = {i: "uncertain" for i in ISSUES}
    cluster = BLOCKS[block_ids[0]]["cluster"]
    if len(block_ids) > 1:
        cluster = "combo"
    if facts["in_scope"] == "unknown":
        raise ValueError(f"block(s) {block_ids} never set in_scope")
    rec = {"lang": lang, "text": text, "issues": issues, "facts": facts,
           "enums": enums, "spans": spans,
           "meta": {"cluster": cluster, "blocks": list(block_ids)}}
    return rec, warnings


def generate(seed=SEED):
    rng = random.Random(seed)
    records = []
    seen = set()
    warn_counts = Counter()
    have = Counter()  # bucket -> records made so far (incremental; no rescan)
    lang_pick = (["en"] * 2 + ["kn", "kn_roman"])  # 50% EN, 25% KN, 25% roman
    attempts = 0
    while len(records) < N_TOTAL:
        attempts += 1
        if attempts > N_TOTAL * 100:
            raise RuntimeError("could not reach 5000 unique records")
        bucket = None
        for kind, count in PLAN:
            if have[kind] < count:
                bucket = kind
                break
        if bucket is None:
            break
        lang = rng.choice(lang_pick)
        if bucket == "single":
            bids = [rng.choice(CORE_SINGLE)]
        elif bucket == "combo":
            bids = list(rng.choice(COMBOS))
        elif bucket == "hn_f":
            # ~58% family-law hn_f (hypothetical / third-party / quoted /
            # pre-BNSS / past) vs ~42% OOS domains, so OOS is ~250/600.
            pool = (HN_BLOCKS["hn_f"] if rng.random() < 0.58
                    else HN_BLOCKS["hn_f_oos"])
            bids = [rng.choice(pool)]
        else:
            bids = [rng.choice(HN_BLOCKS[bucket])]
        rec, warns = build_record(bids, lang, rng)
        for w in warns:
            warn_counts[w] += 1
        key = (lang, rec["text"])
        if key in seen:
            continue
        seen.add(key)
        records.append(rec)
        have[_bucket_of(rec)] += 1
    rng.shuffle(records)
    val = records[:N_VAL]
    train = records[N_VAL:]
    for i, r in enumerate(train, 1):
        r["id"] = f"SYN-TR-{i:04d}"
        r["meta"]["split"] = "train"
    for i, r in enumerate(val, 1):
        r["id"] = f"SYN-VA-{i:04d}"
        r["meta"]["split"] = "validation"
    # Reorder keys: id first.
    for r in train + val:
        r2 = {"id": r.pop("id")}
        r2.update(r)
        r.clear()
        r.update(r2)
    return train, val, warn_counts


def _bucket_of(rec):
    cluster = rec["meta"]["cluster"]
    if cluster == "combo":
        return "combo"
    if cluster == "core":
        return "single"
    return cluster


def validate(train, val):
    """Schema + span-offset self-check; raises on the first bad record."""
    seen_texts = set()
    for r in train + val:
        assert set(r["issues"]) == set(ISSUES), r["id"]
        assert set(r["facts"]) == set(FACTS), r["id"]
        assert all(v in INTENTS for v in r["issues"].values()), r["id"]
        assert all(v in FACT_STATES for v in r["facts"].values()), r["id"]
        assert r["enums"]["claimant_sex"] in ("F", "M", "U"), r["id"]
        assert r["enums"]["claimant_role"] in (
            "spouse", "parent", "child", "other"), r["id"]
        assert r["enums"]["modality_time"] in (
            "present", "past", "future", "hypothetical", "quoted"), r["id"]
        assert r["lang"] in ("en", "kn", "kn_roman"), r["id"]
        for s in r["spans"]:
            assert r["text"][s["start"]:s["end"]] == s["text"], (r["id"], s)
            assert s["kind"] in ("fact", "issue"), r["id"]
        key = (r["lang"], r["text"])
        assert key not in seen_texts, ("duplicate text", r["id"])
        seen_texts.add(key)


def manifest(train, val):
    allr = train + val
    return {
        "name": "synthetic_v7_1",
        "seed": SEED,
        "n_total": len(allr),
        "n_train": len(train),
        "n_validation": len(val),
        "method": "statutory-grammar paraphrase templates + hard-negative "
                  "perturbations; never from test banks",
        "languages": dict(Counter(r["lang"] for r in allr)),
        "clusters": dict(Counter(r["meta"]["cluster"] for r in allr)),
        "issues_requested": {
            i: sum(1 for r in allr if r["issues"][i] == "requested")
            for i in ISSUES},
        "issues_denied": {
            i: sum(1 for r in allr if r["issues"][i] == "denied")
            for i in ISSUES},
        "facts_supported": {
            f: sum(1 for r in allr if r["facts"][f] == "supported")
            for f in FACTS},
        "facts_denied": {
            f: sum(1 for r in allr if r["facts"][f] == "denied")
            for f in FACTS},
        "facts_conflicting": {
            f: sum(1 for r in allr if r["facts"][f] == "conflicting")
            for f in FACTS},
        "enums_sex": dict(Counter(r["enums"]["claimant_sex"] for r in allr)),
        "enums_role": dict(Counter(r["enums"]["claimant_role"] for r in allr)),
        "enums_modality": dict(Counter(r["enums"]["modality_time"]
                                       for r in allr)),
        "mean_words_en": round(sum(len(r["text"].split()) for r in allr
                                   if r["lang"] == "en") /
                               max(1, sum(1 for r in allr
                                          if r["lang"] == "en")), 2),
        "schema": {"issues": ISSUES, "facts": FACTS,
                   "intents": list(INTENTS), "fact_states": list(FACT_STATES)},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/synthetic_v7_1",
                    help="output directory")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args(argv)
    train, val, warns = generate(seed=args.seed)
    validate(train, val)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "train.jsonl", "w", encoding="utf-8") as fh:
        for r in train:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out / "validation.jsonl", "w", encoding="utf-8") as fh:
        for r in val:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    man = manifest(train, val)
    man["merge_warnings"] = dict(warns)
    with open(out / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(man, fh, ensure_ascii=False, indent=1)
    with open(out / "schema.json", "w", encoding="utf-8") as fh:
        json.dump({"issues": ISSUES, "facts": FACTS,
                   "intents": list(INTENTS), "fact_states": list(FACT_STATES),
                   "enums": {
                       "claimant_sex": ["F", "M", "U"],
                       "claimant_role": ["spouse", "parent", "child", "other"],
                       "modality_time": ["present", "past", "future",
                                         "hypothetical", "quoted"]},
                   "span": {"key": "fact-or-issue name",
                            "kind": "fact | issue",
                            "text": "surface phrase",
                            "start": "char offset", "end": "char offset"}},
                  fh, ensure_ascii=False, indent=1)
    print(f"wrote {len(train)} train + {len(val)} validation "
          f"-> {out} (seed={args.seed})")
    print("languages:", man["languages"])
    print("clusters:", man["clusters"])
    print("merge warnings:", dict(warns) or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
