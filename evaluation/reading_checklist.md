# Reading checklist · Performance Brief · prompt v1

One question per instruction in `prompts/reading_v1.md`, in the order the prompt gives them, worded as the prompt words them. Nothing stricter, nothing extra. For each output, answer yes or no; a "no" gets one line in the notes column.

| # | From the prompt | Question (yes / no) |
| --- | --- | --- |
| 1 | Output format | Did it return only the JSON, with status, sentences, numbers_used and note, and nothing before or after it? |
| 2 | Sentence 1 | Does sentence 1 give the biggest change in the table, with the earlier value, the later value and the months they belong to? |
| 3 | Sentence 2 | Does sentence 2 make one connection between two indicators that explains or qualifies sentence 1, quoting the numbers it uses? |
| 4 | Sentence 3 | Does sentence 3 give one thing the owner should watch next month, with the number that justifies it? |
| 5 | Rule 1 | Exactly three sentences, no title, no bullet points, no greeting? |
| 6 | Rule 2 | Does every number in the sentences appear in the table exactly as written there, not rounded or reformatted? |
| 7 | Rule 3 | No percentage, difference, ratio, total or average computed by the model? (words like "rose", "fell", "more than doubled", "stayed flat" are allowed) |
| 8 | Rule 4 | Each sentence 30 words or fewer? |
| 9 | Rule 5 | Plain language, no jargon such as "KPI", "metric", "quarter-over-quarter", "trend line"? |
| 10 | Rule 6 | No invented cause? It may say what moved together; it may not say why ("because of the promotion", "due to the weather"). |
| 11 | Rule 7 | If followers rose and sales did not, does it say the growth has not yet shown up in sales? (skip if not applicable) |
| 12 | Rule 8 | If the table has one month only, a missing value, or is not a table of this shape: status "unknown", empty sentences, and a note saying what is missing? (skip if not applicable) |
| 13 | Rule 9 | If nothing changed across the months: status "ok" and three sentences saying sales, customers and returns stayed at the same numbers, naming them? (skip if not applicable) |
| 14 | numbers_used | Does numbers_used list the numbers that appear in the sentences, as integers, in order? |

## Then, in your own words

After the 14 questions, write one line for the output as a whole: "fine", or what is wrong. Group the lines afterwards into named families and count them. The families from the v1 run are a starting point, not a list to fit into:

- F1 invalid response (question 1 or 5 failed)
- F2 trivial watch (question 4: true but points at a move of one or two units)
- F3 wrong months or wrong indicator (question 2 or 3: compares adjacent months and misses the period story, or builds on an indicator that is not the biggest change)
- F4 wording (question 8 or 9, or awkward phrasing)
- F5 beyond the table (question 7 or 10)
- F6 wrong refusal (question 12 or 13)

A case can be in more than one family. Counts in the report are per family.

## What the script already answers

`run_eval.py` answers questions 1, 5 (count only), 6, 7 (the % sign only), 8, 12 and 14 automatically. Read them anyway when the script flags a case; for the rest, the script says nothing and your reading is the only evidence.
