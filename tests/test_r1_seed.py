from apps.api.scripts.seed_courses import COURSE, seed
from apps.api.src.schemas.questions import QuestionCreate
from tests.mentor_support import STUDENT, TEACHER, TEACHER_UID, db

def test_seed_is_idempotent_and_valid(client, db):
    assert seed(db, TEACHER_UID, "Docente Demo") == {"courses": 1, "questions": 9}
    seed(db, TEACHER_UID, "Docente Demo")
    questions = db.dump("questions")
    assert len(questions) == 9
    for row in questions.values():
        assert row["topic"] in COURSE["topics"]
        QuestionCreate.model_validate({k: row[k] for k in (
            "topic", "difficulty", "statement", "options", "correct_index", "reinforcement_activity")})

    courses = client.get("/api/v1/courses", headers=STUDENT).get_json()["data"]
    assert [c["code"] for c in courses] == ["EDA-101"] and courses[0]["enrollment_status"] is None
    rows = client.get(f"/api/v1/courses/{courses[0]['id']}/questions", headers=TEACHER).get_json()["data"]
    assert [q["difficulty"] for q in rows[:3]] == [1, 2, 3]
