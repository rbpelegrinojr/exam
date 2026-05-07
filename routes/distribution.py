import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file
from database.db import get_db
from database.models import Exam, Student, ExamAssignment
from modules.pdf_generator import generate_paper

distribution_bp = Blueprint("distribution", __name__)


def _next_paper_id(db, exam_id):
    """Generate the next unique_paper_id in format EX{year}-{seq:03d}."""
    year = datetime.utcnow().year
    prefix = f"EX{year}-"
    # Count existing assignments across all exams to get global sequence
    count = db.query(ExamAssignment).count()
    return f"{prefix}{count + 1:03d}"


@distribution_bp.route("/exams/<int:exam_id>/assign")
def assign_students(exam_id):
    db = get_db()
    try:
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            flash("Exam not found.", "danger")
            return redirect(url_for("exams.list_exams"))
        all_students = db.query(Student).order_by(Student.full_name).all()
        assigned_ids = {a.student_id for a in exam.assignments}
        return render_template(
            "students/assign.html",
            exam=exam,
            all_students=all_students,
            assigned_ids=assigned_ids,
        )
    finally:
        db.close()


@distribution_bp.route("/exams/<int:exam_id>/assign", methods=["POST"])
def assign_students_post(exam_id):
    db = get_db()
    try:
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            flash("Exam not found.", "danger")
            return redirect(url_for("exams.list_exams"))

        student_ids = request.form.getlist("student_ids")
        if not student_ids:
            flash("No students selected.", "warning")
            return redirect(url_for("distribution.assign_students", exam_id=exam_id))

        added = 0
        skipped = 0
        for sid in student_ids:
            try:
                sid = int(sid)
            except ValueError:
                continue
            existing = (
                db.query(ExamAssignment)
                .filter(ExamAssignment.exam_id == exam_id, ExamAssignment.student_id == sid)
                .first()
            )
            if existing:
                skipped += 1
                continue
            paper_id = _next_paper_id(db, exam_id)
            assignment = ExamAssignment(
                exam_id=exam_id,
                student_id=sid,
                unique_paper_id=paper_id,
                assigned_at=datetime.utcnow(),
            )
            db.add(assignment)
            db.flush()
            added += 1

        db.commit()
        flash(f"{added} student(s) assigned. {skipped} already assigned.", "success")
    except Exception as exc:
        db.rollback()
        flash(f"Error assigning students: {exc}", "danger")
    finally:
        db.close()
    return redirect(url_for("distribution.assign_students", exam_id=exam_id))


@distribution_bp.route("/exams/<int:exam_id>/generate-papers", methods=["POST"])
def generate_papers(exam_id):
    db = get_db()
    try:
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            flash("Exam not found.", "danger")
            return redirect(url_for("exams.list_exams"))

        generated = 0
        errors = 0
        for assignment in exam.assignments:
            try:
                generate_paper(db, assignment.id)
                generated += 1
            except Exception as exc:
                errors += 1
                flash(f"Error generating paper for {assignment.unique_paper_id}: {exc}", "warning")

        flash(f"{generated} paper(s) generated. {errors} error(s).", "success" if errors == 0 else "warning")
    except Exception as exc:
        flash(f"Error: {exc}", "danger")
    finally:
        db.close()
    return redirect(url_for("exams.exam_detail", exam_id=exam_id))


@distribution_bp.route("/assignments/<int:assignment_id>/download")
def download_paper(assignment_id):
    db = get_db()
    try:
        assignment = db.query(ExamAssignment).filter(ExamAssignment.id == assignment_id).first()
        if not assignment:
            flash("Assignment not found.", "danger")
            return redirect(url_for("exams.list_exams"))

        from config import GENERATED_PAPERS_FOLDER
        pdf_path = os.path.join(GENERATED_PAPERS_FOLDER, f"{assignment.unique_paper_id}.pdf")

        if not os.path.exists(pdf_path):
            # Try to generate on the fly
            pdf_path = generate_paper(db, assignment_id)

        return send_file(pdf_path, as_attachment=True, download_name=f"{assignment.unique_paper_id}.pdf")
    except Exception as exc:
        flash(f"Error downloading paper: {exc}", "danger")
        return redirect(url_for("exams.list_exams"))
    finally:
        db.close()
