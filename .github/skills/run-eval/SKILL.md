---
name: run-eval
description: Use when asked to evaluate, score, test or check how Performance Brief is doing on the golden set. Runs evaluation/run_eval.py and summarises pass rates per check and judge agreement.
---

# Run the evaluation

1. Run `python evaluation/run_eval.py` from the repository root.
2. Report the pass rate for each check in a short table: valid JSON, three sentences, numbers in table, no percentages, sentence length, unknown handling.
3. If the judge has been run, report TPR and TNR against evaluation/labels.csv.
4. List the ids of the cases that failed any check, with the check they failed.
5. Do not change the prompt, the golden set or the checks. Only report.
