"""Auto groups + auto personas (Groq + similarity assignment)."""

from __future__ import annotations

import json
import os
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from scipy.sparse import csr_matrix, vstack  # type: ignore
from sklearn.feature_extraction.text import TfidfVectorizer

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

# Keeps the first Groq call under typical on-demand TPM; override via env if needed.
_SAMPLE_N_DEFAULT = 180
_REVIEW_TEXT_MAX = 200


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


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


@dataclass(frozen=True)
class Review:
    id: str
    content_raw: str
    content_clean: str
    score: int | None


def _load_reviews(clean_path: Path) -> list[Review]:
    rows = _read_jsonl(clean_path)
    out: list[Review] = []
    for r in rows:
        rid = r.get("id")
        if not rid:
            continue
        out.append(
            Review(
                id=rid,
                content_raw=r.get("content_raw", "") or "",
                content_clean=r.get("content_clean", "") or "",
                score=r.get("score"),
            )
        )
    if not out:
        raise RuntimeError("No reviews found in data/reviews_clean.jsonl")
    return out


def _groq_chat(api_key: str, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
    """Call Groq; on 429, sleep and retry (parses 'try again in Xs' when present)."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"model": MODEL_NAME, "messages": messages, "temperature": temperature}
    max_attempts = 12
    for attempt in range(max_attempts):
        resp = requests.post(GROQ_BASE_URL, headers=headers, json=body, timeout=180)
        if resp.status_code == 429:
            msg = resp.text
            try:
                err = resp.json().get("error", {})
                if isinstance(err, dict) and err.get("message"):
                    msg = str(err["message"])
            except Exception:
                pass
            m = re.search(r"try again in ([0-9]+(?:\.[0-9]+)?)\s*s", msg, re.I)
            wait = float(m.group(1)) + 2.0 if m else min(2.0**attempt, 90.0)
            time.sleep(wait)
            continue
        if resp.status_code >= 400:
            raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    raise RuntimeError("Groq API: rate limit retries exhausted")


def _extract_json(text: str) -> Any:
    t = text.strip()
    if t.startswith("```"):
        t = "\n".join(t.splitlines()[1:])
        if t.strip().endswith("```"):
            t = "\n".join(t.splitlines()[:-1])
        t = t.strip()
    return json.loads(t)


def main() -> int:
    repo = _repo_root()
    clean_path = repo / "data" / "reviews_clean.jsonl"
    out_groups_path = repo / "data" / "review_groups_auto.json"
    out_personas_path = repo / "personas" / "personas_auto.json"
    out_prompt_path = repo / "prompts" / "prompt_auto.json"

    reviews = _load_reviews(clean_path)
    idx_by_id = {r.id: i for i, r in enumerate(reviews)}

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")

    grouping_prompt = (
        "You are a software requirements analyst.\n\n"
        "Task:\n"
        "Group the given Headspace app user reviews into EXACTLY 5 non-overlapping groups.\n\n"
        "Rules:\n"
        "- Each review_id in this input must appear in exactly ONE group (no duplicates across groups).\n"
        "- Every provided review_id in this input must be assigned to one of the 5 groups (no omissions).\n"
        "- Each group must represent a distinct user problem or user need.\n"
        "- Each group must contain at least 10 review_ids.\n"
        "- Use only the provided review_ids. Do NOT invent or modify any IDs.\n"
        "- Theme must be concise (5–10 words) and clearly describe the issue.\n\n"
        "Output Requirements:\n"
        "- Return ONLY valid JSON (no explanations, no extra text).\n"
        "- Do NOT include markdown code blocks.\n"
        "- The output MUST contain exactly 5 groups.\n\n"
        "Schema:\n"
        "{\n"
        "  \"groups\": [\n"
        "    { \"group_id\": \"A1\", \"theme\": \"...\", \"review_ids\": [\"rev_...\"], \"example_reviews\": [\"...\", \"...\"] },\n"
        "    { \"group_id\": \"A2\", \"theme\": \"...\", \"review_ids\": [\"rev_...\"], \"example_reviews\": [\"...\", \"...\"] },\n"
        "    { \"group_id\": \"A3\", \"theme\": \"...\", \"review_ids\": [\"rev_...\"], \"example_reviews\": [\"...\", \"...\"] },\n"
        "    { \"group_id\": \"A4\", \"theme\": \"...\", \"review_ids\": [\"rev_...\"], \"example_reviews\": [\"...\", \"...\"] },\n"
        "    { \"group_id\": \"A5\", \"theme\": \"...\", \"review_ids\": [\"rev_...\"], \"example_reviews\": [\"...\", \"...\"] }\n"
        "  ]\n"
        "}\n\n"
        "Additional Constraints:\n"
        "- example_reviews must be short quotes (max 200 characters each).\n"
        "- Quotes must come from the provided reviews (do not invent).\n"
        "- Keep groups balanced and meaningful (not random splits).\n"
    )

    persona_prompt = (
        "You are helping a software requirements class project.\n"
        "Given a review group (theme + example reviews + review ids), create ONE persona.\n"
        "Do NOT invent details not supported by the reviews.\n"
        "IMPORTANT: Persona name must be unique and specific (NOT generic like \"Frustrated User\").\n"
        "Return ONLY JSON with this structure:\n"
        "{\n"
        "  \"id\": \"P_auto_X\",\n"
        "  \"name\": \"Unique persona name\",\n"
        "  \"description\": \"1-2 sentences\",\n"
        "  \"derived_from_group\": \"A#\",\n"
        "  \"goals\": [\"...\"],\n"
        "  \"pain_points\": [\"...\"],\n"
        "  \"context\": [\"...\"],\n"
        "  \"constraints\": [\"...\"],\n"
        "  \"evidence_reviews\": [\"rev_...\", \"rev_...\"]\n"
        "}\n"
        "Keep lists short (3-5 items). Evidence reviews must be ids from the group.\n"
    )

    _write_json(
        out_prompt_path,
        {
            "model": MODEL_NAME,
            "grouping_method": "Groq LLM grouping on a sample + TF-IDF similarity assignment for full dataset",
            "grouping_prompt": grouping_prompt,
            "persona_prompt": persona_prompt,
        },
    )

    rnd = random.Random(4312)
    sample_cap = int(os.getenv("GROQ_GROUP_SAMPLE_N", str(_SAMPLE_N_DEFAULT)))
    sample_n = min(max(sample_cap, 50), len(reviews))
    sample = rnd.sample(reviews, k=sample_n)
    sample_payload = [
        {"review_id": r.id, "review_text": (r.content_raw or r.content_clean)[:_REVIEW_TEXT_MAX]} for r in sample
    ]

    def _validate_grouping(groups_obj: Any) -> tuple[dict[str, str], dict[str, str], list[str]]:
        if not isinstance(groups_obj, list) or len(groups_obj) != 5:
            raise RuntimeError("LLM grouping did not return exactly 5 groups.")

        seen: dict[str, str] = {}
        dups: list[str] = []
        th: dict[str, str] = {}

        for g in groups_obj:
            gid = g.get("group_id")
            if gid not in {"A1", "A2", "A3", "A4", "A5"}:
                raise RuntimeError(f"Invalid group_id from LLM: {gid}")
            th[gid] = (g.get("theme") or "").strip() or gid
            rids = g.get("review_ids", [])
            if not isinstance(rids, list):
                raise RuntimeError("LLM grouping review_ids must be a list.")
            for rid in rids:
                if rid in seen:
                    dups.append(rid)
                else:
                    seen[rid] = gid
        return seen, th, sorted(set(dups))

    messages: list[dict[str, str]] = [
        {"role": "system", "content": grouping_prompt},
        {"role": "user", "content": json.dumps({"reviews": sample_payload})},
    ]

    assigned: dict[str, str] = {}
    themes: dict[str, str] = {}
    duplicates: list[str] = []
    for _attempt in range(1, 4):
        grouping_resp = _groq_chat(api_key, messages=messages, temperature=0.2)
        grouping_json = _extract_json(grouping_resp)
        groups = grouping_json.get("groups", [])
        assigned, themes, duplicates = _validate_grouping(groups)
        if not duplicates:
            break

        messages.append(
            {
                "role": "user",
                "content": (
                    "Your previous output had duplicate review_ids across groups.\n"
                    f"Duplicate review_ids: {duplicates}\n"
                    "Please output the FULL JSON again, fixing duplicates so each review_id appears in exactly one group."
                ),
            }
        )

    if duplicates:
        pass

    vectorizer = TfidfVectorizer(max_features=8000, stop_words="english")
    X = vectorizer.fit_transform([r.content_clean for r in reviews])

    centroid_gids = ["A1", "A2", "A3", "A4", "A5"]
    centroid_rows = []
    for gid in centroid_gids:
        member_idxs = [idx_by_id[rid] for rid, ggid in assigned.items() if ggid == gid and rid in idx_by_id]
        if not member_idxs:
            member_idxs = [rnd.randrange(0, len(reviews))]
        centroid_rows.append(csr_matrix(X[member_idxs].mean(axis=0)))
    C = vstack(centroid_rows)

    sims = X @ C.T
    auto_groups: dict[str, list[str]] = {gid: [] for gid in centroid_gids}
    for i, r in enumerate(reviews):
        row = sims.getrow(i).toarray()[0]
        best = int(row.argmax())
        auto_groups[centroid_gids[best]].append(r.id)

    groups_payload = {"groups": []}
    for gid in centroid_gids:
        member_ids = sorted(auto_groups[gid])
        examples: list[str] = []
        for rid in member_ids:
            raw = (reviews[idx_by_id[rid]].content_raw or "").strip().replace("\n", " ")
            if raw:
                examples.append(raw[:200])
            if len(examples) >= 2:
                break
        groups_payload["groups"].append(
            {"group_id": gid, "theme": themes.get(gid, gid), "review_ids": member_ids, "example_reviews": examples}
        )

    personas: list[dict[str, Any]] = []
    for idx, g in enumerate(groups_payload["groups"], start=1):
        gid = g["group_id"]
        ids = list(g["review_ids"])
        sample_ids_for_persona = ids if len(ids) <= 12 else rnd.sample(ids, 12)
        persona_input = {
            "group_id": gid,
            "theme": g["theme"],
            "example_reviews": g["example_reviews"],
            "review_ids_sample": sample_ids_for_persona[:8],
        }
        persona_resp = _groq_chat(
            api_key,
            messages=[
                {"role": "system", "content": persona_prompt},
                {"role": "user", "content": json.dumps(persona_input)},
            ],
            temperature=0.3,
        )
        persona = _extract_json(persona_resp)
        persona["id"] = f"P_auto_{idx}"
        persona["derived_from_group"] = gid
        ev = [rid for rid in persona.get("evidence_reviews", []) if rid in set(ids)]
        if not ev:
            ev = sample_ids_for_persona[:2]
        persona["evidence_reviews"] = ev[:5]
        personas.append(persona)
        time.sleep(float(os.getenv("GROQ_PERSONA_DELAY_S", "1.2")))

    _write_json(out_groups_path, groups_payload)
    _write_json(out_personas_path, {"personas": personas})

    print(f"Wrote automated review groups: {out_groups_path.as_posix()}")
    print(f"Wrote automated personas: {out_personas_path.as_posix()}")
    print(f"Wrote prompt record: {out_prompt_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
