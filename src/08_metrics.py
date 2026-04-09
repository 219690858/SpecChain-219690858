"""Compute metrics for manual/auto/hybrid + summary."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


AMBIGUOUS_TERMS = [
    "fast",
    "easy",
    "better",
    "user-friendly",
    "reasonable",
    "smooth",
    "intuitive",
    "simple",
    "quick",
    "convenient",
    "seamless",
    "reliable",
    "stable",
    "good",
    "great",
    "nice",
    "minor",
    "typical",
    "major",
    "long waiting",
    "hard",
    "difficult",
    "slow",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _parse_requirements(md_path: Path) -> list[dict[str, str]]:
    if not md_path.exists():
        return []
    reqs: list[dict[str, str]] = []
    cur: dict[str, str] | None = None
    for line in md_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Requirement ID:"):
            if cur:
                reqs.append(cur)
            cur = {"id": line.split(":", 1)[1].strip(), "persona": "", "description": "", "ac": ""}
        elif cur and line.strip().startswith("- Source Persona:"):
            cur["persona"] = line.split(":", 1)[1].strip().strip("[]")
        elif cur and line.strip().startswith("- Description:"):
            cur["description"] = line.split(":", 1)[1].strip().strip("[]")
        elif cur and line.strip().startswith("- Acceptance Criteria:"):
            cur["ac"] = line.split(":", 1)[1].strip().strip("[]")
    if cur:
        reqs.append(cur)
    return reqs


def _ambiguity_ratio(reqs: list[dict[str, str]]) -> float:
    if not reqs:
        return 0.0
    terms = [t.lower() for t in AMBIGUOUS_TERMS]
    flagged = 0
    for r in reqs:
        text = (r.get("description", "") + " " + r.get("ac", "")).lower()
        if any(t in text for t in terms):
            flagged += 1
    return round(flagged / len(reqs), 4)


def _compute_pipeline_metrics(
    pipeline: str,
    dataset_size: int,
    groups_path: Path,
    personas_path: Path,
    spec_path: Path,
    tests_path: Path,
) -> dict[str, Any]:
    groups_obj = _read_json(groups_path) if groups_path.exists() else {"groups": []}
    groups = groups_obj.get("groups", [])
    covered_reviews = set()
    links_review_group = 0
    for g in groups:
        rids = g.get("review_ids", []) if isinstance(g, dict) else []
        if isinstance(rids, list):
            links_review_group += len(rids)
            covered_reviews.update(rids)

    personas_obj = _read_json(personas_path) if personas_path.exists() else {"personas": []}
    personas = personas_obj.get("personas", [])
    persona_count = len(personas) if isinstance(personas, list) else 0
    persona_names = {p.get("name") for p in personas if isinstance(p, dict) and p.get("name")}
    links_group_persona = sum(1 for p in personas if isinstance(p, dict) and p.get("derived_from_group"))

    reqs = _parse_requirements(spec_path)
    requirements_count = len(reqs)
    links_persona_req = sum(1 for r in reqs if r.get("persona") in persona_names)
    traceability_ratio = round(links_persona_req / requirements_count, 4) if requirements_count else 0.0

    tests_obj = _read_json(tests_path) if tests_path.exists() else {"tests": []}
    tests = tests_obj.get("tests", [])
    tests_count = len(tests) if isinstance(tests, list) else 0
    by_req = Counter(t.get("requirement_id") for t in tests if isinstance(t, dict))
    testable = sum(1 for r in reqs if by_req.get(r.get("id"), 0) >= 1)
    testability_rate = round(testable / requirements_count, 4) if requirements_count else 0.0
    links_req_test = sum(1 for t in tests if isinstance(t, dict) and t.get("requirement_id"))

    review_coverage = round(len(covered_reviews) / dataset_size, 4) if dataset_size else 0.0
    ambiguity_ratio = _ambiguity_ratio(reqs)

    traceability_links = links_review_group + links_group_persona + links_persona_req + links_req_test

    return {
        "pipeline": pipeline,
        "dataset_size": dataset_size,
        "persona_count": persona_count,
        "requirements_count": requirements_count,
        "tests_count": tests_count,
        "traceability_links": traceability_links,
        "review_coverage": review_coverage,
        "traceability_ratio": traceability_ratio,
        "testability_rate": testability_rate,
        "ambiguity_ratio": ambiguity_ratio,
    }


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    repo = _repo_root()
    dataset_size = _read_jsonl_count(repo / "data" / "reviews_clean.jsonl")

    manual = _compute_pipeline_metrics(
        "manual",
        dataset_size,
        repo / "data" / "review_groups_manual.json",
        repo / "personas" / "personas_manual.json",
        repo / "spec" / "spec_manual.md",
        repo / "tests" / "tests_manual.json",
    )
    auto = _compute_pipeline_metrics(
        "automated",
        dataset_size,
        repo / "data" / "review_groups_auto.json",
        repo / "personas" / "personas_auto.json",
        repo / "spec" / "spec_auto.md",
        repo / "tests" / "tests_auto.json",
    )
    hybrid = _compute_pipeline_metrics(
        "hybrid",
        dataset_size,
        repo / "data" / "review_groups_hybrid.json",
        repo / "personas" / "personas_hybrid.json",
        repo / "spec" / "spec_hybrid.md",
        repo / "tests" / "tests_hybrid.json",
    )

    _write_json(repo / "metrics" / "metrics_manual.json", manual)
    _write_json(repo / "metrics" / "metrics_auto.json", auto)
    _write_json(repo / "metrics" / "metrics_hybrid.json", hybrid)

    summary = {
        "dataset_size": dataset_size,
        "pipelines": {
            "manual": manual,
            "automated": auto,
            "hybrid": hybrid,
        },
    }
    _write_json(repo / "metrics" / "metrics_summary.json", summary)

    print("Wrote metrics for manual/automated/hybrid + summary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())