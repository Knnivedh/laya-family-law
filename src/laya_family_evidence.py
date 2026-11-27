"""Extract verifiable procedural facts from the user's own case statements."""

from dataclasses import dataclass
import re


# ---------------------------------------------------------------------------
# V71-P1-4 — Supervised classifier-head wiring (PLACEHOLDER interface)
# ---------------------------------------------------------------------------
# Lane 03 owns the multi-head Stage 0/1 classifier
# (src/laya_v7_classifier.py, plan §1.2 V71-P1-3).  Until that classifier
# ships, every function in this module is called with supervised=None and
# behaves exactly as the regex-only evidence layer did before.
#
# CONTRACT (see docs/clarification-fallback-spec.md §5 for the full spec):
# Lane 03's classifier MUST return, per question, a mapping keyed by field
# name — "new_support", "interim", "permanent", "recover", "vary",
# "wife", "minor_child", "parent" — to SupervisedSignal objects.  This
# module NEVER invents classifier outputs: a signal is admitted as
# evidence ONLY when (a) value == "yes", (b) score >= tau_high (0.70, the
# same threshold src/laya_family.py:_interpret uses for numeric model
# scores), and (c) its evidence span verifies against the literal question
# text (exact start/end/text match).  Signals below tau_high, "no" /
# "unknown" signals, and signals whose span does not verify are dropped
# here — uncertainty is Lane 05's clarifier's job (V71-P1-5), not silent
# evidence.  No score, span, or label in this file is a classifier output;
# the defaults below are empty by construction.
# ---------------------------------------------------------------------------

#: Fields a supervised head may supply to this module.
SUPERVISED_FIELDS = frozenset(
    {"new_support", "interim", "permanent", "recover", "vary",
     "wife", "minor_child", "parent"}
)
#: Beneficiary fields (subset of SUPERVISED_FIELDS) used by
#: grounded_beneficiaries().
BENEFICIARY_FIELDS = frozenset({"wife", "minor_child", "parent"})
#: Purpose fields (subset of SUPERVISED_FIELDS) used by
#: requested_procedural_actions().
PURPOSE_FIELDS = frozenset({"interim", "permanent", "recover", "vary"})
#: High-confidence threshold, mirroring laya_family._interpret (score >=
#: 0.70 -> "yes").  Kept as a named constant so Lane 03 / Lane 10 calibrate
#: it in one place instead of scattering literals.
SUPERVISED_TAU_HIGH = 0.70


@dataclass(frozen=True)
class SupervisedSignal:
    """One classifier-head prediction with its evidence span.

    field: one of SUPERVISED_FIELDS (purpose or beneficiary).
    value: "yes" | "no" | "unknown" (head's own label, not invented here).
    score: head probability in [0, 1] for `value`.
    span: {"start": int, "end": int, "text": str} — the token/clause span
        the head attended to.  Must verify verbatim against the question.
    head: which classifier head produced it, e.g. "purpose_head",
        "beneficiary_head" (Lane 03 names the heads).
    model: model identifier, for audit only.
    """

    field: str
    value: str
    score: float
    span: dict | None = None
    head: str = "unknown"
    model: str = "laya_v7_classifier (Lane 03 — not yet implemented)"

    @classmethod
    def from_mapping(cls, mapping: dict) -> "SupervisedSignal":
        """Build from a plain dict (Lane 03's JSON-able head output)."""
        return cls(
            field=mapping["field"],
            value=mapping["value"],
            score=float(mapping["score"]),
            span=mapping.get("span"),
            head=mapping.get("head", "unknown"),
            model=mapping.get("model", "laya_v7_classifier (Lane 03 — not yet implemented)"),
        )


def verify_supervised_span(question: str, signal: SupervisedSignal) -> bool:
    """Evidence-span verification: the claimed span must be literally true.

    Returns True only when the span dict has integer start/end inside the
    question, non-empty, and question[start:end] == span["text"] exactly.
    A signal that fails this check is dropped, never repaired or guessed.
    """
    span = signal.span
    if not isinstance(span, dict):
        return False
    start, end, text = span.get("start"), span.get("end"), span.get("text")
    if type(start) is not int or type(end) is not int or not isinstance(text, str):
        return False
    if not 0 <= start < end <= len(question) or not text:
        return False
    if question[start:end] != text:
        return False
    if not any(char.isalpha() for char in text):
        return False
    return True


def supervised_signals_to_evidence(question: str, supervised, *, tau_high: float = SUPERVISED_TAU_HIGH) -> dict:
    """Admit verified high-confidence supervised signals as evidence.

    `supervised` is a mapping field -> SupervisedSignal (or a plain dict
    with the same keys, coerced via SupervisedSignal.from_mapping).
    Only "yes" signals at score >= tau_high with a verified span are
    admitted, as {"value": "yes", "source": "supervised_verified_span",
    "span": ..., "score": ...}.  Everything else is dropped silently —
    this function never emits "unknown" or "no" evidence, so a weak head
    can never veto regex evidence or masquerade as a user statement.
    """
    evidence = {}
    if not supervised:
        return evidence
    for field, raw in dict(supervised).items():
        if field not in SUPERVISED_FIELDS:
            continue
        signal = raw if isinstance(raw, SupervisedSignal) else SupervisedSignal.from_mapping(raw)
        if signal.value != "yes":
            continue
        score = signal.score
        if type(score) not in {float, int} or not 0.0 <= score <= 1.0 or score < tau_high:
            continue
        if not verify_supervised_span(question, signal):
            continue
        evidence[field] = {
            "value": "yes",
            "source": "supervised_verified_span",
            "span": dict(signal.span),
            "score": round(float(score), 4),
            "head": signal.head,
        }
    return evidence


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
    r"(?:[\w.]+\s+){0,5}(?:order|maintenance)|"
    r"(?:i|we)\s+(?:already\s+)?(?:have|got|received|hold)\s+(?:(?:an?|the|my|our)\s+)?"
    r"(?:[\w.]+\s+){0,5}(?:order|maintenance)|"
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
SUPPORT = re.compile(r"\b(?:support|maint[ae]nan\w*|alimony|money|expenses|allowance|contribut\w*|help|cash)\b", re.I)
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
    r"(?:want|need|seek|wish|would like|am asking|am requesting|am applying|am trying|intend to (?:request|apply|seek|ask))|"
    r"i(?:'d|’d)\s+like|how\s+(?:to|do|can|could|may|should|would)|"
    r"where\s+(?:do|can|could|may|should)\s+(?:i|we)\s+(?:apply|seek|file|go|claim|ask)\b|"
    r"what\s+(?:is|are)\s+the\s+(?:process(?:es)?|procedure)\s+to\b|"
    r"what\s+do\s+(?:i|we)\s+file\b|"
    r"is\s+(?:an?\s+)?order\b.{0,50}\bpossible\b|"
    r"(?:can|could|may|should)\s+(?:i|we|the court|the judge)|is there a way|"
    r"what\s+(?:can i|steps|about)|are both goals|"
    r"what steps|what should i do)\b",
    re.I,
)
DECLINED = re.compile(
    r"\b(?:(?:i\s+(?:do not|don't|don’t|never|am not)|i['’]m\s+not)\s+"
    r"(?:want|need|seek|wish|ask|asking|seeking)|"
    r"i\s+(?:explicitly\s+)?declin\w*\s+(?:any\s+)?(?:request|claim|application|support|maintenance)|"
    r"not interested in|not looking for|not asking for|no request for)\b",
    re.I,
)
MARRIAGE_CASE = re.compile(r"\b(?:marriage|marital|matrimonial|divorce|judicial separation|nullity|hma)\b", re.I)
FAMILY_ORDER = re.compile(r"\b(?:maintenance|support|allowance|alimony|child support)\b", re.I)
INTERIM_REQUEST = re.compile(
    r"\b(?:(?:interim|temporary)\s+(?:\w+\s+){0,2}(?:support|maintenance|money|aid|funds|help|expenses|fees|costs)|"
    r"(?:expenses|costs)\s+(?:paid\s+)?(?:for|of)\s+(?:defending|responding to|contesting)\s+"
    r"(?:\w+\s+){0,5}(?:case|petition|proceeding)|"
    r"(?:costs?|fees?|expenses?)\s+of\s+(?:the\s+)?(?:case|proceeding|petition|suit|litigation)\b|"
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
    r"(?:apply|ask|petition|request)\s+to\s+(?:vary|change|modify|adjust|increase|reduce|lower|raise)\b|"
    r"(?:amount|rate|allowance|payment|maintenance)\s+(?:needs?|requires?)\s+"
    r"(?:reduc(?:e|ed|ing)|increas(?:e|ed|ing)|chang(?:e|ed|ing)|var(?:y|ied|ying)|"
    r"lower(?:ed|ing)|rais(?:e|ed|ing)|adjust(?:ed|ing|ment)?)\b|"
    r"(?:apply|ask)\s+for\s+(?:an?\s+)?(?:reduction|increase|change|variation|modification)|"
    r"(?:raise|reduce|lower|vary|change)\s+what\s+(?:it|the court|the judge)\s+(?:ordered|set|fixed)|"
    r"(?:have|get)\s+(?:my|the|our)\s+(?:monthly\s+)?(?:amount|rate|maintenance|allowance|payment)s?"
    r"\s+(?:raised|lowered|reduced|altered|changed|increased|varied|modified))\b",
    re.I,
)
CONTRAST = re.compile(r"(?<!\w)(?:but|however|whereas)(?!\w)", re.I)


def requested_procedural_actions(question: str, *, supervised=None) -> dict:
    """Find express requests and keep the authority check independent.

    `supervised` (V71-P1-4, optional, default None = regex-only behaviour)
    is a mapping field -> SupervisedSignal from the Lane 03 classifier
    heads.  Verified high-confidence "yes" signals are merged in with
    setdefault: they fill a purpose the regex conjunction missed (e.g. a
    vary ask phrased without any REQUEST form) but never overwrite a
    regex "no" (a declined clause) or an already-found regex "yes".
    """
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
                previous = masked[max(0, local_start - 180):local_start]
                if _recovery_ask(clause, previous):
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
    if supervised is not None:
        for field, record in supervised_signals_to_evidence(question, supervised).items():
            if field in PURPOSE_FIELDS:
                evidence.setdefault(field, record)
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
    r"\b(?:as|i am|i'm|i’m)\s+(?:(?:his|her|their|the|a|retired|ageing|aging|elderly|old|aged)\s+){0,3}(?:father|mother|parent)\b",
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
    r"\b(?:not for (?:me|myself)|(?:only|just)\s+for (?:my |our |the )?(?:child|children|son|daughter)|"
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


def grounded_beneficiaries(question: str, *, supervised=None) -> dict:
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

    if supervised is not None:
        # V71-P1-4 supervised wiring: a verified beneficiary "yes" from the
        # Lane 03 classifier heads grounds the beneficiary even when the
        # regex role patterns miss the phrasing.  Regex evidence wins on
        # conflict (setdefault above); supervised never overwrites it.
        for field, record in supervised_signals_to_evidence(question, supervised).items():
            if field in BENEFICIARY_FIELDS and record["value"] == "yes":
                evidence.setdefault(field, record)

    return evidence


DIRECT_SUPPORT_ASK = re.compile(
    r"\b(?:can|could|may)\s+(?:my|our)\b.{1,75}\bbe\s+(?:made|required|ordered)\s+"
    r"to\s+(?:support|maintain|provide for)\s+(?:me|us)\b",
    re.I,
)


def _recovery_ask(clause: str, previous: str = "") -> bool:
    """True when a clause asks to collect money already due under an order.

    Single source for the recovery conjunction, used by both
    requested_procedural_actions() and _direct_support_ask().  A bare
    "claim" / "recover" / "collect" is NOT enough on its own: "start a
    claim ... for monthly living money" (final_check 002) is fresh support,
    so recovery needs unpaid-money language in the clause (or just before
    it) or an enforcement verb.  Mirrors the pre-V71-P1-4 inline logic.
    """
    recovery = RECOVERY_REQUEST.search(clause)
    if not recovery:
        return False
    if PAYMENTS_DUE.search(clause) or recovery[0].casefold().startswith("enforc"):
        return True
    return bool(
        PAYMENTS_DUE.search(previous)
        and (
            "collect" in recovery[0].casefold()
            or re.search(r"\bclaim\s+(?:those|these|them|it)\b", clause, re.I)
        )
    )


def _direct_support_ask(clause: str) -> bool:
    """True when one clause expressly asks for fresh support.

    V71-P1-4: the old DIRECT_SUPPORT_ASK pattern alone fired on 1 of 162
    maintenance-fixture questions (verification 006, "be made to support
    me"), so every fresh-support (bnss-144) row depended entirely on the
    neural model's new_support score — the final_check bnss-144 FN. The
    conjunction below covers the ordinary ask forms ("want a court to
    arrange regular support", "how do I start a claim ... for monthly
    living money", "I am requesting maintenance just for my daughter",
    "Can the court tell them to contribute", "How do I seek court-ordered
    support") while staying out of the other purposes:

    * interim / permanent asks are excluded (INTERIM_REQUEST /
      PERMANENT_REQUEST) — those route to hma-24 / hma-25, never bnss-144;
    * a genuine change request (CHANGE_REQUEST) or a recovery ask
      (RECOVERY_REQUEST + PAYMENTS_DUE / "enforc-") is excluded — those
      route to bnss-146 / bnss-144-3.  Bare "claim" alone is NOT a
      recovery ask: "start a claim ... for monthly living money"
      (final_check 002) is fresh support, so recovery needs the
      payments-due / enforcement conjunction, mirroring
      requested_procedural_actions().
    * DECLINED / existing-order / beneficiary gates live in
      direct_support_evidence(), not here.
    """
    if DIRECT_SUPPORT_ASK.search(clause):
        return True
    if not (REQUEST.search(clause) and SUPPORT.search(clause)):
        return False
    if INTERIM_REQUEST.search(clause) or PERMANENT_REQUEST.search(clause):
        return False
    if CHANGE_REQUEST.search(clause):
        return False
    if _recovery_ask(clause):
        return False
    return True


def direct_support_evidence(question: str, *, supervised=None) -> dict | None:
    masked = QUOTED.sub(lambda match: " " * len(match[0]), question)
    beneficiaries = grounded_beneficiaries(question, supervised=supervised)
    if not beneficiaries:
        return None
    if supervised is not None:
        # V71-P1-4 supervised wiring: a verified new_support "yes" from the
        # Lane 03 classifier heads is sufficient evidence on its own — the
        # regex ask is not required to also match.  Span verification happens
        # inside supervised_signals_to_evidence(); unverified or
        # below-threshold signals never reach here.
        verified = supervised_signals_to_evidence(question, supervised)
        if verified.get("new_support", {}).get("value") == "yes":
            if not ORDER.search(masked) or not ORDER_ISSUED.search(masked):
                return verified["new_support"]
    for start, end in _clause_ranges(masked):
        clause = masked[start:end]
        if _direct_support_ask(clause) and not DECLINED.search(clause):
            if not ORDER.search(masked) or not ORDER_ISSUED.search(masked):
                return {"value": "yes", "source": "user_text", "span": _span(question, start, end)}
    # V71-P1-4 whole-text fallback: lay ask forms often split the request
    # verb and the support noun across clauses ("My grown-up daughter will
    # not support me. What can I file?", challenge 25; "Who handles a
    # request for cash ...? ... I am applying for the child.", verification
    # 003; "Can I make an application?" after a non-support clause,
    # development 007).  The conjunction is therefore also tried across the
    # whole question, with the SAME exclusions applied whole-text, plus an
    # UNCERTAIN guard so a hypothetical ("suppose ...") never becomes
    # evidence.  The beneficiary + no-issued-order gates above still apply.
    # The span is the minimal clause range covering every clause that
    # carries the request or the support noun — never a guessed span.
    if (
        REQUEST.search(masked)
        and SUPPORT.search(masked)
        and not DECLINED.search(masked)
        and not UNCERTAIN.search(masked)
        and not INTERIM_REQUEST.search(masked)
        and not PERMANENT_REQUEST.search(masked)
        and not CHANGE_REQUEST.search(masked)
        and not _recovery_ask(masked)
    ):
        if not ORDER.search(masked) or not ORDER_ISSUED.search(masked):
            covering = [
                (start, end)
                for start, end in _clause_ranges(masked)
                if REQUEST.search(masked[start:end]) or SUPPORT.search(masked[start:end])
            ]
            if covering:
                span_start = min(start for start, _ in covering)
                span_end = max(end for _, end in covering)
                return {"value": "yes", "source": "user_text",
                        "span": _span(question, span_start, span_end)}
    return None
