from __future__ import annotations

import re
import shlex
from pathlib import Path

from typer.testing import CliRunner

from tudelft_cli.main import app


README = Path(__file__).resolve().parents[1] / "README.md"

IMPLEMENTED_COMMANDS = {
    "login",
    "logout",
    "whoami",
    "grades",
    "ec",
    "enrollments",
    "suggest-courses",
    "suggest-exams",
    "enroll-course",
    "enroll-exam",
    "course",
}


def _actual_typer_commands() -> set[str]:
    commands: set[str] = set()
    for group in app.registered_groups:
        typer_instance = group.typer_instance
        commands.update(command.name for command in typer_instance.registered_commands)
    return commands


def _readme_text() -> str:
    return README.read_text(encoding="utf-8")


def _documented_tudelft_commands() -> list[list[str]]:
    commands: list[list[str]] = []
    for line in _readme_text().splitlines():
        if not line.startswith("    tudelft"):
            continue
        commands.append(shlex.split(line.strip()))
    return commands


def test_readme_does_not_document_removed_commands_or_flags() -> None:
    text = _readme_text()

    assert "curriculum" not in text
    assert "--json" not in text
    assert "tudelft enroll-course\n" not in text
    assert "tudelft enroll-course\r\n" not in text


def test_readme_command_surface_matches_typer_commands() -> None:
    runner = CliRunner()
    root_help = runner.invoke(app, ["--help"])
    actual_commands = _actual_typer_commands()

    assert root_help.exit_code == 0
    assert actual_commands == IMPLEMENTED_COMMANDS

    for command in actual_commands:
        assert command in root_help.output

    for command in actual_commands:
        assert re.search(rf"- `tudelft {re.escape(command)}(?:[ `]|$)", _readme_text())


def test_readme_tudelft_examples_use_implemented_commands_and_flags() -> None:
    runner = CliRunner()
    actual_commands = _actual_typer_commands()

    for match in re.finditer(r"\btudelft[ \t]+([a-z][a-z-]*)", _readme_text()):
        assert match.group(1) in actual_commands

    for tokens in _documented_tudelft_commands():
        if len(tokens) == 1:
            continue

        command = tokens[1]
        assert command in actual_commands

        help_result = runner.invoke(app, [command, "--help"])
        assert help_result.exit_code == 0

        documented_flags = [token for token in tokens[2:] if token.startswith("--")]
        for flag in documented_flags:
            assert flag in help_result.output
