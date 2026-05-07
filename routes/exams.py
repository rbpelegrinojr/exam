from flask import Blueprint, render_template, redirect, url_for, request, flash
from database.db import get_db
from database.models import Exam
from modules.exam_creator import create_exam, get_exam_with_groups, delete_exam

exams_bp = Blueprint("exams", __name__)


@exams_bp.route("/exams")
def list_exams():
    db = get_db()
    try:
        exams = db.query(Exam).order_by(Exam.created_at.desc()).all()
        exam_data = []
        for exam in exams:
            exam_data.append({
                "exam": exam,
                "groups_count": len(exam.groups),
            })
        return render_template("exams/list.html", exam_data=exam_data)
    finally:
        db.close()


@exams_bp.route("/exams/create", methods=["GET"])
def create_exam_form():
    return render_template("exams/create.html")


@exams_bp.route("/exams/create", methods=["POST"])
def create_exam_post():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip() or None
    if not title:
        flash("Exam title is required.", "danger")
        return redirect(url_for("exams.create_exam_form"))
    db = get_db()
    try:
        exam = create_exam(db, title, description)
        flash(f"Exam '{exam.title}' created successfully.", "success")
        return redirect(url_for("exams.exam_detail", exam_id=exam.id))
    except Exception as exc:
        flash(f"Error creating exam: {exc}", "danger")
        return redirect(url_for("exams.create_exam_form"))
    finally:
        db.close()


@exams_bp.route("/exams/<int:exam_id>")
def exam_detail(exam_id):
    db = get_db()
    try:
        exam = get_exam_with_groups(db, exam_id)
        if not exam:
            flash("Exam not found.", "danger")
            return redirect(url_for("exams.list_exams"))
        return render_template("exams/detail.html", exam=exam)
    finally:
        db.close()


@exams_bp.route("/exams/<int:exam_id>/delete", methods=["POST"])
def delete_exam_post(exam_id):
    db = get_db()
    try:
        success = delete_exam(db, exam_id)
        if success:
            flash("Exam deleted successfully.", "success")
        else:
            flash("Exam not found.", "danger")
    except Exception as exc:
        flash(f"Error deleting exam: {exc}", "danger")
    finally:
        db.close()
    return redirect(url_for("exams.list_exams"))
