# LAYA chatbot integration

This local service connects a chatbot backend to the Indian family-law evidence runtime. It returns potential provisions, official statute links, route reason codes, forums, questions and escalation status.

## Run the endpoint

From the repository root, start Python 3.11 or newer.

```powershell
python -m src.laya_chat_api --port 8765 --mode auto
```

The server binds to `127.0.0.1`. With `--mode auto` (the default) and a trained checkpoint at `models/v71-classifier/best/model.pt`, `make_server()` pre-warms the `google/muril-base-cased` Stage-1 classifier so English queries stay anchored on grounded evidence rules while Kannada, Kanglish, and paraphrased queries use the calibrated MuRIL extractor. Pass `--mode evidence` (or omit the checkpoint directory) to run the zero-model CPU evidence extractor alone. `GET /health` reports the selected extractor and API version. `POST /v1/assess` accepts JSON.

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

The intake checks the user's governing marriage law before returning provisions under that law. For a clear request for judicial separation, it can discuss HMA §10 or SMA §23 when the governing Act is established from the user's answer or a clear statement about their own marriage. A generic reference to a court marriage leaves the Act unresolved. The answer explains the potential remedy and leaves statutory grounds and local forum for verification. [Hindu Marriage Act §§10, 19](https://www.indiacode.nic.in/bitstream/123456789/12232/1/the_hindu_marriage_act%2C_1955.pdf) · [Special Marriage Act §§23, 31](https://www.indiacode.nic.in/bitstream/123456789/20574/1/special_marriage_act.pdf) · [Family Courts Act §§7–8](https://www.indiacode.nic.in/bitstream/123456789/19489/1/the_family_court_act%2C1984.pdf)

For a focused request to enforce or vary an existing maintenance order, the intake checks the issuing statute and the requested action. It can return BNSS §144(3) for recovery or §146 for variation when the BNSS order is established. Older, unclear and mixed orders can require clarification or review. Express domestic-violence denials and independently reported threats are evaluated separately. Ordinary maintenance can remain available for consideration while an unsupported domestic-violence route is withheld. [BNSS](https://www.indiacode.nic.in/indiacode/handle/123456789/20099?view_type=browse) · [PWDVA §§2, 3, 12 and 20](https://www.indiacode.nic.in/bitstream/123456789/15436/1/protection_of_women_from_domestic_violence_act%2C_2005.pdf)

## Reproduce the checks

```powershell
python -m unittest discover -s tests -p "test_*.py" -q
python -m tests.integrated_backtest --mode auto --suite all --misses 0 --json-out results/laya_v71_muril_auto.json
python -m tests.chat_backtest --mode auto --json-out results/laya_v71_muril_chat_http.json
python scripts/ci_gate.py --all --allow-blocked
```

With calibrated `google/muril-base-cased` (`models/v71-classifier/best/model.pt`), `tests.chat_backtest --mode auto` completed `774` non-sealed HTTP `POST /v1/assess` requests with `0` HTTP errors: Turn-1 exact provision sets improved to **369/500** (`283/500` with delivered answers; `p95 = 65.05 ms`, vs `219/500` in `--mode evidence`) on `validation-500`, **181/230** (`357 TP / 0 FP`; `p95 = 51.21 ms`, vs `169/230` in `--mode evidence`) on `brutal-230`, **13/16** (`40 TP / 0 FP`) on `16-Q`, and **10/28** (`p95 = 46.55 ms`) on `kaanoon-28` (where HMA marriage applicability intentionally waits for Turn-2 user confirmation before emitting `hma-*` sections).

The integrated benchmark checks the section set before chatbot-specific clarifications and handoffs. The HTTP benchmark checks the returned statutory IDs on the first user turn and separately counts responses with an answer. The 16-question score of 7.6/10 includes its measured pre-recheck penalty. Brutal-230 has a separate pass criterion. Kaanoon uses real user wording with expected section sets derived from the existing graph, so its score measures extraction and routing agreement with that graph. These commands leave the sealed questions out of scoring.

For GPU comparison, use `python -m tests.v7_backtest --suite both --mode laya --device cuda --misses 0`. An explicit `--kannada-strategy nllb_then_en` reproduces the historical noncommercial translation path for research. The local chat service uses neither translation model nor classifier weights. [NLLB model card](https://huggingface.co/facebook/nllb-200-distilled-600M)

## Sequence to release

1. **Establish the Indian family-law coverage.** Inventory executable provisions by statute, personal-law applicability, proceeding stage, territorial jurisdiction and effective date. Mark routes that require professional review. The graph covers selected maintenance, HMA matrimonial, custody, domestic violence, Stridhan and civil-registration scenarios. It lacks comprehensive coverage of other marriage statutes, personal-law regimes, adoption, succession and related state rules.
2. **Separate extraction misses from routing misses.** Have family-law reviewers independently label statutes, material facts, reasonable alternate remedies and forum. Compare gold facts passed to the graph with predicted facts passed to the same graph. Fix graph prerequisites and provenance first when the gold-input result fails. Report false provisions, misses, silent responses and unsafe escalations separately.
3. **Validate the bilingual classifier.** Group the training/validation data by scenario family, keep independent layman questions apart from training and calibration, and publish the trained checkpoint, model/tokenizer revisions and calibrated thresholds together. Compare English, Kannada script and Romanized Kannada separately. Measure a provision and safety regression before promoting a language route.
4. **Verify the chat itself.** Use independent multi-turn transcripts to test clarifications, corrected facts, region and governing-law questions, mixed issues and safe handoffs. Score exact statutory results after relevant facts are supplied and separately measure first-turn answer coverage. Test correctness of cited legal sources, forums and urgent-safety handling.
5. **Use the repository's release gates.** Run the blind multilingual set after freezing the candidate. Require independent legal review, zero unsupported statutory or case citations in the reviewed set, safety-gate passes and a second confirmation run. Keep a bounded release scope if any language, issue category or safety gate fails. A perfect benchmark score describes that benchmark and version.

See the [statutory coverage roadmap](family-law-coverage-roadmap.md) and the
[corpus audit and training split](family-law-data-audit.md) for the measured gaps and commands.
