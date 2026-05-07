from flask import Blueprint, render_template, redirect, url_for, request, flash
from database.db import get_db
from database.models import Student

students_bp = Blueprint("students", __name__)


@students_bp.route("/students")
def list_students():
    db = get_db()
    try:
        students = db.query(Student).order_by(Student.full_name).all()
        return render_template("students/list.html", students=students)
    finally:
        db.close()


@students_bp.route("/students/add", methods=["POST"])
def add_student():
    db = get_db()
    try:
        student_number = request.form.get("student_number", "").strip()
        full_name = request.form.get("full_name", "").strip()
        section = request.form.get("section", "").strip()

        if not student_number or not full_name or not section:
            flash("All fields (student number, name, section) are required.", "danger")
            return redirect(url_for("students.list_students"))

        existing = db.query(Student).filter(Student.student_number == student_number).first()
        if existing:
            flash(f"Student number '{student_number}' already exists.", "danger")
            return redirect(url_for("students.list_students"))

        student = Student(student_number=student_number, full_name=full_name, section=section)
        db.add(student)
        db.commit()
        flash(f"Student '{full_name}' added successfully.", "success")
    except Exception as exc:
        flash(f"Error adding student: {exc}", "danger")
    finally:
        db.close()
    return redirect(url_for("students.list_students"))


@students_bp.route("/students/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    db = get_db()
    try:
        student = db.query(Student).filter(Student.id == student_id).first()
        if student:
            db.delete(student)
            db.commit()
            flash("Student deleted.", "success")
        else:
            flash("Student not found.", "danger")
    except Exception as exc:
        flash(f"Error deleting student: {exc}", "danger")
    finally:
        db.close()
    return redirect(url_for("students.list_students"))
