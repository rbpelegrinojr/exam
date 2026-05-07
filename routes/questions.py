import json
from flask import Blueprint, render_template, redirect, url_for, request, flash
from database.db import get_db
from database.models import Exam, QuestionGroup, Question
from modules.exam_creator import create_question_group, update_question, get_exam_with_groups

questions_bp = Blueprint("questions", __name__)

VALID_TYPES = {"multiple_choice", "modified_true_false", "essay", "coding"}


@questions_bp.route("/exams/<int:exam_id>/groups")
def manage_groups(exam_id):
    db = get_db()
    try:
        exam = get_exam_with_groups(db, exam_id)
        if not exam:
            flash("Exam not found.", "danger")
            return redirect(url_for("exams.list_exams"))
        return render_template("questions/manage.html", exam=exam, active_group=None)
    finally:
        db.close()


@questions_bp.route("/exams/<int:exam_id>/groups/add", methods=["POST"])
def add_group(exam_id):
    db = get_db()
    try:
        group_number = request.form.get("group_number", "").strip()
        question_type = request.form.get("question_type", "").strip()
        points_per_item = request.form.get("points_per_item", "1.0")
        num_items = request.form.get("num_items", "1")

        if not group_number or question_type not in VALID_TYPES:
            flash("Invalid group data. Check all fields.", "danger")
            return redirect(url_for("questions.manage_groups", exam_id=exam_id))

        try:
            points_per_item = float(points_per_item)
            num_items = int(num_items)
        except ValueError:
            flash("Points and number of items must be numbers.", "danger")
            return redirect(url_for("questions.manage_groups", exam_id=exam_id))

        if num_items < 1 or num_items > 100:
            flash("Number of items must be between 1 and 100.", "danger")
            return redirect(url_for("questions.manage_groups", exam_id=exam_id))

        group = create_question_group(db, exam_id, group_number, question_type, points_per_item, num_items)
        flash(f"Group '{group_number}' with {num_items} questions added.", "success")
        return redirect(url_for("questions.group_questions", exam_id=exam_id, group_id=group.id))
    except Exception as exc:
        flash(f"Error adding group: {exc}", "danger")
        return redirect(url_for("questions.manage_groups", exam_id=exam_id))
    finally:
        db.close()


@questions_bp.route("/exams/<int:exam_id>/groups/<int:group_id>/questions")
def group_questions(exam_id, group_id):
    db = get_db()
    try:
        exam = get_exam_with_groups(db, exam_id)
        if not exam:
            flash("Exam not found.", "danger")
            return redirect(url_for("exams.list_exams"))
        active_group = db.query(QuestionGroup).filter(QuestionGroup.id == group_id).first()
        if not active_group:
            flash("Group not found.", "danger")
            return redirect(url_for("questions.manage_groups", exam_id=exam_id))
        return render_template("questions/manage.html", exam=exam, active_group=active_group)
    finally:
        db.close()


@questions_bp.route("/questions/<int:question_id>/update", methods=["POST"])
def update_question_post(question_id):
    db = get_db()
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            flash("Question not found.", "danger")
            db.close()
            return redirect(url_for("exams.list_exams"))

        exam_id = question.group.exam_id
        group_id = question.group_id

        question_text = request.form.get("question_text", "").strip() or None
        correct_answer = request.form.get("correct_answer", "").strip() or None

        # Build choices dict for MC questions
        choices_dict = None
        if question.group.question_type == "multiple_choice":
            choices_dict = {}
            for opt in ["A", "B", "C", "D"]:
                val = request.form.get(f"choice_{opt}", "").strip()
                if val:
                    choices_dict[opt] = val

        update_question(db, question_id, question_text, correct_answer, choices_dict)
        flash("Question updated.", "success")
        return redirect(url_for("questions.group_questions", exam_id=exam_id, group_id=group_id))
    except Exception as exc:
        flash(f"Error updating question: {exc}", "danger")
        return redirect(url_for("exams.list_exams"))
    finally:
        db.close()


@questions_bp.route("/exams/<int:exam_id>/groups/<int:group_id>/delete", methods=["POST"])
def delete_group(exam_id, group_id):
    db = get_db()
    try:
        group = db.query(QuestionGroup).filter(QuestionGroup.id == group_id).first()
        if group:
            db.delete(group)
            db.commit()
            flash("Group deleted.", "success")
        else:
            flash("Group not found.", "danger")
    except Exception as exc:
        flash(f"Error deleting group: {exc}", "danger")
    finally:
        db.close()
    return redirect(url_for("questions.manage_groups", exam_id=exam_id))
