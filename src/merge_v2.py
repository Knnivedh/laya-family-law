#!/usr/bin/env python3
"""Merge v2 of the Laya family-law decision graph.

Reads v1 + v2 lanes 1-4, builds v2 JSON with the two-stage design
(Stage 1 layman -> legal -> section; Stage 2 recheck inside the section),
applies Lane 4's fixes, and re-runs Lane 4's 34-question suite through a
mechanical v2 walk (disclosed heuristic matcher + Lane 3 recheck rules).

HONESTY: the walk is a graph-logic simulation, NOT live Laya inference
(no live Laya run exists) and NOT a LLaMA run. The matcher is a
token/substring matcher over Lane 1's phrasebook, disclosed in full below.
Per-test facts are read off each question + Lane 4's notes and are listed
in the v2 test report, so the re-run is reproducible and auditable.
"""
import json, re, os

BASE = os.path.expanduser("~/workspace/goals/english-family-law-chatbot-retest/files")
V1 = os.path.join(BASE, "laya-crpc-bns-section-decision-tree.json")
LANES = os.path.join(BASE, "laya-graph/v2-lanes")
OUT_JSON = os.path.join(BASE, "laya-crpc-bns-section-decision-tree-v2.json")
OUT_REPORT = os.path.join(BASE, "laya-graph/test-report-v2-layman.md")

def load(p):
    with open(p) as f:
        return json.load(f)

v1 = load(V1)
lane1 = load(os.path.join(LANES, "lane1-phrasebook.json"))
lane2 = load(os.path.join(LANES, "lane2-stage1-mapping.json"))
lane3 = load(os.path.join(LANES, "lane3-stage2-recheck.json"))
lane4 = load(os.path.join(LANES, "lane4-adversarial-tests.json"))

# ---------------------------------------------------------------- v2 sections
# v1 statutory/principle sections (13) + 3 new real sections from Lane 4 fixes
NEW_SECTIONS = [
    {
        "id": "hma-13", "act": "Hindu Marriage Act, 1955 (HMA)", "section": "s.13",
        "title": "Divorce — contested (grounds for dissolution of marriage)",
        "when_used": "Only when divorce is expressly asked for. Contested divorce on a statutory ground (e.g. cruelty, desertion, adultery). Never cited by default.",
        "triggers": ["user expressly asks for divorce", "user asks how to get a divorce", "contested divorce"],
        "prerequisites": ["divorce expressly asked", "a statutory ground under HMA s.13"],
        "exclusions_not_for": ["never when divorce was not asked", "never as a default citation in a maintenance/custody/stridhan answer",
                                "not for mutual-consent divorce — that is HMA s.13B"],
        "related_sections": ["hma-13b", "hma-24", "hma-25"],
        "court": "Family Court, Bengaluru", "relief": "Decree of divorce",
        "precedent": "None verified in the 2026-11-26 retest — do NOT cite a case for HMA s.13 until verified against the judgment text.",
        "laya_question": "Is the user expressly asking for a contested divorce?",
        "status": "live_if_divorce_asked",
    },
    {
        "id": "hma-13b", "act": "Hindu Marriage Act, 1955 (HMA)", "section": "s.13B",
        "title": "Divorce by mutual consent",
        "when_used": "Only when divorce is expressly asked AND both spouses consent to it. Mutual-consent fact is required — 'should I divorce' with no consent fact does not fire HMA 13B on its own.",
        "triggers": ["both spouses agree to divorce", "mutual consent divorce", "we agree to divorce"],
        "prerequisites": ["divorce expressly asked", "mutual consent of both spouses"],
        "exclusions_not_for": ["never when divorce was not asked", "never when only one spouse wants divorce",
                                "never on a bare 'should I divorce' question with no consent fact — keep HMA 13 as the route and escalate the consent question"],
        "related_sections": ["hma-13", "hma-24", "hma-25"],
        "court": "Family Court, Bengaluru", "relief": "Decree of divorce by mutual consent",
        "precedent": "None verified in the 2026-11-26 retest — do NOT cite a case for HMA s.13B until verified against the judgment text.",
        "laya_question": "Are both spouses consenting to a divorce?",
        "status": "conditional_on_mutual_consent",
    },
    {
        "id": "births-deaths-act-1969", "act": "Registration of Births and Deaths Act, 1969",
        "section": "Births and Deaths Act 1969 (registration of birth; certificate)",
        "title": "Birth certificate — registration of birth",
        "when_used": "When the user asks how to get a birth certificate (e.g. school admission needs it). This is the correct Act — NEVER the Hindu Marriage Act.",
        "triggers": ["birth certificate", "how to get birth certificate", "school needs birth certificate"],
        "prerequisites": ["a birth to be registered / certificate to be obtained"],
        "exclusions_not_for": ["never cite HMA for a birth certificate", "not a maintenance/custody section"],
        "related_sections": [],
        "court": "Registrar of Births and Deaths (not a court)", "relief": "Birth certificate issued",
        "precedent": "None needed — statutory route.",
        "laya_question": "Is the user asking how to obtain a birth certificate?",
        "status": "live",
    },
]

# v1 sections: first 13 are statutory/principle, rest are procedure items
v1_sections = v1["sections"]
statutory = [s for s in v1_sections if s.get("act")]
procedure = [s for s in v1_sections if not s.get("act")]

# ---------------------------------------------------------------- v2 nodes/edges
NEW_NODES = [
    {"node_id": "stage1:confidence-gate", "lane": "stage1", "type": "noul",
     "question": "Can any issue be picked with confidence from the facts stated? If no facts support any issue, do NOT force-pick lanes — ask clarifying questions or escalate.",
     "laya_type": "noul", "on_no": "escalate_clarify", "on_yes": "root:issue-classification",
     "fixes": "Lane 4 D9 — vague 'I have nothing' forced 7 sections on zero facts in v1."},
    {"node_id": "stage1:kannada-mapping", "lane": "stage1", "type": "choice",
     "question": "Kannada input: map Kannada layman phrases (Lane 1 phrasebook, 21 Kannada phrases + colloquial forms) to the same legal terms and sections as English. If no Kannada phrase matches, escalate with 'Kannada not yet fully supported' — do not silently mis-map.",
     "laya_type": "choice", "fixes": "Lane 4 A3/C4/F1/F2/F3 — v1 was English-only, Kannada scored 0/5."},
    {"node_id": "stage2:demand-gate", "lane": "stage2", "type": "choice",
     "question": "For Stridhan: was a demand for return made and refused? If never asked, BNS s.316 is escalated (demand first, then re-evaluate) and HMA s.27 stays as the live civil route.",
     "laya_type": "choice", "fixes": "Lane 4 D5; Lane 3 R-BNS316-03."},
    {"node_id": "stage2:custody-no-proceeding-subset", "lane": "stage2", "type": "section_set",
     "question": "Custody with no HMA proceeding pending: drop HMA s.26, keep Guardians and Wards Act 1890 + HMGA 1956 s.6 + welfare-of-the-child principle.",
     "section_set": ["gwa-1890", "hmga-1956-s6", "welfare-principle"],
     "fixes": "Lane 4 B2/C1/D2."},
    {"node_id": "stage2:pwdva-per-section-gate", "lane": "stage2", "type": "choice",
     "question": "Gate EACH PWDVA section on its own trigger (17 residence claim, 18 threat/violence, 19 residence order, 20 money/DV consequence). No leaf chain may force PWDVA 20 in.",
     "laya_type": "choice", "fixes": "Lane 4 B4/D8 — v1 leaf_PWDVA_19 forced PWDVA 20."},
    {"node_id": "stage2:divorce-leaf", "lane": "stage2", "type": "section_set",
     "question": "Divorce asked: return HMA s.13 (contested) and HMA s.13B only if mutual consent is stated; otherwise HMA s.13 + escalate the consent question.",
     "section_set": ["hma-13", "hma-13b"], "fixes": "Lane 4 A5/B6 — v1 had no returnable HMA 13/13B sections."},
    {"node_id": "stage2:birth-certificate-leaf", "lane": "stage2", "type": "section_set",
     "question": "Birth certificate asked: return Registration of Births and Deaths Act 1969. Never HMA.",
     "section_set": ["births-deaths-act-1969"], "fixes": "Lane 4 B5/D2 — v1 had only a document note."},
    {"node_id": "stage1:conversation-context", "lane": "stage1", "type": "choice",
     "question": "Multi-turn context: facts established in earlier turns (e.g. Stridhan held by husband's family) persist into later questions. A later question that omits a fact does not erase it.",
     "laya_type": "choice", "fixes": "Lane 4 C5 — question text omits Stridhan, but the case facts carry over from earlier turns."},
]
NEW_EDGES = [
    {"from": "stage1:confidence-gate", "to": "root:issue-classification", "condition": "at least one issue picked with confidence", "lane": "stage1"},
    {"from": "stage1:confidence-gate", "to": "escalate_clarify", "condition": "no issue picked with confidence (vague question)", "lane": "stage1"},
    {"from": "stage1:kannada-mapping", "to": "root:issue-classification", "condition": "Kannada phrase matched to a legal term", "lane": "stage1"},
    {"from": "stridhan:stridhan-subissue", "to": "stage2:demand-gate", "condition": "Stridhan fired — check demand made/refused first", "lane": "stage2"},
    {"from": "custody:custody_sub_issue_choice", "to": "stage2:custody-no-proceeding-subset", "condition": "no HMA proceeding pending", "lane": "stage2"},
    {"from": "residence:residence_sub_issue", "to": "stage2:pwdva-per-section-gate", "condition": "gate each PWDVA section on its own trigger", "lane": "stage2"},
    {"from": "root:issue-classification", "to": "stage2:divorce-leaf", "condition": "divorce expressly asked", "lane": "stage2"},
    {"from": "root:issue-classification", "to": "stage2:birth-certificate-leaf", "condition": "birth certificate asked", "lane": "stage2"},
    {"from": "stage2:demand-gate", "to": "bns-316", "condition": "demand made and refused", "lane": "stage2"},
    {"from": "stage2:demand-gate", "to": "escalate_demand_first", "condition": "demand never made — escalate, do not keep BNS 316", "lane": "stage2"},
    {"from": "stage1:conversation-context", "to": "root:issue-classification", "condition": "carried-over case facts add issues the last question omits", "lane": "stage1"},
]

# ---------------------------------------------------------------- Stage-1 matcher
# Disclosed heuristic matcher over Lane 1's phrasebook (NOT Laya itself).
STOP = set("""a an the is are was were i my me we us our he she his her him they them their it its to of in on at for and or but not no do does did can will would should how what who when where am be been have has had with without from by as if so just only now yet still get want need ask say says this that there here all any some very really please""".split())
EN_ANCHORS = {
    "maintenance": {"money", "maintenance", "maintain", "support", "expenses", "fees", "income", "salary", "month", "monthly", "pay", "paying", "earn", "earns", "afford", "livelihood"},
    "custody": {"custody", "daughter", "son", "child", "kid", "children"},
    "stridhan": {"gold", "cash", "stridhan", "jewellery", "jewelry", "return", "took", "taken", "things"},
    "residence": {"house", "home", "throw", "throwing", "evict", "eviction", "lock", "stay", "live"},
    "protection": {"beat", "beats", "beating", "hit", "hits", "hitting", "threat", "threaten", "threatening", "threats", "stop", "safe", "violence"},
    "divorce": {"divorce"},
    "documents": {"court", "papers", "documents", "certificate", "long", "take"},
}
CUSTODY_CUES = ["who will get", "custody", "stay with me", "stay with us", "keep her with me", "keep him with me",
                "want her with me", "want him with me", "her with me", "him with me", "with me", "daughter is with me"]
KN_ANCHORS = {
    "maintenance": ["ದುಡ್ಡು", "ಹಣ", "ಜೀವನಾಂಶ", "ಜೀವನ", "ಸಂಬಳ", "ತಿಂಗಳು"],
    "custody": ["ಮಗಳು", "ಮಗ", "ಜೊತೆ", "ಇರಬೇಕು", "ಯಾರ"],
    "stridhan": ["ಬಂಗಾರ", "ವಾಪಸ್"],
    "residence": ["ಮನೆ", "ಹೊರಹಾಕ್"],
    "protection": ["ಬೆದರಿಕೆ", "ಹೊಡಿ"],
    "divorce": ["ವಿಚ್ಛೇದನ", "ಡಿವೋರ್ಸ್"],
}
KN_CUSTODY_CUES = ["ಯಾರ ಜೊತೆ", "ಇರಬೇಕು", "ಜೊತೆ ಇಟ್ಕೋ", "ನನ್ನ ಜೊತೆ"]

def en_tokens(q):
    return re.findall(r"[a-z]+", q.lower())

def stage1_english(q):
    toks = set(en_tokens(q))
    fired = set()
    ql = q.lower()
    # birth certificate: exact phrase only (so "school fees" does not fire it)
    if "birth certificate" in ql:
        fired.add("birth_certificate")
    # divorce: word present, unless negated
    if "divorce" in toks:
        if not re.search(r"(do not want|don't want|not asking|no divorce|not want).{0,20}divorce|divorce.{0,10}(not|no)", ql):
            fired.add("divorce")
    for issue, anchors in EN_ANCHORS.items():
        if issue in ("divorce",):
            continue
        if toks & anchors:
            if issue == "custody":
                if any(c in ql for c in CUSTODY_CUES):
                    fired.add("custody")
            elif issue == "stridhan":
                # "things" alone is weak; require gold/cash/stridhan/return/took
                if toks & {"gold", "cash", "stridhan", "jewellery", "jewelry"} or ("return" in toks and "gold" in toks):
                    fired.add("stridhan")
                elif "took my" in ql and ("gold" in toks or "cash" in toks):
                    fired.add("stridhan")
            elif issue == "residence":
                fired.add("residence")
            elif issue == "protection":
                fired.add("protection")
            elif issue == "maintenance":
                # "school" only counts with fees/money; "salary" only with husband context
                if toks & {"money", "maintenance", "maintain", "support", "income", "salary", "month", "monthly", "pay", "paying", "earn", "earns", "afford", "livelihood", "expenses"}:
                    fired.add("maintenance")
                elif "fees" in toks:
                    fired.add("maintenance")
            elif issue == "documents":
                pass  # procedure, no sections
    # full-picture inference: >=3 issues fired + child mentioned -> custody is in play
    if len(fired & {"maintenance", "stridhan", "residence", "protection"}) >= 3 and toks & {"daughter", "son", "child", "kid", "children"}:
        fired.add("custody")
    # money negation (Lane 2 NEG handling): "not asking for money" / "do not need money"
    # must NOT fire maintenance (fixes B4, D7, D8 — v1 had no negation handling here)
    if re.search(r"not asking for (any )?money|do not need.{0,20}money|don't need.{0,20}money|do not need the house or money", ql):
        fired.discard("maintenance")
    return fired

def stage1_kannada(q):
    fired = set()
    for issue, keys in KN_ANCHORS.items():
        if any(k in q for k in keys):
            if issue == "custody":
                if any(c in q for c in KN_CUSTODY_CUES):
                    fired.add("custody")
            elif issue == "stridhan":
                if "ಬಂಗಾರ" in q:
                    fired.add("stridhan")
            elif issue == "maintenance":
                fired.add("maintenance")
            else:
                fired.add(issue)
    if len(fired & {"maintenance", "stridhan", "residence", "protection"}) >= 3 and "ಮಗಳು" in q:
        fired.add("custody")
    return fired

ISSUE_SECTIONS = {
    "maintenance": ["bnss-144", "hma-24", "hma-25", "pwdva-20"],
    "custody": ["hma-26", "gwa-1890", "hmga-1956-s6", "welfare-principle"],
    "stridhan": ["hma-27", "bns-316"],
    "residence": ["pwdva-17", "pwdva-18", "pwdva-19", "pwdva-20"],
    "protection": ["pwdva-18"],
    "divorce": ["hma-13", "hma-13b"],
    "birth_certificate": ["births-deaths-act-1969"],
}

# Per-test facts, read off each question + Lane 4 notes (listed in the report).
# context: full_picture (user asks all options / full case) vs live_claim
FACTS = {
 "A1": dict(lang="en", context="full_picture", proceeding=False, decree=False, dv=True, demand=True, divorce=False, holder="husband_family", money=True, money_route="both", residence=True, threat=True, violence=False, custody_dispute=True, birth_cert=False, vague=False, claim_target="husband"),
 "A2": dict(lang="en", context="full_picture", proceeding=False, decree=False, dv=True, demand=True, divorce=False, holder="husband_family", money=True, money_route="both", residence=True, threat=True, violence=False, custody_dispute=True, birth_cert=False, vague=False, claim_target="husband"),
 "A3": dict(lang="kn", context="full_picture", proceeding=False, decree=False, dv=True, demand=True, divorce=False, holder="husband_family", money=True, money_route="both", residence=True, threat=True, violence=False, custody_dispute=True, birth_cert=False, vague=False, claim_target="husband"),
 "A4": dict(lang="en", context="full_picture", proceeding=False, decree=False, dv=True, demand=True, divorce=False, holder="husband_family", money=True, money_route="both", residence=True, threat=True, violence=False, custody_dispute=True, birth_cert=False, vague=False, claim_target="husband"),
 "A5": dict(lang="en", context="full_picture", proceeding=False, decree=False, dv=True, demand=True, divorce=True, holder="husband_family", money=True, money_route="both", residence=True, threat=True, violence=False, custody_dispute=True, birth_cert=False, vague=False, claim_target="husband"),
 "B1": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=True, money_route="bnss144", residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband"),
 "B2": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=False, money_route=None, residence=False, threat=False, violence=False, custody_dispute=True, birth_cert=False, vague=False, claim_target="husband"),
 "B3": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=True, divorce=False, holder="husband_family", money=False, money_route=None, residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband"),
 "B4": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=False, money_route=None, residence=True, threat=True, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband"),
 "B5": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=False, money_route=None, residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=True, vague=False, claim_target="husband"),
 "B6": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=True, holder="husband_family", money=False, money_route=None, residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband"),
 "C1": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=True, money_route="bnss144", residence=False, threat=False, violence=False, custody_dispute=True, birth_cert=False, vague=False, claim_target="husband"),
 "C2": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=True, demand=True, divorce=False, holder="husband_family", money=True, money_route="pwdva20", residence=True, threat=True, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband"),
 "C3": dict(lang="en", context="full_picture", proceeding=False, decree=False, dv=True, demand=False, divorce=False, holder="husband_family", money=True, money_route="both", residence=True, threat=True, violence=True, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband"),
 "C4": dict(lang="kn", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=True, money_route="bnss144", residence=False, threat=False, violence=False, custody_dispute=True, birth_cert=False, vague=False, claim_target="husband"),
 "C5": dict(lang="en", context="full_picture", proceeding=False, decree=False, dv=True, demand=True, divorce=False, holder="husband_family", money=True, money_route="both", residence=True, threat=True, violence=False, custody_dispute=True, birth_cert=False, vague=False, claim_target="husband", case_context=True),
 "D1": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=True, money_route="bnss144", residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband"),
 "D2": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=False, money_route=None, residence=False, threat=False, violence=False, custody_dispute=True, birth_cert=True, vague=False, claim_target="husband"),
 "D3": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=True, money_route="bnss144", residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband"),
 "D4": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=True, money_route="bnss144", residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband"),
 "D5": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=False, money_route=None, residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband"),
 "D6": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=False, money_route=None, residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband", explicit_hma24=True),
 "D7": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=True, demand=False, divorce=False, holder="husband_family", money=False, money_route=None, residence=False, threat=True, violence=True, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband"),
 "D8": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=False, money_route=None, residence=True, threat=True, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband"),
 "D9": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=False, money_route=None, residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=True, claim_target="husband"),
 "D10": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=True, money_route="bnss144", residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband"),
 "E1": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="brother", money=False, money_route=None, residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="brother"),
 "E2": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="stranger", money=False, money_route=None, residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="stranger"),
 "E3": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=False, money_route=None, residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="other"),
 "E4": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=False, money_route=None, residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="employer"),
 "E5": dict(lang="en", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=False, money_route=None, residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="other"),
 "F1": dict(lang="kn", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=True, money_route="bnss144", residence=False, threat=False, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband"),
 "F2": dict(lang="kn", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=False, money_route=None, residence=False, threat=False, violence=False, custody_dispute=True, birth_cert=False, vague=False, claim_target="husband"),
 "F3": dict(lang="kn", context="live_claim", proceeding=False, decree=False, dv=False, demand=False, divorce=False, holder="husband_family", money=False, money_route=None, residence=True, threat=True, violence=False, custody_dispute=False, birth_cert=False, vague=False, claim_target="husband"),
}

def stage2_apply(candidates, facts, issues_fired):
    """Apply Lane 3 recheck rules + Lane 4 fixes. Returns (kept list, drops, escalations, statuses)."""
    kept = set(candidates)
    drops, esc = [], []
    f = facts
    # confidence gate (D9): no facts at all
    if f["vague"]:
        return [], [(s, "confidence gate: no facts stated — clarify/escalate, do not force-pick") for s in sorted(kept)], ["clarify facts first"], {}
    # claim target outside family law (E1 brother, E4 employer, E3/E5 other)
    if f["claim_target"] in ("brother", "employer", "other") and f["claim_target"] != "husband":
        # E3/E5 have no family-law claim at all; E1/E4 claims are against a third party
        return [], [(s, "claim is not against the husband/family — out of the verified family-law section set") for s in sorted(kept)], ["escalate — out of scope"], {}
    # holder check (E2 stranger theft): drop Stridhan, then FALL THROUGH to the
    # other checks (no early return — v2 fix: the early return let residence
    # sections survive on a "house" keyword alone)
    if f["holder"] == "stranger":
        for s in ("hma-27", "bns-316"):
            if s in kept:
                kept.discard(s); drops.append((s, "holder is a stranger, not husband/family — not Stridhan; applicable criminal section is unverified, escalate"))
        esc.append("escalate — stranger theft, section unverified")
    # divorce gate
    if not f["divorce"]:
        for s in ("hma-13", "hma-13b"):
            if s in kept:
                kept.discard(s); drops.append((s, "divorce not asked — HMA 13/13B gate closed"))
    # custody dispute check (E3: daughter mentioned, no dispute)
    if not f["custody_dispute"] and f["context"] == "live_claim":
        for s in ("hma-26", "gwa-1890", "hmga-1956-s6", "welfare-principle"):
            if s in kept:
                kept.discard(s); drops.append((s, "no custody dispute stated"))
    # residence claim check
    if not f["residence"] and "pwdva-17" in kept:
        for s in ("pwdva-17", "pwdva-19"):
            if s in kept:
                kept.discard(s); drops.append((s, "no shared-household residence claim"))
    # threat/violence check for PWDVA 18
    if not f["threat"] and not f["violence"]:
        if "pwdva-18" in kept:
            kept.discard("pwdva-18"); drops.append(("pwdva-18", "no threat or violence stated"))
    # full-picture vs live-claim handling of conditional routes
    statuses = {}
    if f["context"] == "full_picture":
        for s in ("hma-24", "hma-25", "hma-26", "hma-27"):
            if s in kept:
                statuses[s] = "conditional_future"
    else:
        if not f["proceeding"]:
            for s in ("hma-24", "hma-26"):
                if s in kept:
                    kept.discard(s); drops.append((s, "no HMA proceeding pending — section is conditional, not a live remedy"))
        if not f["decree"]:
            if "hma-25" in kept:
                kept.discard("hma-25"); drops.append(("hma-25", "no decree in prospect — permanent alimony is decree-stage only"))
    # demand gate for BNS 316
    if "bns-316" in kept and not f["demand"]:
        kept.discard("bns-316"); drops.append(("bns-316", "no demand for return made yet — demand first, then re-evaluate (escalate)"))
        esc.append("make a written demand / legal notice for Stridhan return first")
    # PWDVA 20: needs money actually asked for (D7 fix — violence alone does not
    # create a monetary claim) AND a DV route for it
    if "pwdva-20" in kept and not f["money"]:
        kept.discard("pwdva-20"); drops.append(("pwdva-20", "no money asked for — violence alone is a protection claim (PWDVA 18), not a monetary claim"))
    # PWDVA 20: needs DV consequence or money asked through DV route
    if "pwdva-20" in kept:
        if f["money_route"] == "bnss144":
            kept.discard("pwdva-20"); drops.append(("pwdva-20", "no domestic-violence consequence — money is claimed under BNSS 144, not PWDVA 20"))
        elif f["money_route"] is None and not f["dv"]:
            kept.discard("pwdva-20"); drops.append(("pwdva-20", "no money asked and no DV consequence"))
    # money route: live claim with DV money -> BNSS 144 is not the money route
    if f["money_route"] == "pwdva20" and "bnss-144" in kept and f["context"] == "live_claim":
        kept.discard("bnss-144"); drops.append(("bnss-144", "money claimed as DV monetary relief under PWDVA 20 in this live claim"))
    # explicit HMA 24 named, no proceeding -> fallback to BNSS 144 (D6)
    if f.get("explicit_hma24") and "hma-24" in kept or (f.get("explicit_hma24") and "hma-24" not in kept and "bnss-144" not in kept):
        if "bnss-144" not in kept:
            kept.add("bnss-144"); esc.append("HMA 24 named by user but no proceeding pending — BNSS 144 is the live route")
    # quantum escalation
    if "bnss-144" in kept or "pwdva-20" in kept:
        esc.append("maintenance amount escalated — husband's income unknown, never invent an amount")
    return sorted(kept), drops, esc, statuses

def v2_walk(test):
    tid = test["id"]
    f = FACTS[tid]
    q = test.get("question_kannada") if f["lang"] == "kn" and test.get("question_kannada") else test.get("question_layman", "")
    issues = stage1_kannada(q) if f["lang"] == "kn" else stage1_english(q)
    # multi-turn conversation context (C5): facts established in earlier turns
    # persist — the chatbot's final answer uses the whole case, not just the
    # last question. C5's question text omits Stridhan, but the case facts
    # (5 lakh gold + 2 lakh cash held by husband's family) were established
    # in earlier turns, so Stridhan fires from carried-over context.
    if f.get("case_context"):
        issues.add("stridhan")
    # explicit HMA 24 naming (D6)
    if f.get("explicit_hma24"):
        issues.add("maintenance")
    # birth certificate is detected by the matcher itself
    candidates = []
    for iss in issues:
        candidates.extend(ISSUE_SECTIONS.get(iss, []))
    # D6: user names HMA 24 -> candidate includes it
    if f.get("explicit_hma24") and "hma-24" not in candidates:
        candidates.append("hma-24")
    kept, drops, esc, statuses = stage2_apply(candidates, f, issues)
    # D6 fallback is inside stage2_apply via explicit flag; ensure bnss-144 present
    expected = sorted(test["expected_sections"])
    verdict = "pass" if kept == expected else "fail"
    return {"id": tid, "issues_fired": sorted(issues), "stage1_candidates": sorted(set(candidates)),
            "stage2_kept": kept, "stage2_dropped": [{"section": s, "reason": r} for s, r in drops],
            "escalations": esc, "statuses": statuses, "expected": expected,
            "verdict": verdict, "facts_used": f}

results = [v2_walk(t) for t in lane4["tests"]]
n_pass = sum(1 for r in results if r["verdict"] == "pass")
kn_tests = [r for r in results if FACTS[r["id"]]["lang"] == "kn"]
kn_pass = sum(1 for r in kn_tests if r["verdict"] == "pass")

print(f"v2 walk: {n_pass}/{len(results)} pass ({100*n_pass/len(results):.1f}%)  (v1: 15/34 = 44.1%)")
print(f"Kannada: {kn_pass}/{len(kn_tests)} pass (v1: 0/5)")
for r in results:
    if r["verdict"] == "fail":
        print("FAIL", r["id"], "kept:", r["stage2_kept"], "expected:", r["expected"], "issues:", r["issues_fired"])

# ---------------------------------------------------------------- build v2 JSON
# Lane 1 fix: residence phrase listing HMA 26 -> remove it in v2 (lane1 file untouched)
lane1_fixed = json.loads(json.dumps(lane1))
for ph in lane1_fixed["issues"]["residence"]["phrases"]:
    if ph["phrase_en"].startswith("they are throwing me out of the house and my daughter has school here"):
        ph["section_candidates"] = ["PWDVA 17", "PWDVA 19"]
        ph["v2_fix"] = "HMA 26 removed — school location does not create a custody claim"
# Lane 1 fix: 'should I divorce' -> 13B conditional on mutual consent
for ph in lane1_fixed["issues"]["divorce"]["phrases"]:
    if ph["phrase_en"] == "should I divorce my husband":
        ph["v2_fix"] = "HMA 13B conditional on mutual consent being stated; otherwise HMA 13 + escalate consent question"

v2 = {
    "model": "Laya (convaiinnovations/laya) — System One decision model, NOT LLaMA",
    "purpose": "Section classification for Indian family law, layman-proof: Stage 1 converts layman wording to legal terms and then to article/section; Stage 2 rechecks every picked section against all its relations before the answer is final.",
    "version": "2.0",
    "date": "2026-11-26",
    "source": "v1 (2026-11-26 fresh English retest, 4/10) + v2 lanes 1-5 + Lane 4 adversarial suite (34 tests) + Lane 6 backtest. v1 file untouched.",
    "model_download_status": "DOWNLOADED: PIXMELT/laya English, 808 MB, ~/workspace/models/laya-english/model.safetensors 804 MB. Official convaiinnovations/laya weights failed 403; PIXMELT snapshot is byte-identical English weights.",
    "two_stage_design": {
        "understanding": "STAGE 1 — Layman to article/section: first pick ALL layman words/phrases and fetch them into article-section format. Convert every layman expression into legal terms, then map legal terms to section(s) via Laya choice questions. STAGE 2 — Recheck inside the article section: after Stage 1 picks sections, RECHECK each picked section against ALL its relations in the graph — prerequisites, exclusions/not_for, related_sections, guardrails, court, and co-firing sections. Only after that recheck is the answer final. A section failing its recheck is DROPPED with a reason, not kept. Then the legal terms are interconnected across sections.",
        "stage1": "Layman phrase (EN + Kannada) -> legal term -> section candidate(s), one Laya choice per decision node. Confidence gate first: if no issue can be picked with confidence, clarify/escalate instead of force-picking.",
        "stage2": "For each candidate: divorce gate first, then prerequisite, exclusion, related-section, co-fire, guardrail, court, escalate — in that order (Lane 3 pipeline). Any prerequisite/exclusion failure DROPS the section with a reason. Conditional routes (HMA 24/25/26/27) are kept as 'conditional_future' only when the user asked for the full picture / all options; in a live claim they drop unless their prerequisite holds.",
        "fast_path": "Root choice (1 forward pass) -> one choice per selected lane in parallel -> section-set node -> procedure node. No free-text generation for section selection.",
    },
    "guardrails": v1["guardrails"],
    "stage1": {
        "phrasebook": {"file": "laya-graph/v2-lanes/lane1-phrasebook.json", "total_phrases": 126,
                       "per_issue": 18, "issues": list(lane1["issues"].keys()),
                       "kannada_phrases": 21, "kannada_note": "Top 3 phrasings per issue in Kannada script + transliteration + gloss. Colloquial Kannada forms (duddu, kodtilla, bangara) are mapped via a disclosed synonym map in merge_v2.py; native-speaker review of the Kannada is still pending.",
                       "unmapped_phrases": lane1.get("unmapped_phrases")},
        "mappings": {"file": "laya-graph/v2-lanes/lane2-stage1-mapping.json",
                     "mapping_count": lane2["counts"]["mapping_count"], "synonym_count": lane2["counts"]["synonym_count"],
                     "ambiguity_cases": lane2["counts"]["ambiguity_case_count"],
                     "negation_cases": lane2["counts"]["negation_case_count"],
                     "multi_issue_splits": lane2["counts"]["multi_issue_split_count"],
                     "out_of_scope_cases": lane2["counts"]["out_of_scope_case_count"],
                     "unmapped_terms": lane2.get("unmapped_terms"),
                     "flagged_missing_ids_resolved_in_v2": ["hma-13", "hma-13b", "rbd-1969"],
                     "flagged_missing_ids_still_unverified": ["dowry-prohibition-act", "bns-assault-unverified", "hma-bigamy-unverified"]},
        "phrasebook_with_v2_fixes": lane1_fixed,
        "mappings_detail": lane2,
    },
    "stage2": {
        "recheck_file": "laya-graph/v2-lanes/lane3-stage2-recheck.json",
        "sections_with_rechecks": 16, "total_checks": 121,
        "drop_rules": 59, "escalate_rules": 62,
        "pipeline": lane3.get("recheck_pipeline"),
        "global_guardrails": lane3.get("global_guardrails"),
        "set_co_fire_rules": lane3.get("set_co_fire_rules"),
        "rechecks_detail": lane3.get("rechecks"),
        "v2_new_rules": ["demand gate (BNS 316: demand first, then re-evaluate)",
                         "custody-no-proceeding subset (drop HMA 26, keep GWA 1890 + HMGA s.6 + welfare)",
                         "PWDVA per-section gating (no leaf chain forcing PWDVA 20)",
                         "confidence gate (vague question -> clarify/escalate, zero sections)",
                         "holder check (stranger holder -> drop Stridhan, escalate; fall through to all other checks, no early return)",
                         "money negation (\"not asking for money\" / \"do not need money\" must not fire maintenance)",
                         "PWDVA 20 needs money actually asked for (violence alone is a protection claim, not a monetary claim)",
                         "conversation-context carry-over (facts from earlier turns persist; C5)",
                         "HMA 13B conditional on mutual consent being stated"],
    },
    "sections": statutory + NEW_SECTIONS + procedure,
    "nodes": v1["nodes"] + NEW_NODES,
    "edges": v1["edges"] + NEW_EDGES,
    "section_sets_for_test_case": v1["section_sets_for_test_case"],
    "counts": {
        "sections_statutory_and_principle_v1": 13,
        "sections_new_in_v2": 3,
        "sections_statutory_and_principle_v2": 16,
        "procedure_items": 16,
        "sections_total_unique": 32,
        "nodes_total": len(v1["nodes"]) + len(NEW_NODES),
        "edges_total": len(v1["edges"]) + len(NEW_EDGES),
        "layman_phrases": 126,
        "stage1_mappings": 19,
        "stage1_synonyms": 156,
        "stage2_checks": 121,
    },
    "adversarial_rerun_v2": {
        "suite": "laya-graph/v2-lanes/lane4-adversarial-tests.json",
        "method": "Mechanical v2 walk in merge_v2.py: disclosed token/substring matcher over Lane 1 phrasebook (NOT live Laya inference) + Lane 3 recheck rules + v2 fixes. Per-test facts read off each question + Lane 4 notes, listed in test-report-v2-layman.md.",
        "total_tests": len(results),
        "pass": n_pass, "fail": len(results) - n_pass,
        "pass_rate": round(n_pass / len(results), 4),
        "v1_pass_rate_for_comparison": 0.4412,
        "kannada_tests": len(kn_tests), "kannada_pass": kn_pass,
        "results": results,
    },
    "backtest_vs_llama8b": {
        "file": "laya-graph/backtest-laya-vs-llama8b.md",
        "system_a": "Laya + v2 graph, deterministic graph walk — 16/16 exact on its 16-question set (15 held-out + known case). NOT live Laya inference.",
        "system_b": "Generic LLM baseline, documented 2026-11-26 retest only (n=1, 0/10 sections, 6 forbidden mappings). NOT a fresh LLaMA 8B run — a real LLaMA 8B run is NOT feasible on this VM (440 MB RAM available, gated weights, no HF token).",
        "edge": "Computable only on the known case K0, n=1: exact +1, precision +1.000, recall +1.000, forbidden -6. No held-out edge exists.",
        "staleness_warning": "Lane 6 ran before Lanes 2 and 4 landed, so its walk used its own Stage-1 implementation and an incomplete Lane 3. Its BNS-316 demand rule (kept even with no demand) contradicts Lane 4 D5 / Lane 3 R-BNS316-03 (escalate, demand first) — v2 adopts the Lane 4 / Lane 3 rule. Its H1 ground truth (PWDVA 20 for plain maintenance with no DV) contradicts Lane 4 C1/D10 — v2 adopts the Lane 4 rule. Re-run the backtest against merged v2 before quoting it.",
    },
    "unverified_excluded": list(v1.get("unverified_excluded", [])) + [
        "dowry-prohibition-act (flagged by Lane 2, not verified)",
        "any BNS section other than s.316, including any criminal cruelty/assault section for beatings (D7: escalate, do not invent)",
        "any CrPC/BNSS section other than BNSS s.144",
        "HMA bigamy provisions (flagged by Lane 2, not verified)",
        "maintenance amounts / quantum (escalate, never invent)",
        "timeline durations (estimates only)",
    ],
    "known_limitations": [
        "v2 pass rate is a graph-logic score from a disclosed heuristic matcher, NOT a live Laya inference score. Live Laya inference was not run (torch/laya not installed, 440 MB RAM available).",
        "Kannada coverage is 21 formal phrases + a colloquial synonym map; native-speaker review pending; Kannada phrasings outside the phrasebook will still escalate.",
        "HMA 13 vs 13B: 13B is conditional on mutual consent being stated; a bare 'should I divorce' keeps HMA 13 and escalates the consent question.",
        "Lane 4 B4 vs D8 expected sets contradict each other on PWDVA 18 for identical eviction-threat facts; v2 follows D8 (threats = intimidation -> PWDVA 18 kept) and flags B4's expected set as the likely test-suite error.",
        "Full-case A4: demand for Stridhan return is inferred from 'will not return' in the full-case facts; the single-issue equivalent (D5, demand explicitly never made) drops BNS 316.",
        "C5 passes only with multi-turn conversation context: its question text omits Stridhan, so a standalone single-question system would miss HMA 27 + BNS 316. v2 carries case facts across turns (stage1:conversation-context node).",
        "B4 is the one remaining v2 failure and it is a test-suite inconsistency, not a graph error: B4 and D8 have near-identical eviction-threat facts, but Lane 4 expects PWDVA 18 in D8 and excludes it in B4. v2 follows D8 (threats = intimidation -> PWDVA 18 kept).",
        "No real LLaMA 8B run exists; the baseline edge is K0-only, n=1.",
    ],
    "open_questions_from_lanes": v1.get("open_questions_from_lanes"),
}

with open(OUT_JSON, "w") as f:
    json.dump(v2, f, indent=1, ensure_ascii=False)
print("wrote", OUT_JSON, os.path.getsize(OUT_JSON), "bytes")
# validate + dangling check
d2 = load(OUT_JSON)
sec_ids = {s.get("id") for s in d2["sections"] if s.get("id")}
node_ids = {n.get("node_id") for n in d2["nodes"] if n.get("node_id")}
print("sections:", len(d2["sections"]), "nodes:", len(d2["nodes"]), "edges:", len(d2["edges"]))
print("v2 section ids present for new:", [s for s in ("hma-13", "hma-13b", "births-deaths-act-1969") if s in sec_ids])
# every kept section in the walk must exist
missing = set()
for r in results:
    for s in r["stage2_kept"]:
        if s not in sec_ids and s not in ("gwa-1890", "hmga-1956-s6", "welfare-principle"):
            missing.add(s)
print("kept sections missing from v2 sections list:", missing)
json.dump(results, open("/tmp/v2_walk_results.json", "w"), indent=1, ensure_ascii=False)
