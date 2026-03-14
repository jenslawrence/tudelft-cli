from pathlib import Path


APP_NAME = "tudelft-cli"


def config_dir() -> Path:
    return Path.home() / ".config" / APP_NAME


def session_file() -> Path:
    return config_dir() / "session.json"
