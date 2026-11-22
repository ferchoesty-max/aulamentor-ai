from flask import Blueprint, g, request

from src.auth.security import require_roles
from src.http.envelope import ok
from src.http.validation import parse_body
from src.schemas.adaptive import RecommendationStatusUpdate
from src.services import adaptive_service
from src.services.access import ALL_ROLES

adaptive_bp = Blueprint("adaptive", __name__, url_prefix="/api/v1")


@adaptive_bp.get("/mastery/<course_id>")
@require_roles(*ALL_ROLES)
def get_mastery(course_id: str):
    student_uid = request.args.get("student_uid")
    return ok(adaptive_service.get_course_mastery(g.current_user, course_id, student_uid=student_uid))


@adaptive_bp.get("/recommendations")
@require_roles(*ALL_ROLES)
def get_recommendations():
    return ok(
        adaptive_service.list_recommendations(
            g.current_user,
            course_id=request.args.get("course_id"),
            status=request.args.get("status"),
            student_uid=request.args.get("student_uid"),
        )
    )


@adaptive_bp.patch("/recommendations/<recommendation_id>/status")
@require_roles(*ALL_ROLES)
def patch_recommendation_status(recommendation_id: str):
    payload = parse_body(RecommendationStatusUpdate)
    return ok(adaptive_service.update_recommendation_status(g.current_user, recommendation_id, payload.status))
