"""
OMR Engine — analyzes scanned exam images using OpenCV.
"""

import os
import cv2
import numpy as np

from database.models import ScanResult, ExamAssignment, Score, QuestionGroup, Question


# ---------------------------------------------------------------------------
# QR Code reading
# ---------------------------------------------------------------------------

def read_qr_code(image_path):
    """
    Read QR code from image.
    Returns (unique_paper_id, page_number) or (None, None).
    """
    try:
        from pyzbar.pyzbar import decode as pyzbar_decode
        img = cv2.imread(image_path)
        if img is None:
            return None, None
        decoded = pyzbar_decode(img)
        for obj in decoded:
            data = obj.data.decode("utf-8")
            if "|" in data:
                parts = data.split("|")
                if len(parts) == 2:
                    try:
                        return parts[0], int(parts[1])
                    except ValueError:
                        return parts[0], 1
    except Exception:
        pass
    return None, None


# ---------------------------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------------------------

def preprocess_image(image_path):
    """
    Load image, convert to grayscale, deskew, and apply OTSU threshold.
    Returns a binary numpy array (uint8).
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Deskew using Hough lines
    gray = _deskew(gray)

    # OTSU thresholding
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary


def _deskew(gray):
    """Rotate image to correct skew using Hough line transform."""
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
    if lines is None:
        return gray

    angles = []
    for line in lines[:20]:  # use first 20 lines
        rho, theta = line[0]
        angle = (theta * 180 / np.pi) - 90
        if abs(angle) < 45:
            angles.append(angle)

    if not angles:
        return gray

    median_angle = float(np.median(angles))
    if abs(median_angle) < 0.5:
        return gray

    (h, w) = gray.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated


# ---------------------------------------------------------------------------
# Bubble/checkbox detection helpers
# ---------------------------------------------------------------------------

def _is_filled(region, threshold=0.30):
    """Return True if the region has more than `threshold` fraction of dark pixels."""
    if region is None or region.size == 0:
        return False
    dark_pixels = np.sum(region > 128)  # inverted binary: >128 means originally dark
    ratio = dark_pixels / region.size
    return ratio >= threshold


def _crop(image, x, y, w, h):
    """Safely crop a region from image."""
    ih, iw = image.shape[:2]
    x, y, w, h = int(x), int(y), int(w), int(h)
    x = max(0, x)
    y = max(0, y)
    x2 = min(iw, x + w)
    y2 = min(ih, y + h)
    return image[y:y2, x:x2]


# ---------------------------------------------------------------------------
# MC bubble detection
# ---------------------------------------------------------------------------

def detect_mc_bubbles(image, question_regions):
    """
    Detect filled MC bubbles.
    question_regions: dict {question_num: {'A': (x,y,w,h), 'B': ..., 'C': ..., 'D': ...}}
    Returns dict {question_num: 'A'/'B'/'C'/'D' or None}
    """
    results = {}
    for q_num, options in question_regions.items():
        best_option = None
        best_fill = 0.0
        for opt_label, (x, y, w, h) in options.items():
            region = _crop(image, x, y, w, h)
            dark_ratio = np.sum(region > 128) / max(region.size, 1)
            if dark_ratio > best_fill and dark_ratio >= 0.30:
                best_fill = dark_ratio
                best_option = opt_label
        results[q_num] = best_option
    return results


# ---------------------------------------------------------------------------
# True/False checkbox detection
# ---------------------------------------------------------------------------

def detect_tf_checkboxes(image, checkbox_regions):
    """
    Detect ✓ or ✗ checkboxes.
    checkbox_regions: dict {question_num: {'True': (x,y,w,h), 'False': (x,y,w,h)}}
    Returns dict {question_num: True/False/None}
    """
    results = {}
    for q_num, options in checkbox_regions.items():
        detected = None
        for label, (x, y, w, h) in options.items():
            region = _crop(image, x, y, w, h)
            if _is_filled(region):
                detected = label == "True"
                break
        results[q_num] = detected
    return results


# ---------------------------------------------------------------------------
# Score grid detection
# ---------------------------------------------------------------------------

def detect_score_grid(image, grid_region):
    """
    Detect shaded bubble in score grid (1–10).
    grid_region: list of (score_value, x, y, w, h) tuples
    Returns integer score (1–10) or None.
    """
    best_score = None
    best_fill = 0.0
    for score_val, x, y, w, h in grid_region:
        region = _crop(image, x, y, w, h)
        dark_ratio = np.sum(region > 128) / max(region.size, 1)
        if dark_ratio > best_fill and dark_ratio >= 0.30:
            best_fill = dark_ratio
            best_score = score_val
    return best_score


# ---------------------------------------------------------------------------
# Full analysis pipeline
# ---------------------------------------------------------------------------

def analyze_scan(db, scan_result_id):
    """
    Full OMR pipeline:
    1. Read QR code to identify paper/page
    2. Preprocess image
    3. Detect answers for all question types
    4. Save Score records to DB

    Returns dict with analysis summary.
    """
    scan = db.query(ScanResult).filter(ScanResult.id == scan_result_id).first()
    if not scan:
        raise ValueError(f"ScanResult {scan_result_id} not found")

    image_path = scan.image_path

    # Step 1: Read QR
    paper_id, page_number = read_qr_code(image_path)

    # Resolve assignment from QR or from scan's existing assignment
    assignment = scan.assignment
    if paper_id and assignment and assignment.unique_paper_id != paper_id:
        # QR doesn't match — trust QR
        from database.models import ExamAssignment as EA
        qr_assignment = db.query(EA).filter(EA.unique_paper_id == paper_id).first()
        if qr_assignment:
            assignment = qr_assignment
            scan.assignment_id = qr_assignment.id

    if not assignment:
        scan.processed = True
        db.commit()
        return {"error": "Could not identify assignment from QR code"}

    # Step 2: Preprocess
    try:
        binary_image = preprocess_image(image_path)
    except Exception as exc:
        return {"error": f"Image preprocessing failed: {exc}"}

    # Step 3: Detect answers using approximate coordinate mapping
    exam = assignment.exam
    img_h, img_w = binary_image.shape[:2]

    # Scale factors relative to a standard LETTER page scanned at ~150 DPI
    # LETTER = 8.5 x 11 inches → at 150 DPI: 1275 x 1650 px
    REF_W, REF_H = 1275, 1650
    scale_x = img_w / REF_W
    scale_y = img_h / REF_H

    # Approximate layout constants (in reference pixels, matching pdf_generator.py layout)
    MARGIN_PX = int(0.75 * 150)        # 0.75 inch margin
    HEADER_H = int(1.2 * 150)          # header height
    ROW_H = int(0.50 * 150)            # height per question row
    COL_W = int(1.3 * 150)             # width per MC option column
    BUBBLE_W = int(0.14 * 150)         # bubble width
    BUBBLE_H = int(0.14 * 150)

    saved_scores = 0
    y_cursor = HEADER_H

    groups = sorted(exam.groups, key=lambda g: g.id)
    for group in groups:
        y_cursor += int(0.25 * 150)  # group header
        questions = sorted(group.questions, key=lambda q: q.question_number)
        for question in questions:
            q_y = int(y_cursor * scale_y)
            q_x = int((MARGIN_PX + 0.3 * 150) * scale_x)

            detected_answer = None

            if group.question_type == "multiple_choice":
                mc_regions = {}
                opts = ["A", "B", "C", "D"]
                for i, opt in enumerate(opts):
                    bx = int((MARGIN_PX + 0.3 * 150 + i * 1.3 * 150) * scale_x)
                    by = int((y_cursor + 0.22 * 150) * scale_y)
                    mc_regions[opt] = (bx, by, int(BUBBLE_W * scale_x), int(BUBBLE_H * scale_y))
                results = detect_mc_bubbles(binary_image, {1: mc_regions})
                detected_answer = results.get(1)

            elif group.question_type == "modified_true_false":
                tf_regions = {
                    "True": (
                        int((MARGIN_PX + 0.3 * 150) * scale_x),
                        int((y_cursor + 0.22 * 150) * scale_y),
                        int(BUBBLE_W * scale_x),
                        int(BUBBLE_H * scale_y),
                    ),
                    "False": (
                        int((MARGIN_PX + 0.3 * 150 + 0.8 * 150) * scale_x),
                        int((y_cursor + 0.22 * 150) * scale_y),
                        int(BUBBLE_W * scale_x),
                        int(BUBBLE_H * scale_y),
                    ),
                }
                results = detect_tf_checkboxes(binary_image, {1: tf_regions})
                val = results.get(1)
                detected_answer = str(val) if val is not None else None

            else:  # essay / coding — score grid
                grid = []
                for row_idx, row_start in enumerate([1, 6]):
                    for num in range(row_start, row_start + 5):
                        gx = int((MARGIN_PX + 0.9 * 150 + (num - row_start) * 0.28 * 150) * scale_x)
                        gy = int((y_cursor + (0.22 + row_idx * 0.25) * 150) * scale_y)
                        grid.append((num, gx, gy, int(0.18 * 150 * scale_x), int(0.18 * 150 * scale_y)))
                score_val = detect_score_grid(binary_image, grid)
                detected_answer = str(score_val) if score_val is not None else None

            # Determine points awarded
            points = 0.0
            if question.correct_answer and detected_answer:
                if group.question_type in ("multiple_choice", "modified_true_false"):
                    if str(detected_answer).strip().lower() == str(question.correct_answer).strip().lower():
                        points = group.points_per_item
                else:
                    # Essay/coding: detected_answer is numeric score
                    try:
                        points = float(detected_answer)
                    except (TypeError, ValueError):
                        points = 0.0

            # Upsert Score record
            existing = (
                db.query(Score)
                .filter(Score.assignment_id == assignment.id, Score.question_id == question.id)
                .first()
            )
            if existing and not existing.is_manual:
                existing.detected_answer = detected_answer
                existing.points_awarded = points
            elif not existing:
                score_rec = Score(
                    assignment_id=assignment.id,
                    group_id=group.id,
                    question_id=question.id,
                    detected_answer=detected_answer,
                    points_awarded=points,
                    is_manual=False,
                )
                db.add(score_rec)
                saved_scores += 1

            y_cursor += int(ROW_H)

    scan.processed = True
    db.commit()
    return {"saved_scores": saved_scores, "assignment_id": assignment.id}
