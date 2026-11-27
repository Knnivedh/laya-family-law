# Maintenance raw-text accuracy plan

## Objective and baseline

Improve the existing Indian family-law maintenance intake from commit
`2e9fb91`. The observed smoke baseline was 7/12 exact from initial text,
including 2/7 cases with a nonempty expected provision set. The guided
workflow scored 12/12 with scripted answers. Preserve both entry points and
the frozen historic graph, notebooks, benchmarks and prior results.

## Implementation sequence

1. Freeze an engineering development bank and a separate verification bank
   with case-family IDs, expected provision sets, and expected clarification
   or handoff where applicable. Cover five live maintenance routes, role
   confusions, multiple requests, procedural ambiguity, hypotheticals,
   negation, quoted text, orders under other laws and unrelated requests.
   Freeze bank hashes before the baseline. Use only raw question text at
   the inference boundary.
2. Reproduce the baseline on both banks. Development traces classify misses
   by intent, beneficiary, procedural evidence or routing. Withhold
   verification case details during tuning. Track exact-set accuracy,
   positive exact, false provision emissions, unsupported citations, and
   required questions separately.
3. Accept decisive procedural facts evidenced in the initial question.
   Proof must link the named law to the user's actual case stage or to their
   existing order. A hypothetical filing, denied condition, another
   person's case, an unrelated provision in an advice quote, and an
   unidentified order stay unresolved. Preserve the text span and its
   provenance. User follow-up answers can supersede an initial finding.
4. Compare alternative extraction using development evidence. Evaluate a
   compact local structured extractor if the model is available. Treat its
   span locations or quotes as untrusted until verified against the input.
   Keep the legal predicate layer deterministic, and use the resulting
   calibration or evidence policy across cases. Use no test IDs or
   ground-truth facts as inference inputs. Keep each experiment small enough
   to attribute improvement and record accuracy and latency before promoting.
5. Run the locked candidate on the untouched verification bank twice in
   fresh processes on the RTX 5050. Compare the provision sets, clarification
   outcomes, duplicate/unsupported citations and runtime errors. Check both
   terminal and JSON paths and rerun the existing frozen integrity tests.
   If verification cases drive a subsequent fix, treat that result as
   regression and prepare a new bank for the next independent estimate.

## Success criterion

A scoped 10/10 means every case on a pre-registered, independently
lawyer-reviewed maintenance release suite matches its exact provision set and
the required clarification, forum and evidence outcome, with zero unsupported
citations and zero runtime errors, on two unchanged live runs. Report raw
and guided outcomes separately. The authored banks in this iteration are
engineering evidence and use only the routes the current intake implements.
Independent legal review, the original family-law gate, and broader family
law including Kannada remain separate milestones.
