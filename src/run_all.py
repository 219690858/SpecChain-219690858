"""Run the automated pipeline end-to-end."""

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

    python = sys.executable  # ensures python3 is used on macOS

    # 1) Collect/import (raw)
    _run([python, "src/01_collect_or_import.py"], repo_root)

    # 2) Clean
    _run([python, "src/02_clean.py"], repo_root)

    # 3) Automated pipeline artifacts
    _run([python, "src/05_personas_auto.py"], repo_root)
    _run([python, "src/06_spec_generate.py"], repo_root)
    _run([python, "src/07_tests_generate.py"], repo_root)

    # 4) Metrics for all pipelines + summary (script decides what can be computed)
    _run([python, "src/08_metrics.py"], repo_root)

    print("\nrun_all complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())