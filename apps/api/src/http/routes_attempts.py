from flask import Blueprint, g, request
from src.auth.security import require_roles
from src.http.envelope import ok
from src.http.validation import parse_body
from src.schemas.attempts import AttemptCreate
from src.services import attempt_service
from src.services.access import ALL_ROLES, ROLE_STUDENT

attempts_bp = Blueprint("attempts", __name__, url_prefix="/api/v1")

@attempts_bp.post("/attempts")
@require_roles(ROLE_STUDENT)
def create_attempt():
    payload = parse_body(AttemptCreate)
    return ok(attempt_service.submit_attempt(g.current_user, payload), 201)

@attempts_bp.get("/attempts")
@require_roles(*ALL_ROLES)
def list_attempts():
    return ok(
        attempt_service.list_attempts(
            g.current_user,
            course_id=(request.args.get("course_id") or "").strip() or None,
            student_uid=(request.args.get("student_uid") or "").strip() or None,
        )
    )
