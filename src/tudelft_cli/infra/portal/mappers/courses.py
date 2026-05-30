from __future__ import annotations

from typing import Any

from tudelft_cli.domain.errors import PortalChangedError
from tudelft_cli.domain.models import CourseEnrollment, SuggestedCourse
from tudelft_cli.infra.portal.parsing import (
    as_optional_string,
    parse_bool_jn,
    parse_float,
    optional_float,
    optional_int,
    require_dict_item,
    required_int,
    required_list,
    required_str,
)


def map_suggested_courses_payload(payload: object) -> list[SuggestedCourse]:
    if not isinstance(payload, dict):
        raise PortalChangedError("Suggested courses endpoint returned an unexpected payload shape.")

    items = required_list(payload, "items", "course enrollment suggestions payload")

    return [
        map_suggested_course(require_dict_item(item, "course enrollment suggestion"))
        for item in items
    ]


def map_course_enrollments_payload(payload: object) -> list[CourseEnrollment]:
    if not isinstance(payload, dict):
        raise PortalChangedError("Course enrollments endpoint returned an unexpected payload shape.")

    items = required_list(payload, "items", "course enrollments payload")

    return [map_course_enrollment(require_dict_item(item, "course enrollment")) for item in items]


def map_suggested_course(item: dict[str, Any]) -> SuggestedCourse:
    academic_year = optional_int(item, "collegejaar", "course enrollment suggestion")
    optional_float(item, "punten", "course enrollment suggestion")

    return SuggestedCourse(
        course_offering_id=required_int(item, "id_cursus_blok", "course enrollment suggestion"),
        course_id=required_int(item, "id_cursus", "course enrollment suggestion"),
        course_code=required_str(item, "cursus", "course enrollment suggestion"),
        academic_year=str(academic_year) if academic_year is not None else None,
        block=as_optional_string(item.get("blok")),
        period_description=as_optional_string(item.get("periode_omschrijving")),
        period_date_range=None,
        course_name=required_str(item, "cursus_korte_naam", "course enrollment suggestion"),
        faculty=as_optional_string(item.get("faculteit_naam")),
        category=as_optional_string(item.get("categorie_omschrijving")),
        ec=as_optional_string(item.get("punten")),
        ec_unit=as_optional_string(item.get("punteneenheid")),
        availability=True,
        waiting_list=None,
        coordinating_unit=as_optional_string(item.get("coordinerend_onderdeel_oms")),
        course_type=as_optional_string(item.get("cursustype_omschrijving")),
        teaching_form_description=as_optional_string(item.get("onderwijsvorm_omschrijving")),
        course_note=as_optional_string(item.get("opmerking_cursus")),
        course_block_note=as_optional_string(item.get("opmerking_cursus_blok")),
        programme_part=as_optional_string(item.get("onderdeel_van")),
    )


def map_course_enrollment(item: dict[str, Any]) -> CourseEnrollment:
    return CourseEnrollment(
        course_offering_id=required_int(item, "id_cursus_blok", "course enrollment"),
        course_id=required_int(item, "id_cursus", "course enrollment"),
        course_code=required_str(item, "cursus", "course enrollment"),
        academic_year=optional_int(item, "collegejaar", "course enrollment"),
        block=as_optional_string(item.get("blok")),
        period_description=as_optional_string(item.get("periode_omschrijving")),
        period_date_range=as_optional_string(item.get("periode_start_einddatum")),
        course_name=required_str(item, "cursus_korte_naam", "course enrollment"),
        ec=optional_float(item, "punten", "course enrollment"),
        ec_unit=as_optional_string(item.get("punteneenheid")),
        programme_part=as_optional_string(item.get("onderdeel_van")),
        can_unenroll=parse_bool_jn(item.get("mag_uitschrijven")),
        is_new=parse_bool_jn(item.get("nieuw")),
        is_historical=parse_bool_jn(item.get("historie")),
    )


def build_course_enrollment_payload(course: SuggestedCourse) -> dict[str, Any]:
    return {
        "toets_voorzieningen": [],
        "toetsen": [],
        "werkvorm_groepen": [],
        "werkvormgroepen_per_werkvorm": [],
        "werkvormen": [],
        "werkvormen_niet_beschikbaar": [],
        "werkvorm_voorzieningen": [],
        "blokken": [],
        "blokken_nested": [],
        "kosten": [],
        "voertalen": [{"voertaal_omschrijving": "Engels"}],
        "voorkeuren": [],
        "inschrijfperiodes": [],
        "enrollment_type": "regular",
        "infolinks": [],
        "id_cursus_blok": course.course_offering_id,
        "id_cursus": course.course_id,
        "studentnummer": "",
        "cursus": course.course_code,
        "collegejaar": int(course.academic_year) if course.academic_year else None,
        "blok": course.block or "",
        "periode_omschrijving": course.period_description or "",
        "periode_start_einddatum": course.period_date_range or "",
        "cursus_korte_naam": course.course_name,
        "opmerking_cursus": course.course_note or "",
        "opmerking_cursus_blok": course.course_block_note or "",
        "onderwijsvorm_omschrijving": course.teaching_form_description or "",
        "punten": parse_float(course.ec) or 0,
        "punteneenheid": course.ec_unit or "",
        "coordinerend_onderdeel_oms": course.coordinating_unit or "",
        "faculteit_naam": course.faculty or "",
        "categorie_omschrijving": course.category or "",
        "cursustype_omschrijving": course.course_type or "Cursus",
        "timeslots": "",
        "min_voorkeursgroepen": 0,
        "max_voorkeursgroepen": 0,
        "wachtlijst": "N",
        "locatie": "",
        "onderdeel_van": course.programme_part or "",
        "toelatingsproces": "N",
        "is_in_enrollment_period": False,
        "vol_geen_wachtlijst": False,
    }
