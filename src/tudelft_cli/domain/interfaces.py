from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from tudelft_cli.domain.models import AuthSession, EcProgress, Grade, StudentProfile


class AuthProvider(ABC):
    @abstractmethod
    def login(self) -> AuthSession:
        raise NotImplementedError

    @abstractmethod
    def load_session(self) -> AuthSession | None:
        raise NotImplementedError

    @abstractmethod
    def logout(self) -> None:
        raise NotImplementedError


class StudentPortal(ABC):
    @abstractmethod
    def get_profile(self, session: AuthSession) -> StudentProfile:
        raise NotImplementedError

    @abstractmethod
    def get_grades(self, session: AuthSession) -> Sequence[Grade]:
        raise NotImplementedError

    @abstractmethod
    def get_ec_progress(self, session: AuthSession) -> EcProgress:
        raise NotImplementedError
