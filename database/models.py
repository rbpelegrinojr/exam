import json
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database.db import Base


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    groups = relationship("QuestionGroup", back_populates="exam", cascade="all, delete-orphan")
    assignments = relationship("ExamAssignment", back_populates="exam", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class QuestionGroup(Base):
    __tablename__ = "question_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    group_number = Column(String(20), nullable=False)  # e.g., "I", "II", "III"
    question_type = Column(String(50), nullable=False)  # multiple_choice | modified_true_false | essay | coding
    points_per_item = Column(Float, nullable=False, default=1.0)
    num_items = Column(Integer, nullable=False, default=1)

    exam = relationship("Exam", back_populates="groups")
    questions = relationship("Question", back_populates="group", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="group", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "exam_id": self.exam_id,
            "group_number": self.group_number,
            "question_type": self.question_type,
            "points_per_item": self.points_per_item,
            "num_items": self.num_items,
        }


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("question_groups.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=True)
    correct_answer = Column(String(50), nullable=True)  # A/B/C/D or True/False
    choices = Column(Text, nullable=True)  # JSON string: {"A": "...", "B": "...", "C": "...", "D": "..."}

    group = relationship("QuestionGroup", back_populates="questions")
    scores = relationship("Score", back_populates="question", cascade="all, delete-orphan")

    @property
    def choices_dict(self):
        if self.choices:
            try:
                return json.loads(self.choices)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "question_number": self.question_number,
            "question_text": self.question_text,
            "correct_answer": self.correct_answer,
            "choices": self.choices_dict,
        }


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_number = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    section = Column(String(100), nullable=False)

    assignments = relationship("ExamAssignment", back_populates="student", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "student_number": self.student_number,
            "full_name": self.full_name,
            "section": self.section,
        }


class ExamAssignment(Base):
    __tablename__ = "exam_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    unique_paper_id = Column(String(50), unique=True, nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", name="uq_exam_student"),
    )

    exam = relationship("Exam", back_populates="assignments")
    student = relationship("Student", back_populates="assignments")
    scan_results = relationship("ScanResult", back_populates="assignment", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="assignment", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "exam_id": self.exam_id,
            "student_id": self.student_id,
            "unique_paper_id": self.unique_paper_id,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
        }


class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("exam_assignments.id"), nullable=False)
    page_number = Column(Integer, nullable=False, default=1)
    image_path = Column(String(500), nullable=False)
    processed = Column(Boolean, default=False)
    scanned_at = Column(DateTime, default=datetime.utcnow)

    assignment = relationship("ExamAssignment", back_populates="scan_results")

    def to_dict(self):
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "page_number": self.page_number,
            "image_path": self.image_path,
            "processed": self.processed,
            "scanned_at": self.scanned_at.isoformat() if self.scanned_at else None,
        }


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("exam_assignments.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("question_groups.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    detected_answer = Column(String(100), nullable=True)
    points_awarded = Column(Float, nullable=False, default=0.0)
    is_manual = Column(Boolean, default=False)

    assignment = relationship("ExamAssignment", back_populates="scores")
    group = relationship("QuestionGroup", back_populates="scores")
    question = relationship("Question", back_populates="scores")

    def to_dict(self):
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "group_id": self.group_id,
            "question_id": self.question_id,
            "detected_answer": self.detected_answer,
            "points_awarded": self.points_awarded,
            "is_manual": self.is_manual,
        }
