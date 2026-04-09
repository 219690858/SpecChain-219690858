"""Task 7 — run the whole *automated* pipeline in order.

We don't call manual coding or hybrid stuff here (the handout says that's fine).
Each step overwrites / updates the auto side; manual + hybrid files stay as you
already committed them — 08_metrics still reads those for the comparison.

Order + what gets written:
  01  → data/reviews_raw.jsonl, data/dataset_metadata.json
  02  → data/reviews_clean.jsonl
  05  → data/review_groups_auto.json, personas/personas_auto.json, prompts/prompt_auto.json
  06  → spec/spec_auto.md  (Groq / API)
  07  → tests/tests_auto.json
  08  → metrics/*.json (manual + auto + hybrid + summary)

From the repo root:  python src/run_all.py  or  python3 src/run_all.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], repo_root: Path) -> None:
    printable = " ".join(cmd)
    print(f"\n==> {printable}")
    subprocess.run(cmd, cwd=str(repo_root), check=True)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]

    python = sys.executable  # whatever you used to launch this file

    # grab raw + metadata
    _run([python, "src/01_collect_or_import.py"], repo_root)

    # clean text
    _run([python, "src/02_clean.py"], repo_root)

    # auto pipeline only (LLM calls in 05–07)
    _run([python, "src/05_personas_auto.py"], repo_root)
    _run([python, "src/06_spec_generate.py"], repo_root)
    _run([python, "src/07_tests_generate.py"], repo_root)

    # recount everything incl. manual/hybrid files on disk
    _run([python, "src/08_metrics.py"], repo_root)

    print("\nrun_all finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())