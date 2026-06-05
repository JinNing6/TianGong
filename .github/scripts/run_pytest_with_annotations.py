"""Run pytest and expose the first failure through GitHub check annotations."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

DISPLAY_COMMAND = "python -m pytest -q -p no:cacheprovider --basetemp=.pytest-tmp-ci --tb=short --maxfail=1"
PYTEST_ARGS = [
    "-m",
    "pytest",
    "-q",
    "-p",
    "no:cacheprovider",
    "--basetemp=.pytest-tmp-ci",
    "--tb=short",
    "--maxfail=1",
]
MAX_ANNOTATION_CHARS = 5000


def _escape_github_annotation(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _failure_excerpt(output: str, *, exit_code: int) -> str:
    lines = output.splitlines()
    first_failure = next(
        (
            index
            for index, line in enumerate(lines)
            if line.startswith(("FAILED ", "ERROR ")) or " short test summary info " in line
        ),
        max(0, len(lines) - 80),
    )
    excerpt = "\n".join(lines[first_failure:first_failure + 80]).strip()
    if not excerpt:
        excerpt = output.strip() or "pytest exited without output"
    message = f"Command: {DISPLAY_COMMAND}\nExit code: {exit_code}\n\n{excerpt}"
    return message[:MAX_ANNOTATION_CHARS]


def _append_step_summary(summary: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with Path(path).open("a", encoding="utf-8") as file:
        file.write("## Pytest Failure Summary\n\n")
        file.write(f"Command: `{DISPLAY_COMMAND}`\n\n")
        file.write("```text\n")
        file.write(summary)
        file.write("\n```\n")


def main() -> int:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    result = subprocess.run(
        [sys.executable, *PYTEST_ARGS],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        summary = _failure_excerpt(result.stdout, exit_code=result.returncode)
        _append_step_summary(summary)
        print(f"::error title=pytest failed::{_escape_github_annotation(summary)}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
