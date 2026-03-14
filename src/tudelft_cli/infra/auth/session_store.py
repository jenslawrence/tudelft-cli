import json
from pathlib import Path

from tudelft_cli.domain.models import AuthSession
from tudelft_cli.infra.config.settings import config_dir, session_file


class SessionStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or session_file()

    def save(self, session: AuthSession) -> None:
        config_dir().mkdir(parents=True, exist_ok=True)
        self.path.write_text(session.model_dump_json(indent=2), encoding="utf-8")

    def load(self) -> AuthSession | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return AuthSession.model_validate(data)

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
