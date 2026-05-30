from __future__ import annotations

import re
import shlex
from pathlib import Path

from typer.testing import CliRunner

from tudelft_cli.main import app


README = Path(__file__).resolve().parents[1] / "README.md"
TUDELFT_EXAMPLE_RE = re.compile(r"^\s*tudelft(?:\s+.*)?$")


def _readme_tudelft_examples() -> list[tuple[int, list[str]]]:
    examples: list[tuple[int, list[str]]] = []

    for line_number, line in enumerate(README.read_text(encoding="utf-8").splitlines(), start=1):
        if not TUDELFT_EXAMPLE_RE.match(line):
            continue

        try:
            parts = shlex.split(line.strip())
        except ValueError:
            continue

        if parts:
            examples.append((line_number, parts))

    return examples


def _long_flags(args: list[str]) -> list[str]:
    return [arg.split("=", maxsplit=1)[0] for arg in args if arg.startswith("--")]


def test_readme_tudelft_examples_use_implemented_commands_and_flags() -> None:
    runner = CliRunner()
    root_result = runner.invoke(app, ["--help"])

    assert root_result.exit_code == 0

    for line_number, example in _readme_tudelft_examples():
        if len(example) == 1:
            continue

        command = example[1]
        command_result = runner.invoke(app, [command, "--help"])

        assert command_result.exit_code == 0, (
            f"README.md:{line_number} documents unknown command '{command}' in "
            f"example: {' '.join(example)}"
        )

        for flag in _long_flags(example[2:]):
            assert flag in command_result.output, (
                f"README.md:{line_number} documents flag '{flag}' for command "
                f"'{command}', but `tudelft {command} --help` does not list it. "
                f"Example: {' '.join(example)}"
            )
