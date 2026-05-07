import os
from flask import Flask, redirect, url_for, render_template
from config import (
    SECRET_KEY, DEBUG, UPLOAD_FOLDER, GENERATED_PAPERS_FOLDER, MAX_CONTENT_LENGTH
)
from database.db import init_db, get_db
from database.models import Exam, Student
from routes.exams import exams_bp
from routes.questions import questions_bp
from routes.students import students_bp
from routes.distribution import distribution_bp
from routes.scanning import scanning_bp
from routes.results import results_bp

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["GENERATED_PAPERS_FOLDER"] = GENERATED_PAPERS_FOLDER
app.config["DEBUG"] = DEBUG

# Register blueprints
app.register_blueprint(exams_bp)
app.register_blueprint(questions_bp)
app.register_blueprint(students_bp)
app.register_blueprint(distribution_bp)
app.register_blueprint(scanning_bp)
app.register_blueprint(results_bp)

# Ensure upload directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_PAPERS_FOLDER, exist_ok=True)

# Initialize database
with app.app_context():
    init_db()


@app.route("/")
def index():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    db = get_db()
    try:
        total_exams = db.query(Exam).count()
        total_students = db.query(Student).count()
        recent_exams = db.query(Exam).order_by(Exam.created_at.desc()).limit(5).all()
        return render_template(
            "dashboard.html",
            total_exams=total_exams,
            total_students=total_students,
            recent_exams=recent_exams,
        )
    finally:
        db.close()


if __name__ == "__main__":
    # debug=True is only active when run directly (python app.py).
    # Set DEBUG=False in config.py for production deployments.
    app.run(host="0.0.0.0", port=5000, debug=DEBUG)
