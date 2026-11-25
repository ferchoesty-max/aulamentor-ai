from src.core.errors import ApiError
from src.services.access import ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER, assert_course_manager, can_manage_course
from src.services.repos import courses_repo, enrollments_repo, questions_repo

def fetch_course(course_id: str) -> dict:
    course = courses_repo.find_by_id(course_id)
    if course is None:
        raise ApiError("Curso no encontrado", 404, "COURSE_NOT_FOUND")
    return course

def list_courses(user: dict) -> list[dict]:
    role = user["role"]
    if role == ROLE_TEACHER:
        rows = courses_repo.where({"teacher_uid": user["uid"]})
    elif role == ROLE_ADMIN:
        rows = courses_repo.where()
    else:
        rows = courses_repo.where({"status": "active"})
        status_by_course = {e["course_id"]: e.get("status") for e in enrollments_repo.where({"student_uid": user["uid"]})}
        for row in rows:
            row["enrollment_status"] = status_by_course.get(row["id"])
    rows.sort(key=lambda row: row.get("title", "").casefold())
    return rows

def get_course_for_user(user: dict, course_id: str) -> dict:
    course = fetch_course(course_id)
    if can_manage_course(user, course):
        return course
    if user["role"] == ROLE_STUDENT:
        if course.get("status") != "active":
            raise ApiError("Curso no encontrado", 404, "COURSE_NOT_FOUND")
        enrollment = enrollments_repo.find_by_id(f"{course_id}_{user['uid']}")
        course["enrollment_status"] = enrollment.get("status") if enrollment else None
        return course
    assert_course_manager(user, course)
    return course

def create_course(user: dict, payload) -> dict:
    data = payload.model_dump()
    if courses_repo.where({"code": data["code"]}):
        raise ApiError("Ya existe un curso con ese código", 409, "DUPLICATE_CODE")
    return courses_repo.create(
        {
            **data,
            "teacher_uid": user["uid"],
            "teacher_name": user.get("display_name", ""),
            "status": "active",
        }
    )

def update_course(user: dict, course_id: str, payload) -> dict:
    course = fetch_course(course_id)
    assert_course_manager(user, course)
    changes = payload.model_dump(exclude_unset=True)
    if "topics" in changes:
        removed = set(course.get("topics", [])) - set(changes["topics"])
        in_use = {
            q["topic"]
            for q in questions_repo.where({"course_id": course_id})
            if q.get("active", True) and q.get("topic") in removed
        }
        if in_use:
            raise ApiError(
                f"No puedes quitar temas con preguntas activas: {', '.join(sorted(in_use))}",
                409,
                "TOPIC_IN_USE",
            )
    return courses_repo.update(course_id, changes)

def archive_course(user: dict, course_id: str) -> dict:
    course = fetch_course(course_id)
    assert_course_manager(user, course)
    return courses_repo.update(course_id, {"status": "archived"})
