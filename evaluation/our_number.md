# The number we defend

**Metric:** share of briefs in which every quoted number exists in the pasted table, exactly as written there (checklist question 6, script check `numbers_in_table`).

**Result, prompt v2 (kept), 20 golden cases, run of 18 October 2026:** 20/20 (100%). Same on v1 (16 October): 20/20. Measured in code, the same way every time.

**Why this one.** It is the promise in the problem statement: "every figure traceable to the table". It is objective, a number is in the table or it is not, and it is the first thing a shop owner would lose trust over: one invented figure and the brief is worthless. Everything else we measure sits on top of it.

**What it does not cover.** Whether the brief is useful. A brief can quote only real numbers and still tell the owner to watch the wrong thing. We measure that separately, by hand and with a judge:

- By hand (two readers, 14 checklist questions plus one criterion, "does sentence 3 point at the largest remaining risk?"): v1 10 PASS of 18 briefs, v2 14 PASS of 18.
- LLM judge, one criterion, evidence quoted before the verdict, temperature 0, calibrated against our own labels on cases not used to write it: v1 held-out TPR 0.67, TNR 1.00 (10 cases, one calibration round); v2 TPR 0.64, TNR 1.00 (18 cases, never seen by the judge). The judge never passes a brief we failed. It fails about a third of the briefs we pass, always the same pattern: sentence 3 watching good news when nothing moved the wrong way. We report the judge as a conservative second opinion, not as the number.

It also does not cover direction claims ("rose", "fell"): one wrong direction in v1 (G07) and one in v2 (G01), found by reading, caught by no check. And it says nothing about tables outside the golden set: thousands separators, other months, two-month tables were not tested.

**What would move it.** Any number invented, rounded or reformatted by the model. We saw none in 40 briefs. A table with "12.400" or "12,400" is where it would break first, because the check compares strings.

**One honest sentence for the slide:** "100% of quoted numbers are real; by our own reading, 14 of 18 briefs also point the owner at the right thing, and our judge agrees with us on the failures but is stricter than us on the passes."
