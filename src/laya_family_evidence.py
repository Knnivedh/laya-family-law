"""Extract verifiable procedural facts from the user's own case statements."""

import re


HMA_NAME = r"\b(?:hindu\s+marriage\s+act|hma)\b"
HMA_DOCUMENT = re.compile(
    rf"(?:{HMA_NAME}\s+(?:(?:divorce|judicial separation|nullity|marriage|matrimonial)\s+)?"
    r"(?:case|proceedings?|petition|application|suit|decree)|"
    r"\b(?:case|proceedings?|petition|application|suit|decree|divorce|judicial separation|nullity)\b"
    r"[^,]{0,75}?\b(?:under|pursuant to|governed by)\s+(?:s(?:ec(?:tion)?)?\.?\s*\d+[a-z]?\s+of\s+)?"
    rf"(?:the\s+)?{HMA_NAME})",
    re.I,
)
BNSS_NAME = r"\b(?:bnss|bharatiya\s+nagarik\s+suraksha\s+sanhita)\b"
BNSS = re.compile(BNSS_NAME, re.I)
SECTION_PREFIX = r"(?:section|sec\.?|s\.?|u\s*/\s*s\.?|§)\s*"
BNSS_144 = re.compile(
    rf"(?:{BNSS_NAME}(?:[, ]+(?:of\s+)?2023)?(?:['’]s)?\s*,?\s*(?:{SECTION_PREFIX})?144\b|"
    rf"(?:{SECTION_PREFIX})?144\b\s*(?:of\s+(?:the\s+)?)?{BNSS_NAME})",
    re.I,
)
SECTION_144 = re.compile(r"\b144\b")
CASE = re.compile(r"\b(?:case|proceedings?|petition|application|suit|hearing)\b", re.I)
ORDER = re.compile(r"\b(?:order|ordered|fixed|awarded|granted)\b", re.I)
DECREE = re.compile(r"\b(?:decree|(?:grant(?:ed|ing)\s+(?:me\s+)?(?:a\s+)?(?:divorce|judicial separation|nullity)))\b", re.I)
PENDING = re.compile(
    r"\b(?:pending|ongoing|going on|still hearing|(?:still|currently) being heard|still (?:in|before) (?:the |a )?(?:court|judge)|"
    r"before (?:the |a )?(?:court|judge)|next hearing|has not concluded|hasn't concluded|underway|in progress)\b",
    re.I,
)
DECREE_EFFECTIVE = re.compile(
    r"\b(?:(?:court|judge)\s+(?:has |had |already |is ){0,3}"
    r"(?:granted|entered|passed|issued|pronounced|passing|granting)|"
    r"(?:was|has\s+(?:already\s+)?been|had\s+(?:already\s+)?been|is being|got)\s+(?:already\s+)?(?:granted|entered|passed|issued|pronounced)|"
    r"decree\s+(?:ended|dissolved)|(?:ended|dissolved)\s+by\s+(?:a|the)\s+decree)\b",
    re.I,
)
ORDER_AUTHORITY = re.compile(
    r"\b(?:under|pursuant to|cites?|states?|reads?|says?)\s*[:,]?\s*(?:the\s+)?$",
    re.I,
)
ORDER_AFTER_CITATION = re.compile(
    r"^\s*[,–-]?\s*(?:(?:existing|court|maintenance|support|monthly)\s+){0,3}order\b",
    re.I,
)
OWN_ORDER_FOLLOWUP = re.compile(
    r"^[.!?;\s]*i\s+(?:already\s+)?(?:have|hold|got|received)\s+(?:it|that order)\b",
    re.I,
)
ORDER_ISSUED = re.compile(
    r"\b(?:(?:existing|current|previous|earlier|prior|my|our)\s+"
    r"(?:\w+\s+){0,5}(?:order|maintenance)|"
    r"(?:i|we)\s+(?:already\s+)?(?:have|got|received|hold)\s+(?:(?:an?|the|my|our)\s+)?"
    r"(?:\w+\s+){0,5}(?:order|maintenance)|"
    r"(?:court|judge|magistrate)\s+(?:has |had |already ){0,3}(?:made|issued|passed|awarded|granted|fixed|ordered)|"
    r"(?:i am|i'm|i’m|we are)\s+(?:the\s+)?(?:payer|payee|recipient|respondent|beneficiary)"
    r"\s+(?:in|on|under)\s+(?:an?|the|my|our)\s+(?:maintenance\s+)?order|"
    r"order\s+(?:cites?|says?|states?|reads?)|"
    r"(?:was|has been|had been)\s+(?:already\s+)?(?:made|issued|passed|awarded|granted|fixed)|"
    r"order\b.{0,85}\b(?:has run|has been in place|is in force|is active|binds|requires))\b",
    re.I,
)
OWN = re.compile(r"\b(?:i|my|our|me|we|us)\b", re.I)
OTHER = re.compile(
    r"\b(?:(?:my|our)\s+(?:friend|neighbor|neighbour|sister|brother|cousin|colleague|client|"
    r"relative|parents?|mother|father|daughter|son)|(?:someone\s+else)|"
    r"(?:article|textbook|internet|example|video|search result|forum post))\b",
    re.I,
)
UNCERTAIN = re.compile(
    r"\b(?:if|suppos(?:e|ing)|imagine|pretend|hypothetical|assum(?:e|ing)|someday|"
    r"might|maybe|may\s+be|could\s+be|perhaps|unclear|unsure|uncertain|whether|"
    r"don't know|do not know|can't tell|cannot tell|can't confirm|cannot confirm|don't have|"
    r"do not have|haven't received|have not received|not sure|think|planned|planning|draft)\b",
    re.I,
)
NO_PENDING = re.compile(
    r"\b(?:no\s+(?:(?:HMA|Hindu Marriage Act|ongoing|pending|active|current)\s+){0,2}(?:case|petition|proceedings?)|"
    r"(?:my|our|the)\s+(?:\w+\s+){0,3}(?:case|petition|proceedings?)\s+"
    r"(?:(?:is|was|has been)\s+)?(?:disposed|dismissed|withdrawn|closed|concluded|not pending|no longer pending)|"
    r"not\s+(?:yet\s+)?filed|no petition has been lodged)\b",
    re.I,
)
NO_DECREE = re.compile(
    r"\b(?:no\s+(?:final\s+)?decree|without (?:a|any) decree|"
    r"(?:decree|divorce)\s+(?:\w+\s+){0,3}(?:not|never)\s+(?:yet\s+|been\s+)?(?:passed|granted|issued|entered)|"
    r"has not been passed|hasn't been passed)\b",
    re.I,
)
NO_ORDER = re.compile(
    r"\b(?:no\s+(?:(?:court|existing|maintenance)\s+){0,2}order|not (?:yet )?(?:made|issued|ordered)|"
    r"(?:do not|don't) have (?:any|an|a) (?:maintenance )?order|"
    r"(?:court|judge)\s+(?:has not|hasn't|never)\s+(?:made|issued|passed)\s+(?:an?|any)\s+order)\b",
    re.I,
)
OLD_ORDER = re.compile(r"\b(?:crpc|criminal procedure code|code of criminal procedure|section\s+125)\b", re.I)
OTHER_OWNER = re.compile(
    r"\b(?:my|our)\s+\w+['’]s\s+(?:\w+\s+){0,4}(?:case|proceeding|petition|decree|order)\b",
    re.I,
)
PAST_PENDING = re.compile(
    r"\b(?:was|were|had been|used to be)\s+(?:then\s+|still\s+)?(?:pending|ongoing|before court)\b",
    re.I,
)
CLOSED_LATER = re.compile(
    r"^\s*(?:it|that case|that petition)\s+(?:was|is|has been|has since been)\s+"
    r"(?:dismissed|withdrawn|disposed of|closed|concluded)\b",
    re.I,
)
FUTURE_EVENT = re.compile(r"\b(?:scheduled|next (?:week|month|year)|tomorrow|will be|not yet)\b", re.I)
ORDER_SOUGHT = re.compile(
    r"\b(?:apply(?:ing)? for|ask(?:ing)? for|want|seek(?:ing)?)\b.{0,43}"
    r"\border\s+(?:to be|that (?:will|would) be)\s+(?:issued|made|passed|granted)\b",
    re.I,
)
# S.O. 848(E) brought BNSS into force on 1 July 2024. Earlier dates need review.
PRE_BNSS = re.compile(
    r"\b(?:(?:in|on|dated)\s+(?:\d{1,2}\s+)?(?:[A-Za-z]+\s+)?(?:19\d{2}|20[01]\d|202[0-3])|"
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?)\s+2024)\b",
    re.I,
)

# Sentence boundaries preserve section abbreviations and never join evidence across a quote.
BOUNDARY = re.compile(r"[!?;\n]+|(?<!\bs)(?<!\bsec)\.(?=\s|$)", re.I)
QUOTED = re.compile(r'''“[^”]*”|‘[^’]*’|"[^"\n]*"|(?<!\w)'[^'\n]+'(?!\w)''')


def _clause_ranges(text: str):
    start = 0
    for match in BOUNDARY.finditer(text):
        if start < match.start():
            yield start, match.start()
        start = match.end()
    if start < len(text):
        yield start, len(text)


def _span(question: str, start: int, end: int) -> dict:
    while start < end and question[start].isspace():
        start += 1
    while end > start and question[end - 1].isspace():
        end -= 1
    return {"start": start, "end": end, "text": question[start:end]}


def _bnss_order_span(question: str, masked: str, start: int, end: int) -> dict | None:
    clause = masked[start:end]
    if ORDER_SOUGHT.search(clause) or PRE_BNSS.search(clause):
        return None
    for citation in BNSS_144.finditer(clause):
        prefix = clause[:citation.start()]
        suffix = clause[citation.end():]
        attached_after = ORDER_AFTER_CITATION.match(suffix)
        attached_before = ORDER.search(prefix) and (
            ORDER_AUTHORITY.search(prefix) or re.match(r"u\s*/\s*s\b", citation[0], re.I)
        )
        if (attached_before or attached_after) and ORDER_ISSUED.search(clause):
            return _span(question, start, end)
        if attached_after and not prefix.strip() and not suffix[attached_after.end():].strip():
            confirmation = OWN_ORDER_FOLLOWUP.match(masked[end:])
            if confirmation:
                return _span(question, start, end + confirmation.end())
    return None


def procedural_evidence(question: str) -> dict:
    masked = QUOTED.sub(lambda m: " " * len(m[0]), question)
    user_case = bool(OWN.search(masked))
    supported = {}
    contradicted = set()
    for start, end in _clause_ranges(masked):
        clause = masked[start:end]
        if not clause.strip() or OTHER.search(clause):
            continue
        if OTHER_OWNER.search(clause) and not re.search(r"\bour\s+marriage\b", clause, re.I):
            continue
        if NO_PENDING.search(clause) or CLOSED_LATER.search(clause):
            contradicted.add("hma_pending")
        if NO_DECREE.search(clause):
            contradicted.add("hma_decree")
        if NO_ORDER.search(clause) or (ORDER.search(clause) and OLD_ORDER.search(clause)):
            contradicted.add("bnss_order")
        if not user_case or UNCERTAIN.search(clause):
            continue

        span = _span(question, start, end)
        if HMA_DOCUMENT.search(clause):
            if CASE.search(clause) and PENDING.search(clause) and not PAST_PENDING.search(clause):
                supported.setdefault("hma_pending", span)
            if DECREE.search(clause) and DECREE_EFFECTIVE.search(clause) and not FUTURE_EVENT.search(clause):
                supported.setdefault("hma_decree", span)
        order = _bnss_order_span(question, masked, start, end)
        if order:
            supported.setdefault("bnss_order", order)

    return {field: {"value": "yes", "source": "user_text", "span": span}
            for field, span in supported.items() if field not in contradicted}


SEPARATE_CLAIM = re.compile(
    r"\b(?:separately|(?:separate|independent|additional)\s+(?:\w+\s+){0,3}"
    r"(?:application|claim|order|request|support))\b",
    re.I,
)
SUPPORT = re.compile(r"\b(?:support|maintenan\w*|alimony|money|expenses|allowance)\b", re.I)
NO_SEPARATE = re.compile(r"\b(?:do not|don't|does not|doesn't|never|not asking|not seeking|no)\b", re.I)


def separate_support_evidence(question: str) -> dict | None:
    masked = QUOTED.sub(lambda match: " " * len(match[0]), question)
    for start, end in _clause_ranges(masked):
        clause = masked[start:end]
        if SEPARATE_CLAIM.search(clause) and SUPPORT.search(clause) and REQUEST.search(clause) and not NO_SEPARATE.search(clause):
            return {"value": "yes", "source": "user_text", "span": _span(question, start, end)}
    return None

REQUEST = re.compile(
    r"\b(?:i\b.{0,96}\band\s+(?:(?:now|also|still)\s+){0,2}(?:need|want|seek|wish|intend to (?:request|apply|seek|ask))|"
    r"i\s+(?:really\s+|now\s+|only\s+|also\s+|just\s+|specifically\s+){0,2}"
    r"(?:want|need|seek|wish|would like|am asking|am trying|intend to (?:request|apply|seek|ask))|"
    r"i(?:'d|’d)\s+like|how\s+(?:to|do|can|could|may|should|would)|"
    r"(?:can|could|may|should)\s+(?:i|we|the court|the judge)|is there a way|"
    r"what\s+(?:can i|steps|about)|are both goals|"
    r"what steps|what should i do)\b",
    re.I,
)
DECLINED = re.compile(
    r"\b(?:(?:i\s+(?:do not|don't|don’t|never|am not)|i['’]m\s+not)\s+"
    r"(?:want|need|seek|wish|ask|asking|seeking)|"
    r"not interested in|not looking for|not asking for|no request for)\b",
    re.I,
)
MARRIAGE_CASE = re.compile(r"\b(?:marriage|marital|matrimonial|divorce|judicial separation|nullity|hma)\b", re.I)
FAMILY_ORDER = re.compile(r"\b(?:maintenance|support|allowance|alimony|child support)\b", re.I)
INTERIM_REQUEST = re.compile(
    r"\b(?:(?:interim|temporary)\s+(?:\w+\s+){0,2}(?:support|maintenance|money|aid|funds|help|expenses|fees|costs)|"
    r"(?:expenses|costs)\s+(?:paid\s+)?(?:for|of)\s+(?:defending|responding to|contesting)\s+"
    r"(?:\w+\s+){0,5}(?:case|petition|proceeding)|"
    r"(?:court|case|legal|litigation)\s+(?:costs?|fees?|expenses?)|"
    r"(?:support|maintenance|money|funds|expenses|help).{0,55}\b(?:while|during|until)\b|"
    r"(?:pay|afford|cover|costs? of|money for)\s+(?:\w+\s+){0,5}(?:lawyer|solicitor|litigation|fees))\b",
    re.I,
)
PERMANENT_REQUEST = re.compile(
    r"\b(?:permanent|long[- ]term)\s+(?:\w+\s+){0,2}(?:support|maintenance|alimony|allowance|"
    r"lump sum|financial aid|financial relief)\b",
    re.I,
)
RECOVERY_REQUEST = re.compile(
    r"\b(?:recover(?:y|ed|ing)?|collect(?:ed|ing|ion)?|enforc(?:e|ed|ing|ement)|claim|"
    r"(?:seek|want|need)\s+(?:the\s+)?(?:unpaid|missed|overdue|outstanding)\s+"
    r"(?:ordered\s+)?(?:instal+ments?|payments?|amounts?|dues|sums?))\b",
    re.I,
)
PAYMENTS_DUE = re.compile(
    r"\b(?:unpaid|missing|missed|arrears|owing|owed|owes|outstanding|balance|skipped|shortfall|overdue|remainder|"
    r"remaining\s+(?:sums?|amounts?|instal+ments?|payments?)|"
    r"(?:paid|sent|received)\s+only\s+part|"
    r"(?:instalments?|payments?)\s+(?:were\s+)?(?:not\s+paid|due|behind))\b",
    re.I,
)
CHANGE_REQUEST = re.compile(
    r"\b(?:(?:increas(?:e|ed|ing)|reduc(?:e|ed|ing|tion)|raise|raised|raising|lower|lowered|lowering|"
    r"chang(?:e|ing)|var(?:y|ying|iation)|modif(?:y|ying|ication)|adjust(?:ing|ment)?)\b"
    r"(?:\s+\w+){0,6}\s+(?:amount|rate|maintenance|support|allowance|payment|pay|monthly)|"
    r"(?:higher|larger|lower|smaller|different|revised)\s+(?:monthly\s+)?(?:amount|rate|payment|maintenance)|"
    r"(?:apply|ask)\s+for\s+(?:an?\s+)?(?:reduction|increase|change|variation|modification)|"
    r"(?:raise|reduce|lower|vary|change)\s+what\s+(?:it|the court|the judge)\s+(?:ordered|set|fixed)|"
    r"(?:have|get)\s+(?:my|the|our)\s+(?:monthly\s+)?(?:amount|rate|maintenance|allowance|payment)s?"
    r"\s+(?:raised|lowered|reduced|altered|changed|increased|varied|modified))\b",
    re.I,
)
CONTRAST = re.compile(r"(?<!\w)(?:but|however|whereas)(?!\w)", re.I)


def requested_procedural_actions(question: str) -> dict:
    """Find express requests and keep the authority check independent."""
    masked = QUOTED.sub(lambda match: " " * len(match[0]), question)
    has_marriage_case = bool(MARRIAGE_CASE.search(masked) and CASE.search(masked))
    has_support_order = bool(
        ORDER.search(masked) and (FAMILY_ORDER.search(masked) or BNSS.search(masked) and SECTION_144.search(masked))
    )
    evidence = {}
    for start, end in _clause_ranges(masked):
        boundaries = [start]
        boundaries.extend(start + match.end() for match in CONTRAST.finditer(masked[start:end]))
        boundaries.append(end)
        for local_start, local_end in zip(boundaries, boundaries[1:]):
            clause = masked[local_start:local_end]
            declined = DECLINED.search(clause)
            if not (REQUEST.search(clause) or declined) or OTHER.search(clause):
                continue
            found = []
            if has_marriage_case and INTERIM_REQUEST.search(clause):
                found.append("interim")
            if PERMANENT_REQUEST.search(clause):
                found.append("permanent")
            if has_support_order:
                recovery = RECOVERY_REQUEST.search(clause)
                previous = masked[max(0, local_start - 180):local_start]
                if recovery and (
                    PAYMENTS_DUE.search(clause)
                    or recovery[0].casefold().startswith("enforc")
                    or PAYMENTS_DUE.search(previous) and (
                        "collect" in recovery[0].casefold()
                        or re.search(r"\bclaim\s+(?:those|these|them|it)\b", clause, re.I)
                    )
                ):
                    found.append("recover")
                if CHANGE_REQUEST.search(clause):
                    found.append("vary")
            for field in found:
                value = "no" if declined else "yes"
                if field in evidence and evidence[field]["value"] != value:
                    value = "unknown"
                evidence[field] = {
                    "value": value, "source": "user_text", "span": _span(question, local_start, local_end),
                }
    return evidence


AGE_UNDER_18 = r"(?:1[0-7]|[0-9]|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen)"
YEAR_OLD = r"[-– ]+years?[-– ]+old"
CHILD_WORD = r"(?:child(?:ren)?|daughter|son|twins?|boy|girl|kid)"
WIFE_RECIPIENT = re.compile(
    r"\b(?:(?:my|own)\s+(?:(?:former|ex)[- ]+)?husband|"
    r"(?:as|i am|i'm|i’m|i was)\s+(?:(?:his|the|a|former|divorced)\s+){0,3}wife|"
    r"married woman|\bthe man i (?:used to be|was) married to)\b",
    re.I,
)
MALE_SELF = re.compile(r"\b(?:i am|i'm|i’m)\s+(?:a\s+|the\s+)?(?:man|male)\b", re.I)
PARENT_RECIPIENT = re.compile(
    r"\b(?:(?:my|our)\s+(?:[\w-]+\s+){0,3}(?:adult|grown(?:[- ]up)?|working|employed)\s+(?:son|daughter|child)|"
    r"(?:from|support from)\s+(?:his|her|their)\s+(?:adult|grown(?:[- ]up)?)\s+(?:son|daughter|child))\b",
    re.I,
)
EMPLOYED_OFFSPRING = re.compile(
    r"\b(?:my|our)\s+(?:son|daughter)\b[^.!?;]{0,40}\b(?:employed|earns|works|has a job|salary)\b",
    re.I,
)
PARENT_SELF = re.compile(
    r"\b(?:as|i am|i'm|i’m)\s+(?:(?:his|her|their|the|a|retired|ageing|aging)\s+){0,3}(?:father|mother|parent)\b",
    re.I,
)
MINOR_RECIPIENT = re.compile(
    rf"\b(?:(?:my|our|the)\s+(?:baby|infant|toddler|minor(?:\s+{CHILD_WORD})?)|"
    rf"(?:my|our)\s+{AGE_UNDER_18}{YEAR_OLD}|{AGE_UNDER_18}{YEAR_OLD}\s+{CHILD_WORD}|"
    rf"{CHILD_WORD}(?:\s+\w+){{0,3}}[,\s]+(?:is|are|aged|both|who is|now)\s+{AGE_UNDER_18}"
    rf"(?!\w|\s+(?:years? ago|years? since|rupees|lakh|months late|pm|am)))\b",
    re.I,
)
CHILD_ANTECEDENT = re.compile(rf"\b(?:my|our)\s+(?:\w+\s+){{0,2}}{CHILD_WORD}\b", re.I)
CHILD_PRONOUN_AGE = re.compile(rf"^\s*(?:he|she|they)\s+(?:is|are|are both)\s+{AGE_UNDER_18}\b", re.I)
CHILD_ONLY = re.compile(
    r"\b(?:not for (?:me|myself)|only for (?:my |our |the )?(?:child|children|son|daughter)|"
    r"on behalf of (?:my |our |the )?(?:child|children|son|daughter))\b",
    re.I,
)
SELF_ONLY = re.compile(
    r"\b(?:(?:only|solely|exclusively|just)\s+for myself|not for (?:my |our |the |any )?(?:children|child|son|daughter)|"
    r"do not assess (?:\w+\s+){0,3}?(?:for|towards)\s+(?:my |our |the )?(?:children|child|son|daughter)|"
    r"(?:don't|do not|am not|['’]m not)\s+(?:asking|ask|seeking|seek|want)\s+(?:for\s+)?(?:any\s+)?(?:payments?|support|money|assistance|help)?"
    r"\s*(?:for|towards)\s+(?:my |our |the )?(?:children|child|son|daughter))\b",
    re.I,
)


def grounded_beneficiaries(question: str) -> dict:
    masked = QUOTED.sub(lambda match: " " * len(match[0]), question)
    evidence = {}

    def store(field, start, end):
        evidence.setdefault(field, {"value": "yes", "source": "user_text",
                                    "span": _span(question, start, end)})

    wife = WIFE_RECIPIENT.search(masked)
    if wife and not (MALE_SELF.search(masked) or CHILD_ONLY.search(masked)):
        store("wife", wife.start(), wife.end())

    parent = PARENT_RECIPIENT.search(masked)
    denies_child_as_payer = re.search(
        r"\b(?:not from (?:my|our)\s+(?:(?:adult|grown)\s+)?(?:son|daughter|child)|"
        r"(?:only|solely|just)\s+from (?:my|our)\s+(?:wife|husband|spouse)|"
        r"from (?:my|our)\s+(?:wife|husband|spouse)\s+(?:alone|only))\b",
        masked, re.I,
    )
    if not denies_child_as_payer:
        if parent:
            store("parent", parent.start(), parent.end())
        else:
            child, adult = EMPLOYED_OFFSPRING.search(masked), PARENT_SELF.search(masked)
            if child and adult:
                store("parent", min(child.start(), adult.start()), max(child.end(), adult.end()))

    if not SELF_ONLY.search(masked):
        child = MINOR_RECIPIENT.search(masked)
        if child:
            store("minor_child", child.start(), child.end())
        else:
            antecedent = None
            for start, end in _clause_ranges(masked):
                clause = masked[start:end]
                if antecedent is not None and CHILD_PRONOUN_AGE.search(clause):
                    store("minor_child", antecedent, end)
                    break
                antecedent = start if CHILD_ANTECEDENT.search(clause) else None

    return evidence


DIRECT_SUPPORT_ASK = re.compile(
    r"\b(?:can|could|may)\s+(?:my|our)\b.{1,75}\bbe\s+(?:made|required|ordered)\s+"
    r"to\s+(?:support|maintain|provide for)\s+(?:me|us)\b",
    re.I,
)


def direct_support_evidence(question: str) -> dict | None:
    masked = QUOTED.sub(lambda match: " " * len(match[0]), question)
    if not grounded_beneficiaries(question):
        return None
    for start, end in _clause_ranges(masked):
        clause = masked[start:end]
        if DIRECT_SUPPORT_ASK.search(clause) and not DECLINED.search(clause):
            if not ORDER.search(masked) or not ORDER_ISSUED.search(masked):
                return {"value": "yes", "source": "user_text", "span": _span(question, start, end)}
    return None
