#!/usr/bin/env python3
import csv
import json
from pathlib import Path
from typing import Any


HEADER = ["image文件名", "判定结果", "probability", "human"]


def load_inner_output(record: dict[str, Any]) -> dict[str, Any]:
    output = record.get("output")
    if not isinstance(output, str):
        return {}

    try:
        inner = json.loads(output)
    except json.JSONDecodeError:
        return {}

    return inner if isinstance(inner, dict) else {}


def row_from_record(record: dict[str, Any]) -> list[Any]:
    if "error" in record:
        return [record.get("image", ""), "", "", ""]

    inner = load_inner_output(record)
    return [
        record.get("image", ""),
        inner.get("classification", ""),
        inner.get("hateful_score", ""),
        "",
    ]


def iter_result_records(result_files: list[Path]):
    for result_file in result_files:
        with result_file.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    yield {"image": result_file.name, "error": f"Invalid JSON on line {line_number}"}
                    continue

                if isinstance(record, dict):
                    yield record
                else:
                    yield {"image": result_file.name, "error": f"JSON line {line_number} is not an object"}


def main() -> None:
    root = Path(__file__).resolve().parent
    results_dir = root / "results"
    output_path = results_dir / "results.csv"

    if not results_dir.is_dir():
        raise SystemExit(f"Results directory not found: {results_dir}")

    result_files = sorted(results_dir.glob("*-result.jsonl"))
    if not result_files:
        raise SystemExit(f"No *-result.jsonl files found in {results_dir}")

    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(HEADER)
        row_count = 0
        for record in iter_result_records(result_files):
            writer.writerow(row_from_record(record))
            row_count += 1

    print(f"Wrote {output_path} with {row_count} row(s).")


if __name__ == "__main__":
    main()
