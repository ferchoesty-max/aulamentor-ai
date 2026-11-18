import pytest
from tests.fake_firestore import FakeFirestore

TEACHER = {"Authorization": "Bearer mock-teacher"}   # uid: mock-teacher-uid
STUDENT = {"Authorization": "Bearer mock-student"}   # uid: mock-student-uid
ADMIN = {"Authorization": "Bearer mock-admin"}       # uid: mock-admin-uid
TEACHER_UID = "mock-teacher-uid"

def course_payload(**overrides) -> dict:
    payload = {
        "title": "Estructuras de Datos y Algoritmos",
        "code": "eda-101",
        "description": "Curso ficticio de prueba",
        "topics": ["Arreglos y Listas", "Árboles Binarios"],
    }
    payload.update(overrides)
    return payload

def question_payload(topic="Arreglos y Listas", difficulty=1, correct_index=0, **overrides) -> dict:
    payload = {
        "topic": topic,
        "difficulty": difficulty,
        "statement": f"Pregunta de {topic} nivel {difficulty}",
        "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
        "correct_index": correct_index,
        "reinforcement_activity": {
            "title": f"Repaso de {topic}",
            "description": "Lee la guía base y resuelve dos ejercicios guiados.",
        },
    }
    payload.update(overrides)
    return payload

@pytest.fixture
def db(monkeypatch):
    fake = FakeFirestore()
    monkeypatch.setattr("src.repositories.base.get_db", lambda: fake)
    return fake

@pytest.fixture
def course(client, db):
    response = client.post("/api/v1/courses", json=course_payload(), headers=TEACHER)
    assert response.status_code == 201, response.get_json()
    course_id = response.get_json()["data"]["id"]
    for topic in ("Arreglos y Listas", "Árboles Binarios"):
        for difficulty in (1, 3):
            created = client.post(
                f"/api/v1/courses/{course_id}/questions",
                json=question_payload(topic=topic, difficulty=difficulty, correct_index=1),
                headers=TEACHER,
            )
            assert created.status_code == 201, created.get_json()
    return {"id": course_id}
