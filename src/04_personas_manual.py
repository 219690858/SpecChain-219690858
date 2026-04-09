"""Optional helper for Task 3.2 (manual personas).

Manual personas must still be authored in personas/personas_manual.json. This script only
reads data/review_groups_manual.json and checks that the manual persona file exists and
matches basic traceability rules (group IDs, evidence reviews inside groups).

It does not call an LLM and does not overwrite your persona text.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    repo = _repo_root()
    groups_path = repo / "data" / "review_groups_manual.json"
    personas_path = repo / "personas" / "personas_manual.json"

    if not groups_path.exists():
        print(f"Missing {groups_path.relative_to(repo)} — create review groups first (Task 3.1).")
        return 1
    if not personas_path.exists():
        print(f"Missing {personas_path.relative_to(repo)} — write personas for Task 3.2.")
        return 1

    groups_obj = json.loads(groups_path.read_text(encoding="utf-8"))
    persons_obj = json.loads(personas_path.read_text(encoding="utf-8"))
    groups = groups_obj.get("groups", [])
    personas = persons_obj.get("personas", [])

    id_to_group: dict[str, set[str]] = {}
    group_ids: set[str] = set()
    for g in groups:
        gid = g.get("group_id")
        if not gid:
            continue
        group_ids.add(gid)
        rids = g.get("review_ids") or []
        id_to_group[gid] = set(rids) if isinstance(rids, list) else set()

    errors: list[str] = []
    warnings: list[str] = []

    if not personas:
        errors.append("personas list is empty")
    for p in personas:
        pid = p.get("id", "?")
        src = p.get("derived_from_group")
        if not src:
            errors.append(f"{pid}: missing derived_from_group")
            continue
        if src not in group_ids:
            errors.append(f"{pid}: derived_from_group {src} not in review_groups_manual")
            continue
        allowed = id_to_group.get(src, set())
        for rid in p.get("evidence_reviews") or []:
            if rid not in allowed:
                errors.append(f"{pid}: evidence review {rid} is not in group {src}")

    print(f"Review groups: {len(groups)}, personas: {len(personas)}")
    if errors:
        print("Validation FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    for w in warnings:
        print(f"Warning: {w}")
    print("Manual personas validation: OK (basic traceability).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
