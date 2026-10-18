"""Run the golden-set evaluation for the Performance Brief reader."""

from __future__ import annotations

import csv
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAIError

try:
    from src.app import PROMPT_VERSION, get_brief
    from src.llm import ask
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from src.app import PROMPT_VERSION, get_brief
    from src.llm import ask


EVALUATION_ROOT = Path(__file__).resolve().parent
GOLDEN_PATH = EVALUATION_ROOT / "golden.csv"
LEGACY_GOLDEN_PATH = EVALUATION_ROOT / "goldenset.csv"
OUTPUT_PATH = EVALUATION_ROOT / "outputs.csv"
VERSIONED_OUTPUT_PATH = EVALUATION_ROOT / f"outputs_{PROMPT_VERSION}.csv"
JUDGE_PROMPT_PATH = EVALUATION_ROOT / "judge_prompt.md"
NUMBER_PATTERN = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w]|\.\d)")
CHECKS = (
    "valid_json",
    "exactly_3_sentences",
    "numbers_in_table",
    "numbers_in_sentences",
    "no_percent_sign",
    "sentences_at_most_30_words",
    "hard_cases_unknown",
)


@dataclass(frozen=True)
class Case:
    case_id: str
    case_type: str
    table: str


def _clean_legacy_field(value: str) -> str:
    return value.strip().strip('"').strip(";").strip('"').strip()


def _load_legacy_cases(path: Path) -> list[Case]:
    """Read the line-broken semicolon fixture used by older project snapshots."""
    lines = path.read_text(encoding="utf-8").splitlines()
    cases: list[Case] = []
    for start in range(1, len(lines), 6):
        block = lines[start : start + 6]
        if len(block) != 6:
            raise ValueError(f"Incomplete golden case near line {start + 1} in {path}")

        header = block[0].removesuffix(";;")
        match = re.match(r'^"?([^,]+),([^,]+),([^,]+),"', header)
        if not match:
            raise ValueError(f"Could not parse golden case near line {start + 1} in {path}")

        table_header = header.split(",", 3)[3].lstrip('"').rstrip('"')
        table_lines = [table_header]
        for line in block[1:]:
            cleaned = line.removesuffix(";;")
            if cleaned.startswith('"Followers'):
                cleaned = cleaned[1:].split('""', 1)[0]
            table_lines.append(_clean_legacy_field(cleaned))
        table = "\n".join(table_lines)
        cases.append(Case(match.group(1), match.group(3), table))
    return cases


def load_cases() -> list[Case]:
    path = GOLDEN_PATH if GOLDEN_PATH.exists() else LEGACY_GOLDEN_PATH
    if not path.exists():
        raise FileNotFoundError(f"Golden set not found: {GOLDEN_PATH}")

    if path.name == LEGACY_GOLDEN_PATH.name:
        return _load_legacy_cases(path)

    with path.open(newline="", encoding="utf-8") as golden_file:
        rows = csv.DictReader(golden_file)
        required = {"id", "case_type", "table"}
        if not required.issubset(rows.fieldnames or set()):
            missing = ", ".join(sorted(required - set(rows.fieldnames or set())))
            raise ValueError(f"{path} is missing required columns: {missing}")
        return [
            Case(row["id"].strip(), row["case_type"].strip(), row["table"])
            for row in rows
        ]


def _table_numbers(table: str) -> set[str]:
    return set(NUMBER_PATTERN.findall(table))


def _sentence_numbers(sentences: list[str]) -> list[str]:
    return NUMBER_PATTERN.findall(" ".join(sentences))


def _word_count(sentence: str) -> int:
    return len(sentence.split())


def _empty_result(note: str) -> dict[str, Any]:
    return {
        "status": "error",
        "sentences": [],
        "numbers_used": [],
        "note": note,
    }


def load_judge_prompt() -> str:
    try:
        return JUDGE_PROMPT_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Could not load the judge prompt: {JUDGE_PROMPT_PATH}") from exc


def judge_output(table: str, sentences: list[str]) -> dict[str, str]:
    """Ask the judge to assess direction claims in an otherwise valid output."""
    user_message = (
        f"TABLE:\n{table}\n\nSENTENCES:\n"
        + "\n".join(f"{index}. {sentence}" for index, sentence in enumerate(sentences, 1))
    )
    try:
        raw_verdict = ask(user_message, system=load_judge_prompt())
        cleaned_verdict = re.sub(r"```(?:json)?", "", raw_verdict, flags=re.IGNORECASE).strip()
        start = cleaned_verdict.find("{")
        end = cleaned_verdict.rfind("}")
        verdict = json.loads(cleaned_verdict[start : end + 1])
    except (OpenAIError, RuntimeError, json.JSONDecodeError, TypeError) as exc:
        return {
            "evidence": "",
            "verdict": "UNKNOWN",
            "reason": f"Judge error: {exc}",
        }

    if not isinstance(verdict, dict):
        return {
            "evidence": "",
            "verdict": "UNKNOWN",
            "reason": "Judge returned a non-object JSON value.",
        }

    evidence = verdict.get("evidence")
    reason = verdict.get("reason")
    judge_verdict = verdict.get("verdict")
    if not all(isinstance(value, str) for value in (evidence, reason, judge_verdict)):
        return {
            "evidence": "",
            "verdict": "UNKNOWN",
            "reason": "Judge JSON is missing string evidence, verdict, or reason.",
        }
    if judge_verdict not in {"PASS", "FAIL", "UNKNOWN"}:
        return {
            "evidence": evidence,
            "verdict": "UNKNOWN",
            "reason": f"Judge returned invalid verdict: {judge_verdict}",
        }
    return {"evidence": evidence, "verdict": judge_verdict, "reason": reason}


def evaluate_case(case: Case) -> tuple[dict[str, Any], dict[str, bool], float]:
    started_at = time.perf_counter()
    try:
        result = get_brief(case.table)
        valid_json = True
    except (RuntimeError, OpenAIError) as exc:
        result = _empty_result(str(exc))
        valid_json = False
    latency_seconds = time.perf_counter() - started_at

    sentences = result.get("sentences")
    numbers_used = result.get("numbers_used")
    sentences_are_strings = isinstance(sentences, list) and all(
        isinstance(sentence, str) for sentence in sentences
    )
    numbers_are_valid = isinstance(numbers_used, list) and all(
        isinstance(number, (int, float)) and not isinstance(number, bool)
        for number in numbers_used
    )
    sentence_list = sentences if sentences_are_strings else []
    number_list = [str(number) for number in numbers_used] if numbers_are_valid else []
    table_numbers = _table_numbers(case.table)
    sentence_text = " ".join(sentence_list)
    expected_unknown = case.case_type.startswith(
        ("hard: single month", "hard: missing indicator")
    )

    def contains_number(number: str, text: str) -> bool:
        return bool(re.search(rf"(?<![\w.]){re.escape(number)}(?![\w.])", text))

    checks = {
        "valid_json": valid_json,
        "exactly_3_sentences": (
            expected_unknown or (sentences_are_strings and len(sentence_list) == 3)
        ),
        "numbers_in_table": numbers_are_valid
        and all(number in table_numbers for number in number_list),
        "numbers_in_sentences": numbers_are_valid
        and all(contains_number(number, sentence_text) for number in number_list),
        "no_percent_sign": "%" not in sentence_text,
        "sentences_at_most_30_words": all(
            _word_count(sentence) <= 30 for sentence in sentence_list
        ),
        "hard_cases_unknown": not expected_unknown
        or result.get("status") == "unknown",
    }
    return result, checks, latency_seconds


def write_outputs(rows: list[dict[str, Any]]) -> None:
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=[
                "id",
                "prompt_version",
                "status",
                "sentences",
                "numbers_used",
                "note",
                "latency_seconds",
                "evidence",
                "verdict",
                "reason",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    with VERSIONED_OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=[
                "id",
                "prompt_version",
                "status",
                "sentences",
                "numbers_used",
                "note",
                "latency_seconds",
                "evidence",
                "verdict",
                "reason",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def print_summary(results: list[tuple[str, dict[str, bool]]]) -> None:
    print("| Check | Pass rate | Failed ids |")
    print("|---|---:|---|")
    total = len(results)
    for check in CHECKS:
        failed = [case_id for case_id, checks in results if not checks[check]]
        passed = total - len(failed)
        rate = passed / total * 100 if total else 0
        print(f"| {check} | {passed}/{total} ({rate:.1f}%) | {', '.join(failed) or '-'} |")


def print_judge_comparison(output_rows: list[dict[str, Any]]) -> None:
    labels_path = EVALUATION_ROOT / "labels.csv"
    with labels_path.open(newline="", encoding="utf-8") as labels_file:
        labels = {
            (row["id"].strip(), row["prompt_version"].strip()): row
            for row in csv.DictReader(labels_file)
            if row["human_verdict"].strip().lower() != "n/a"
        }

    comparisons = [
        (row, labels.get((row["id"], row["prompt_version"])))
        for row in output_rows
    ]
    comparisons = [
        (row, label)
        for row, label in comparisons
        if label is not None
    ]

    def print_metrics(title: str, rows: list[tuple[dict[str, Any], dict[str, str]]]) -> None:
        counts = {"TP": 0, "FN": 0, "TN": 0, "FP": 0}
        for output, label in rows:
            judge_passed = output["verdict"] == "PASS"
            human_passed = label["human_verdict"].strip() == "PASS"
            if judge_passed and human_passed:
                counts["TP"] += 1
            elif not judge_passed and human_passed:
                counts["FN"] += 1
            elif not judge_passed and not human_passed:
                counts["TN"] += 1
            else:
                counts["FP"] += 1
        tpr = counts["TP"] / (counts["TP"] + counts["FN"]) if counts["TP"] + counts["FN"] else 0
        tnr = counts["TN"] / (counts["TN"] + counts["FP"]) if counts["TN"] + counts["FP"] else 0
        print(
            f"\n{title}: TP {counts['TP']}, FN {counts['FN']}, TN {counts['TN']}, "
            f"FP {counts['FP']}, TPR {tpr:.3f}, TNR {tnr:.3f}"
        )

    print_metrics("Judge vs human (all labelled)", comparisons)
    held_out = [
        (output, label)
        for output, label in comparisons
        if not label["used_for_prompt"].strip()
    ]
    print_metrics("Judge vs human (held-out)", held_out)

    disagreements = [
        output["id"]
        for output, label in comparisons
        if (output["verdict"] == "PASS") != (label["human_verdict"].strip() == "PASS")
    ]
    print(f"Judge/human disagreements: {', '.join(disagreements) or '-'}")


def main() -> None:
    cases = load_cases()
    summary: list[tuple[str, dict[str, bool]]] = []
    output_rows: list[dict[str, Any]] = []
    verdict_counts = {"PASS": 0, "FAIL": 0, "UNKNOWN": 0}

    for case in cases:
        result, checks, latency_seconds = evaluate_case(case)
        summary.append((case.case_id, checks))
        sentences = result.get("sentences", [])
        if result.get("status") == "ok" and isinstance(sentences, list) and all(
            isinstance(sentence, str) for sentence in sentences
        ):
            judge = judge_output(case.table, sentences)
        else:
            judge = {"evidence": "", "verdict": "UNKNOWN", "reason": ""}
        verdict_counts[judge["verdict"]] += 1
        output_rows.append(
            {
                "id": case.case_id,
                "prompt_version": PROMPT_VERSION,
                "status": result.get("status", ""),
                "sentences": json.dumps(result.get("sentences", []), ensure_ascii=False),
                "numbers_used": json.dumps(result.get("numbers_used", []), ensure_ascii=False),
                "note": result.get("note", ""),
                "latency_seconds": f"{latency_seconds:.6f}",
                "evidence": judge["evidence"],
                "verdict": judge["verdict"],
                "reason": judge["reason"],
            }
        )

    write_outputs(output_rows)
    print_summary(summary)
    print(
        "\nJudge verdicts: "
        + ", ".join(f"{verdict} {verdict_counts[verdict]}" for verdict in verdict_counts)
    )
    print_judge_comparison(output_rows)
    print(
        f"\nSaved {len(output_rows)} outputs to {OUTPUT_PATH} "
        f"and {VERSIONED_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
