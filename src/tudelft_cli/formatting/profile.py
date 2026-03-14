from rich.console import Console

from tudelft_cli.domain.models import StudentProfile


def render_profile(profile: StudentProfile) -> None:
    console = Console()
    console.print(f"[bold]{profile.name}[/bold]")
    if profile.netid:
        console.print(f"NetID: {profile.netid}")
    if profile.student_number:
        console.print(f"Student number: {profile.student_number}")
    if profile.programme:
        console.print(f"Programme: {profile.programme}")
    if profile.faculty:
        console.print(f"Faculty: {profile.faculty}")
