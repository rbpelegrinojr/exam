"""
Seed script — populates the database with a sample subject (Exam),
question groups, and questions.

Usage:
    python seed.py
"""

import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database.db import init_db, get_db
from database.models import Exam, QuestionGroup, Question
from modules.exam_creator import create_exam, create_question_group, update_question


def seed():
    init_db()
    db = get_db()

    try:
        # ------------------------------------------------------------------ #
        # 1. Subject / Exam
        # ------------------------------------------------------------------ #
        exam = create_exam(
            db,
            title="Introduction to Computer Science",
            description=(
                "Midterm examination covering fundamental concepts of "
                "computer science: algorithms, data structures, and basic "
                "programming principles."
            ),
        )
        print(f"[+] Created exam: {exam.title!r} (id={exam.id})")

        # ------------------------------------------------------------------ #
        # 2. Group I — Multiple Choice (10 items, 2 pts each)
        # ------------------------------------------------------------------ #
        mc_group = create_question_group(
            db,
            exam_id=exam.id,
            group_number="I",
            question_type="multiple_choice",
            points_per_item=2.0,
            num_items=10,
        )
        print(f"[+] Created group I — multiple_choice ({mc_group.num_items} items)")

        mc_questions = [
            {
                "text": "Which of the following is NOT a primitive data type in most programming languages?",
                "answer": "C",
                "choices": {"A": "Integer", "B": "Boolean", "C": "Array", "D": "Character"},
            },
            {
                "text": "What is the time complexity of binary search on a sorted array?",
                "answer": "B",
                "choices": {"A": "O(n)", "B": "O(log n)", "C": "O(n²)", "D": "O(1)"},
            },
            {
                "text": "Which data structure follows the LIFO (Last-In, First-Out) principle?",
                "answer": "A",
                "choices": {"A": "Stack", "B": "Queue", "C": "Linked List", "D": "Tree"},
            },
            {
                "text": "In object-oriented programming, the process of hiding internal details is called:",
                "answer": "D",
                "choices": {"A": "Inheritance", "B": "Polymorphism", "C": "Instantiation", "D": "Encapsulation"},
            },
            {
                "text": "Which sorting algorithm has an average-case time complexity of O(n log n)?",
                "answer": "B",
                "choices": {"A": "Bubble Sort", "B": "Merge Sort", "C": "Selection Sort", "D": "Insertion Sort"},
            },
            {
                "text": "What does CPU stand for?",
                "answer": "A",
                "choices": {
                    "A": "Central Processing Unit",
                    "B": "Core Processing Utility",
                    "C": "Central Program Unit",
                    "D": "Computed Processing Unit",
                },
            },
            {
                "text": "Which of the following is a compiled programming language?",
                "answer": "C",
                "choices": {"A": "Python", "B": "JavaScript", "C": "C++", "D": "Ruby"},
            },
            {
                "text": "What is the base of the binary number system?",
                "answer": "B",
                "choices": {"A": "8", "B": "2", "C": "16", "D": "10"},
            },
            {
                "text": "A function that calls itself is known as a:",
                "answer": "D",
                "choices": {
                    "A": "Loop function",
                    "B": "Void function",
                    "C": "Nested function",
                    "D": "Recursive function",
                },
            },
            {
                "text": "Which data structure is used to implement a breadth-first search (BFS)?",
                "answer": "A",
                "choices": {"A": "Queue", "B": "Stack", "C": "Heap", "D": "Graph"},
            },
        ]

        for q_data in mc_questions:
            q = db.query(Question).filter(
                Question.group_id == mc_group.id,
                Question.question_number == mc_questions.index(q_data) + 1,
            ).first()
            if q:
                update_question(db, q.id, q_data["text"], q_data["answer"], q_data["choices"])

        print(f"    Seeded {len(mc_questions)} multiple-choice questions.")

        # ------------------------------------------------------------------ #
        # 3. Group II — Modified True or False (5 items, 1 pt each)
        # ------------------------------------------------------------------ #
        mtf_group = create_question_group(
            db,
            exam_id=exam.id,
            group_number="II",
            question_type="modified_true_false",
            points_per_item=1.0,
            num_items=5,
        )
        print(f"[+] Created group II — modified_true_false ({mtf_group.num_items} items)")

        mtf_questions = [
            {
                "text": (
                    "An algorithm must always terminate after a finite number of steps. "
                    "If the statement is FALSE, write the word that makes it false."
                ),
                "answer": "True",
            },
            {
                "text": (
                    "RAM (Random Access Memory) is a type of non-volatile storage. "
                    "If the statement is FALSE, write the word that makes it false."
                ),
                "answer": "non-volatile",  # should be "volatile"
            },
            {
                "text": (
                    "In a linked list, elements are stored in contiguous memory locations. "
                    "If the statement is FALSE, write the word that makes it false."
                ),
                "answer": "contiguous",  # they are NOT contiguous
            },
            {
                "text": (
                    "The Internet Protocol (IP) operates at the Network layer of the OSI model. "
                    "If the statement is FALSE, write the word that makes it false."
                ),
                "answer": "True",
            },
            {
                "text": (
                    "A binary tree can have at most three children per node. "
                    "If the statement is FALSE, write the word that makes it false."
                ),
                "answer": "three",  # should be "two"
            },
        ]

        for idx, q_data in enumerate(mtf_questions, start=1):
            q = db.query(Question).filter(
                Question.group_id == mtf_group.id,
                Question.question_number == idx,
            ).first()
            if q:
                update_question(db, q.id, q_data["text"], q_data["answer"])

        print(f"    Seeded {len(mtf_questions)} modified true/false questions.")

        # ------------------------------------------------------------------ #
        # 4. Group III — Essay (3 items, 5 pts each)
        # ------------------------------------------------------------------ #
        essay_group = create_question_group(
            db,
            exam_id=exam.id,
            group_number="III",
            question_type="essay",
            points_per_item=5.0,
            num_items=3,
        )
        print(f"[+] Created group III — essay ({essay_group.num_items} items)")

        essay_questions = [
            {
                "text": (
                    "Explain the difference between a stack and a queue. "
                    "Provide a real-world example of each."
                ),
                "answer": (
                    "A stack is a LIFO (Last-In, First-Out) structure where elements are "
                    "added and removed from the same end (top). Example: browser back-button history. "
                    "A queue is a FIFO (First-In, First-Out) structure where elements are added at "
                    "the rear and removed from the front. Example: print job spooler."
                ),
            },
            {
                "text": (
                    "Describe the concept of recursion and explain when it should "
                    "and should not be used."
                ),
                "answer": (
                    "Recursion is a technique where a function calls itself to solve smaller instances "
                    "of the same problem. It is best used when a problem can be naturally broken into "
                    "sub-problems of the same type (e.g., tree traversal, factorial). It should be "
                    "avoided when the recursion depth is too large (risk of stack overflow) or when an "
                    "iterative solution is more efficient."
                ),
            },
            {
                "text": (
                    "What is object-oriented programming (OOP)? "
                    "List and briefly explain its four main principles."
                ),
                "answer": (
                    "OOP is a programming paradigm that organises code around objects (instances of "
                    "classes). Four main principles: "
                    "(1) Encapsulation — bundling data and methods, hiding internal state. "
                    "(2) Abstraction — exposing only necessary details. "
                    "(3) Inheritance — a class can derive properties and behaviour from a parent class. "
                    "(4) Polymorphism — the same interface can represent different underlying forms."
                ),
            },
        ]

        for idx, q_data in enumerate(essay_questions, start=1):
            q = db.query(Question).filter(
                Question.group_id == essay_group.id,
                Question.question_number == idx,
            ).first()
            if q:
                update_question(db, q.id, q_data["text"], q_data["answer"])

        print(f"    Seeded {len(essay_questions)} essay questions.")

        # ------------------------------------------------------------------ #
        # 4. Group IV — Coding (2 items, 10 pts each)
        # ------------------------------------------------------------------ #
        coding_group = create_question_group(
            db,
            exam_id=exam.id,
            group_number="IV",
            question_type="coding",
            points_per_item=10.0,
            num_items=2,
        )
        print(f"[+] Created group IV — coding ({coding_group.num_items} items)")

        coding_questions = [
            {
                "text": (
                    "Write a Python function `fibonacci(n)` that returns the n-th Fibonacci number "
                    "using recursion. Include base cases for n=0 and n=1."
                ),
                "answer": (
                    "def fibonacci(n):\n"
                    "    if n == 0:\n"
                    "        return 0\n"
                    "    if n == 1:\n"
                    "        return 1\n"
                    "    return fibonacci(n - 1) + fibonacci(n - 2)"
                ),
            },
            {
                "text": (
                    "Write a Python function `is_palindrome(s)` that returns True if the string `s` "
                    "is a palindrome (reads the same forwards and backwards), and False otherwise. "
                    "Your solution should be case-insensitive."
                ),
                "answer": (
                    "def is_palindrome(s):\n"
                    "    s = s.lower()\n"
                    "    return s == s[::-1]"
                ),
            },
        ]

        for idx, q_data in enumerate(coding_questions, start=1):
            q = db.query(Question).filter(
                Question.group_id == coding_group.id,
                Question.question_number == idx,
            ).first()
            if q:
                update_question(db, q.id, q_data["text"], q_data["answer"])

        print(f"    Seeded {len(coding_questions)} coding questions.")

        # ------------------------------------------------------------------ #
        # Summary
        # ------------------------------------------------------------------ #
        print("\n✓ Seed complete.")
        print(f"  Exam    : {exam.title!r} (id={exam.id})")
        print(f"  Groups  : {len(exam.groups)} (after refresh: {db.query(QuestionGroup).filter_by(exam_id=exam.id).count()})")
        total_q = db.query(Question).join(QuestionGroup).filter(QuestionGroup.exam_id == exam.id).count()
        print(f"  Questions: {total_q}")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
