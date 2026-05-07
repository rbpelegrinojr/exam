"""
Scorer module — computes and exports exam scores.
"""

import csv
import io
from database.models import Score, ExamAssignment, QuestionGroup, Question, Student, Exam


def score_assignment(db, assignment_id):
    """
    Compute total score for an assignment from Score records.
    Returns dict: {total, max_possible, breakdown: [{group_id, group_number, earned, max}]}
    """
    assignment = db.query(ExamAssignment).filter(ExamAssignment.id == assignment_id).first()
    if not assignment:
        return None

    exam = assignment.exam
    breakdown = []
    total_earned = 0.0
    total_max = 0.0

    for group in sorted(exam.groups, key=lambda g: g.id):
        group_max = group.points_per_item * group.num_items
        group_earned = (
            db.query(Score)
            .filter(Score.assignment_id == assignment_id, Score.group_id == group.id)
            .with_entities(Score.points_awarded)
            .all()
        )
        earned = sum(r[0] for r in group_earned if r[0] is not None)
        breakdown.append({
            "group_id": group.id,
            "group_number": group.group_number,
            "question_type": group.question_type,
            "earned": earned,
            "max": group_max,
        })
        total_earned += earned
        total_max += group_max

    return {
        "assignment_id": assignment_id,
        "total": total_earned,
        "max_possible": total_max,
        "breakdown": breakdown,
        "student": assignment.student.to_dict() if assignment.student else None,
    }


def get_exam_statistics(db, exam_id):
    """
    Compute highest, lowest, and average scores for an exam.
    Returns dict: {highest, lowest, average, count, scores: []}
    """
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        return None

    all_scores = []
    for assignment in exam.assignments:
        result = score_assignment(db, assignment.id)
        if result:
            all_scores.append(result["total"])

    if not all_scores:
        return {"highest": 0, "lowest": 0, "average": 0, "count": 0, "scores": []}

    return {
        "highest": max(all_scores),
        "lowest": min(all_scores),
        "average": sum(all_scores) / len(all_scores),
        "count": len(all_scores),
        "scores": all_scores,
    }


def export_results_csv(db, exam_id):
    """
    Export all assignment results for an exam as a CSV string.
    """
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        return ""

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    group_headers = [
        f"Part {g.group_number} ({g.question_type})"
        for g in sorted(exam.groups, key=lambda g: g.id)
    ]
    writer.writerow(
        ["Student Number", "Full Name", "Section", "Paper ID"] + group_headers + ["Total Score", "Max Score"]
    )

    for assignment in sorted(exam.assignments, key=lambda a: a.student.student_number):
        result = score_assignment(db, assignment.id)
        if not result:
            continue
        student = assignment.student
        group_scores = [b["earned"] for b in result["breakdown"]]
        writer.writerow(
            [
                student.student_number,
                student.full_name,
                student.section,
                assignment.unique_paper_id,
            ]
            + group_scores
            + [result["total"], result["max_possible"]]
        )

    return output.getvalue()
