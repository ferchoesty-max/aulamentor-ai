from datetime import datetime, timezone
import hashlib
import re
import unicodedata

from src.core.errors import ApiError
from src.services.access import ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER, assert_course_manager, can_manage_course
from src.services.course_service import fetch_course
from src.services.repos import (
    courses_repo,
    enrollments_repo,
    mastery_repo,
    questions_repo,
    recommendations_repo,
)

DIFFICULTY_WEIGHTS = {1: 1.0, 2: 1.5, 3: 2.0}
DIFFICULTY_LABELS = {1: "básica", 2: "media", 3: "alta"}
VALID_RECOMMENDATION_STATUSES = ("pending", "in_progress", "completed")
ALLOWED_STATUS_TRANSITIONS = {
    "pending": {"in_progress"},
    "in_progress": {"completed"},
    "completed": set(),
}


def _attempt_consistency_factor(attempt_number: int) -> float:
    """Premia el dominio en primeros intentos y reduce el bono tras fallos repetidos."""
    if attempt_number <= 1:
        return 1.0
    if attempt_number == 2:
        return 0.9
    return max(0.4, round(1.0 - 0.15 * (attempt_number - 1), 2))


def compute_topic_mastery(earned_weight: float, total_weight: float, attempt_number: int) -> tuple[float, str, int]:
    """Calcula índice de dominio (0..100), nivel y nivel recomendado (1..3) sin IA comercial."""
    weighted_accuracy = (earned_weight / total_weight) if total_weight > 0 else 0.0
    consistency = _attempt_consistency_factor(attempt_number)
    score = round(min(100.0, max(0.0, (weighted_accuracy * 70.0) + (weighted_accuracy * consistency * 30.0))), 2)
    if score < 60:
        return score, "requiere_refuerzo", 1
    if score < 85:
        return score, "en_progreso", 2
    return score, "dominado", 3


def _mastery_doc_id(course_id: str, student_uid: str, topic: str) -> str:
    ascii_topic = unicodedata.normalize("NFKD", topic).encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_topic).strip("-")[:32] or "tema"
    short_hash = hashlib.sha1(topic.encode("utf-8")).hexdigest()[:6]
    return f"{course_id}_{student_uid}_{slug}_{short_hash}"


def _pick_reinforcement_activity(topic: str, recommended_level: int, topic_questions: list[dict]) -> tuple[str, str]:
    candidates = [
        q
        for q in topic_questions
        if isinstance(q.get("reinforcement_activity"), dict)
        and q["reinforcement_activity"].get("title")
        and q["reinforcement_activity"].get("description")
    ]
    if candidates:
        candidates.sort(key=lambda q: (abs(int(q.get("difficulty", 1)) - recommended_level), int(q.get("difficulty", 1))))
        chosen = candidates[0]["reinforcement_activity"]
        return chosen["title"], chosen["description"]

    if recommended_level == 1:
        return (
            f"Refuerzo base de {topic}",
            f"Repasa la guía conceptual de {topic} y resuelve 2 ejercicios guiados antes de subir de nivel.",
        )
    if recommended_level == 2:
        return (
            f"Práctica intermedia de {topic}",
            f"Resuelve ejercicios prácticos de {topic} enfocándote en los casos donde tuviste errores.",
        )
    return (
        f"Reto avanzado de {topic}",
        f"Afronta un reto corto avanzado de {topic} para consolidar tu dominio sin repetir teoría básica.",
    )


def _build_explanation(
    topic: str,
    correct: int,
    total: int,
    raw_pct: float,
    weighted_pct: float,
    difficulties: list[int],
    attempt_number: int,
    score: float,
    level: str,
    recommended_level: int,
) -> str:
    if len(difficulties) == 1:
        diff_text = f"dificultad {DIFFICULTY_LABELS.get(difficulties[0], str(difficulties[0]))}"
    else:
        labels = ", ".join(DIFFICULTY_LABELS.get(d, str(d)) for d in difficulties)
        diff_text = f"dificultades {labels}"

    level_desc = {
        1: ("nivel 1 (básico/conceptual)", "te recomendamos repasar la guía base y resolver ejercicios guiados antes de subir de nivel"),
        2: ("nivel 2 (intermedio/práctico)", "te recomendamos practicar ejercicios intermedios para afianzar los casos donde fallaste"),
        3: ("nivel 3 (avanzado/reto)", "te recomendamos un reto corto avanzado para consolidar tu dominio sin repetir teoría básica"),
    }[recommended_level]

    return (
        f"Obtuviste {correct} de {total} aciertos ({raw_pct:.0f}% simple, {weighted_pct:.0f}% ponderado por dificultad) "
        f"en el tema '{topic}' con preguntas de {diff_text} en tu intento #{attempt_number}. "
        f"Tu dominio calculado es {score}/100 ({level}), por eso se asigna una actividad de {level_desc[0]}: {level_desc[1]}."
    )


def _add_topic_item(stats_by_topic: dict[str, dict], topic: str, difficulty: int, is_correct: bool) -> None:
    weight = DIFFICULTY_WEIGHTS.get(difficulty, 1.0)
    bucket = stats_by_topic.setdefault(
        topic,
        {"correct": 0, "total": 0, "earned_weight": 0.0, "total_weight": 0.0, "difficulties": set()},
    )
    bucket["total"] += 1
    bucket["total_weight"] += weight
    bucket["difficulties"].add(difficulty)
    if is_correct:
        bucket["correct"] += 1
        bucket["earned_weight"] += weight


def _extract_topic_stats(
    attempt: dict,
    questions_by_id: dict[str, dict],
    graded_items: list[dict] | None,
) -> dict[str, dict]:
    stats: dict[str, dict] = {}
    items = graded_items if graded_items is not None else attempt.get("graded_items")

    if items is not None:
        for item in items:
            q = questions_by_id.get(item.get("question_id")) if item.get("question_id") else None
            topic = item.get("topic") or (q.get("topic") if q else None)
            if not topic:
                raise ApiError("Cada reactivo calificado debe indicar su tema", 422, "VALIDATION_ERROR")
            difficulty = int(item.get("difficulty") or (q.get("difficulty") if q else 1))
            is_correct = bool(item["is_correct"] if "is_correct" in item else item.get("correct", False))
            _add_topic_item(stats, topic, difficulty, is_correct)
        return stats

    answers = attempt.get("answers")
    if isinstance(answers, dict):
        for qid, selected in answers.items():
            q = questions_by_id.get(qid)
            if q is None:
                continue
            _add_topic_item(stats, q["topic"], int(q.get("difficulty", 1)), selected == q.get("correct_index"))
        if stats:
            return stats
    elif isinstance(answers, list):
        for entry in answers:
            if not isinstance(entry, dict):
                continue
            q = questions_by_id.get(entry.get("question_id")) if entry.get("question_id") else None
            topic = entry.get("topic") or (q.get("topic") if q else None)
            if not topic:
                continue
            difficulty = int(entry.get("difficulty") or (q.get("difficulty") if q else 1))
            if "is_correct" in entry:
                is_correct = bool(entry["is_correct"])
            elif "correct" in entry:
                is_correct = bool(entry["correct"])
            elif q is not None:
                selected = entry.get("selected_index") if "selected_index" in entry else entry.get("answer_index")
                is_correct = selected == q.get("correct_index")
            else:
                is_correct = False
            _add_topic_item(stats, topic, difficulty, is_correct)
        if stats:
            return stats

    breakdown = attempt.get("topic_breakdown")
    entries = (
        [{"topic": topic, **values} for topic, values in breakdown.items() if isinstance(values, dict)]
        if isinstance(breakdown, dict)
        else (breakdown if isinstance(breakdown, list) else [])
    )
    for entry in entries:
        topic = entry.get("topic")
        if not topic:
            continue
        correct = int(entry.get("correct", 0))
        total = int(entry.get("total", 0))
        difficulty = int(entry.get("difficulty", 1))
        weight = DIFFICULTY_WEIGHTS.get(difficulty, 1.0)
        stats[topic] = {
            "correct": correct,
            "total": total,
            "earned_weight": float(entry.get("weighted_correct", correct * weight)),
            "total_weight": float(entry.get("weighted_total", total * weight)),
            "difficulties": set(entry.get("difficulties") or [difficulty]),
        }
    return stats


def process_attempt_adaptation(
    course: dict,
    attempt: dict,
    graded_items: list[dict] | None = None,
    course_questions: list[dict] | None = None,
) -> dict:
    """Hook principal para actualizar masteryProfiles y generar recomendaciones al calificar un intento."""
    course_id = course["id"]
    student_uid = attempt["student_uid"]
    attempt_id = attempt.get("id", "")
    questions = course_questions if course_questions is not None else questions_repo.where({"course_id": course_id})
    questions_by_id = {q["id"]: q for q in questions if "id" in q}
    questions_by_topic: dict[str, list[dict]] = {}
    for q in questions:
        questions_by_topic.setdefault(q.get("topic", ""), []).append(q)

    stats_by_topic = _extract_topic_stats(attempt, questions_by_id, graded_items)
    if not stats_by_topic:
        return {"mastery_profiles": [], "recommendations": []}

    topic_order = {topic: index for index, topic in enumerate(course.get("topics", []))}
    ordered_topics = sorted(stats_by_topic.keys(), key=lambda t: (topic_order.get(t, 999), t))
    now = datetime.now(timezone.utc).isoformat()

    mastery_profiles = []
    recommendations = []
    for topic in ordered_topics:
        stats = stats_by_topic[topic]
        doc_id = _mastery_doc_id(course_id, student_uid, topic)
        prev = mastery_repo.find_by_id(doc_id)
        attempt_number = (int(prev.get("total_attempts", 0)) + 1) if prev else max(1, int(attempt.get("attempt_number", 1)))

        score, level, recommended_level = compute_topic_mastery(
            stats["earned_weight"],
            stats["total_weight"],
            attempt_number,
        )
        raw_pct = round((stats["correct"] / stats["total"]) * 100, 2) if stats["total"] > 0 else 0.0
        weighted_pct = round((stats["earned_weight"] / stats["total_weight"]) * 100, 2) if stats["total_weight"] > 0 else 0.0

        profile_payload = {
            "course_id": course_id,
            "student_uid": student_uid,
            "topic": topic,
            "mastery_score": score,
            "level": level,
            "total_attempts": attempt_number,
            "accuracy_rate": raw_pct,
            "weighted_accuracy": weighted_pct,
            "last_attempt_id": attempt_id,
            "updated_at": now,
        }
        profile_doc = (
            mastery_repo.update(doc_id, profile_payload)
            if prev is not None
            else mastery_repo.create(profile_payload, doc_id=doc_id)
        )
        mastery_profiles.append(profile_doc)

        activity_title, activity_description = _pick_reinforcement_activity(
            topic,
            recommended_level,
            questions_by_topic.get(topic, []),
        )
        explanation = _build_explanation(
            topic=topic,
            correct=stats["correct"],
            total=stats["total"],
            raw_pct=raw_pct,
            weighted_pct=weighted_pct,
            difficulties=sorted(stats["difficulties"] or {1}),
            attempt_number=attempt_number,
            score=score,
            level=level,
            recommended_level=recommended_level,
        )
        rec_doc = recommendations_repo.create(
            {
                "course_id": course_id,
                "student_uid": student_uid,
                "attempt_id": attempt_id,
                "topic": topic,
                "recommended_level": recommended_level,
                "mastery_score": score,
                "mastery_level": level,
                "activity_title": activity_title,
                "activity_description": activity_description,
                "explanation": explanation,
                "status": "pending",
                "created_at": now,
                "updated_at": now,
            }
        )
        recommendations.append(rec_doc)

    return {"mastery_profiles": mastery_profiles, "recommendations": recommendations}


def get_course_mastery(user: dict, course_id: str, student_uid: str | None = None) -> list[dict]:
    course = fetch_course(course_id)
    student_uid = (student_uid or "").strip() or None

    if user["role"] == ROLE_STUDENT:
        if student_uid and student_uid != user["uid"]:
            raise ApiError("No puedes consultar el dominio de otro estudiante", 403, "FORBIDDEN")
        enrollment = enrollments_repo.find_by_id(f"{course_id}_{user['uid']}")
        if enrollment is None or enrollment.get("status") not in ("enrolled", "completed"):
            raise ApiError("No estás inscrito en este curso", 403, "NOT_ENROLLED")
        rows = mastery_repo.where({"course_id": course_id, "student_uid": user["uid"]})
    elif can_manage_course(user, course):
        filters = {"course_id": course_id}
        if student_uid:
            filters["student_uid"] = student_uid
        rows = mastery_repo.where(filters)
    else:
        assert_course_manager(user, course)
        rows = []

    topic_order = {topic: index for index, topic in enumerate(course.get("topics", []))}
    rows.sort(key=lambda row: (row.get("student_uid", ""), topic_order.get(row.get("topic"), 999), row.get("topic", "")))
    return rows


def list_recommendations(
    user: dict,
    course_id: str | None = None,
    status: str | None = None,
    student_uid: str | None = None,
) -> list[dict]:
    course_id = (course_id or "").strip() or None
    status = (status or "").strip() or None
    student_uid = (student_uid or "").strip() or None

    if status and status not in VALID_RECOMMENDATION_STATUSES:
        valid = ", ".join(VALID_RECOMMENDATION_STATUSES)
        raise ApiError(f"Estado inválido '{status}'. Valores permitidos: {valid}", 422, "VALIDATION_ERROR")

    filters: dict[str, str] = {}
    if status:
        filters["status"] = status

    if user["role"] == ROLE_STUDENT:
        if student_uid and student_uid != user["uid"]:
            raise ApiError("No puedes consultar recomendaciones de otro estudiante", 403, "FORBIDDEN")
        filters["student_uid"] = user["uid"]
        if course_id:
            filters["course_id"] = course_id
        rows = recommendations_repo.where(filters)
    elif user["role"] == ROLE_TEACHER:
        if student_uid:
            filters["student_uid"] = student_uid
        if course_id:
            course = fetch_course(course_id)
            assert_course_manager(user, course)
            filters["course_id"] = course_id
            rows = recommendations_repo.where(filters)
        else:
            owned_ids = {course["id"] for course in courses_repo.where({"teacher_uid": user["uid"]})}
            if not owned_ids:
                return []
            # ponytail: FakeFirestore y Firestore sin índice compuesto filtran en Python por conjunto de cursos
            rows = [row for row in recommendations_repo.where(filters) if row.get("course_id") in owned_ids]
    elif user["role"] == ROLE_ADMIN:
        if course_id:
            filters["course_id"] = course_id
        if student_uid:
            filters["student_uid"] = student_uid
        rows = recommendations_repo.where(filters)
    else:
        raise ApiError("Permisos insuficientes para realizar esta accion", 403, "FORBIDDEN")

    rows.sort(key=lambda row: row.get("created_at", ""), reverse=True)
    return rows


def update_recommendation_status(user: dict, recommendation_id: str, new_status: str) -> dict:
    rec = recommendations_repo.find_by_id(recommendation_id)
    if rec is None:
        raise ApiError("Recomendación no encontrada", 404, "RECOMMENDATION_NOT_FOUND")

    is_admin = user["role"] == ROLE_ADMIN
    is_owner_student = user["role"] == ROLE_STUDENT and rec.get("student_uid") == user["uid"]
    is_course_teacher = False
    if user["role"] == ROLE_TEACHER and rec.get("course_id"):
        course = courses_repo.find_by_id(rec["course_id"])
        is_course_teacher = bool(course and can_manage_course(user, course))

    if not (is_admin or is_owner_student or is_course_teacher):
        raise ApiError("No tienes permiso para actualizar esta recomendación", 403, "FORBIDDEN")

    current = rec.get("status", "pending")
    if new_status not in ALLOWED_STATUS_TRANSITIONS.get(current, set()):
        raise ApiError(
            f"Transición de estado inválida: '{current}' -> '{new_status}'",
            409,
            "INVALID_STATUS_TRANSITION",
        )

    return recommendations_repo.update(
        recommendation_id,
        {"status": new_status, "status_updated_by": user["uid"]},
    )
