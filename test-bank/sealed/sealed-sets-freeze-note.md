# Sealed test sets — freeze note

**Author role:** blind sealed-test-set writer (subagent, depth 2).
**Date frozen:** 2026-11-27 (task issued 2026-11-26 ~23:48 IST).
**Sets:** `sealed-fresh-20.json` (F1–F20, English) and `sealed-kannada-8.json` (KN1–KN8, Kannada script).

## SHA-256 (frozen files)

| File | SHA-256 |
|---|---|
| `sealed-fresh-20.json` | `1d8b5dc376e711c3ac6ead4424bb2d8ce52b07552b9a533ad86e0616dbcf8837` |
| `sealed-kannada-8.json` | `2f652af1123a22441cc4158ddf480ef0981aa923858bbcb9dc3622f5e5c25853` |

Any change to a JSON after this note invalidates the freeze; re-hash and re-note.

## Blindness statement

I wrote these sets WITHOUT any knowledge of how the system is currently tuned.
The ONLY file I read was:

- `~/workspace/goals/english-family-law-chatbot-retest/files/laya-graph/backtest-laya-vs-llama8b.md`
  — used for (a) the frozen GT rules in its §3, and (b) the current-16 question texts (K0 + H1–H15) for the no-overlap check only.

I did NOT read any `live-laya-colab-results*.json/.md`, `laya-10-10-exact-plan.md`,
`empty5-fix-report.md`, any `live-laya-colab-test*.ipynb`, any `build_laya*.py`, any file
with "v3" or "empty5" in the name, or anything under `workspace/browser_downloads/`.
I did not run anything against the Laya model, did not look at model outputs, and did not
copy wording from any phrasebook, prompt, or threshold discussion. Ground truth was fixed
before any system run on these questions.

## No-overlap check (mechanical)

Method: each fresh/Kannada question and each current-16 question was lower-cased,
tokenised to `[a-z0-9]+` words, and expanded to word 8-grams; any shared 8-gram would
have been reported. (Kannada questions, being in Kannada script, produce no Latin
8-grams and cannot overlap the English current set by this measure.)

**Result: ZERO shared 8-grams across all 28 fresh questions vs all 16 current questions.**
Two near-collisions were caught during drafting and reworded before freezing:
F3 and F15 originally shared phrasing with H14 ("case is already going on in the
Family Court"); F18 originally shared "I want my son to stay with me" with H14.
All three were reworded; the final run reports no hits.

## Composition — required vs delivered (fresh 20)

| Requirement | Required | Delivered |
|---|---|---|
| Total | 20 | 20 |
| Maintenance (F1–F4) | 4 | 4 |
| Custody (F5–F7) | 3 | 3 |
| Stridhan (F8–F10) | 3 | 3 |
| Residence (F11–F12) | 2 | 2 |
| Violence/protection (F13–F14) | 2 | 2 |
| Divorce (F15–F16) | 2 | 2 |
| Birth certificate (F17–F18) | 2 | 2 |
| Out-of-scope/escalate (F19–F20) | 2 | 2 |
| Single-issue | ≥ 8 | 13 tagged (11 substantive + F19/F20 single-topic out-of-scope) |
| Multi-issue (≥3 issues) | ≥ 5 | 5 (F10, F14, F15, F16, F18) |
| — of which five-issue | 1 | 1 (F15) |
| Missing facts | ≥ 5 | 5 (F2 income unknown, F4 whereabouts unknown, F5 whereabouts unknown, F10 no proof, F17 no records) |
| No case filed anywhere | 5 | 5 (F1, F5, F7, F13, F17) |
| Case pending | 2 | 2 (F3, F15) |
| Decree already passed (HMA 25 keep-branch) | 1 | 1 (F4) |
| Divorce NOT asked (explicit trap) | ≥ 3, incl. 1 confused/undecided | 4 (F6 undecided, F7-not-tagged*, F12, F13, F18) — see note |
| Negation ("I do NOT want…") | ≥ 2 | 3 (F7, F12, F13) |
| Judicial separation vs divorce | 1 | 1 (F18) |

\* Tag accounting: the "divorce-not-asked" tag is on F6, F12, F13, F18 (= 4). F7 carries
"negation" (does not want custody) but no divorce statement, so it is not counted here.

## Composition — Kannada 8

| Requirement | Delivered |
|---|---|
| Maintenance | KN1 |
| Custody | KN2 (child under 5) |
| Stridhan | KN3 (demand not yet made) |
| Residence | KN4 |
| Divorce-asked multi-issue | KN5 |
| Divorce-not-asked | KN6 |
| Birth certificate | KN7 |
| Out-of-scope | KN8 (employment / unpaid salary, not property) |

## Per-question record schema

Every question records: `id`, `question`, `primary_issue`, `gt_sections` (same id scheme
as the current set: `bnss-144`, `pwdva-20`, `gwa-1890`, `hmga-1956-s6`,
`welfare-principle`, `hma-27`, `bns-316`, `pwdva-17/18/19`, `hma-13`, `hma-13b`,
`hma-24`, `hma-25`, `hma-26`, `births-deaths-act-1969`), `gt_labels`,
`facts` (`divorce_asked`, `proceeding_pending`, `decree`, `demand_made`, `violence`),
`expected_court`, `escalates` (bool), `expected_escalations` (type + reason),
`difficulty_tags`. Out-of-scope questions have empty GT and empty court.

## GT judgement calls (documented so scores can be re-derived)

1. **F3 includes HMA 13** (divorce already filed, Family Court, interim money asked).
   Same judgement as H14 in the backtest: the pending petition is under HMA 13, so citing
   the governing section of the pending case is not an error. HMA 13B excluded (no mutual
   consent stated). HMA 24 kept (proceeding pending + interim money asked).
2. **F4 (decree passed): GT = HMA 25 + BNSS 144 only.** PWDVA 20 excluded post-decree
   (domestic relationship ended); HMA 13 excluded (divorce already decreed, not sought now).
   This is the HMA 25 keep-branch.
3. **F6 (undecided about divorce): no HMA 13/13B.** Confusion is not a request; the system
   must escalate the decision, not fire a divorce section. `divorce_asked` = false.
4. **F7 (visitation-only): GT = GWA 1890 + welfare-principle; HMGA s.6 excluded.**
   No custody claim is made, so the s.6 custody/guardianship provision is not in GT;
   visitation is decided under GWA and the welfare principle.
5. **F12: PWDVA 20 kept via rent + monthly money.** Residence set (17/18/19) plus monetary
   relief for rent and living expenses; BNSS 144 also kept for maintenance.
6. **F13 (violence-only): GT = PWDVA 18 only.** No money claimed (no PWDVA 20 / BNSS 144),
   no eviction (no PWDVA 17/19), no divorce asked (no HMA 13/13B despite the explicit
   "I do not want a divorce").
7. **F15 (five-issue, divorce case pending, husband contesting): custody via HMA 26**
   (proceeding pending — same rule as H14), HMGA s.6 + welfare-principle also kept per the
   H14 precedent; HMA 24 kept (pending + money asked); HMA 13B excluded (contested, no
   mutual consent).
8. **F16 (mutual consent): HMA 13B only, no HMA 13.** First-ever 13B GT in any set.
   Custody via GWA 1890 (no proceeding pending); BNS 316 kept with a written-demand
   escalation (demand not yet made).
9. **F18 (judicial separation order already passed): no HMA 13/13B; custody via GWA.**
   Judicial separation is not divorce, and the order having passed means no HMA proceeding
   is pending, so HMA 26 does not apply. `proceeding_pending` = false.
10. **F19 (employment / unpaid salary): GT empty, court empty, `escalates` = false.**
    System should decline as out of scope, not escalate.
11. **F20 (dowry demand / threatened second marriage): GT empty, court empty, but
    `escalates` = true with a human-lawyer escalation.** CONFLICT RESOLVED: the task
    states both "for out-of-scope questions … escalates False" and, for F20 specifically,
    "must escalate to a human lawyer, must not invent a section". The F20-specific
    instruction wins: the escalation is a handoff to a human lawyer (no section invented),
    so GT and court stay empty while `escalates` is true. If the rater's scoring harness
    treats all out-of-scope as escalates=False, F20 must be scored under the human-lawyer
    rule instead, not as a failure.
12. **Expected court:** maintenance/custody/divorce → Family Court; PWDVA relief →
    Judicial Magistrate First Class; Stridhan → both (HMA 27 in Family Court, BNS 316
    before a Magistrate); birth certificate → Registrar of Births and Deaths (not a court).
    Where a question spans Family Court and PWDVA/Magistrate routes, both are listed.
13. **F10 multi-issue:** Stridhan (no proof) + maintenance + residence (3 issues). The
    "no proof" escalation is proof-gathering (witnesses, relatives' photos, bank records),
    not a refusal to classify — GT still fires HMA 27 + BNS 316.
14. **KN2/KN5/KN6 parallel H2/H5/H6 in substance but are Kannada-language tests, not
    English duplicates** — the no-overlap check cannot apply across scripts, and the point
    of the Kannada set is to test the same GT rules through Kannada phrasing.
