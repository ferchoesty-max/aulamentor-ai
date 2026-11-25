from flask import Blueprint, g
from src.auth.security import require_roles
from src.http.envelope import ok
from src.http.validation import parse_body
from src.schemas.enrollments import EnrollmentCreate
from src.services import enrollment_service
from src.services.access import ROLE_STUDENT, STAFF_ROLES

enrollments_bp = Blueprint("enrollments", __name__, url_prefix="/api/v1")

@enrollments_bp.post("/enrollments")
@require_roles(ROLE_STUDENT)
def create_enrollment():
    payload = parse_body(EnrollmentCreate)
    return ok(enrollment_service.enroll(g.current_user, payload.course_id), 201)

@enrollments_bp.get("/enrollments/my")
@require_roles(ROLE_STUDENT)
def my_enrollments():
    return ok(enrollment_service.list_my_enrollments(g.current_user))

@enrollments_bp.get("/courses/<course_id>/enrollments")
@require_roles(*STAFF_ROLES)
def course_enrollments(course_id: str):
    return ok(enrollment_service.list_course_enrollments(g.current_user, course_id))
