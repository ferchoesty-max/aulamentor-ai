from tests.mentor_support import ADMIN, STUDENT, TEACHER, course, course_payload, db, question_payload

def _enroll(client, course_id, headers=STUDENT):
    return client.post("/api/v1/enrollments", json={"course_id": course_id}, headers=headers)

def _exam(client, course_id):
    return client.get(f"/api/v1/courses/{course_id}/questions", headers=STUDENT).get_json()["data"]

def test_r2_permissions_by_role(client, course, db):
    cid = course["id"]
    # sin token
    assert client.get("/api/v1/enrollments/my").status_code == 401
    # solo estudiantes se inscriben y rinden intentos
    assert _enroll(client, cid, TEACHER).status_code == 403
    assert client.post("/api/v1/attempts", json={"course_id": cid, "answers": []}, headers=TEACHER).status_code == 403
    # solo maestros dueños y admins editan/dan de baja cursos y preguntas
    assert client.patch(f"/api/v1/courses/{cid}", json={"title": "Nuevo título"}, headers=STUDENT).status_code == 403
    assert client.delete(f"/api/v1/courses/{cid}", headers=STUDENT).status_code == 403
    # un docente ajeno no puede editar el curso
    db.collection("courses").document("ajeno").set(
        {"title": "Ajeno", "code": "AJ-1", "teacher_uid": "otro", "status": "active", "topics": ["Tema X"]}
    )
    assert client.patch("/api/v1/courses/ajeno", json={"title": "Hackeado"}, headers=TEACHER).status_code == 403
    # el admin sí puede
    assert client.patch("/api/v1/courses/ajeno", json={"title": "Editado"}, headers=ADMIN).status_code == 200

def test_r2_invalid_data_rejected(client, course):
    cid = course["id"]
    # inscripción: falta course_id / campo extra
    assert client.post("/api/v1/enrollments", json={}, headers=STUDENT).status_code == 422
    assert client.post("/api/v1/enrollments", json={"course_id": cid, "x": 1}, headers=STUDENT).status_code == 422
    assert _enroll(client, "no-existe").status_code == 404
    # PATCH vacío o con tipos inválidos
    assert client.patch(f"/api/v1/courses/{cid}", json={}, headers=TEACHER).status_code == 422
    bad = client.patch(f"/api/v1/courses/{cid}", json={"topics": ["A", "a"]}, headers=TEACHER)
    assert bad.status_code == 422 and bad.get_json()["error"]["code"] == "VALIDATION_ERROR"
    # intento: respuesta fuera de rango, pregunta inventada y sin inscripción
    assert client.post("/api/v1/attempts", json={"course_id": cid, "answers": []}, headers=STUDENT).status_code == 422
    assert _enroll(client, cid).status_code == 201
    out = client.post("/api/v1/attempts", json={"course_id": cid, "answers": [{"question_id": "q1", "selected_index": 9}]}, headers=STUDENT)
    assert out.status_code == 422
    fake = client.post("/api/v1/attempts", json={"course_id": cid, "answers": [{"question_id": "q1", "selected_index": 1}]}, headers=STUDENT)
    assert fake.status_code == 422 and fake.get_json()["error"]["code"] == "INVALID_QUESTION"

def test_r2_course_and_enrollment_creation(client, db):
    created = client.post("/api/v1/courses", json=course_payload(code="bd-201", title="Bases de Datos"), headers=TEACHER)
    assert created.status_code == 201
    cid = created.get_json()["data"]["id"]

    enrolled = _enroll(client, cid)
    assert enrolled.status_code == 201
    data = enrolled.get_json()["data"]
    assert data["id"] == f"{cid}_mock-student-uid" and data["status"] == "enrolled"
    # duplicada -> 409
    again = _enroll(client, cid)
    assert again.status_code == 409 and again.get_json()["error"]["code"] == "ALREADY_ENROLLED"

    mine = client.get("/api/v1/enrollments/my", headers=STUDENT).get_json()["data"]
    assert [m["course_id"] for m in mine] == [cid] and mine[0]["course_title"] == "Bases de Datos"
    roster = client.get(f"/api/v1/courses/{cid}/enrollments", headers=TEACHER).get_json()["data"]
    assert len(roster) == 1

def test_attempt_grading_hides_answers_and_feeds_engine(client, course, db):
    cid = course["id"]
    assert _enroll(client, cid).status_code == 201
    exam = _exam(client, cid)
    assert len(exam) == 4 and all("correct_index" not in q for q in exam)

    # correct_index real = 1: acierta todo lo de "Arreglos y Listas", falla "Árboles Binarios"
    answers = [{"question_id": q["id"], "selected_index": 1 if q["topic"] == "Arreglos y Listas" else 0} for q in exam]
    res = client.post("/api/v1/attempts", json={"course_id": cid, "answers": answers}, headers=STUDENT)
    assert res.status_code == 201
    body = res.get_json()["data"]
    assert body["score"] == 50.0 and body["attempt_number"] == 1 and body["correct_count"] == 2
    assert all("correct_index" not in a for a in body["answers"])
    by_topic = {t["topic"]: t for t in body["topic_breakdown"]}
    assert by_topic["Arreglos y Listas"]["accuracy"] == 100.0 and by_topic["Árboles Binarios"]["accuracy"] == 0.0
    levels = {p["topic"]: p["level"] for p in body["mastery_profiles"]}
    assert levels == {"Arreglos y Listas": "dominado", "Árboles Binarios": "requiere_refuerzo"}
    assert len(body["recommendations"]) == 2 and len(db.dump("attempts")) == 1

    # historial: el alumno ve solo lo suyo, el segundo intento incrementa attempt_number
    client.post("/api/v1/attempts", json={"course_id": cid, "answers": answers}, headers=STUDENT)
    mine = client.get(f"/api/v1/attempts?course_id={cid}", headers=STUDENT).get_json()["data"]
    assert sorted(a["attempt_number"] for a in mine) == [1, 2]
    assert client.get("/api/v1/attempts?student_uid=otro", headers=STUDENT).status_code == 403
    assert len(client.get(f"/api/v1/attempts?course_id={cid}", headers=TEACHER).get_json()["data"]) == 2

def test_attempt_requires_enrolled_status(client, course, db):
    cid = course["id"]
    exam_blocked = client.post("/api/v1/attempts", json={"course_id": cid, "answers": [{"question_id": "x", "selected_index": 0}]}, headers=STUDENT)
    assert exam_blocked.status_code == 403 and exam_blocked.get_json()["error"]["code"] == "NOT_ENROLLED"
    _enroll(client, cid)
    db.collection("enrollments").document(f"{cid}_mock-student-uid").update({"status": "completed"})
    assert client.post("/api/v1/attempts", json={"course_id": cid, "answers": [{"question_id": "x", "selected_index": 0}]}, headers=STUDENT).status_code == 403

def test_soft_delete_course_and_question_and_update(client, course, db):
    cid = course["id"]
    upd = client.patch(f"/api/v1/courses/{cid}", json={"title": "EDA actualizado", "description": "Nueva"}, headers=TEACHER)
    assert upd.status_code == 200 and upd.get_json()["data"]["title"] == "EDA actualizado"
    # no se puede quitar un tema con preguntas activas
    assert client.patch(f"/api/v1/courses/{cid}", json={"topics": ["Arreglos y Listas"]}, headers=TEACHER).status_code == 409

    qs = client.get(f"/api/v1/courses/{cid}/questions", headers=TEACHER).get_json()["data"]
    qid = qs[0]["id"]
    assert client.patch(f"/api/v1/courses/{cid}/questions/{qid}", json={"statement": "Enunciado corregido"}, headers=TEACHER).get_json()["data"]["statement"] == "Enunciado corregido"
    assert client.patch(f"/api/v1/courses/{cid}/questions/{qid}", json={"topic": "Tema inexistente"}, headers=TEACHER).status_code == 422
    assert client.delete(f"/api/v1/courses/{cid}/questions/{qid}", headers=TEACHER).get_json()["data"]["active"] is False
    assert qid in db.dump("questions")  # el documento sigue existiendo

    _enroll(client, cid)
    assert qid not in [q["id"] for q in _exam(client, cid)]

    archived = client.delete(f"/api/v1/courses/{cid}", headers=TEACHER)
    assert archived.get_json()["data"]["status"] == "archived" and cid in db.dump("courses")
    assert _enroll(client, cid, {"Authorization": "Bearer mock-student"}).status_code == 409
