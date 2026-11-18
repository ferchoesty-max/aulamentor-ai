from src.core.errors import ApiError

ROLE_ADMIN = "admin"
ROLE_TEACHER = "teacher"
ROLE_STUDENT = "student"

ALL_ROLES = (ROLE_ADMIN, ROLE_TEACHER, ROLE_STUDENT)
STAFF_ROLES = (ROLE_ADMIN, ROLE_TEACHER)

def can_manage_course(user: dict, course: dict) -> bool:
    """El admin gestiona cualquier curso, el docente solo los suyos."""
    if user.get("role") == ROLE_ADMIN:
        return True
    return user.get("role") == ROLE_TEACHER and course.get("teacher_uid") == user.get("uid")

def assert_course_manager(user: dict, course: dict) -> None:
    if not can_manage_course(user, course):
        raise ApiError("No eres el docente de este curso", 403, "FORBIDDEN")
