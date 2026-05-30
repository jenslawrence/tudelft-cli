from __future__ import annotations

from typing import Any

from tudelft_cli.domain.errors import PortalChangedError
from tudelft_cli.domain.models import ExamEnrollment, ExamOpportunity, SuggestedExamCourse
from tudelft_cli.infra.portal.parsing import (
    as_optional_string,
    format_time_decimal,
    optional_float,
    optional_int,
    parse_bool_jn,
    parse_datetime,
    require_dict_item,
    required_int,
    required_list,
    required_str,
)


def map_suggested_exam_courses_payload(payload: object) -> list[SuggestedExamCourse]:
    if not isinstance(payload, dict):
        raise PortalChangedError("Suggested exams endpoint returned an unexpected payload shape.")

    items = required_list(payload, "items", "exam course suggestions payload")

    return [
        map_suggested_exam_course(require_dict_item(item, "exam course suggestion"))
        for item in items
    ]


def map_exam_enrollments_payload(payload: object) -> list[ExamEnrollment]:
    if not isinstance(payload, dict):
        raise PortalChangedError("Exam enrollments endpoint returned an unexpected payload shape.")

    items = required_list(payload, "items", "exam enrollments payload")

    return [map_exam_enrollment(require_dict_item(item, "exam enrollment")) for item in items]


def map_exam_opportunities_payload(
    payload: object,
) -> tuple[SuggestedExamCourse, list[ExamOpportunity], list[dict[str, Any]]]:
    if not isinstance(payload, dict):
        raise PortalChangedError("Exam opportunities endpoint returned an unexpected payload shape.")

    toetsen = required_list(payload, "toetsen", "exam opportunities payload")

    course = SuggestedExamCourse(
        course_id=required_int(payload, "id_cursus", "exam opportunities payload"),
        course_code=required_str(payload, "cursus", "exam opportunities payload"),
        academic_year=optional_int(payload, "collegejaar", "exam opportunities payload"),
        course_name=required_str(payload, "cursus_korte_naam", "exam opportunities payload"),
        ec=optional_float(payload, "punten", "exam opportunities payload"),
        ec_unit=as_optional_string(payload.get("punteneenheid")),
        faculty=as_optional_string(payload.get("faculteit_naam")),
        category=as_optional_string(payload.get("categorie_omschrijving")),
        course_type=as_optional_string(payload.get("cursustype_omschrijving")),
        programme_part=as_optional_string(payload.get("onderdeel_van")),
    )

    raw_items = [require_dict_item(item, "exam opportunity") for item in toetsen]
    opportunities = [map_exam_opportunity(item) for item in raw_items]
    return course, opportunities, raw_items


def map_suggested_exam_course(item: dict[str, Any]) -> SuggestedExamCourse:
    return SuggestedExamCourse(
        course_id=required_int(item, "id_cursus", "exam course suggestion"),
        course_code=required_str(item, "cursus", "exam course suggestion"),
        academic_year=optional_int(item, "collegejaar", "exam course suggestion"),
        course_name=required_str(item, "cursus_korte_naam", "exam course suggestion"),
        ec=optional_float(item, "punten", "exam course suggestion"),
        ec_unit=as_optional_string(item.get("punteneenheid")),
        faculty=as_optional_string(item.get("faculteit_naam")),
        category=as_optional_string(item.get("categorie_omschrijving")),
        course_type=as_optional_string(item.get("cursustype_omschrijving")),
        programme_part=as_optional_string(item.get("onderdeel_van")),
    )


def map_exam_opportunity(item: dict[str, Any]) -> ExamOpportunity:
    return ExamOpportunity(
        course_id=required_int(item, "id_cursus", "exam opportunity"),
        exam_offering_id=required_int(item, "id_toets_gelegenheid", "exam opportunity"),
        test_code=as_optional_string(item.get("toets")),
        test_description=as_optional_string(item.get("toets_omschrijving")),
        test_type_description=as_optional_string(item.get("toetsvorm_omschrijving")),
        block=as_optional_string(item.get("blok")),
        period_description=as_optional_string(item.get("periode_omschrijving")),
        opportunity=optional_int(item, "gelegenheid", "exam opportunity"),
        exam_datetime=parse_datetime(item.get("toetsdatum")),
        day=as_optional_string(item.get("dag")),
        start_time=format_time_decimal(item.get("tijd_vanaf")),
        end_time=format_time_decimal(item.get("tijd_tm")),
    )


def map_exam_enrollment(item: dict[str, Any]) -> ExamEnrollment:
    return ExamEnrollment(
        exam_offering_id=required_int(item, "id_toets_gelegenheid", "exam enrollment"),
        course_id=required_int(item, "id_cursus", "exam enrollment"),
        course_code=required_str(item, "cursus", "exam enrollment"),
        academic_year=optional_int(item, "collegejaar", "exam enrollment"),
        course_name=required_str(item, "cursus_korte_naam", "exam enrollment"),
        programme_part=as_optional_string(item.get("onderdeel_van")),
        test_code=as_optional_string(item.get("toets")),
        test_description=as_optional_string(item.get("toets_omschrijving")),
        block=as_optional_string(item.get("blok")),
        period_description=as_optional_string(item.get("periode_omschrijving")),
        opportunity=optional_int(item, "gelegenheid", "exam enrollment"),
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
