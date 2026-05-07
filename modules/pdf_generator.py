"""
PDF Generator — produces per-student exam papers with QR codes.
Each page has a QR code encoding "{unique_paper_id}|{page_number}".
"""

import os
import io
import qrcode
from datetime import datetime
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import GENERATED_PAPERS_FOLDER
from database.models import ExamAssignment, Question

PAGE_WIDTH, PAGE_HEIGHT = LETTER
MARGIN = 0.75 * inch
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN
QR_SIZE = 1.0 * inch
QUESTIONS_PER_PAGE = 25


def _make_qr_image(data: str) -> ImageReader:
    """Generate a QR code image and return as ReportLab ImageReader."""
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def _draw_page_header(c, exam_title, student_name, paper_id, page_num, total_pages):
    """Draw header (QR code + exam info) at top of page."""
    # QR code in top-left
    qr_data = f"{paper_id}|{page_num}"
    qr_img = _make_qr_image(qr_data)
    c.drawImage(qr_img, MARGIN, PAGE_HEIGHT - MARGIN - QR_SIZE, width=QR_SIZE, height=QR_SIZE)

    # Exam title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN + QR_SIZE + 0.15 * inch, PAGE_HEIGHT - MARGIN - 0.3 * inch, exam_title)

    # Student info
    c.setFont("Helvetica", 10)
    info_x = MARGIN + QR_SIZE + 0.15 * inch
    c.drawString(info_x, PAGE_HEIGHT - MARGIN - 0.55 * inch, f"Name: {student_name}")
    c.drawString(info_x, PAGE_HEIGHT - MARGIN - 0.72 * inch, f"Paper ID: {paper_id}")
    c.drawString(info_x, PAGE_HEIGHT - MARGIN - 0.89 * inch, f"Date: {datetime.now().strftime('%B %d, %Y')}")

    # Page number (top-right)
    c.setFont("Helvetica", 10)
    c.drawRightString(
        PAGE_WIDTH - MARGIN,
        PAGE_HEIGHT - MARGIN - 0.3 * inch,
        f"Page {page_num} of {total_pages}",
    )

    # Horizontal rule
    rule_y = PAGE_HEIGHT - MARGIN - QR_SIZE - 0.15 * inch
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(MARGIN, rule_y, PAGE_WIDTH - MARGIN, rule_y)
    return rule_y - 0.2 * inch  # return y cursor below header


def _draw_mc_question(c, y, q_num, question_text, choices_dict):
    """Draw a multiple-choice question with ○A ○B ○C ○D bubbles. Returns new y."""
    c.setFont("Helvetica-Bold", 10)
    label = f"{q_num}."
    c.drawString(MARGIN, y, label)
    c.setFont("Helvetica", 10)
    text = question_text or f"Question {q_num}"
    c.drawString(MARGIN + 0.3 * inch, y, text[:90])
    y -= 0.22 * inch

    # Choices row
    option_labels = ["A", "B", "C", "D"]
    x = MARGIN + 0.3 * inch
    for opt in option_labels:
        # Draw circle
        c.circle(x + 0.08 * inch, y + 0.06 * inch, 0.07 * inch)
        c.setFont("Helvetica", 9)
        c.drawString(x + 0.18 * inch, y, opt)
        choice_text = ""
        if choices_dict and opt in choices_dict:
            choice_text = str(choices_dict[opt])[:18]
        c.setFont("Helvetica", 8)
        c.drawString(x + 0.30 * inch, y, choice_text)
        x += 1.3 * inch

    return y - 0.28 * inch


def _draw_tf_question(c, y, q_num, question_text):
    """Draw a modified True/False question. Returns new y."""
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN, y, f"{q_num}.")
    c.setFont("Helvetica", 10)
    text = question_text or f"Statement {q_num}"
    c.drawString(MARGIN + 0.3 * inch, y, text[:90])
    y -= 0.22 * inch

    x = MARGIN + 0.3 * inch
    # True checkbox
    c.rect(x, y - 0.02 * inch, 0.14 * inch, 0.14 * inch)
    c.setFont("Helvetica", 9)
    c.drawString(x + 0.17 * inch, y, "True")
    # False checkbox
    c.rect(x + 0.8 * inch, y - 0.02 * inch, 0.14 * inch, 0.14 * inch)
    c.drawString(x + 0.97 * inch, y, "False")
    # Answer line
    c.line(x + 1.6 * inch, y + 0.10 * inch, x + 3.5 * inch, y + 0.10 * inch)
    c.setFont("Helvetica", 7)
    c.drawString(x + 1.6 * inch, y - 0.08 * inch, "Answer/Correction")

    return y - 0.30 * inch


def _draw_essay_question(c, y, q_num, question_text):
    """Draw an essay/coding question with answer lines and score grid. Returns new y."""
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN, y, f"{q_num}.")
    c.setFont("Helvetica", 10)
    text = question_text or f"Essay/Coding Question {q_num}"
    c.drawString(MARGIN + 0.3 * inch, y, text[:90])
    y -= 0.22 * inch

    # Answer lines
    for _ in range(3):
        c.line(MARGIN + 0.3 * inch, y, PAGE_WIDTH - MARGIN, y)
        y -= 0.22 * inch

    # Score grid — bubbles 1–10
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN + 0.3 * inch, y, "Score:")
    grid_x = MARGIN + 0.9 * inch
    for row_start, row_end in [(1, 6), (6, 11)]:
        for num in range(row_start, row_end):
            cx = grid_x + (num - row_start) * 0.28 * inch
            c.circle(cx, y + 0.06 * inch, 0.09 * inch)
            c.setFont("Helvetica", 7)
            c.drawCentredString(cx, y + 0.02 * inch, str(num))
        y -= 0.25 * inch

    return y - 0.10 * inch


def generate_paper(db, assignment_id):
    """
    Generate a PDF exam paper for the given assignment.
    Saves to generated_papers/{unique_paper_id}.pdf
    Returns the file path.
    """
    assignment = db.query(ExamAssignment).filter(ExamAssignment.id == assignment_id).first()
    if not assignment:
        raise ValueError(f"Assignment {assignment_id} not found")

    exam = assignment.exam
    student = assignment.student
    paper_id = assignment.unique_paper_id

    # Collect all questions across groups in order
    all_items = []  # list of (group, question)
    for group in sorted(exam.groups, key=lambda g: g.id):
        for question in sorted(group.questions, key=lambda q: q.question_number):
            all_items.append((group, question))

    # Split into pages (QUESTIONS_PER_PAGE per page)
    pages = []
    for i in range(0, max(len(all_items), 1), QUESTIONS_PER_PAGE):
        pages.append(all_items[i: i + QUESTIONS_PER_PAGE])
    if not pages:
        pages = [[]]
    total_pages = len(pages)

    os.makedirs(GENERATED_PAPERS_FOLDER, exist_ok=True)
    pdf_path = os.path.join(GENERATED_PAPERS_FOLDER, f"{paper_id}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=LETTER)

    for page_idx, page_items in enumerate(pages):
        page_num = page_idx + 1
        y = _draw_page_header(c, exam.title, student.full_name, paper_id, page_num, total_pages)

        current_group = None
        for group, question in page_items:
            # Draw group header when group changes
            if current_group is None or current_group.id != group.id:
                current_group = group
                if y < 1.5 * inch:
                    c.showPage()
                    page_num += 1
                    y = _draw_page_header(c, exam.title, student.full_name, paper_id, page_num, total_pages)
                c.setFont("Helvetica-Bold", 11)
                type_label = group.question_type.replace("_", " ").title()
                c.drawString(
                    MARGIN,
                    y,
                    f"Part {group.group_number} — {type_label} ({group.points_per_item} pt each)",
                )
                y -= 0.25 * inch

            # Check page space
            min_height = 0.8 * inch
            if y < min_height:
                c.showPage()
                page_num += 1
                y = _draw_page_header(c, exam.title, student.full_name, paper_id, page_num, total_pages)

            qtype = group.question_type
            if qtype == "multiple_choice":
                y = _draw_mc_question(c, y, question.question_number, question.question_text, question.choices_dict)
            elif qtype == "modified_true_false":
                y = _draw_tf_question(c, y, question.question_number, question.question_text)
            else:  # essay or coding
                y = _draw_essay_question(c, y, question.question_number, question.question_text)

        c.showPage()

    c.save()
    return pdf_path
