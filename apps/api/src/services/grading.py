from src.services.adaptive_service import DIFFICULTY_WEIGHTS

def grade_answers(answers: list[dict], questions_by_id: dict[str, dict]) -> tuple[float, list[dict], list[dict]]:
    graded: list[dict] = []
    topics: dict[str, dict] = {}
    earned = total = 0.0
    for answer in answers:
        question = questions_by_id[answer["question_id"]]
        weight = DIFFICULTY_WEIGHTS.get(question["difficulty"], 1.0)
        is_correct = answer["selected_index"] == question["correct_index"]
        graded.append(
            {
                "question_id": question["id"],
                "topic": question["topic"],
                "difficulty": question["difficulty"],
                "selected_index": answer["selected_index"],
                "is_correct": is_correct,
            }
        )
        bucket = topics.setdefault(
            question["topic"],
            {"topic": question["topic"], "correct": 0, "total": 0, "weighted_correct": 0.0, "weighted_total": 0.0},
        )
        bucket["total"] += 1
        bucket["weighted_total"] += weight
        total += weight
        if is_correct:
            bucket["correct"] += 1
            bucket["weighted_correct"] += weight
            earned += weight

    breakdown = []
    for bucket in topics.values():
        bucket["accuracy"] = round(bucket["correct"] / bucket["total"] * 100, 2)
        bucket["weighted_accuracy"] = round(bucket["weighted_correct"] / bucket["weighted_total"] * 100, 2)
        breakdown.append(bucket)
    score = round(earned / total * 100, 2) if total else 0.0
    return score, graded, breakdown
