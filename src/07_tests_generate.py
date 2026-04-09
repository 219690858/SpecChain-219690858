"""Auto tests from auto spec (Groq)."""

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
# Groq rejects completion max_tokens above this for this model (see API 400).
_GROQ_COMPLETION_TOKEN_CAP = 8192


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _groq_chat(
    api_key: str,
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    *,
    max_tokens: int = _GROQ_COMPLETION_TOKEN_CAP,
    use_json_object_mode: bool = True,
) -> str:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body: dict[str, Any] = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if use_json_object_mode:
        body["response_format"] = {"type": "json_object"}
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
            # Some models reject json_object; retry once without it
            if use_json_object_mode and resp.status_code == 400 and "response_format" in body:
                del body["response_format"]
                use_json_object_mode = False
                resp = requests.post(GROQ_BASE_URL, headers=headers, json=body, timeout=180)
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
    if not t.startswith("{"):
        start = t.find("{")
        end = t.rfind("}")
        if start != -1 and end != -1 and end > start:
            t = t[start : end + 1]
    return json.loads(t)


def _parse_requirements(md: str) -> list[dict[str, str]]:
    reqs: list[dict[str, str]] = []
    cur: dict[str, str] | None = None
    for line in md.splitlines():
        if line.startswith("## Requirement ID:"):
            if cur:
                reqs.append(cur)
            cur = {"id": line.split(":", 1)[1].strip(), "description": "", "acceptance_criteria": ""}
        elif cur and line.strip().startswith("- Description:"):
            cur["description"] = line.split(":", 1)[1].strip().strip("[]")
        elif cur and line.strip().startswith("- Acceptance Criteria:"):
            cur["acceptance_criteria"] = line.split(":", 1)[1].strip().strip("[]")
    if cur:
        reqs.append(cur)
    return reqs


def main() -> int:
    repo = _repo_root()
    spec_path = repo / "spec" / "spec_auto.md"
    out_path = repo / "tests" / "tests_auto.json"

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")

    md = spec_path.read_text(encoding="utf-8")
    reqs = _parse_requirements(md)
    if not reqs:
        raise RuntimeError("spec/spec_auto.md has no requirements.")

    prompt = (
        "You are helping a software requirements class project.\n"
        "Generate validation test scenarios for each requirement.\n"
        "Return ONLY JSON with this schema:\n"
        "{\n"
        "  \"tests\": [\n"
        "    {\n"
        "      \"test_id\": \"T_auto_1\",\n"
        "      \"requirement_id\": \"FR_auto_1\",\n"
        "      \"scenario\": \"...\",\n"
        "      \"steps\": [\"...\"],\n"
        "      \"expected_result\": \"...\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "Rules:\n"
        "- Create exactly 2 tests per requirement.\n"
        "- Each test must reference a requirement_id from the input.\n"
        "- Steps should be short and clear.\n"
        "- expected_result should match the requirement.\n"
    )

    raw_cap = int(os.getenv("GROQ_MAX_TEST_TOKENS", str(_GROQ_COMPLETION_TOKEN_CAP)))
    max_tokens = max(256, min(raw_cap, _GROQ_COMPLETION_TOKEN_CAP))
    parse_retries = max(1, int(os.getenv("GROQ_TESTS_PARSE_RETRIES", "5")))

    data: Any = None
    last_parse_err: Exception | None = None
    for p_attempt in range(parse_retries):
        resp = _groq_chat(
            api_key,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps({"requirements": reqs})},
            ],
            temperature=0.25,
            max_tokens=max_tokens,
        )
        try:
            data = _extract_json(resp)
            break
        except json.JSONDecodeError as e:
            last_parse_err = e
            if p_attempt + 1 >= parse_retries:
                raise RuntimeError(
                    "Groq returned invalid or truncated JSON for tests after "
                    f"{parse_retries} attempt(s). For this model max output is "
                    f"{_GROQ_COMPLETION_TOKEN_CAP} tokens; retry later or shorten spec_auto.md."
                ) from e
            time.sleep(2.0 + p_attempt * 1.5)

    tests = data.get("tests", [])
    if not isinstance(tests, list) or not tests:
        raise RuntimeError("LLM did not return tests.")

    # Validate coverage
    req_ids = {r["id"] for r in reqs}
    seen = set()
    for t in tests:
        rid = t.get("requirement_id")
        if rid not in req_ids:
            raise RuntimeError(f"Test references unknown requirement_id: {rid}")
        seen.add(rid)
    if seen != req_ids:
        missing = sorted(list(req_ids - seen))
        raise RuntimeError(f"Missing tests for requirement(s): {missing[:5]}")

    _write_json(out_path, {"tests": tests})
    print(f"Wrote automated tests: {out_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())