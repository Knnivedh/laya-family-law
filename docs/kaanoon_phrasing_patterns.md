# Kaanoon Phrasing Patterns — Layman Family-Law Questions (LANE 11 study)

**Source:** 16 real public questions from https://www.kaanoon.com/ (study sample
only, `data/kaanoon_eval/study_sample.jsonl`, IDs KAN-S01–S16). **Patterns here
come ONLY from the study sample — never from the held-out eval set**
(contract R7). Question text only; lawyers' answers were not used and are not
cited anywhere. Fragments below are short illustrative excerpts (2–3 max per
pattern), never full questions and never answers.

**For:** Lane 02 (paraphrase templates), Lane 03 (regex anchors), Lane 08
(Stage 1 routes audit). Templates stay our own — these patterns inform them;
nothing here is copied into the training corpus.

## Cross-cutting shapes (all categories)

1. **Narrative first, question last.** A 3–10 sentence story (marriage length,
   who did what, money, children) then a closing ask: "Kindly advice how to
   proceed", "Please suggest", "what am i suppose to do?"
   - "I am separated from last 6 years reason very abusive."
   - "what am i suppose to do?"
2. **Numbered sub-questions.** One post, several numbered asks (Q1–Q4 / 1. 2.
   3. 4.), often mixing issues (custody + maintenance + divorce in one post).
   - "Can the court Jail me ( No offense has ever been made from my side barring these 6 months fees) ?"
   - "What will be the time limit to appeal for any such claims?"
3. **Third-party askers.** The asker is often not the claimant: a friend, a
   brother, a mother-in-law, a son asking for the mother.
   - "I am here asking for friend who is married for about 7 years now."
   - "My daughter-in-law and son do not have cordial relationship with each other"
4. **Unedited lay spelling/grammar.** Phonetic spelling, missing articles,
   SMS abbreviations. Anchors must not depend on clean spelling.
   - "is my property clear for smooth sale purchase without ny challenges by her"
   - "i was asked to leave my matrimony house"
5. **Ages and amounts always given as facts.** Child ages, marriage length,
   money in lakhs/rupees, durations ("for last 1 year", "since June' 17").
   - "Our maid who has a 3 year child"
   - "I agreed to pay 14 lakh final settlement amount"

## Custody (S08, S16)

- **"Live separately with the child" framing** — custody is asked as living
  arrangements, not as a legal term.
  - "I want to live separately from my husband with my 2.5 yrs old son."
  - "What are the legal steps to protect myself from him"
- **Fear of the other parent taking the child** ("take away", "get the
  custody", "try his level best").
  - "my husband will try his level best to get the son's custody."
- **Bonding / who the child lives with now** as the argument, not statute.
  - "The child can identify his father but he has absolutely no bonding with him"
- **"Thumb rule" money questions** attached to custody ("1/3rd thumb rule as
  in MC case").

## Maintenance (S05, S06, S15)

- **School-fees itemisation instead of "maintenance".** Askers list what is /
  is not paid rather than naming the remedy.
  - "he is only paying her school fees excluding school bus transport, school dress, stationary"
  - "the court ordered me to pay the child's school fees \"there onwards \""
- **Enforcement fear phrased as jail / fine / confiscation.**
  - "Can the court Jail me ... ?"
  - "can the court confiscate my property to pay the Complainant's unsuitable demands"
- **"I have stopped going to court"** — non-attendance stated flatly, as a
  fact the answer must work around.
  - "Because of my new job I have stopped going to court from last 2 years."
- **Maintenance-while-separated** stated as the situation, not the claim.
  - "filed case in the court for maintenance from her husband while living separately."

## Divorce (S07)

- **Settlement-first framing.** The ask is about the settlement terms, not
  about grounds.
  - "I agreed to pay 14 lakh final settlement amount as I wanted to end the litigations"
  - "Please suggest me the terms/agreement points for final settlement which I can put to the mediator."
- **"End the litigations"** as the goal phrase (plural cases, not one case).

## Stridhan (S01, S02)

- **"Displayed / shown" jewellery** — the claim is argued from wedding
  display, photos, video, not from lists or bills.
  - "all and any jewelry that was displayed at the wedding is her \"streedhan\""
  - "She is using photographs and the wedding video as the evidence"
- **"Gave me / kept by" possession verbs** instead of "entrusted".
  - "Mother gave me her all her gold ornaments which were bought by my father."
- **Emotional-attachment argument** ("last wishes and memory") alongside the
  legal ask.
  - "I don't want to return my mother's gold to my father as those were her last wishes and memory."
- **Bills demanded as proof** ("with bills of those ornaments also which we
  have completely no idea").

## Eviction / residence (S03, S04)

- **"Asked to leave / not taken back"** — lockout told as a story, never as
  "coercive eviction" or "lockout".
  - "one day i was asked to leave my matrimony house stating that he needs a cool off period"
  - "when tried to return house i was not taken back.."
- **"Let her out / clear the property"** — eviction asked from the
  property-owner's side, in plain words.
  - "how can we proceed to let her out of this floor or the entire property?"
  - "is my property clear for smooth sale purchase"
- **Divorce refusal + money** bundled into the eviction ask ("She is not
  agreeing for the divorce", "she did not even apply for ny job").

## Restitution (S12)

- **Leaving told as disappearance** ("leaves India without any information
  to us"), ask is "how do I proceed legally".
  - "one day she leaves India without any information to us."
  - "Can you please guide me with the right suggestion how do I proceed legally"
- **Separation duration as the opening fact** ("living separately from last
  11.5months").

## Violence (S10, S11, S13)

- **Beating described with frequency/habit words** ("usually", "habitual
  drinker", "keeps beating me"), often with a reason clause.
  - "his husband is habitual drinker and beats her regularly."
  - "my husband keeps beating me because i kept my Stridhan with my parents for safety"
- **Injury as the proof** ("fractured her hand", "ruptured my eardrum",
  "tried to kill me by choking my throat") — concrete body facts, no legal
  labels.
  - "she almost fractured her hand and had to rush to hospital."
  - "he tried to kill me by choking my throat"
- **Threats quoted as conditions** ("she do not dare to ask for a single
  rupee as alimony", "he will not give the gold").

## Joint property (S09)

- **"Can wife claim rights in joint property"** — asked as a yes/no about
  the other spouse's rights, with the document fact attached.
  - "Can wife claim rights in joint property of husband? Agreement and share certificates are in joint name."
- **Time-limit question** ("What will be the time limit to appeal for any
  such claims?").

## Out-of-scope flavour (S14, dowry)

- **"Will it be held as ...? And if so what is the punishment"** — the
  asker names the feared label and asks for the consequence.
  - "Will it be held as dowry? And if so what is the punishment under Indian penal code."

## What Stage 1 must NOT assume (from this sample)

- Askers almost never name the statute or section ("125", "498A", "406" appear
  in only a few posts, usually quoted from an existing case, not as the ask).
- "Divorce", "maintenance", "custody" are often NOT the words used: the ask
  is "live separately with my son", "school fees", "let her out of this
  floor", "get the gold back".
- One post routinely spans 2–4 issues; a single-issue read will miss the
  second claim (e.g. custody + school fees + divorce threat in one post).
- Negation is soft: "She is not agreeing for the divorce", "I never marriage
  again so divorce is not essential" — denial is phrased as unwillingness,
  not as "I do not seek divorce".
