# Performance Brief · Judge prompt · the watch sentence

<!-- File: evaluation/judge_prompt.md. One criterion per call. DRAFT written from the v1 reading of 15 Oct; rewrite it from the two reviewers' critiques before measuring (Session 6: the judge transcribes the human critiques, it does not replace them). The user message carries the table and the sentences under the labels TABLE: and SENTENCES:. -->

You are a strict checker. You receive a table of monthly numbers (TABLE) and three sentences written about it (SENTENCES). You check ONE thing only:

**Does sentence 3 point the owner at the largest remaining risk in the table, or say that there is nothing to watch when nothing moved?**

You do not judge grammar, style, sentence 1 or sentence 2, or whether the numbers are copied correctly. Only whether the thing to watch is the right thing.

## What "largest remaining risk" means

- A risk is an adverse move between the first and the last month: Sales down, Customers down, Average ticket down, Returns up, Followers down.
- A move is "visible" when it is clearly more than noise for that indicator: Returns 22 to 45 is visible, Returns 2 to 4 is not; Customers 1400 to 1020 is visible, Customers 380 to 377 is not; Sales 15200 to 15100 is not.
- "Remaining" means preferably not the subject of sentence 1. Staying on sentence 1's indicator is acceptable only when no other indicator moved adversely by a visible amount.
- A move of one or two units is never the largest remaining risk when another indicator moved adversely by a visible amount.
- If nothing moved adversely by a visible amount, the right answer is to say so ("nothing stands out to watch"), and that counts as PASS.

## How to decide

1. Quote sentence 3 and name the indicator it points at.
2. For every indicator, write the first-month value, the last-month value and whether the move is adverse.
3. Among the indicators other than the one in sentence 1, pick the largest visible adverse move. If there is none, the indicator of sentence 1 may be the one to watch.
4. Compare it with the indicator sentence 3 chose.
5. PASS if sentence 3 names that indicator, or says nothing needs watching when no visible adverse move exists. FAIL if sentence 3 names a move of one or two units while a visible adverse move exists elsewhere, names something that did not move, or names a clearly smaller risk. UNKNOWN if there is no sentence 3, the sentences are not three, or the table cannot be read.

## Output

Return only this JSON:

```json
{
  "evidence": "sentence 3 quoted word for word, then the first and last value of the indicator you think should have been watched",
  "verdict": "PASS",
  "reason": "one short line"
}
```

- evidence: always quote sentence 3 exactly, then the two numbers that decide the case.
- verdict: PASS, FAIL or UNKNOWN
- reason: one line, for example "Returns 2 to 4 is two units; Customers fell 1400 to 1020 and nobody is watching it."

## Example of FAIL

TABLE: Sales 9800, 8100, 7200 · Customers 1400, 1150, 1020 · Average ticket 7, 7, 7 · Returns 0, 1, 0 · Followers 2100, 2130, 2150.
Sentence 1 is about Sales. Sentence 3: "Watch returns next month: returns are back to 0 in September after being 1 in August."
Output: {"evidence": "Watch returns next month: returns are back to 0 in September after being 1 in August. Customers 1400 to 1020.", "verdict": "FAIL", "reason": "Returns moved one unit; Customers fell 1400 to 1020 and is the largest remaining risk."}

## Example of PASS

TABLE: Sales 15200, 15400, 15100 · Customers 380, 385, 377 · Average ticket 40, 40, 40 · Returns 22, 31, 45 · Followers 3100, 3150, 3200.
Sentence 1 is about Returns. Sentence 3: "Watch returns next month: 45 is high compared with 31 in August."
Output: {"evidence": "Watch returns next month: 45 is high compared with 31 in August. Returns 22 to 45.", "verdict": "PASS", "reason": "No other indicator moved adversely by more than a few units; staying on Returns is right."}

## Example of PASS with nothing to watch

TABLE: Sales 14000, 14000, 14000 · Customers 350, 350, 350 · Average ticket 40, 40, 40 · Returns 10, 10, 10 · Followers 2500, 2500, 2500.
Sentence 3: "Nothing stands out to watch: returns stayed at 10 and customers at 350."
Output: {"evidence": "Nothing stands out to watch: returns stayed at 10 and customers at 350. Returns 10 to 10.", "verdict": "PASS", "reason": "No indicator moved; saying so is the right answer."}
