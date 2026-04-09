"""Create a CSV sample for manual grouping (Task 3.1)."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main() -> int:
    repo = _repo_root()
    clean_path = repo / "data" / "reviews_clean.jsonl"
    out_path = repo / "reflection" / "manual_coding_sample.csv"

    rows = _read_jsonl(clean_path)
    if not rows:
        raise RuntimeError("Clean dataset is empty. Run src/02_clean.py first.")

    # Sample size: enough to comfortably build 5 groups with >=10 reviews each.
    # You can increase if needed.
    sample_n = min(200, len(rows))
    rnd = random.Random(4312)
    sample = rnd.sample(rows, k=sample_n)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "score",
                "at",
                "content_raw",
                "content_clean",
                "manual_group",  # fill with G1..G5
                "notes",
            ],
        )
        w.writeheader()
        for r in sample:
            w.writerow(
                {
                    "id": r.get("id", ""),
                    "score": r.get("score", ""),
                    "at": r.get("at", ""),
                    "content_raw": r.get("content_raw", ""),
                    "content_clean": r.get("content_clean", ""),
                    "manual_group": "",
                    "notes": "",
                }
            )

    print(f"Wrote manual coding worksheet: {out_path.as_posix()} ({len(sample)} rows)")
    print("Next: open the CSV, assign each row to G1..G5, then update data/review_groups_manual.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())