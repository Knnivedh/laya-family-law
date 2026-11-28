# LAYA chatbot integration

This local service connects a chatbot backend to the Indian family-law evidence runtime. It returns potential provisions, official statute links, route reason codes, forums, questions and escalation status.

## Run the endpoint

From the repository root, start Python 3.11 or newer.

```powershell
python -m src.laya_chat_api --port 8765
```

The server binds to `127.0.0.1`. It uses the evidence extractor on CPU and requires no model download. `GET /health` reports the selected extractor and API version. `POST /v1/assess` accepts JSON.

```json
{
  "messages": [
    {"text": "I want to divorce my husband."}
  ]
}
```

Render the returned question to the person and wait for their answer. To continue the same matter, resend the user turns in order. Supply boolean `answers` for the question IDs returned by the preceding response, only when the person has explicitly answered them.

```json
{
  "messages": [
    {"text": "I want to divorce my husband."},
    {"text": "Yes, it is.", "answers": {"hma_applicable": true}}
  ]
}
```

If the person is unsure, leave that answer unset. Start a new request history when they switch matters. The service replays at most 12 user turns with 4,000 characters per turn and a 64 KiB body limit. The service keeps the history in memory during the request and suppresses request logging. The calling backend controls storage of the history.

### Response handling

- `assessment` includes provisional legal information. Render `answer` and use only the returned `provisions` and `source_url` values.
- `needs_clarification` includes one or two questions. Preserve their IDs in the client and present the questions before concluding the assessment.
- `needs_review` indicates an unresolved, mixed or unsupported route. Use the handoff in the chat UI. An empty provision list in this state carries no conclusion about legal eligibility.
- `out_of_scope` hands off an identified non-family-law request.
- `urgent` prioritizes `safety_message` in the UI, even when the assessment has no provisions.

HTTP 400, 413 and 415 indicate a request problem. HTTP 503 indicates unavailable assessment. Keep the service behind the chatbot backend. A shared deployment needs authentication and authorization, transport security, a retention policy, throttling and an independently reviewed handoff process.

The intake checks Hindu Marriage Act applicability before returning that Act's provisions. For a focused request to enforce or vary an existing maintenance order, it checks the issuing statute and the requested action. It can return BNSS 144(3) for recovery or BNSS 146 for variation when the BNSS order is established. Older, unclear and mixed orders can require clarification or review. [Hindu Marriage Act](https://www.indiacode.nic.in/bitstream/123456789/1560/1/A1955-25Eng.pdf) · [BNSS](https://www.indiacode.nic.in/indiacode/handle/123456789/20099?view_type=browse)

## Reproduce the checks

```powershell
python -m unittest discover -s tests -p "test_*.py" -q
python -m tests.integrated_backtest --mode auto --suite all --misses 0 --json-out laya-integrated-results.json
python -m tests.chat_backtest
python scripts/ci_gate.py --all
```

The integrated benchmark checks the section set before chatbot-specific clarifications and handoffs. The HTTP benchmark checks the returned statutory IDs on the first user turn and separately counts responses with an answer. The 16-question score of 7.6/10 includes its measured pre-recheck penalty. Brutal-230 has a separate pass criterion. Kaanoon uses real user wording with expected section sets derived from the existing graph, so its score measures extraction and routing agreement with that graph. These commands leave the sealed questions out of scoring.

For GPU comparison, use `python -m tests.v7_backtest --suite both --mode laya --device cuda --misses 0`. An explicit `--kannada-strategy nllb_then_en` reproduces the historical noncommercial translation path for research. The local chat service uses neither translation model nor classifier weights. [NLLB model card](https://huggingface.co/facebook/nllb-200-distilled-600M)

## Sequence to release

1. **Establish the Indian family-law coverage.** Inventory executable provisions by statute, personal-law applicability, proceeding stage, territorial jurisdiction and effective date. Mark routes that require professional review. The graph covers selected maintenance, HMA matrimonial, custody, domestic violence, Stridhan and civil-registration scenarios. It lacks comprehensive coverage of other marriage statutes, personal-law regimes, adoption, succession and related state rules.
2. **Separate extraction misses from routing misses.** Have family-law reviewers independently label statutes, material facts, reasonable alternate remedies and forum. Compare gold facts passed to the graph with predicted facts passed to the same graph. Fix graph prerequisites and provenance first when the gold-input result fails. Report false provisions, misses, silent responses and unsafe escalations separately.
3. **Validate the bilingual classifier.** Group the training/validation data by scenario family, keep independent layman questions apart from training and calibration, and publish the trained checkpoint, model/tokenizer revisions and calibrated thresholds together. Compare English, Kannada script and Romanized Kannada separately. Measure a provision and safety regression before promoting a language route.
4. **Verify the chat itself.** Use independent multi-turn transcripts to test clarifications, corrected facts, region and governing-law questions, mixed issues and safe handoffs. Score exact statutory results after relevant facts are supplied and separately measure first-turn answer coverage. Test correctness of cited legal sources, forums and urgent-safety handling.
5. **Use the repository's release gates.** Run the blind multilingual set after freezing the candidate. Require independent legal review, zero unsupported statutory or case citations in the reviewed set, safety-gate passes and a second confirmation run. Keep a bounded release scope if any language, issue category or safety gate fails. A perfect benchmark score describes that benchmark and version.
