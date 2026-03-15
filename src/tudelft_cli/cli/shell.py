import shlex

from rich.console import Console
from pathlib import Path
from prompt_toolkit.history import FileHistory
from prompt_toolkit import PromptSession

from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
from tudelft_cli.infra.auth.session_store import SessionStore
from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal

console = Console()


BANNER = r"""
                               ▓█
                             ███
                        ▓█████▓
                  █████████▓
            ▓███████████
          █████████████
       ▓█████████████
      ███████▓▓██████       ▓▓
    ████████ ▓███████▓   ▓███
   ██████▓  ▓███████████████
   ████    ▓██████▓████████▓
  ▓██▓     ▓█████▓ ███████
  ▓█▓        ▓▓   ███████
   █▓            ▓█████▓
   █▓           █████▓
            ▓▓████
"""


def run_shell() -> None:
    from tudelft_cli.main import app

    _render_shell_home()

    history_path = Path.home() / ".config" / "tudelft-cli" / "shell_history"
    history_path.parent.mkdir(parents=True, exist_ok=True)

    session = PromptSession(history=FileHistory(str(history_path)))

    while True:
        try:
            command = session.prompt("tudelft> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            break

        if not command:
            continue

        if command in {"exit", "quit", "q"}:
            break

        if command in {"help", "h", "?"}:
            try:
                app(prog_name="tudelft", args=["--help"])
            except SystemExit:
                pass
            continue
        
        if command in {"reset", "clear", "cls"}:
            _render_shell_home()
            continue

        try:
            parts = shlex.split(command)
            if (
                parts
                and parts[0] in {"whoami", "ec", "grades"}
                and "--output" not in parts
                and "-o" not in parts
            ):
                parts.extend(["--output", "pretty"])

            app(prog_name="tudelft", args=parts)
        except SystemExit:
            pass
        except Exception as exc:
            console.print(f"[red]Error:[/red] {exc}")

def _build_shell_header() -> list[str]:
    auth_provider = BrowserAuthProvider(SessionStore())
    session = auth_provider.load_session()

    if session is None:
        return [
            "[bold cyan]TU Delft CLI shell[/bold cyan]",
            "[yellow]Not logged in[/yellow]",
            "Type 'login' to authenticate, 'help' for commands, 'exit' to quit.",
        ]

    portal = MyTUDelftPortal()

    try:
        profile = portal.get_profile(session)
        identity = profile.name
        if profile.student_number:
            identity = f"{identity} ({profile.student_number})"

        return [
            "[bold cyan]TU Delft CLI shell[/bold cyan]",
            f"[green]{identity}[/green]",
            "Type 'help' for commands, 'exit' to quit.",
        ]
    except Exception:
        return [
            "[bold cyan]TU Delft CLI shell[/bold cyan]",
            "[yellow]Session found, but profile could not be loaded[/yellow]",
            "Type 'help' for commands, 'exit' to quit.",
        ]

def _render_shell_home() -> None:
    console.clear()
    console.print(BANNER, style="bright_blue")
    for line in _build_shell_header():
        console.print(line)
    console.print()
