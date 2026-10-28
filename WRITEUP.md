# WRITEUP: AI proposal triage (MATACS-TH-2026-02)

**One-line design:** AI reads each proposal and reports facts with exact quotes. Plain code checks the facts, applies the admin's criteria and ranks. People review the result and make the award decision. See `diagram/flow.png`.

## 1. AI vs. rules

- **AI does one job:** turning messy proposal prose into facts (price, weeks, warranty years, licence held, install list, team details). Rules cannot read "all-in" or "to be confirmed after award".
- **Rules do everything else:** text extraction, a scan for text aimed at AI, quote checks, mandatory pass/fail gates, scoring formulas, ranking and the reason text.
- **Why there:** the AI may report what a document says, but never decides what it is worth. Scores must be identical every run and explainable to a non-developer. AI scoring is neither, and it can be talked into things by the text it reads.

## 2. Consistency and explainability

- Extraction runs once per file at temperature 0 with a pinned model. The facts are saved against the file hash and the criteria version.
- Ranking again with the same proposals reuses the saved facts and fixed formulas, so **the result is identical**. Re-extraction only happens if a file changes.
- Formulas (all in `prototype/score.py`): experience bands; price = lowest eligible price / bid price; timeline = shortest eligible weeks / bid weeks; warranty = half panel, half workmanship; team = 25 points each for named lead, crew, safety plan, monitoring plan. Ties: score, then experience, then lower price, then ID.
- Price and timeline compare against the other eligible bids, so a score depends on the batch. The batch is recorded with the result.
- A reviewer sees, for each proposal, a per-criterion table and, next to every fact, the quote and page it came from. The reason text is built from those numbers, not written by the AI.

## 3. Human in the loop

- **Checkpoint 1, reviewer:** must open every flagged and ineligible proposal. They can correct a fact (shown beside its quote) or clear a flag, always with a written reason. The system then re-runs the rules. People change facts, never raw scores, so every change is traceable.
- **Checkpoint 2, award:** a person decides and writes the rationale. The decision does not have to follow the ranking.
- **Logged:** file hashes, criteria version, prompt and model version, raw AI output, failed checks, flags, scores, each override (who, when, old value, new value, reason) and the final decision.

## 4. Changing criteria

- The admin never edits a live set. Saving creates version N+1; version N stays as it was.
- Results scored under N are marked **stale**, not silently changed. Re-scoring is an explicit action. It reuses saved facts, and only a new or changed field needs a new AI call.
- The reviewer sees the old and new ranking side by side, with rank changes and any proposal that flips eligibility (for example, a new mandatory criterion).
- Weights must total 100% or the save is blocked. All proposals in one decision are scored under one version, so nobody is judged on different rules. After an award is recorded, results are locked; changing them needs an admin reason in the log.

## 5. Risks and guards

| Risk | Guard |
|---|---|
| Wrong extraction | Every value needs a verbatim quote that code finds in the PDF; a missing quote means "not stated". Reviewer sees quotes. |
| Made-up facts | "Not stated" is allowed and preferred to guessing; no inference, no outside knowledge; the numbers and gates are code. |
| Manipulation (text telling the AI to rank first) | Proposal text is wrapped as untrusted data; rule-based scan plus AI report of injection attempts; output is JSON-only; the AI cannot rank or call tools. The attempt raises a flag and a human decides. |
| Bias | Scorer sees facts only, never company names or free text; one rubric for all; reviewers see score breakdowns, so odd patterns (for example, penalising small firms) are visible. |
| Unverified claims (licence, insurance) | Output says "stated", not "verified". The reviewer checks the licence number against the public ECRA/ESA register before award. |
| Cost, outages, model drift | One call per proposal, capped input size, cached results; re-scoring costs nothing. Model version is pinned and a fixed test set is re-run before any change. |

## Sample set result (assumptions stated)

Assumptions: "last 5 years" counts back from 2026; A, B and E state periods inside it. C says "since 2020" and cannot be split, so its count is flagged as unconfirmed. The odd instruction text appears right after C's text, so I attribute it to C.

| Rank | Proposal | Score | Why |
|---|---|---|---|
| 1 | A | 98.0 | Passes both gates; best on experience, timeline and team. |
| 2 | E | 91.7 | Passes; best warranty and team, slightly higher price. |
| 3 | D | 76.2 | Passes; best price but no schedule stated (timeline scores 0) and a thin team. Even a 12-week schedule would not pass E. |
| none | B | not scored | **Ineligible:** its electrical work goes to an unnamed subcontractor "after award", so the bidder does not hold the licence. It is cheapest and fastest, so a human may ask the admin whether subcontracting is acceptable. |
| none | C | 81.8 provisional | **Flagged:** contains a note to automated reviewers asking for rank 1 and full marks. Ignored in scoring; no rank until a person clears or disqualifies it. If cleared, it would rank 3rd, ahead of D. |

Facts per proposal are in `prototype/extracted_samples.json`. Running `python prototype/score.py` reproduces `ranking.json`.
