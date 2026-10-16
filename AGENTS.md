# Performance Brief

Small business owners paste their monthly numbers and get a three-sentence brief on what changed and what to watch, with every figure traceable to the table.

## Stack

Python, single screen. Web interface with Streamlit, run with streamlit run src/app.py. Never use tkinter or any desktop GUI; the app runs in Codespaces.
- Evaluation: `python evaluation/run_eval.py`.

## Where things go

- All model calls go through `ask()` in `src/llm.py`. Never create another API client.
- The system prompt lives in `prompts/` and is loaded from file at runtime. Never paste prompt text inside code.
- Test cases live in `evaluation/golden.csv`. Evaluation code lives in `evaluation/`.
- Every run is logged to `data/traces.jsonl` with input, output, prompt version and latency.

## Always

- Never open, read, print or edit `.env`. The API key is read by `src/llm.py` only.
- Synthetic data only. No real shops, customers or figures.
- One screen, no login, no database, no settings page.
- Run `python evaluation/run_eval.py` before calling any change done, and report the pass rates.
- Ask before adding a dependency.
