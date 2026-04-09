"""Collect Google Play reviews and write raw dataset + metadata."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_APP_NAME = "Headspace"
DEFAULT_GOOGLE_PLAY_APP_ID = "com.getsomeheadspace.android"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _normalize_raw_review(r: dict[str, Any], idx: int) -> dict[str, Any]:
    """
    Normalize a google_play_scraper review dict into a stable JSONL row.
    """
    # Prefer a stable platform id if available.
    platform_id = r.get("reviewId") or r.get("review_id") or r.get("id")
    rid = platform_id if platform_id else f"raw_{idx}"
    return {
        "id": f"rev_{rid}",
        "platform": "google_play",
        "app_id": r.get("appId"),
        "review_id": platform_id,
        "user_name": r.get("userName"),
        "score": r.get("score"),
        "at": (r.get("at").isoformat() if getattr(r.get("at"), "isoformat", None) else r.get("at")),
        "content": r.get("content") or "",
        "reply_content": r.get("replyContent"),
        "replied_at": (
            r.get("repliedAt").isoformat()
            if getattr(r.get("repliedAt"), "isoformat", None)
            else r.get("repliedAt")
        ),
        "thumbs_up_count": r.get("thumbsUpCount"),
        "review_created_version": r.get("reviewCreatedVersion"),
    }


def collect_reviews(app_id: str, target_count: int) -> list[dict[str, Any]]:
    """
    Collect reviews via google_play_scraper.

    If network/package isn't available, this will raise with a clear error.
    """
    try:
        from google_play_scraper import Sort, reviews  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "Missing dependency `google-play-scraper`. Install it first (see requirements.txt)."
        ) from e

    out: list[dict[str, Any]] = []
    continuation_token = None
    while len(out) < target_count:
        batch, continuation_token = reviews(
            app_id,
            lang="en",
            country="us",
            sort=Sort.NEWEST,
            count=min(200, target_count - len(out)),
            continuation_token=continuation_token,
        )
        out.extend(batch)
        if continuation_token is None or not batch:
            break
    return out


def main() -> int:
    repo = _repo_root()
    data_dir = repo / "data"
    raw_path = data_dir / "reviews_raw.jsonl"
    meta_path = data_dir / "dataset_metadata.json"

    app_name = os.getenv("SPECCHAIN_APP_NAME", DEFAULT_APP_NAME)
    app_id = os.getenv("SPECCHAIN_GOOGLE_PLAY_APP_ID", DEFAULT_GOOGLE_PLAY_APP_ID)
    target_count = int(os.getenv("SPECCHAIN_TARGET_REVIEWS", "1200"))

    # If raw already exists and is non-empty, do not overwrite (keeps work reproducible).
    existing = _read_jsonl(raw_path)
    if existing:
        print(f"Raw reviews already present: {len(existing)} rows in {raw_path.as_posix()}")
        # Still ensure metadata exists/updated.
        metadata = {
            "app_name": app_name,
            "app_id": app_id,
            "collection_method": "google_play_scraper (import-existing)",
            "raw_dataset_path": "data/reviews_raw.jsonl",
            "raw_dataset_size": len(existing),
            "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        _write_json(meta_path, metadata)
        print(f"Wrote metadata: {meta_path.as_posix()}")
        return 0

    print(f"Collecting reviews for {app_name} ({app_id}) ...")
    raw_reviews = collect_reviews(app_id=app_id, target_count=target_count)
    normalized = [_normalize_raw_review(r, i) for i, r in enumerate(raw_reviews)]
    _write_jsonl(raw_path, normalized)
    print(f"Wrote raw dataset: {raw_path.as_posix()} ({len(normalized)} reviews)")

    metadata = {
        "app_name": app_name,
        "app_id": app_id,
        "collection_method": "google_play_scraper",
        "raw_dataset_path": "data/reviews_raw.jsonl",
        "raw_dataset_size": len(normalized),
        "notes": "If the app store limits results, collect as many as possible and document the limitation here.",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(meta_path, metadata)
    print(f"Wrote metadata: {meta_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())