import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.utils import secure_filename
from database.db import get_db
from database.models import Exam, ExamAssignment, ScanResult
from modules.omr_engine import analyze_scan, read_qr_code

scanning_bp = Blueprint("scanning", __name__)


def _allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


@scanning_bp.route("/exams/<int:exam_id>/scan")
def scan_upload(exam_id):
    db = get_db()
    try:
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            flash("Exam not found.", "danger")
            return redirect(url_for("exams.list_exams"))

        # Collect recent scan results for this exam
        recent_scans = []
        for assignment in exam.assignments:
            for scan in assignment.scan_results:
                recent_scans.append({
                    "scan": scan,
                    "student": assignment.student,
                    "paper_id": assignment.unique_paper_id,
                })
        recent_scans.sort(key=lambda x: x["scan"].scanned_at or datetime.min, reverse=True)
        recent_scans = recent_scans[:20]

        return render_template("scanning/upload.html", exam=exam, recent_scans=recent_scans)
    finally:
        db.close()


@scanning_bp.route("/exams/<int:exam_id>/scan/upload", methods=["POST"])
def scan_upload_post(exam_id):
    from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS
    db = get_db()
    try:
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            flash("Exam not found.", "danger")
            return redirect(url_for("exams.list_exams"))

        files = request.files.getlist("scan_images")
        if not files or all(f.filename == "" for f in files):
            flash("No files selected.", "warning")
            return redirect(url_for("scanning.scan_upload", exam_id=exam_id))

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        processed = 0
        errors = 0

        for file in files:
            if not file.filename or not _allowed_file(file.filename, ALLOWED_EXTENSIONS):
                errors += 1
                continue

            filename = secure_filename(file.filename)
            # Prepend timestamp to avoid collisions
            ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
            filename = f"{ts}_{filename}"
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(image_path)

            # Try to identify the paper via QR code
            paper_id, page_number = read_qr_code(image_path)
            assignment = None
            if paper_id:
                assignment = (
                    db.query(ExamAssignment)
                    .filter(ExamAssignment.unique_paper_id == paper_id)
                    .first()
                )

            # Fall back: attach to exam without a specific assignment (will be resolved during OMR)
            if not assignment:
                # Use first unscanned assignment for this exam as a placeholder
                for a in exam.assignments:
                    assignment = a
                    break

            if not assignment:
                errors += 1
                continue

            scan_result = ScanResult(
                assignment_id=assignment.id,
                page_number=page_number or 1,
                image_path=image_path,
                processed=False,
                scanned_at=datetime.utcnow(),
            )
            db.add(scan_result)
            db.flush()

            # Run OMR analysis immediately
            try:
                analyze_scan(db, scan_result.id)
                processed += 1
            except Exception as exc:
                flash(f"OMR warning for {file.filename}: {exc}", "warning")
                processed += 1  # still counted as uploaded

        db.commit()
        flash(f"{processed} scan(s) uploaded and processed. {errors} file(s) skipped.", "success")
    except Exception as exc:
        db.rollback()
        flash(f"Upload error: {exc}", "danger")
    finally:
        db.close()
    return redirect(url_for("scanning.scan_upload", exam_id=exam_id))


@scanning_bp.route("/scan-results/<int:scan_id>/process", methods=["POST"])
def reprocess_scan(scan_id):
    db = get_db()
    try:
        scan = db.query(ScanResult).filter(ScanResult.id == scan_id).first()
        if not scan:
            flash("Scan result not found.", "danger")
            db.close()
            return redirect(url_for("exams.list_exams"))
        exam_id = scan.assignment.exam_id
        result = analyze_scan(db, scan_id)
        flash(f"Re-processed scan. Scores saved: {result.get('saved_scores', 0)}", "success")
        return redirect(url_for("scanning.scan_upload", exam_id=exam_id))
    except Exception as exc:
        flash(f"Error reprocessing: {exc}", "danger")
        return redirect(url_for("exams.list_exams"))
    finally:
        db.close()
