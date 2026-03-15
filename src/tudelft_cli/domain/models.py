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

class SuggestedCourse(BaseModel):
    course_offering_id: int
    course_id: int
    course_code: str
    academic_year: Optional[str] = None
    block: Optional[str] = None
    period_description: Optional[str] = None
    period_date_range: Optional[str] = None
    course_name: str
    faculty: Optional[str] = None
    category: Optional[str] = None
    ec: Optional[str] = None
    ec_unit: Optional[str] = None
    availability: Optional[bool] = None
    waiting_list: Optional[bool] = None
    coordinating_unit: Optional[str] = None
    course_type: Optional[str] = None
    teaching_form_description: Optional[str] = None
    course_note: Optional[str] = None
    course_block_note: Optional[str] = None
    programme_part: Optional[str] = None


class CourseEnrollment(BaseModel):
    course_offering_id: int
    course_id: int
    course_code: str
    academic_year: Optional[int] = None
    block: Optional[str] = None
    period_description: Optional[str] = None
    period_date_range: Optional[str] = None
    course_name: str
    ec: Optional[float] = None
    ec_unit: Optional[str] = None
    programme_part: Optional[str] = None
    can_unenroll: Optional[bool] = None
    is_new: Optional[bool] = None
    is_historical: Optional[bool] = None
