# Failure taxonomy · prompt v1 · 20 golden cases

Run of 15 October 2026, prompt `prompts/reading_v1.md`, outputs in `evaluation/outputs.csv`, read against `evaluation/reading_checklist.md` (14 questions, one per instruction in the prompt).
16 cases returned a brief, 2 returned `unknown` as expected (G17, G18), 2 returned an error (G16, G20).

We separate two things the first version of this file mixed up: **failures**, where the output breaks something the prompt asks for, and **gaps**, where the output is weak but the prompt never said otherwise. Failures are the model's; gaps are the prompt's, and they are what v2 fixes.

## What worked

- Every number quoted exists in the table: 20/20 (checklist question 6). No percentages, no computed figures: 20/20 (question 7).
- Every direction claimed (rose, fell, flat) matches the table in all 16 readable briefs (judge criterion).
- The two incomplete tables (G17, G18) were refused with `unknown` (question 12); the flat table (G19) got three honest sentences (question 13).
- Latency about 3 seconds per call; the first call took 61 seconds (cold start, warm up before the demo).

## Failures: the prompt asked, the model did not do it

| # | Failure type | Cases | Count | Checklist question | What it looks like |
| --- | --- | --- | --- | --- | --- |
| F1 | Invalid response | G16, G20 | 2/20 | 1, 5 | No parseable JSON came back. Raw text not logged, so the cause is unknown. G20 is a hard case (customers down, ticket up), so this is the costliest failure. |
| F3 | Headline is not the biggest change | G10 | 1/20 | 2 | Sentence 1 calls August to September (12800 to 12100) "the biggest change" when the same indicator moved more over July to September (13300 to 12100). |
| F4 | Sentence over 30 words | G05 | 1/20 | 8 | Sentence 2 runs long. |
| F5 | States a cause or gives advice | G12 | 1/20 | 10 | "keeping them low helps sales keep improving" says why, which rule 6 forbids. |
| F6 | Refusal note inaccurate | G17 | 1/20 | 12 (borderline) | The note does say what is missing, as rule 8 asks, but adds that "three complete months are needed", which contradicts rule 8 (one month is the only case refused). |

Six cases with at least one failure; fourteen pass every question in the checklist.

## Gaps: the output is weak, but the prompt never forbade it

These go to prompt v2, not to the model's account. They were found by reading, which is the point of the exercise.

| # | Gap | Cases | Count | What v1 said | What v2 should say |
| --- | --- | --- | --- | --- | --- |
| G-a | "Watch" sentence points at a trivial move | G02, G03, G06, G07, G09, G11 | 6/16 | "one thing the owner should watch next month, with the number" | The thing to watch is the largest remaining risk over the period; a move of one or two units is never it; if nothing moved much, say so. |
| G-b | Sentence 2 links adjacent months and misses the period story | G01 | 1/16 | "one connection between two indicators that explains or qualifies sentence 1" | Compare first and last month unless one month is clearly the outlier. |
| G-c | "Biggest change" is undefined | G02, G06, G09, G15 and others | implicit | "the biggest change in the table" | Say how to measure it: sales first, then customers; returns and followers only if they moved by more than half. Without this, returns going 0 to 2 is, literally, the biggest change. |
| G-d | Awkward phrasing | G09, G15 | 2/16 | nothing | "Write each sentence as one clean clause; no em dashes; at most two numbers per sentence unless the third is a month." |
| G-e | Two-month tables | not in the 20 | - | "three monthly columns" in the table description, but rule 8 only refuses one month | "two or three monthly columns". Tested by G21 in the robustness set. |

## A check that was wrong, not the model

`run_eval.py` reported `numbers_in_sentences` failing on G01, G02, G06, G10, G11, G12 and G14. Read by hand, every number in `numbers_used` appears in the sentences. The number pattern in the script refused a digit followed by a full stop, so "rose from 46 to 52." was never matched. The model was right; the test was wrong. Fixed by changing the lookahead so a dot only blocks a match when followed by another digit. These seven are not failures.

## Which grader for which failure

Session 6: code for everything with a right answer, a judge only for what code cannot check and only for failures we will re-run, human reading for the rest.

| Family | Grader | Why |
| --- | --- | --- |
| F1 invalid response | code (`valid_json`, `exactly_3_sentences`) | A right answer exists: it parses or it does not. |
| Numbers traceable to the table | code (`numbers_in_table`, `numbers_in_sentences`, `no_percent_sign`) | Substring and pattern checks; no judgement needed. |
| F4 sentence over 30 words | code (`sentences_at_most_30_words`) | Word count. |
| Incomplete tables refused | code (`hard_cases_unknown`, status only) | Status is checkable; the wording of the note (F6) is not. |
| G-a watch sentence points at a trivial move | **LLM judge** (`judge_prompt.md`, criterion of record) | Needs judgement of scale (22 to 45 matters, 2 to 4 does not); it is the family with most cases (6/16) and the one v2 changes, so the same judge measures v1 against v2. |
| Directions correct (rose / fell / flat) | human reading; `judge_prompt_direction.md` as optional second call | 16/16 by hand on v1; no observed failure to calibrate a judge on. |
| F3 headline not the biggest change, G-b, G-c | human reading now; code once v2 fixes the definition | "Biggest change" had no definition in v1, so no grader could check it. With the v2 rule (sales first, then customers) it becomes computable: next step. |
| F5 cause or advice, F6 note wording, G-d phrasing | human reading (checklist questions 10, 12, and the free line) | One or two cases each; a judge is not worth building for a failure we are not re-running. |

## What we take from this

- The number we defend is **20/20 numbers traceable to the table** (100%, checklist question 6). It does not tell us whether the brief is useful: the gaps show that in 7 of 16 readable briefs it partly is not, and the prompt did not ask for better.
- Measured strictly against what the prompt asks, the model failed in 6 of 20 cases, 2 of them format, 4 of them one rule each.
- Prompt v2 is the gaps table turned into rules (G-a to G-e). We measure it with the same 14 questions plus one new question per new rule, and compare failure counts and gap counts with v1.
- Before the next run: log the raw model text on invalid JSON and retry once, so F1 can be diagnosed.
