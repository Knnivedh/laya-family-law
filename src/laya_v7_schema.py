"""Typed Stage 0/1/2 schema and scorer-isolated contracts for LAYA v7."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

FactStatus = Literal["supported", "denied", "unknown", "conflicting"]
IssueIntent = Literal["requested", "incidental", "denied", "uncertain"]
DispositionStatus = Literal["eligible", "conditional", "needs_fact", "inapplicable"]
ModalityTime = Literal["present", "past", "future", "hypothetical", "quoted", "general"]

FACT_STATUSES = ("supported", "denied", "unknown", "conflicting")
ISSUE_INTENTS = ("requested", "incidental", "denied", "uncertain")
DISPOSITION_STATUSES = ("eligible", "conditional", "needs_fact", "inapplicable")
ESCALATION_KINDS = (
    "quantum",
    "custody",
    "residence",
    "safety",
    "recovery",
    "demand",
    "procedure",
    "court",
    "fact",
)


@dataclass
class TextSpan:
    start: int
    end: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {"start": self.start, "end": self.end, "text": self.text}


@dataclass
class IssueEvidence:
    issue: str
    intent: IssueIntent = "uncertain"
    source: str = "model"
    confidence: float = 0.0
    span: TextSpan | None = None
    turn: int = 0

    def to_dict(self) -> dict[str, Any]:
        out = {
            "issue": self.issue,
            "intent": self.intent,
            "source": self.source,
            "confidence": round(float(self.confidence), 4),
            "turn": self.turn,
        }
        if self.span is not None:
            out["span"] = self.span.to_dict()
        return out


@dataclass
class FactEvidence:
    key: str
    status: FactStatus = "unknown"
    value: Any = None
    subject: str = "unknown"
    beneficiary: str = "unknown"
    modality_time: ModalityTime = "present"
    source: str = "default"
    confidence: float = 0.0
    span: TextSpan | None = None
    turn: int = 0

    @property
    def is_supported(self) -> bool:
        return self.status == "supported"

    @property
    def is_denied(self) -> bool:
        return self.status == "denied"

    def to_dict(self) -> dict[str, Any]:
        out = {
            "key": self.key,
            "status": self.status,
            "value": self.value,
            "subject": self.subject,
            "beneficiary": self.beneficiary,
            "modality_time": self.modality_time,
            "source": self.source,
            "confidence": round(float(self.confidence), 4),
            "turn": self.turn,
        }
        if self.span is not None:
            out["span"] = self.span.to_dict()
        return out


@dataclass
class RemedyDisposition:
    section_id: str
    status: DispositionStatus
    reason_codes: list[str] = field(default_factory=list)
    missing_facts: list[str] = field(default_factory=list)
    forum: str | None = None
    forum_authority: str | None = None
    applied_principles: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def proved_true(facts: dict[str, Any], key: str, default: bool = False) -> bool:
    """Strict three-valued -> bool projection: NEVER treats 'unknown'/'no' strings as True."""
    if key not in facts:
        return default
    val = facts[key]
    if isinstance(val, FactEvidence):
        return val.status == "supported" and (val.value is not False)
    if isinstance(val, dict) and "status" in val:
        return val.get("status") == "supported" and (val.get("value") is not False)
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        norm = val.strip().lower()
        return norm in {"true", "yes", "1", "supported"}
    return False


def fact_value(facts: dict[str, Any], key: str, default: Any = None) -> Any:
    """Extract canonical tri-state value (`True`, `False`, `None`) or enum string safely."""
    if key not in facts:
        return default
    val = facts[key]
    if isinstance(val, FactEvidence):
        if val.status == "supported":
            return True if val.value is None else val.value
        if val.status == "denied":
            return False if val.value in (None, True) else val.value
        return default
    if isinstance(val, dict) and "status" in val:
        st = val.get("status")
        inner = val.get("value")
        if st == "supported":
            return True if inner is None else inner
        if st == "denied":
            return False if inner in (None, True) else inner
        return default
    if isinstance(val, str):
        norm = val.strip().lower()
        if norm in {"true", "yes", "1", "supported"}:
            return True
        if norm in {"false", "no", "0", "denied"}:
            return False
        if norm in {"", "unknown", "none", "null", "unclear", "conflicting"}:
            return default
    return val


def is_denied(facts: dict[str, Any], key: str) -> bool:
    if key not in facts:
        return False
    val = facts[key]
    if isinstance(val, FactEvidence):
        return val.status == "denied"
    if isinstance(val, dict) and "status" in val:
        return val.get("status") == "denied"
    if isinstance(val, bool):
        return val is False
    if isinstance(val, str):
        return val.strip().lower() in {"false", "no", "0", "denied"}
    return False
