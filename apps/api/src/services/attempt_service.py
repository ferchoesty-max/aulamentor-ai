from datetime import datetime, timezone
from src.core.errors import ApiError
from src.services import adaptive_service
from src.services.access import ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER
from src.services.course_service import fetch_course
from src.services.grading import grade_answers
from src.services.repos import attempts_repo, courses_repo, enrollments_repo, questions_repo

def public_attempt(attempt: dict) -> dict:
    return {k: v for k, v in attempt.items() if k != "correct_index"}

def submit_attempt(user: dict, payload) -> dict:
    course_id = payload.course_id
    course = fetch_course(course_id)
    enrollment = enrollments_repo.find_by_id(f"{course_id}_{user['uid']}")
    if enrollment is None or enrollment.get("status") != "enrolled":
        raise ApiError("No estás inscrito en este curso", 403, "NOT_ENROLLED")
    if course.get("status") != "active":
        raise ApiError("El curso está archivado", 409, "COURSE_ARCHIVED")

    answers = [a.model_dump() for a in payload.answers]
    ids = [a["question_id"] for a in answers]
    if len(set(ids)) != len(ids):
        raise ApiError("Hay preguntas respondidas más de una vez", 422, "DUPLICATE_ANSWER")

    questions = [q for q in questions_repo.where({"course_id": course_id}) if q.get("active", True)]
    questions_by_id = {q["id"]: q for q in questions}
    unknown = [qid for qid in ids if qid not in questions_by_id]
    if unknown:
        raise ApiError(
            "Hay preguntas que no pertenecen al examen de este curso",
            422,
            "INVALID_QUESTION",
            {"question_ids": unknown},
        )

    score, graded, breakdown = grade_answers(answers, questions_by_id)
    previous = attempts_repo.where({"course_id": course_id, "student_uid": user["uid"]})
    attempt = attempts_repo.create(
        {
            "course_id": course_id,
            "student_uid": user["uid"],
            "attempt_number": len(previous) + 1,
            "answers": graded,
            "score": score,
            "total_questions": len(graded),
            "correct_count": sum(1 for g in graded if g["is_correct"]),
            "topic_breakdown": breakdown,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    adaptation = adaptive_service.process_attempt_adaptation(
        {**course}, attempt, graded_items=graded, course_questions=questions
    )
    return {
        **public_attempt(attempt),
        "mastery_profiles": adaptation["mastery_profiles"],
        "recommendations": adaptation["recommendations"],
    }

def list_attempts(user: dict, course_id: str | None = None, student_uid: str | None = None) -> list[dict]:
    filters: dict = {}
    if course_id:
        filters["course_id"] = course_id
    role = user["role"]
    if role == ROLE_STUDENT:
        if student_uid and student_uid != user["uid"]:
            raise ApiError("No puedes consultar intentos de otro estudiante", 403, "FORBIDDEN")
        filters["student_uid"] = user["uid"]
        rows = attempts_repo.where(filters)
    else:
        if student_uid:
            filters["student_uid"] = student_uid
        if role == ROLE_TEACHER:
            owned = {c["id"] for c in courses_repo.where({"teacher_uid": user["uid"]})}
            if course_id and course_id not in owned:
                fetch_course(course_id)
                raise ApiError("No eres el docente de este curso", 403, "FORBIDDEN")
            rows = [r for r in attempts_repo.where(filters) if r.get("course_id") in owned]
        elif role == ROLE_ADMIN:
            rows = attempts_repo.where(filters)
        else:
            raise ApiError("Permisos insuficientes para realizar esta accion", 403, "FORBIDDEN")
    rows.sort(key=lambda r: r.get("submitted_at", ""), reverse=True)
    return [public_attempt(r) for r in rows]
