"""Streamlit interface for turning a pasted table into a performance brief."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import streamlit as st
from openai import OpenAIError

try:
    from .llm import ask
except ImportError:
    from llm import ask


APP_ROOT = Path(__file__).resolve().parent.parent
TRACE_PATH = APP_ROOT / "data" / "traces.jsonl"
PROMPT_VERSION = os.environ.get("PROMPT_VERSION", "v1")
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", PROMPT_VERSION):
    raise RuntimeError("PROMPT_VERSION must contain only letters, numbers, '.', '_' or '-'.")
PROMPT_PATH = APP_ROOT / "prompts" / f"reading_{PROMPT_VERSION}.md"
DEFAULT_TABLE = """Indicator | July | August | September
Sales (EUR) | 12400 | 11100 | 13800
Customers | 310 | 240 | 265
Average ticket (EUR) | 40 | 46 | 52
Returns | 9 | 14 | 7
Followers | 1850 | 1920 | 2310"""


def load_system_prompt() -> str:
    """Load the versioned reader prompt used for every model request."""
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Could not load the reader prompt: {PROMPT_PATH}") from exc


def log_run(table: str, output: str, latency_seconds: float) -> None:
    """Append one JSON record for each model run."""
    record = {
        "input": table,
        "output": output,
        "prompt_version": PROMPT_VERSION,
        "latency_seconds": latency_seconds,
    }
    try:
        TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with TRACE_PATH.open("a", encoding="utf-8") as trace_file:
            trace_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        raise RuntimeError(f"Could not write run trace: {TRACE_PATH}") from exc


def get_brief(table: str) -> dict[str, object]:
    """Ask the model for a brief and validate the JSON envelope we display."""
    system_prompt = load_system_prompt()
    for attempt in range(2):
        started_at = time.perf_counter()
        raw_response = ""
        try:
            raw_response = ask(table, system=system_prompt)
            try:
                result = json.loads(raw_response)
            except (json.JSONDecodeError, TypeError) as exc:
                if attempt == 0:
                    continue
                preview = str(raw_response)[:200]
                raise RuntimeError(
                    f"The model returned an invalid response: {preview}"
                ) from exc

            if not isinstance(result, dict):
                raise RuntimeError("The model returned an unexpected response. Please try again.")

            status = result.get("status")
            if status not in {"ok", "unknown"}:
                raise RuntimeError("The model returned an unexpected status. Please try again.")

            sentences = result.get("sentences")
            if status == "ok" and (
                not isinstance(sentences, list)
                or len(sentences) != 3
                or not all(isinstance(sentence, str) for sentence in sentences)
            ):
                raise RuntimeError("The model returned an incomplete brief. Please try again.")
            if status == "unknown" and sentences != []:
                raise RuntimeError("The model returned an unexpected response. Please try again.")
            return result
        finally:
            log_run(table, raw_response, time.perf_counter() - started_at)


def render_brief(result: dict[str, object]) -> None:
    """Render the validated model response below the Read button."""
    if result.get("status") == "unknown":
        note = result.get("note") or "The table could not be read."
        st.warning(str(note))
        return

    st.subheader("Your three-sentence brief")
    for sentence in result["sentences"]:
        st.write(sentence)


def main() -> None:
    st.set_page_config(page_title="Performance Brief", page_icon="📊")
    st.title("Performance Brief")
    st.caption("Paste your monthly table and get three clear sentences about what to watch.")

    table = st.text_area("Your table", value=DEFAULT_TABLE, height=220)
    if st.button("Read", type="primary"):
        table = table.strip()
        if not table:
            st.info("Paste your table before clicking Read.")
            return

        with st.spinner("Reading your table…"):
            try:
                result = get_brief(table)
            except (RuntimeError, OpenAIError) as exc:
                st.error(str(exc))
                return
        render_brief(result)


if __name__ == "__main__":
    main()
