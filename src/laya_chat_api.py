"""Local JSON interface for the evidence-only Indian family law intake."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import re
from socket import timeout
from typing import Any

from .laya_family import assess as assess_maintenance
from .laya_family_evidence import OLD_ORDER, PRE_BNSS
from .laya_runtime import assess_turn

MAX_BODY_BYTES = 64 * 1024
MAX_TURNS = 12
MAX_TEXT_LENGTH = 4000

ACT_SOURCES = {
    "hma": "https://www.indiacode.nic.in/bitstream/123456789/12232/1/the_hindu_marriage_act%2C_1955.pdf",
    "sma": "https://www.indiacode.nic.in/bitstream/123456789/20574/1/special_marriage_act.pdf",
    "pwdva": "https://www.indiacode.nic.in/bitstream/123456789/6845/1/domviolence.pdf",
    "bnss": "https://www.indiacode.nic.in/indiacode/handle/123456789/20099?view_type=browse",
    "bns": "https://www.indiacode.nic.in/bitstream/123456789/20062/1/a2023-45.pdf",
    "gwa": "https://www.indiacode.nic.in/bitstream/123456789/2318/1/189008.pdf",
    "births": "https://www.indiacode.nic.in/bitstream/123456789/1682/3/a1969-18.pdf",
}

HMA_QUESTION = {
    "id": "hma_applicable",
    "text": "Is your marriage governed by the Hindu Marriage Act? If you are unsure, check your marriage certificate or ask a lawyer.",
}

_QUOTED = re.compile(r'"[^"]*"|“[^”]*”|‘[^’]*’')
_UNCERTAIN_ACT = re.compile(
    r"\b(?:if|suppose|maybe|might|probably|assuming|possibly|not sure|"
    r"whether|do not know|don['’]t know|not)\b", re.I,
)
_MARRIAGE_ACT = re.compile(
    r"\b(?:"
    r"we (?:got |were |are )?married under"
    r"|we registered our marriage under"
    r"|(?:our|my) marriage (?:was |is )?(?:solemni[sz]ed|registered|governed) under"
    r"|(?:our|my) marriage certificate (?:says|names|cites|states|lists)"
    r")\s+(?:the\s+)?(Hindu|Special) Marriage Act\b",
    re.I,
)


def _declared_marriage_acts(text: str) -> set[str]:
    """Read explicit own-marriage statements without inferring a law from identity."""
    text = _QUOTED.sub(" ", text)
    acts = set()
    for clause in re.split(r"[,.;!?\n]+", text):
        if not _UNCERTAIN_ACT.search(clause):
            acts.update("hma" if match.lower() == "hindu" else "sma"
                        for match in _MARRIAGE_ACT.findall(clause))
    return acts


class InvalidRequest(ValueError):
    pass


def _messages(payload: Any) -> list[tuple[str, dict[str, bool]]]:
    if not isinstance(payload, dict) or set(payload) != {"messages"}:
        raise InvalidRequest("Send a JSON object with a messages array.")
    messages = payload["messages"]
    if not isinstance(messages, list) or not 1 <= len(messages) <= MAX_TURNS:
        raise InvalidRequest(f"Send between 1 and {MAX_TURNS} user messages.")
    validated = []
    for item in messages:
        if not isinstance(item, dict) or set(item) - {"text", "answers"}:
            raise InvalidRequest("Each message accepts text and optional answers.")
        text = item.get("text")
        if (not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT_LENGTH
                or any(0xD800 <= ord(char) <= 0xDFFF for char in text)):
            raise InvalidRequest(f"Send nonempty Unicode text up to {MAX_TEXT_LENGTH} characters.")
        answers = item.get("answers", {})
        if not isinstance(answers, dict) or any(type(value) is not bool for value in answers.values()):
            raise InvalidRequest("Use true or false for answers to LAYA questions.")
        validated.append((text.strip(), answers))
    return validated


def _chat_result(result: dict[str, Any], hma_applicable: bool | None) -> dict[str, Any]:
    if result["error"] or result["extractor_mode"] not in ("evidence", "classifier"):
        raise RuntimeError("Assessment extractor runtime failed.")

    sections = result["kept_statutory_ids"]
    hma_unconfirmed = hma_applicable is not True and any(sec.startswith("hma-") for sec in sections)
    questions = [
        {"id": q["fact_key"], "text": q["question"]}
        for q in result["pending_clarifications"]
    ]
    if hma_unconfirmed and hma_applicable is None:
        questions.insert(0, HMA_QUESTION)
    questions = questions[:2]

    safety = "safety" in result["escalation_kinds"]
    checked_prose = isinstance(result.get("prose"), str) and result.get("prose_fp_hits") == []
    deliverable = checked_prose and not hma_unconfirmed and bool(sections)
    if safety:
        status = "urgent"
    elif not result["in_scope"]:
        status = "out_of_scope"
    elif questions:
        status = "needs_clarification"
    elif deliverable:
        status = "assessment"
    else:
        status = "needs_review"

    dispositions = result["dispositions"]
    provisions = [
        {
            "id": sec,
            "source_url": ACT_SOURCES.get(sec.partition("-")[0]),
            "reason_codes": dispositions[sec]["reason_codes"],
        }
        for sec in sections if checked_prose and (not hma_unconfirmed or not sec.startswith("hma-"))
    ]
    return {
        "status": status,
        "turn": result["turn_id"],
        "language": result["lang"],
        "extractor": result["extractor_mode"],
        "provisions": provisions,
        "forums": result["court_live"] if deliverable else [],
        "escalations": result["escalation_kinds"],
        "questions": questions,
        "answer": result["prose"] if deliverable else None,
        "safety_message": (
            "If you or a child are in immediate danger, contact local emergency services now."
            if safety else None
        ),
    }


def _post_order_result(response: dict[str, Any], intake: dict[str, Any],
                       text: str, bnss_answer: bool | None, mixed: bool) -> None:
    """Replace general maintenance results with the narrower order assessment."""
    response.update(provisions=[], forums=[], questions=[], answer=None, escalations=[])
    if mixed:
        response.update(status="needs_review", review_reason="mixed_order_and_other_requests")
    elif bnss_answer is False or OLD_ORDER.search(text) or PRE_BNSS.search(text):
        response.update(status="needs_review", review_reason="issuing_statute_needs_review")
    elif intake["routes"]:
        routes = intake["routes"]
        response.update(
            status="assessment",
            provisions=[
                {"id": r["id"], "source_url": r["url"], "reason_codes": r["because"]}
                for r in routes
            ],
            forums=list(dict.fromkeys(r["forum"] for r in routes)),
            answer="\n\n".join(
                " ".join([r["provision"] + ".", *r["requirements"], r["forum"]])
                for r in routes
            ),
        )
    else:
        response.update(
            status="needs_clarification",
            questions=[{
                "id": "bnss_order",
                "text": "Does the existing order itself cite section 144 of the BNSS, 2023?",
            }],
        )


def assess_conversation(payload: Any, *, extractor_mode: str = "auto") -> dict[str, Any]:
    """Replay user turns from the same matter and return the last assessment."""
    if extractor_mode not in ("auto", "evidence"):
        raise InvalidRequest("Unsupported server extractor_mode.")
    state = None
    hma_confirmation = None
    declared_acts: set[str] = set()
    order_text = None
    bnss_answer = None
    offered: set[str] = set()
    for text, answers in _messages(payload):
        if answers.keys() - offered:
            raise InvalidRequest("Answers must match question IDs from the preceding assessment.")
        confirmations = dict(answers)
        hma_confirmation = confirmations.pop("hma_applicable", hma_confirmation)
        declared_acts.update(_declared_marriage_acts(text))
        act_conflict = (
            len(declared_acts) > 1
            or ("sma" in declared_acts and hma_confirmation is True)
            or ("hma" in declared_acts and hma_confirmation is False)
        )
        sma_declared = "sma" in declared_acts and not act_conflict
        hma_applicable = hma_confirmation
        if act_conflict or sma_declared:
            hma_applicable = False
        elif "hma" in declared_acts:
            hma_applicable = True
        result, state = assess_turn(
            state, text, confirmations=confirmations, mode=extractor_mode, device="auto",
            vocab_profile="brutal_primary",
            judicial_separation_act="sma" if sma_declared else "hma",
            strict_pwdva=True,
        )
        response = _chat_result(result, hma_applicable)
        if response["status"] == "needs_review" and any(
            sec.startswith("hma-") for sec in result["kept_statutory_ids"]
        ):
            if act_conflict:
                response["review_reason"] = "conflicting_governing_marriage_law"
            elif sma_declared:
                response["review_reason"] = "unsupported_sma_relief"
        # The maintenance intake verifies the issuing law from the user's text
        # and separates post-order actions from an initial support application.
        if response["status"] != "out_of_scope":
            intake = assess_maintenance(text, lambda _: {})
            facts = intake["facts"]
            if any(facts.get(key, {}).get("value") == "yes" for key in ("recover", "vary")):
                order_text = text
                bnss_answer = None
            bnss_answer = confirmations.get("bnss_order", bnss_answer)
            maintenance = state.active_issues.get("maintenance")
            if maintenance is not None and maintenance.intent == "denied":
                order_text = None
            if order_text is not None:
                if response["status"] == "urgent":
                    response.update(provisions=[], forums=[], questions=[], answer=None,
                                    review_reason="urgent_order_review")
                else:
                    confirmed = {} if bnss_answer is None else {"bnss_order": bnss_answer}
                    if order_text != text or confirmed:
                        intake = assess_maintenance(order_text, lambda _: {}, confirmed)
                    mixed = any(
                        key not in {"maintenance", "procedure"} and issue.intent == "requested"
                        for key, issue in state.active_issues.items()
                    ) or any(
                        intake["facts"].get(key, {}).get("value") == "yes"
                        for key in ("new_support", "interim", "permanent")
                    )
                    _post_order_result(response, intake, order_text, bnss_answer, mixed)
        offered = {q["id"] for q in response["questions"]}
    return response


class _ChatHandler(BaseHTTPRequestHandler):
    timeout = 5
    extractor_mode = "auto"

    def log_message(self, format: str, *args: Any) -> None:
        # Request paths and bodies may contain private case details.
        pass

    def _active_extractor_name(self) -> str:
        if self.extractor_mode == "auto":
            try:
                from .laya_integrated import checkpoint_exists
                if checkpoint_exists():
                    return "classifier"
            except Exception:
                pass
        return "evidence"

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(200, {"status": "ok", "extractor": self._active_extractor_name(), "api_version": "1"})
        else:
            self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/v1/assess":
            self._json(404, {"error": "not_found"})
            return
        if self.headers.get_content_type() != "application/json":
            self._json(415, {"error": "expected_application_json"})
            return
        lengths = self.headers.get_all("Content-Length", [])
        if (len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit()
                or len(lengths[0]) > 10 or "Transfer-Encoding" in self.headers):
            self._json(400, {"error": "invalid_content_length"})
            return
        size = int(lengths[0])
        if size > MAX_BODY_BYTES:
            # Drain buffered payload bytes up to a cap so Windows loopback sockets
            # do not reset (WinError 10053) before the client reads the 413 response.
            to_drain = min(size, MAX_BODY_BYTES + 16384)
            try:
                while to_drain > 0:
                    chunk = self.rfile.read(min(8192, to_drain))
                    if not chunk:
                        break
                    to_drain -= len(chunk)
            except Exception:
                pass
            self.close_connection = True
            self._json(413, {"error": "payload_too_large"})
            return
        try:
            body = self.rfile.read(size)
            if len(body) != size:
                raise InvalidRequest("Incomplete request body.")
            result = assess_conversation(
                json.loads(body.decode("utf-8")),
                extractor_mode=self.extractor_mode,
            )
        except (InvalidRequest, UnicodeError, json.JSONDecodeError, RecursionError, timeout):
            self._json(400, {"error": "invalid_request"})
        except Exception:
            self._json(503, {"error": "assessment_unavailable"})
        else:
            self._json(200, result)


def make_server(port: int = 8765, *, extractor_mode: str = "auto") -> HTTPServer:
    if extractor_mode in ("auto", "classifier"):
        try:
            from .laya_integrated import checkpoint_exists, _load_classifier, resolve_checkpoint
            if checkpoint_exists():
                _load_classifier(resolve_checkpoint(None))
        except Exception:
            pass
    handler_cls = type(
        "_ConfiguredChatHandler",
        (_ChatHandler,),
        {"extractor_mode": extractor_mode},
    )
    return HTTPServer(("127.0.0.1", port), handler_cls)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--mode", choices=("auto", "classifier", "evidence"), default="auto")
    args = parser.parse_args()
    with make_server(args.port, extractor_mode=args.mode) as server:
        print(f"LAYA listening on http://127.0.0.1:{server.server_port} (mode={args.mode})", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
