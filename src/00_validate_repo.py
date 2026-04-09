"""Validate required repo files/folders exist."""

from __future__ import annotations

from pathlib import Path


REQUIRED_PATHS = [
    "data/reviews_raw.jsonl",
    "data/reviews_clean.jsonl",
    "data/dataset_metadata.json",
    "data/review_groups_manual.json",
    "data/review_groups_auto.json",
    "data/review_groups_hybrid.json",
    "personas/personas_manual.json",
    "personas/personas_auto.json",
    "personas/personas_hybrid.json",
    "spec/spec_manual.md",
    "spec/spec_auto.md",
    "spec/spec_hybrid.md",
    "tests/tests_manual.json",
    "tests/tests_auto.json",
    "tests/tests_hybrid.json",
    "metrics/metrics_manual.json",
    "metrics/metrics_auto.json",
    "metrics/metrics_hybrid.json",
    "metrics/metrics_summary.json",
    "prompts/prompt_auto.json",
    "reflection/reflection.md",
    "src/01_collect_or_import.py",
    "src/02_clean.py",
    "src/05_personas_auto.py",
    "src/06_spec_generate.py",
    "src/07_tests_generate.py",
    "src/08_metrics.py",
    "src/run_all.py",
]


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]

    print("Checking repository structure...")
    missing: list[str] = []
    for rel in REQUIRED_PATHS:
        p = repo_root / rel
        if p.exists():
            print(f"{rel} found")
        else:
            print(f"{rel} MISSING")
            missing.append(rel)

    if missing:
        print("\nRepository validation complete: FAILED")
        print(f"Missing {len(missing)} required path(s).")
        return 1

    print("\nRepository validation complete: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())