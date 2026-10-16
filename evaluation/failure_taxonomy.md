# Failure taxonomy · prompt v1 · 20 golden cases

Run of 15 October 2026, prompt `prompts/reading_v1.md`, outputs in `evaluation/outputs.csv`.
We read every output against its table. 16 cases returned a brief, 2 returned `unknown` as expected (G17, G18), 2 returned an error (G16, G20).

## What worked

- Every number quoted exists in the table: 20/20. No percentages, no invented figures.
- Every direction claimed (rose, fell, flat) matches the table in all 16 briefs we could read.
- The two incomplete tables (G17, G18) were correctly refused with `unknown`.
- The flat table (G19) was handled as the prompt asks: three honest sentences saying nothing changed.
- Latency is about 3 seconds per call (the first call took 61 seconds, a cold start to keep in mind for the demo).

## Failure types

| # | Failure type | Cases | Count | What it looks like |
|---|---|---|---|---|
| F1 | Invalid response (not JSON) | G16, G20 | 2/20 | The app shows "The model returned an invalid response". We do not know what the model actually sent back because the raw text is not logged. G20 is one of our hard cases (customers down, ticket up), so this is the most costly failure. |
| F2 | "Watch" sentence picks a trivial indicator | G02, G03, G06, G07, G09, G11 | 6/20 | Sentence 3 tells the owner to watch returns moving from 0 to 1 or 2 to 4, while customers fell by a third (G03) or the real story is elsewhere. The sentence is true but useless. |
| F3 | Compares only adjacent months and misses the period story | G01, G10 | 2/20 | G01: sentence 2 says customers went 240 to 265, which is true, but the point is that 265 is still far below July's 310. G10: headline is August to September (12800 to 12100) when the whole-period fall (13300 to 12100) is the real change. |
| F4 | Wording slips | G05, G09, G15 | 3/20 | G05: sentence 2 is over 30 words. G15: "stayed flat at 15 to 15". G09: an em dash and three numbers crammed into sentence 1. |
| F5 | Adds advice or a hint of cause | G12 | 1/20 | "keeping them low helps sales keep improving" goes beyond what the table shows, which rule 6 forbids. |
| F6 | Inaccurate `unknown` note | G17 | 1/20 | The note says "at least three complete months are needed". The prompt says two. The verdict is right, the explanation is not. |

Several cases have more than one failure; counts are per failure type, not per case.

## A check we do not trust yet

`run_eval.py` reports `numbers_in_sentences` failing on G01, G02, G06, G10, G11, G12 and G14. Reading those seven by hand, every number in `numbers_used` does appear in the sentences. Either the check has a bug (likely in how it extracts numbers from the text) or it tests something other than what its name says. Until we have read the check's code and fixed or renamed it, we do not count these seven as model failures.

## What we take from this

- The number we defend is **20/20 numbers traceable to the table** (100%). It does not tell us whether the brief is useful; F2 and F3 show that in 8 of 16 readable briefs it partly is not.
- The one change worth trying in prompt v2 is aimed at F2 and F3: tell the model that sentence 3 must point at the indicator with the largest change over the whole period that sentence 1 did not already cover, and that sentence 1 compares the first and last month unless a single month is clearly the outlier.
- Before the next run, log the raw model text in `data/traces.jsonl` so F1 can be diagnosed, and add one automatic retry on invalid JSON.
