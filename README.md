# TU Delft CLI

An unofficial command-line interface for TU Delft student portal workflows.

TU Delft CLI connects to `my.tudelft.nl` and allows students to access common academic information directly from the terminal, including grades, EC progress, enrollments, curriculum data, and course enrollment workflows.

---

## Features

Current functionality includes:

- View grades
- View EC progress
- View student profile
- View current course enrollments
- View current exam enrollments
- Suggest currently available courses from your fixed programme
- Enroll in courses directly from the terminal
- Interactive shell mode

![Shell Preview](docs/shell-preview2.png)

---

## Installation

### Recommended: install with pipx

Install using `pipx` so the CLI is available globally without affecting your Python environment.

    pipx install git+https://github.com/jenslawrence/tudelft-cli.git

### Install browser dependency for login

This project uses Playwright for browser-based TU Delft authentication.

After installation, install Chromium once:

    playwright install chromium

---

## First Use

Start the shell:

    tudelft

Or use one-shot commands:

    tudelft grades
    tudelft ec
    tudelft whoami

Log in:

    tudelft login

A browser window opens for TU Delft authentication.

After successful login, your session is stored locally.

---

## Example Commands

    tudelft grades
    tudelft grades --json
    tudelft grades --final-only

    tudelft ec
    tudelft curriculum

    tudelft enrollments
    tudelft enrollments --courses
    tudelft enrollments --exams

    tudelft suggest-courses
    tudelft enroll-course

---

## Interactive Shell

Running:

    tudelft

opens the interactive shell.

Shell shortcuts:

    help / h / ?
    reset
    exit / quit / q

---

## Authentication

Authentication is performed through TU Delft Single Sign-On.

The CLI does **not** ask for your password in the terminal.

Instead:

- a browser window opens
- you authenticate through TU Delft SSO
- the CLI captures the resulting bearer token
- the token is stored locally for future requests

Session files are stored in:

    ~/.config/tudelft-cli/

---

## Development Setup

Clone the repository:

    git clone https://github.com/jenslawrence/tudelft-cli.git
    cd tudelft-cli

Create virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate

Install editable package:

    pip install -e .

Install browser dependency:

    playwright install chromium

Run:

    tudelft

---

## Disclaimer

This project is unofficial and not affiliated with TU Delft.

Use at your own responsibility when performing enrollment actions.

TU Delft portal APIs may change without notice.

---

## Roadmap

Planned features:

- Smarter enrollment recommendations
- Auto-update checks
- PyPI release
- Cross-platform packaging

---

## License

MIT License
