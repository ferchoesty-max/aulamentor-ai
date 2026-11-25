from src.core.errors import ApiError
from src.services.access import assert_course_manager
from src.services.course_service import fetch_course
from src.services.repos import courses_repo, enrollments_repo

def enroll(user: dict, course_id: str) -> dict:
    course = fetch_course(course_id)
    if course.get("status") != "active":
        raise ApiError("El curso está archivado y no admite inscripciones", 409, "COURSE_ARCHIVED")
    enrollment_id = f"{course_id}_{user['uid']}"  # evita duplicados
    if enrollments_repo.find_by_id(enrollment_id) is not None:
        raise ApiError("Ya estás inscrito en este curso", 409, "ALREADY_ENROLLED")
    return enrollments_repo.create(
        {
            "course_id": course_id,
            "student_uid": user["uid"],
            "student_name": user.get("display_name", ""),
            "status": "enrolled",
            "enrolled_at": _now(),
        },
        doc_id=enrollment_id,
    )

def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

def list_my_enrollments(user: dict) -> list[dict]:
    rows = enrollments_repo.where({"student_uid": user["uid"]})
    titles = {}
    for row in rows:
        course = courses_repo.find_by_id(row["course_id"])
        titles[row["course_id"]] = (course or {}).get("title", "")
        row["course_title"] = titles[row["course_id"]]
    rows.sort(key=lambda r: r.get("enrolled_at", ""), reverse=True)
    return rows

def list_course_enrollments(user: dict, course_id: str) -> list[dict]:
    course = fetch_course(course_id)
    assert_course_manager(user, course)
    rows = enrollments_repo.where({"course_id": course_id})
    rows.sort(key=lambda r: r.get("student_name", "").casefold())
    return rows
