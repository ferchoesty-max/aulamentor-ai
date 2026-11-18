from flask import Blueprint, g
from src.auth.security import require_roles
from src.http.envelope import ok
from src.http.validation import parse_body
from src.schemas.courses import CourseCreate
from src.schemas.questions import QuestionCreate
from src.services import course_service, question_service
from src.services.access import ALL_ROLES, STAFF_ROLES

courses_bp = Blueprint("courses", __name__, url_prefix="/api/v1")

@courses_bp.get("/courses")
@require_roles(*ALL_ROLES)
def list_courses():
    return ok(course_service.list_courses(g.current_user))

@courses_bp.post("/courses")
@require_roles(*STAFF_ROLES)
def create_course():
    payload = parse_body(CourseCreate)
    return ok(course_service.create_course(g.current_user, payload), 201)

@courses_bp.get("/courses/<course_id>")
@require_roles(*ALL_ROLES)
def get_course(course_id: str):
    return ok(course_service.get_course_for_user(g.current_user, course_id))

@courses_bp.get("/courses/<course_id>/questions")
@require_roles(*ALL_ROLES)
def list_questions(course_id: str):
    return ok(question_service.list_questions(g.current_user, course_id))

@courses_bp.post("/courses/<course_id>/questions")
@require_roles(*STAFF_ROLES)
def create_question(course_id: str):
    payload = parse_body(QuestionCreate)
    return ok(question_service.create_question(g.current_user, course_id, payload), 201)
