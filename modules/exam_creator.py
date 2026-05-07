import json
from datetime import datetime
from database.models import Exam, QuestionGroup, Question


def create_exam(db, title, description=None):
    """Create a new Exam record."""
    exam = Exam(title=title, description=description)
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


def create_question_group(db, exam_id, group_number, question_type, points_per_item, num_items):
    """Create a QuestionGroup and auto-generate Question slots."""
    group = QuestionGroup(
        exam_id=exam_id,
        group_number=group_number,
        question_type=question_type,
        points_per_item=float(points_per_item),
        num_items=int(num_items),
    )
    db.add(group)
    db.flush()  # get group.id without full commit

    for i in range(1, int(num_items) + 1):
        question = Question(
            group_id=group.id,
            question_number=i,
            question_text=None,
            correct_answer=None,
            choices=None,
        )
        db.add(question)

    db.commit()
    db.refresh(group)
    return group


def update_question(db, question_id, question_text=None, correct_answer=None, choices_dict=None):
    """Update a question's text, correct answer, and choices."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return None

    if question_text is not None:
        question.question_text = question_text
    if correct_answer is not None:
        question.correct_answer = correct_answer
    if choices_dict is not None:
        question.choices = json.dumps(choices_dict)

    db.commit()
    db.refresh(question)
    return question


def get_exam_with_groups(db, exam_id):
    """Return an Exam with all its groups and questions eagerly loaded."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        return None
    # Access relationships to ensure they are loaded in this session
    for group in exam.groups:
        _ = group.questions
    return exam


def delete_exam(db, exam_id):
    """Delete an exam and cascade to groups, questions, assignments, scores."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        return False
    db.delete(exam)
    db.commit()
    return True
