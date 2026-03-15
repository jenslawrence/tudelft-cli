import sys
import typer

from tudelft_cli.cli.auth import app as auth_app
from tudelft_cli.cli.whoami import app as whoami_app
from tudelft_cli.cli.course import app as course_app
from tudelft_cli.cli.enroll_exam import app as enroll_exam_app
from tudelft_cli.cli.enroll_courses import app as enroll_courses_app
from tudelft_cli.cli.enrollments import app as enrollments_app
from tudelft_cli.cli.grades import app as grades_app
from tudelft_cli.cli.ec import app as ec_app
from tudelft_cli.cli.suggest_courses import app as suggest_courses_app
from tudelft_cli.cli.suggest_exams import app as suggest_exams_app
from tudelft_cli.cli.root import app as root_app
from tudelft_cli.cli.shell import run_shell


app = typer.Typer(
    help=(
        "TU Delft student portal CLI.\n\n"
        "Use this tool to inspect grades, EC progress, enrollments, "
        "course suggestions, exam suggestions, and Study Guide links."
    ),
    no_args_is_help=False,
    add_completion=False,
)


@app.callback()
def main_callback() -> None:
    """TU Delft student portal command-line interface."""
    pass


app.add_typer(auth_app, help="Authentication commands.")
app.add_typer(whoami_app, help="Student profile commands.")
app.add_typer(grades_app, help="Grade and progress commands.")
app.add_typer(ec_app, help="EC and progress commands.")
app.add_typer(enrollments_app, help="Enrollment overview commands.")
app.add_typer(suggest_courses_app, help="Suggested course enrollment commands.")
app.add_typer(suggest_exams_app, help="Suggested exam enrollment commands.")
app.add_typer(enroll_exam_app, help="Exam enrollment commands.")
app.add_typer(enroll_courses_app, help="Course enrollment commands.")
app.add_typer(course_app, help="Study Guide course commands.")
app.add_typer(root_app, help="General student profile commands.")


def main() -> None:
    if len(sys.argv) == 1:
        run_shell()
    else:
        app()

if __name__ == "__main__":
    main()
