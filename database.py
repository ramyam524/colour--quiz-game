import sqlite3
import os
import hashlib
from datetime import datetime


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE = os.path.join(
    BASE_DIR,
    "quiz.db"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# PASSWORD HASH
# =========================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# CREATE DATABASE
# =========================================================

def create_database():

    conn = get_connection()

    cursor = conn.cursor()


    # =====================================================
    # USERS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            created_at TEXT NOT NULL

        )
    """)


    # =====================================================
    # QUESTIONS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            question TEXT NOT NULL,

            option1 TEXT NOT NULL,

            option2 TEXT NOT NULL,

            option3 TEXT NOT NULL,

            option4 TEXT NOT NULL,

            correct_answer TEXT NOT NULL

        )
    """)


    # =====================================================
    # RESULTS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_name TEXT NOT NULL,

            score INTEGER NOT NULL,

            total INTEGER NOT NULL,

            quiz_date TEXT NOT NULL

        )
    """)


    # =====================================================
    # CHECK QUESTIONS
    # =====================================================

    cursor.execute("""
        SELECT COUNT(*)
        FROM questions
    """)

    question_count = cursor.fetchone()[0]


    # =====================================================
    # INSERT COLOR QUIZ QUESTIONS
    # =====================================================

    if question_count == 0:

        questions = [

            (
                "Which color is created by mixing red and blue?",

                "Purple",

                "Green",

                "Orange",

                "Yellow",

                "Purple"
            ),

            (
                "Which color is created by mixing red and yellow?",

                "Green",

                "Orange",

                "Purple",

                "Blue",

                "Orange"
            ),

            (
                "Which color is created by mixing blue and yellow?",

                "Purple",

                "Green",

                "Orange",

                "Pink",

                "Green"
            ),

            (
                "Which of the following is a primary color?",

                "Green",

                "Purple",

                "Red",

                "Orange",

                "Red"
            ),

            (
                "Which color is commonly associated with calmness and peace?",

                "Red",

                "Blue",

                "Orange",

                "Yellow",

                "Blue"
            )

        ]


        cursor.executemany("""
            INSERT INTO questions
            (
                question,
                option1,
                option2,
                option3,
                option4,
                correct_answer
            )

            VALUES (?, ?, ?, ?, ?, ?)
        """, questions)


    # =====================================================
    # SAVE CHANGES
    # =====================================================

    conn.commit()

    conn.close()

    print("Database ready!")


# =========================================================
# REGISTER USER
# =========================================================

def register_user(name, email, password):

    conn = get_connection()

    try:

        conn.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                created_at
            )

            VALUES (?, ?, ?, ?)
        """, (

            name.strip(),

            email.lower().strip(),

            hash_password(password),

            datetime.now().strftime(
                "%d-%m-%Y %H:%M"
            )

        ))

        conn.commit()

        return True


    except sqlite3.IntegrityError:

        return False


    finally:

        conn.close()


# =========================================================
# LOGIN USER
# =========================================================

def login_user(email, password):

    conn = get_connection()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE email = ?
        AND password = ?
    """, (

        email.lower().strip(),

        hash_password(password)

    )).fetchone()

    conn.close()

    return user


# =========================================================
# SAVE QUIZ RESULT
# =========================================================

def save_result(student_name, score, total):

    conn = get_connection()

    try:

        conn.execute("""
            INSERT INTO results
            (
                student_name,
                score,
                total,
                quiz_date
            )

            VALUES (?, ?, ?, ?)
        """, (

            student_name,

            score,

            total,

            datetime.now().strftime(
                "%d-%m-%Y %H:%M"
            )

        ))

        conn.commit()

    finally:

        conn.close()


# =========================================================
# GET QUIZ HISTORY
# =========================================================

def get_results():

    conn = get_connection()

    results = conn.execute("""
        SELECT
            id,
            student_name,
            score,
            total,
            quiz_date
        FROM results
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return results


# =========================================================
# GET QUESTION COUNT
# =========================================================

def get_question_count():

    conn = get_connection()

    result = conn.execute("""
        SELECT COUNT(*) AS total
        FROM questions
    """).fetchone()

    conn.close()

    return result["total"]


# =========================================================
# RESET QUESTIONS
# =========================================================

def reset_questions():

    conn = get_connection()

    cursor = conn.cursor()


    # Delete existing questions
    cursor.execute("""
        DELETE FROM questions
    """)


    # Reset ID counter
    cursor.execute("""
        DELETE FROM sqlite_sequence
        WHERE name = 'questions'
    """)


    # New Color Quiz questions
    questions = [

        (
            "Which color is created by mixing red and blue?",

            "Purple",

            "Green",

            "Orange",

            "Yellow",

            "Purple"
        ),

        (
            "Which color is created by mixing red and yellow?",

            "Green",

            "Orange",

            "Purple",

            "Blue",

            "Orange"
        ),

        (
            "Which color is created by mixing blue and yellow?",

            "Purple",

            "Green",

            "Orange",

            "Pink",

            "Green"
        ),

        (
            "Which of the following is a primary color?",

            "Green",

            "Purple",

            "Red",

            "Orange",

            "Red"
        ),

        (
            "Which color is commonly associated with calmness and peace?",

            "Red",

            "Blue",

            "Orange",

            "Yellow",

            "Blue"
        )

    ]


    cursor.executemany("""
        INSERT INTO questions
        (
            question,
            option1,
            option2,
            option3,
            option4,
            correct_answer
        )

        VALUES (?, ?, ?, ?, ?, ?)
    """, questions)


    conn.commit()

    conn.close()

    print("Color Quiz questions reset successfully!")


# =========================================================
# RUN DATABASE DIRECTLY
# =========================================================

if __name__ == "__main__":

    create_database()

    print(
        "Total questions:",
        get_question_count()
    )
# =========================================================
# GET ONE RESULT - VIEW DETAILS
# =========================================================

def get_result_by_id(result_id):
    conn = get_connection()
    try:
        return conn.execute("""
            SELECT id, student_name, score, total, quiz_date
            FROM results
            WHERE id = ?
        """, (result_id,)).fetchone()
    finally:
        conn.close()
