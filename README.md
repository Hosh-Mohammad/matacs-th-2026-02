# MATACS-TH-2026-02: AI Proposal Triage Design

- **Name:** Hosh Muhammad Tunio
- **Reference:** MATACS-TH-2026-02
- **Role:** Associate Software Developer
- **Time actually spent:** 2 hours

## What is in this repository

| File | What it is |
|---|---|
| [WRITEUP.md](WRITEUP.md) | Answers to the five questions, plus how the design ranks the sample set (A-E) |
| [diagram/flow.png](diagram/flow.png) | Process flow from upload to ranked output, colour-coded: AI step, rules, human checkpoints |
| [PROMPTS.md](PROMPTS.md) | The extraction prompt exactly as it would be sent, plus the field list and what code does with the answer |
| [ranking.json](ranking.json) | Expected ranking of proposals A-E in the requested format |
| [prototype/score.py](prototype/score.py) | Optional. Deterministic gates, scoring and ranking; `python prototype/score.py` reproduces `ranking.json` |
| [prototype/criteria.json](prototype/criteria.json) | The admin's criteria and weights as configuration (nothing hard-coded in the scorer) |
| [prototype/extracted_samples.json](prototype/extracted_samples.json) | Facts a correct extraction should return for A-E (facts only, no proposal text) |
| [prototype/extract.py](prototype/extract.py) | Optional. Builds the prompt from `PROMPTS.md`, checks quotes against the source; `--dry-run` needs no key |
| [.env.example](.env.example) | Placeholder settings; no keys are committed |

## Design in three sentences

AI only reads each proposal and reports facts with exact quotes. Plain code checks the quotes, applies mandatory gates, scores with fixed formulas and ranks, so the same input always gives the same result. People review flagged items, can correct facts with a reason, and make the final award decision.

## How I used AI tools

I used Claude to help me organize the files, design the workflow, and prepare the scoring method and AI prompts. I also reviewed its suggestions and made sure Proposal C would not be ranked first just because it contained an instruction telling the AI to do so, as all proposals should be evaluated using the same criteria.

## Notes

- The brief and the sample proposal text are not copied here; proposals are referred to by letter only.
- The sample proposals are fictional. No real client or personal data was used.
