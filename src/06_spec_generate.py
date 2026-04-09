"""Auto spec from auto personas (Groq)."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

import requests

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _groq_chat(api_key: str, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
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
    # strip fenced blocks if any
    if t.startswith("```"):
        t = "\n".join(t.splitlines()[1:])
        if t.strip().endswith("```"):
            t = "\n".join(t.splitlines()[:-1])
        t = t.strip()
    # try to find first JSON object
    if not t.startswith("{"):
        start = t.find("{")
        end = t.rfind("}")
        if start != -1 and end != -1 and end > start:
            t = t[start : end + 1]
    return json.loads(t)


def main() -> int:
    repo = _repo_root()
    personas_path = repo / "personas" / "personas_auto.json"
    out_path = repo / "spec" / "spec_auto.md"

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")

    personas_obj = _read_json(personas_path)
    personas = personas_obj.get("personas", [])
    if not isinstance(personas, list) or not personas:
        raise RuntimeError("personas/personas_auto.json is empty or invalid.")

    forbidden_vague = [
        "seamless",
        "smooth",
        "reasonable",
        "user-friendly",
        "easy",
        "better",
        "fast",
        "quick",
        "efficiently",
        "nicely",
        "good",
        "great",
        "typical",
        "without delay",
    ]

    prompt = (
        "You are helping a software requirements class project.\n"
        "Generate a structured software specification from the given personas for the Headspace app.\n"
        "Write requirements in a student-style but keep them testable.\n\n"
        "Output ONLY JSON with this schema:\n"
        "{\n"
        "  \"requirements\": [\n"
        "    {\n"
        "      \"id\": \"FR_auto_1\",\n"
        "      \"description\": \"...\",\n"
        "      \"source_persona\": \"...\",\n"
        "      \"traceability\": \"Derived from review group A1\",\n"
        "      \"acceptance_criteria\": \"Given ... When ... Then ...\"\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- Create 10 to 12 requirements total.\n"
        "- Each requirement must be specific and measurable (include numbers like seconds/minutes, counts, or clear UI states).\n"
        "- Avoid vague words like: "
        + ", ".join(forbidden_vague)
        + ".\n"
        "- Focus on realistic Headspace concerns: crashes/freezes, loading time, playback stopping, offline downloads, login loops, subscription access errors, paywall clarity, navigation/continue progress, and settings (especially turning OFF haptics).\n"
        "- source_persona must EXACTLY match one of the persona names in the input.\n"
        "- traceability must be exactly: \"Derived from review group A#\" using the persona's derived_from_group (A1..A5).\n"
        "- Acceptance criteria must follow Given/When/Then and be directly testable.\n"
        "- Do not mention workouts, fitness tracking, payments, or billing.\n"
    )

    resp = _groq_chat(
        api_key,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps({"personas": personas})},
        ],
        temperature=0.25,
    )
    data = _extract_json(resp)
    reqs = data.get("requirements", [])
    if not isinstance(reqs, list) or len(reqs) < 10:
        raise RuntimeError("LLM did not return at least 10 requirements.")

    # Render to markdown in the same style as manual spec.
    lines: list[str] = ["# Automated Specification (Headspace)", ""]
    for i, r in enumerate(reqs, start=1):
        rid = f"FR_auto_{i}"
        desc = r.get("description", "").strip()
        persona = r.get("source_persona", "").strip()
        trace = r.get("traceability", "").strip()
        ac = r.get("acceptance_criteria", "").strip()
        m = re.search(r"(A[1-5])", trace)
        if m:
            trace = f"Derived from review group {m.group(1)}"
        lines.extend(
            [
                f"## Requirement ID: {rid}",
                f"- Description: [{desc}]",
                f"- Source Persona: [{persona}]",
                f"- Traceability: [{trace}]",
                f"- Acceptance Criteria: [{ac}]",
                "",
            ]
        )

    _write_text(out_path, "\n".join(lines).rstrip() + "\n")
    print(f"Wrote automated spec: {out_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())