# Exam Management System

A full-featured, browser-based Exam Management System built with **Python Flask**, **SQLite/SQLAlchemy**, **OpenCV OMR**, and **ReportLab PDF generation**.

---

## Features

- **Exam creation** with multiple question groups (Multiple Choice, Modified True/False, Essay, Coding)
- **Per-student PDF exam papers** with embedded QR codes (unique paper ID per student)
- **OMR scanning** — upload scanned paper images; the system auto-reads QR codes and detects filled bubbles/checkboxes
- **Automatic scoring** with per-group breakdown
- **Results dashboard** with statistics (highest, lowest, average)
- **CSV export** of all results
- Clean Bootstrap 5 UI with sidebar navigation

---

## Installation

### 1. Install system dependency (pyzbar)

```bash
# Ubuntu / Debian
sudo apt-get install libzbar0

# macOS
brew install zbar
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

The SQLite database (`exam_system.db`) is created automatically on first run.

---

## Switching from SQLite to MySQL

1. Install PyMySQL (already in requirements): `pip install PyMySQL`
2. Create a MySQL database: `CREATE DATABASE exam_db CHARACTER SET utf8mb4;`
3. Edit `config.py`:

```python
# Comment out SQLite line:
# DATABASE_URL = "sqlite:///" + os.path.join(BASE_DIR, "exam_system.db")

# Uncomment and configure MySQL:
DATABASE_URL = "mysql+pymysql://username:password@localhost/exam_db"
```

4. Restart `python app.py` — tables will be created automatically.

---

## Usage Walkthrough

### Step 1 — Create an Exam
- Go to **Exams → New Exam**
- Enter a title and optional description
- Click **Create Exam**

### Step 2 — Add Question Groups
- Open the exam → **Manage Questions**
- Click **Add Group**: choose type (Multiple Choice / Modified T/F / Essay / Coding), number of items, and points per item
- After the group is created, edit each question: enter question text, correct answer, and MC choices

### Step 3 — Add Students
- Go to **Students → Add New Student**
- Enter student number, full name, section

### Step 4 — Assign Students to Exam
- Open exam → **Assign Students**
- Select students and click **Assign Selected**
- Each student gets a unique paper ID (e.g., `EX2026-001`)

### Step 5 — Generate & Print Papers
- Open exam → click **Generate Papers** (generates one PDF per assigned student)
- Download individual PDFs via the **Assigned Students** table
- Each PDF has a QR code on every page and answer bubbles for each question type

### Step 6 — Scan & Upload
- After students complete the exam, scan their papers
- Open exam → **Upload Scans**
- Upload one or more scanned images (PNG/JPG/TIFF)
- The OMR engine reads the QR code, identifies the student, and detects all answers automatically

### Step 7 — View Results
- Open exam → **View Results**
- See per-student scores, group breakdowns, and class statistics
- Click **Export CSV** to download results as a spreadsheet

---

## OMR Scan Quality Tips

For best OMR accuracy:
- Scan at **150 DPI or higher**
- Use **black ink** for filled bubbles
- Avoid shadows, folds, or heavy background marks
- Ensure the **QR code** in the top-left corner is clearly visible
- If a bubble is poorly detected, use the **Re-run** button on the scan results page
- Manual score overrides can be applied directly in the database (set `is_manual = 1`)

---

## Project Structure

```
exam/
├── app.py                  # Flask app entry point
├── config.py               # Configuration (DB URL, folders, etc.)
├── requirements.txt
├── database/
│   ├── db.py               # SQLAlchemy engine + session
│   └── models.py           # ORM models
├── modules/
│   ├── exam_creator.py     # Exam/group/question CRUD
│   ├── pdf_generator.py    # ReportLab PDF generation
│   ├── omr_engine.py       # OpenCV OMR analysis
│   └── scorer.py           # Score computation & CSV export
├── routes/                 # Flask blueprints
├── templates/              # Jinja2 HTML templates
├── static/                 # CSS + JS
├── uploads/                # Scanned images (auto-created)
└── generated_papers/       # Generated PDFs (auto-created)
```

---

## License

MIT
