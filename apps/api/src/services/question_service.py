from src.core.errors import ApiError
from src.services.access import ROLE_STUDENT, assert_course_manager, can_manage_course
from src.services.course_service import fetch_course
from src.services.repos import enrollments_repo, questions_repo

PUBLIC_QUESTION_FIELDS = ("id", "course_id", "topic", "difficulty", "statement", "options")

def public_question(question: dict) -> dict:
    """Versión para el estudiante: NUNCA incluye correct_index ni reinforcement_activity."""
    return {field: question[field] for field in PUBLIC_QUESTION_FIELDS if field in question}

def sort_questions(course: dict, rows: list[dict]) -> list[dict]:
    order = {topic: index for index, topic in enumerate(course.get("topics", []))}
    rows.sort(key=lambda q: (order.get(q.get("topic"), 999), q.get("difficulty", 0), q["id"]))
    return rows

def assert_topic_in_course(course: dict, topic: str) -> None:
    if topic not in course.get("topics", []):
        valid = ", ".join(course.get("topics", []))
        raise ApiError(f"El tema '{topic}' no pertenece al curso. Temas válidos: {valid}", 422, "INVALID_TOPIC")

def list_questions(user: dict, course_id: str) -> list[dict]:
    course = fetch_course(course_id)
    rows = questions_repo.where({"course_id": course_id})

    if can_manage_course(user, course):
        return sort_questions(course, rows)

    if user["role"] == ROLE_STUDENT:
        enrollment = enrollments_repo.find_by_id(f"{course_id}_{user['uid']}")
        if enrollment is None or enrollment.get("status") != "enrolled":
            raise ApiError("No estás inscrito en este curso", 403, "NOT_ENROLLED")
        if course.get("status") != "active":
            raise ApiError("El curso está archivado", 409, "COURSE_ARCHIVED")
        active = [row for row in rows if row.get("active", True)]
        return [public_question(row) for row in sort_questions(course, active)]

    assert_course_manager(user, course)
    return []

def create_question(user: dict, course_id: str, payload) -> dict:
    course = fetch_course(course_id)
    assert_course_manager(user, course)
    data = payload.model_dump()
    assert_topic_in_course(course, data["topic"])
    return questions_repo.create({**data, "course_id": course_id, "active": True, "created_by": user["uid"]})
