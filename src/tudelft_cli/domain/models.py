from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuthSession(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
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
