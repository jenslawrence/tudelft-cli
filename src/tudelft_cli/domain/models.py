from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuthSession(BaseModel):
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    scope: Optional[str] = None
    expires_at: Optional[datetime] = None
    obtained_at: Optional[datetime] = None
    student_number: Optional[str] = None
    netid: Optional[str] = None


class StudentProfile(BaseModel):
    name: str
    netid: Optional[str] = None
    student_number: Optional[str] = None
    programme: Optional[str] = None
    faculty: Optional[str] = None


class Grade(BaseModel):
    course_code: str
    course_name: str
    component: str
    value: str
    passed: Optional[bool] = None
    published_at: Optional[datetime] = None

class EcPhaseProgress(BaseModel):
    programme_name: str
    faculty: Optional[str] = None
    exam_programme_name: Optional[str] = None
    phase_description: str
    earned_ec: Optional[int] = None
    required_ec: Optional[int] = None
    percentage: Optional[int] = None
    completed: Optional[bool] = None
    other_earned_ec: Optional[int] = None


class EcProgress(BaseModel):
    items: list[EcPhaseProgress]
