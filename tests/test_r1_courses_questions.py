from tests.mentor_support import ADMIN, STUDENT, TEACHER, TEACHER_UID, course, course_payload, db, question_payload

def test_teacher_lists_only_own_courses(client, course, db):
    rows = client.get("/api/v1/courses", headers=TEACHER).get_json()["data"]
    assert [row["code"] for row in rows] == ["EDA-101"]
    assert rows[0]["teacher_uid"] == TEACHER_UID and rows[0]["status"] == "active"
    # un curso de otro docente no aparece en la lista del docente, pero sí en la del admin
    db.collection("courses").document("ajeno").set({"title": "Ajeno", "code": "AJ-1", "teacher_uid": "otro", "status": "active", "topics": ["Tema X"]})
    assert len(client.get("/api/v1/courses", headers=TEACHER).get_json()["data"]) == 1
    assert len(client.get("/api/v1/courses", headers=ADMIN).get_json()["data"]) == 2

def test_permissions_by_role(client, course, db):
    assert client.post("/api/v1/courses", json=course_payload(code="X-1"), headers=STUDENT).status_code == 403
    denied = client.get(f"/api/v1/courses/{course['id']}/questions", headers=STUDENT)
    assert denied.status_code == 403
    assert denied.get_json()["error"]["code"] == "NOT_ENROLLED"
    assert client.get("/api/v1/courses").status_code == 401
    db.collection("courses").document("ajeno").set({"title": "Ajeno", "code": "AJ-1", "teacher_uid": "otro", "status": "active", "topics": ["Tema X"]})
    assert client.get("/api/v1/courses/ajeno/questions", headers=TEACHER).status_code == 403
    assert client.post("/api/v1/courses/ajeno/questions", json=question_payload(topic="Tema X"), headers=TEACHER).status_code == 403

def test_invalid_course_payloads_return_422(client, db):
    for body in ({}, course_payload(topics=[]), course_payload(title="ab"), course_payload(teacher_uid="hack")):
        response = client.post("/api/v1/courses", json=body, headers=TEACHER)
        assert response.status_code == 422, body
        error = response.get_json()["error"]
        assert response.get_json()["success"] is False and error["code"] == "VALIDATION_ERROR" and error["details"]["fields"]

def test_invalid_questions_return_422_and_valid_one_is_persisted(client, course, db):
    url = f"/api/v1/courses/{course['id']}/questions"
    bad_bodies = (
        question_payload(correct_index=9),
        question_payload(options=["a", "b", "c"]),
        question_payload(options=["a", "A", "c", "d"]),
        question_payload(difficulty=5),
        question_payload(topic="Tema que no existe"),
    )
    for body in bad_bodies:
        assert client.post(url, json=body, headers=TEACHER).status_code == 422, body
    created = client.post(url, json=question_payload(difficulty=2), headers=TEACHER)
    assert created.status_code == 201
    saved = db.dump("questions")[created.get_json()["data"]["id"]]
    assert saved["correct_index"] == 0 and saved["course_id"] == course["id"] and saved["active"] is True

def test_duplicate_course_code_returns_409(client, course):
    response = client.post("/api/v1/courses", json=course_payload(code="EDA-101"), headers=TEACHER)
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "DUPLICATE_CODE"
