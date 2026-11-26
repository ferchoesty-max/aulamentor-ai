import os

from src.firebase.client import is_emulator_mode, sanitize_emulator_env
from src.services.adaptive_service import compute_topic_mastery, process_attempt_adaptation
from tests.mentor_support import ADMIN, STUDENT, TEACHER, course, db


def _course_doc_and_questions(db, course_id: str):
    course_doc = db.collection("courses").document(course_id).get().to_dict()
    course_doc["id"] = course_id
    questions = [
        {"id": qid, **data}
        for qid, data in db.dump("questions").items()
        if data.get("course_id") == course_id
    ]
    return course_doc, questions


def _enroll(db, course_id: str, student_uid: str, status: str = "enrolled"):
    db.collection("enrollments").document(f"{course_id}_{student_uid}").set(
        {
            "course_id": course_id,
            "student_uid": student_uid,
            "student_name": student_uid,
            "status": status,
        }
    )


def test_adaptive_differentiates_two_students(client, course, db):
    course_doc, questions = _course_doc_and_questions(db, course["id"])
    by_topic_diff = {(q["topic"], q["difficulty"]): q for q in questions}

    _enroll(db, course["id"], "student-1")
    _enroll(db, course["id"], "student-2")

    # Alumno 1: domina Arreglos y Listas (todo bien) y falla Árboles Binarios (todo mal)
    attempt_1 = {
        "id": "attempt-s1",
        "course_id": course["id"],
        "student_uid": "student-1",
        "attempt_number": 1,
        "answers": [
            {"question_id": by_topic_diff[("Arreglos y Listas", 1)]["id"], "selected_index": 1},
            {"question_id": by_topic_diff[("Arreglos y Listas", 3)]["id"], "selected_index": 1},
            {"question_id": by_topic_diff[("Árboles Binarios", 1)]["id"], "selected_index": 0},
            {"question_id": by_topic_diff[("Árboles Binarios", 3)]["id"], "selected_index": 0},
        ],
    }
    # Alumno 2: falla Arreglos y Listas (todo mal) y domina Árboles Binarios (todo bien)
    attempt_2 = {
        "id": "attempt-s2",
        "course_id": course["id"],
        "student_uid": "student-2",
        "attempt_number": 1,
        "answers": [
            {"question_id": by_topic_diff[("Arreglos y Listas", 1)]["id"], "selected_index": 0},
            {"question_id": by_topic_diff[("Arreglos y Listas", 3)]["id"], "selected_index": 0},
            {"question_id": by_topic_diff[("Árboles Binarios", 1)]["id"], "selected_index": 1},
            {"question_id": by_topic_diff[("Árboles Binarios", 3)]["id"], "selected_index": 1},
        ],
    }

    res_1 = process_attempt_adaptation(course_doc, attempt_1, course_questions=questions)
    res_2 = process_attempt_adaptation(course_doc, attempt_2, course_questions=questions)

    p1 = {p["topic"]: p for p in res_1["mastery_profiles"]}
    p2 = {p["topic"]: p for p in res_2["mastery_profiles"]}
    assert p1["Arreglos y Listas"]["level"] == "dominado"
    assert p1["Arreglos y Listas"]["mastery_score"] == 100.0
    assert p1["Árboles Binarios"]["level"] == "requiere_refuerzo"
    assert p1["Árboles Binarios"]["mastery_score"] == 0.0

    assert p2["Arreglos y Listas"]["level"] == "requiere_refuerzo"
    assert p2["Árboles Binarios"]["level"] == "dominado"

    r1 = {r["topic"]: r for r in res_1["recommendations"]}
    r2 = {r["topic"]: r for r in res_2["recommendations"]}
    assert r1["Arreglos y Listas"]["recommended_level"] == 3
    assert r1["Árboles Binarios"]["recommended_level"] == 1
    assert r2["Arreglos y Listas"]["recommended_level"] == 1
    assert r2["Árboles Binarios"]["recommended_level"] == 3
    assert r1["Árboles Binarios"]["explanation"] != r2["Árboles Binarios"]["explanation"]
    assert "intento #1" in r1["Árboles Binarios"]["explanation"]
    assert "0 de 2" in r1["Árboles Binarios"]["explanation"]

    assert len(db.dump("masteryProfiles")) == 4
    assert len(db.dump("recommendations")) == 4
    assert all(rec["status"] == "pending" for rec in db.dump("recommendations").values())


def test_difficulty_weighting_and_attempt_consistency_upsert(client, course, db):
    # Nivel 3 (peso 2.0) vale más que nivel 1 (peso 1.0)
    score_hard_ok, level_hard_ok, rec_hard = compute_topic_mastery(2.0, 3.0, 1)
    score_easy_ok, level_easy_ok, rec_easy = compute_topic_mastery(1.0, 3.0, 1)
    assert score_hard_ok == 66.67 and level_hard_ok == "en_progreso" and rec_hard == 2
    assert score_easy_ok == 33.33 and level_easy_ok == "requiere_refuerzo" and rec_easy == 1
    assert score_hard_ok > score_easy_ok

    course_doc, questions = _course_doc_and_questions(db, course["id"])
    by_topic_diff = {(q["topic"], q["difficulty"]): q for q in questions}

    # Repetir intentos del mismo alumno actualiza el mismo documento de masteryProfiles
    for idx in range(1, 4):
        result = process_attempt_adaptation(
            course_doc,
            {
                "id": f"att-{idx}",
                "course_id": course["id"],
                "student_uid": "mock-student-uid",
                "answers": {
                    by_topic_diff[("Arreglos y Listas", 1)]["id"]: 1,
                    by_topic_diff[("Arreglos y Listas", 3)]["id"]: 1,
                },
            },
            course_questions=questions,
        )
        assert result["mastery_profiles"][0]["total_attempts"] == idx

    stored_profiles = list(db.dump("masteryProfiles").values())
    assert len(stored_profiles) == 1
    assert stored_profiles[0]["total_attempts"] == 3
    # Intento 3 -> factor de consistencia 0.7 -> 70 + 0.7*30 = 91.0
    assert stored_profiles[0]["mastery_score"] == 91.0

    # Fallback con topic_breakdown cuando no vienen respuestas por pregunta
    breakdown_res = process_attempt_adaptation(
        course_doc,
        {
            "id": "att-breakdown",
            "course_id": course["id"],
            "student_uid": "student-breakdown",
            "attempt_number": 1,
            "topic_breakdown": {"Árboles Binarios": {"correct": 1, "total": 2, "difficulty": 2}},
        },
        course_questions=questions,
    )
    assert breakdown_res["mastery_profiles"][0]["mastery_score"] == 50.0
    assert breakdown_res["recommendations"][0]["recommended_level"] == 1


def test_mastery_and_recommendations_endpoints_role_permissions(client, course, db):
    # Sin token -> 401
    assert client.get(f"/api/v1/mastery/{course['id']}").status_code == 401

    # Estudiante no inscrito -> 403 NOT_ENROLLED
    denied = client.get(f"/api/v1/mastery/{course['id']}", headers=STUDENT)
    assert denied.status_code == 403
    assert denied.get_json()["error"]["code"] == "NOT_ENROLLED"

    course_doc, questions = _course_doc_and_questions(db, course["id"])
    _enroll(db, course["id"], "mock-student-uid")
    _enroll(db, course["id"], "otro-estudiante")

    for uid in ("mock-student-uid", "otro-estudiante"):
        process_attempt_adaptation(
            course_doc,
            {
                "id": f"att-{uid}",
                "course_id": course["id"],
                "student_uid": uid,
                "attempt_number": 1,
                "graded_items": [
                    {"topic": "Arreglos y Listas", "difficulty": 1, "is_correct": uid == "mock-student-uid"},
                    {"topic": "Árboles Binarios", "difficulty": 3, "is_correct": False},
                ],
            },
            course_questions=questions,
        )

    # Estudiante inscrito solo ve los suyos
    own_mastery = client.get(f"/api/v1/mastery/{course['id']}", headers=STUDENT)
    assert own_mastery.status_code == 200
    assert len(own_mastery.get_json()["data"]) == 2
    assert all(row["student_uid"] == "mock-student-uid" for row in own_mastery.get_json()["data"])

    # No puede consultar otro student_uid
    assert client.get(f"/api/v1/mastery/{course['id']}?student_uid=otro-estudiante", headers=STUDENT).status_code == 403
    assert client.get("/api/v1/recommendations?student_uid=otro-estudiante", headers=STUDENT).status_code == 403
    assert client.get("/api/v1/recommendations?status=invalido", headers=STUDENT).status_code == 422

    own_recs = client.get("/api/v1/recommendations?status=pending", headers=STUDENT)
    assert own_recs.status_code == 200
    assert len(own_recs.get_json()["data"]) == 2
    assert all(row["student_uid"] == "mock-student-uid" for row in own_recs.get_json()["data"])

    # Docente dueño ve todos los del curso; otro curso ajeno devuelve 403
    teacher_mastery = client.get(f"/api/v1/mastery/{course['id']}", headers=TEACHER)
    assert teacher_mastery.status_code == 200
    assert len(teacher_mastery.get_json()["data"]) == 4

    teacher_recs = client.get(f"/api/v1/recommendations?course_id={course['id']}", headers=TEACHER)
    assert teacher_recs.status_code == 200
    assert len(teacher_recs.get_json()["data"]) == 4

    db.collection("courses").document("curso-ajeno").set(
        {"title": "Ajeno", "code": "AJ-2", "teacher_uid": "otro-docente", "status": "active", "topics": ["Tema Z"]}
    )
    assert client.get("/api/v1/mastery/curso-ajeno", headers=TEACHER).status_code == 403
    assert client.get("/api/v1/recommendations?course_id=curso-ajeno", headers=TEACHER).status_code == 403
    assert client.get("/api/v1/mastery/curso-ajeno", headers=ADMIN).status_code == 200


def test_recommendation_status_transitions_and_permissions(client, course, db):
    course_doc, questions = _course_doc_and_questions(db, course["id"])
    _enroll(db, course["id"], "mock-student-uid")
    _enroll(db, course["id"], "otro-estudiante")

    own_out = process_attempt_adaptation(
        course_doc,
        {
            "id": "att-own",
            "course_id": course["id"],
            "student_uid": "mock-student-uid",
            "attempt_number": 1,
        },
        graded_items=[{"topic": "Arreglos y Listas", "difficulty": 1, "is_correct": False}],
        course_questions=questions,
    )
    other_out = process_attempt_adaptation(
        course_doc,
        {
            "id": "att-other",
            "course_id": course["id"],
            "student_uid": "otro-estudiante",
            "attempt_number": 1,
        },
        graded_items=[{"topic": "Arreglos y Listas", "difficulty": 1, "is_correct": False}],
        course_questions=questions,
    )
    rec_id = own_out["recommendations"][0]["id"]
    other_rec_id = other_out["recommendations"][0]["id"]

    # Transición inválida pending -> completed -> 409
    bad_jump = client.patch(f"/api/v1/recommendations/{rec_id}/status", json={"status": "completed"}, headers=STUDENT)
    assert bad_jump.status_code == 409
    assert bad_jump.get_json()["error"]["code"] == "INVALID_STATUS_TRANSITION"

    # Payloads inválidos -> 422
    assert client.patch(f"/api/v1/recommendations/{rec_id}/status", json={"status": "otro"}, headers=STUDENT).status_code == 422
    assert (
        client.patch(
            f"/api/v1/recommendations/{rec_id}/status",
            json={"status": "in_progress", "extra": 1},
            headers=STUDENT,
        ).status_code
        == 422
    )

    # Transición válida pending -> in_progress por el alumno dueño
    step1 = client.patch(f"/api/v1/recommendations/{rec_id}/status", json={"status": "in_progress"}, headers=STUDENT)
    assert step1.status_code == 200
    assert step1.get_json()["data"]["status"] == "in_progress"

    # Transición válida in_progress -> completed por el docente dueño del curso
    step2 = client.patch(f"/api/v1/recommendations/{rec_id}/status", json={"status": "completed"}, headers=TEACHER)
    assert step2.status_code == 200
    assert step2.get_json()["data"]["status"] == "completed"
    assert db.dump("recommendations")[rec_id]["status"] == "completed"

    # No puede retroceder desde completed
    assert client.patch(f"/api/v1/recommendations/{rec_id}/status", json={"status": "in_progress"}, headers=STUDENT).status_code == 409
    assert client.patch(f"/api/v1/recommendations/{rec_id}/status", json={"status": "pending"}, headers=STUDENT).status_code == 409

    # Otro alumno no puede modificar recomendación ajena y un id inexistente devuelve 404
    assert client.patch(f"/api/v1/recommendations/{other_rec_id}/status", json={"status": "in_progress"}, headers=STUDENT).status_code == 403
    assert client.patch("/api/v1/recommendations/no-existe/status", json={"status": "in_progress"}, headers=STUDENT).status_code == 404

    # Curso ajeno no puede ser modificado por otro docente
    db.collection("courses").document("curso-ajeno").set(
        {"title": "Ajeno", "code": "AJ-3", "teacher_uid": "otro-docente", "status": "active", "topics": ["Tema Z"]}
    )
    db.collection("recommendations").document("rec-ajena").set(
        {"course_id": "curso-ajeno", "student_uid": "otro-estudiante", "status": "pending"}
    )
    assert client.patch("/api/v1/recommendations/rec-ajena/status", json={"status": "in_progress"}, headers=TEACHER).status_code == 403


def test_sanitize_emulator_env_removes_only_blank_values(monkeypatch):
    monkeypatch.setenv("FIREBASE_AUTH_EMULATOR_HOST", "")
    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", "   ")
    sanitize_emulator_env()
    assert "FIREBASE_AUTH_EMULATOR_HOST" not in os.environ
    assert "FIRESTORE_EMULATOR_HOST" not in os.environ
    assert is_emulator_mode() is False

    monkeypatch.setenv("FIREBASE_AUTH_EMULATOR_HOST", "")
    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")
    sanitize_emulator_env()
    assert "FIREBASE_AUTH_EMULATOR_HOST" not in os.environ
    assert os.environ["FIRESTORE_EMULATOR_HOST"] == "127.0.0.1:8080"
    assert is_emulator_mode() is True
