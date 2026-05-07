from flask import Blueprint, render_template, redirect, url_for, flash, Response
from database.db import get_db
from database.models import Exam, ExamAssignment, Score, Question
from modules.scorer import score_assignment, get_exam_statistics, export_results_csv

results_bp = Blueprint("results", __name__)


@results_bp.route("/exams/<int:exam_id>/results")
def exam_results(exam_id):
    db = get_db()
    try:
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            flash("Exam not found.", "danger")
            return redirect(url_for("exams.list_exams"))

        stats = get_exam_statistics(db, exam_id)
        results = []
        for assignment in sorted(exam.assignments, key=lambda a: a.student.student_number):
            result = score_assignment(db, assignment.id)
            results.append({
                "assignment": assignment,
                "student": assignment.student,
                "result": result,
            })

        return render_template(
            "results/list.html",
            exam=exam,
            results=results,
            stats=stats,
        )
    finally:
        db.close()


@results_bp.route("/assignments/<int:assignment_id>/results")
def assignment_results(assignment_id):
    db = get_db()
    try:
        assignment = db.query(ExamAssignment).filter(ExamAssignment.id == assignment_id).first()
        if not assignment:
            flash("Assignment not found.", "danger")
            return redirect(url_for("exams.list_exams"))

        result = score_assignment(db, assignment_id)
        exam = assignment.exam

        # Build detailed per-question view
        detailed = []
        for group in sorted(exam.groups, key=lambda g: g.id):
            group_detail = {"group": group, "questions": []}
            for question in sorted(group.questions, key=lambda q: q.question_number):
                score_rec = (
                    db.query(Score)
                    .filter(Score.assignment_id == assignment_id, Score.question_id == question.id)
                    .first()
                )
                is_correct = False
                is_ambiguous = False
                if score_rec:
                    if group.question_type in ("multiple_choice", "modified_true_false"):
                        if question.correct_answer and score_rec.detected_answer:
                            is_correct = (
                                str(score_rec.detected_answer).strip().lower()
                                == str(question.correct_answer).strip().lower()
                            )
                        elif not score_rec.detected_answer:
                            is_ambiguous = True
                    else:
                        is_correct = score_rec.points_awarded > 0

                group_detail["questions"].append({
                    "question": question,
                    "score": score_rec,
                    "is_correct": is_correct,
                    "is_ambiguous": is_ambiguous,
                })
            detailed.append(group_detail)

        return render_template(
            "results/detail.html",
            assignment=assignment,
            student=assignment.student,
            exam=exam,
            result=result,
            detailed=detailed,
        )
    finally:
        db.close()


@results_bp.route("/exams/<int:exam_id>/results/export")
def export_csv(exam_id):
    db = get_db()
    try:
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            flash("Exam not found.", "danger")
            return redirect(url_for("exams.list_exams"))
        csv_data = export_results_csv(db, exam_id)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=results_{exam_id}.csv"},
        )
    finally:
        db.close()
