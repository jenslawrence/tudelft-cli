from __future__ import annotations

from typing import Any

from tudelft_cli.domain.errors import PortalChangedError
from tudelft_cli.domain.models import ExamEnrollment, ExamOpportunity, SuggestedExamCourse
from tudelft_cli.infra.portal.parsing import (
    as_optional_string,
    format_time_decimal,
    parse_bool_jn,
    parse_datetime,
    parse_float,
    parse_int,
    required_string,
)


def map_suggested_exam_courses_payload(payload: object) -> list[SuggestedExamCourse]:
    if not isinstance(payload, dict):
        raise PortalChangedError("Suggested exams endpoint returned an unexpected payload shape.")

    items = payload.get("items")
    if not isinstance(items, list):
        raise PortalChangedError("Suggested exams payload is missing expected items.")

    return [map_suggested_exam_course(item) for item in items if isinstance(item, dict)]


def map_exam_enrollments_payload(payload: object) -> list[ExamEnrollment]:
    if not isinstance(payload, dict):
        raise PortalChangedError("Exam enrollments endpoint returned an unexpected payload shape.")

    items = payload.get("items")
    if not isinstance(items, list):
        raise PortalChangedError("Exam enrollments payload is missing expected items.")

    return [map_exam_enrollment(item) for item in items if isinstance(item, dict)]


def map_exam_opportunities_payload(
    payload: object,
) -> tuple[SuggestedExamCourse, list[ExamOpportunity], list[dict[str, Any]]]:
    if not isinstance(payload, dict):
        raise PortalChangedError("Exam opportunities endpoint returned an unexpected payload shape.")

    toetsen = payload.get("toetsen")
    if not isinstance(toetsen, list):
        raise PortalChangedError("Exam opportunities payload is missing expected toetsen list.")

    course = SuggestedExamCourse(
        course_id=int(payload["id_cursus"]),
        course_code=required_string(payload, "cursus"),
        academic_year=parse_int(payload.get("collegejaar")),
        course_name=required_string(payload, "cursus_korte_naam"),
        ec=parse_float(payload.get("punten")),
        ec_unit=as_optional_string(payload.get("punteneenheid")),
        faculty=as_optional_string(payload.get("faculteit_naam")),
        category=as_optional_string(payload.get("categorie_omschrijving")),
        course_type=as_optional_string(payload.get("cursustype_omschrijving")),
        programme_part=as_optional_string(payload.get("onderdeel_van")),
    )

    opportunities = [map_exam_opportunity(item) for item in toetsen if isinstance(item, dict)]
    raw_items = [item for item in toetsen if isinstance(item, dict)]
    return course, opportunities, raw_items


def map_suggested_exam_course(item: dict[str, Any]) -> SuggestedExamCourse:
    return SuggestedExamCourse(
        course_id=int(item["id_cursus"]),
        course_code=required_string(item, "cursus"),
        academic_year=parse_int(item.get("collegejaar")),
        course_name=required_string(item, "cursus_korte_naam"),
        ec=parse_float(item.get("punten")),
        ec_unit=as_optional_string(item.get("punteneenheid")),
        faculty=as_optional_string(item.get("faculteit_naam")),
        category=as_optional_string(item.get("categorie_omschrijving")),
        course_type=as_optional_string(item.get("cursustype_omschrijving")),
        programme_part=as_optional_string(item.get("onderdeel_van")),
    )


def map_exam_opportunity(item: dict[str, Any]) -> ExamOpportunity:
    return ExamOpportunity(
        course_id=int(item["id_cursus"]),
        exam_offering_id=int(item["id_toets_gelegenheid"]),
        test_code=as_optional_string(item.get("toets")),
        test_description=as_optional_string(item.get("toets_omschrijving")),
        test_type_description=as_optional_string(item.get("toetsvorm_omschrijving")),
        block=as_optional_string(item.get("blok")),
        period_description=as_optional_string(item.get("periode_omschrijving")),
        opportunity=parse_int(item.get("gelegenheid")),
        exam_datetime=parse_datetime(item.get("toetsdatum")),
        day=as_optional_string(item.get("dag")),
        start_time=format_time_decimal(item.get("tijd_vanaf")),
        end_time=format_time_decimal(item.get("tijd_tm")),
    )


def map_exam_enrollment(item: dict[str, Any]) -> ExamEnrollment:
    return ExamEnrollment(
        exam_offering_id=int(item["id_toets_gelegenheid"]),
        course_id=int(item["id_cursus"]),
        course_code=required_string(item, "cursus"),
        academic_year=parse_int(item.get("collegejaar")),
        course_name=required_string(item, "cursus_korte_naam"),
        programme_part=as_optional_string(item.get("onderdeel_van")),
        test_code=as_optional_string(item.get("toets")),
        test_description=as_optional_string(item.get("toets_omschrijving")),
        block=as_optional_string(item.get("blok")),
        period_description=as_optional_string(item.get("periode_omschrijving")),
        opportunity=parse_int(item.get("gelegenheid")),
        exam_datetime=parse_datetime(item.get("toetsdatum")),
        day=as_optional_string(item.get("dag")),
        start_time=format_time_decimal(item.get("tijd_vanaf")),
        end_time=format_time_decimal(item.get("tijd_tm")),
        can_unenroll=parse_bool_jn(item.get("mag_uitschrijven")),
        is_new=parse_bool_jn(item.get("nieuw")),
        result=as_optional_string(item.get("resultaat")),
        is_historical=parse_bool_jn(item.get("historie")),
    )


def build_exam_enrollment_payload(raw_exam: dict[str, Any]) -> dict[str, Any]:
    exam = dict(raw_exam)
    exam["voorzieningen"] = exam.get("voorzieningen", [])
    exam["renderIndex"] = 0

    if exam.get("tijd_vanaf") is not None:
        exam["tijd_vanaf"] = format_time_decimal(exam["tijd_vanaf"])
    if exam.get("tijd_tm") is not None:
        exam["tijd_tm"] = format_time_decimal(exam["tijd_tm"])

    return {"toetsen": [exam]}
