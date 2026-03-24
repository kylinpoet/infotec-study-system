from collections.abc import Iterable


def _normalize(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        return [str(item).strip() for item in value]
    return value


def grade_answers(questions, submitted_answers):
    answers_map = {answer.question_key: answer.value for answer in submitted_answers}
    results = []
    total_score = 0.0
    correct_count = 0

    for question in questions:
        expected = _normalize(question.correct_answer)
        actual = _normalize(answers_map.get(question.key))
        is_correct = actual == expected
        if question.type == "hotspot" and isinstance(actual, str) and isinstance(expected, str):
            is_correct = expected.lower() in actual.lower()

        score = float(question.points if is_correct else 0)
        if is_correct:
            total_score += score
            correct_count += 1

        results.append(
            {
                "question_key": question.key,
                "answer": {"value": actual},
                "is_correct": is_correct,
                "score": score,
                "feedback": "回答正确，继续保持。" if is_correct else "还需要结合课堂内容再检查一次。",
            }
        )

    return {
        "answers": results,
        "total_score": total_score,
        "correct_count": correct_count,
    }
