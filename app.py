from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import create_database, save_result, register_user, login_user, get_results, get_result_by_id
import sqlite3
import os

app = Flask(__name__, template_folder='.')
app.secret_key = "quiz_secret_key_change_this"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "quiz.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


create_database()


@app.route("/")
def index():
    conn = get_db()
    try:
        result = conn.execute("SELECT COUNT(*) AS total FROM questions").fetchone()
        question_count = result["total"]
    except sqlite3.Error:
        question_count = 0
    finally:
        conn.close()

    return render_template(
        "index.html",
        question_count=question_count,
        logged_in="user_id" in session,
        user_name=session.get("user_name")
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
            return render_template("register.html")

        if len(name) < 2:
            flash("Please enter a valid name.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
            return render_template("register.html")

        if register_user(name, email, password):
            user = login_user(email, password)
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            flash("Account created successfully!", "success")
            return redirect(url_for("index"))

        flash("An account with this email already exists.", "error")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = login_user(email, password)

        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            flash("Login successful!", "success")
            return redirect(url_for("index"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/start", methods=["POST"])
def start():
    if "user_id" not in session:
        flash("Please login before starting the quiz.", "error")
        return redirect(url_for("login"))

    session["student_name"] = session.get("user_name", "Guest")
    session["question_number"] = 0
    session["score"] = 0
    session.pop("final_score", None)
    session.pop("final_total", None)
    session.pop("final_percentage", None)
    session.pop("final_name", None)

    return redirect(url_for("quiz"))


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "user_id" not in session:
        flash("Please login to take the quiz.", "error")
        return redirect(url_for("login"))

    conn = get_db()
    try:
        questions = conn.execute("""
            SELECT id, question, option1, option2, option3, option4, correct_answer
            FROM questions
            ORDER BY id
        """).fetchall()
    except sqlite3.Error as e:
        return f"Database error: {e}"
    finally:
        conn.close()

    if not questions:
        return "<h2>No questions available.</h2><p>Please add questions to the database.</p>"

    if "question_number" not in session:
        session["question_number"] = 0
        session["score"] = 0

    question_number = session.get("question_number", 0)

    if request.method == "POST":
        selected_answer = request.form.get("answer")

        if question_number < len(questions) and selected_answer:
            current_question = questions[question_number]
            correct_answer = current_question["correct_answer"]
            if selected_answer.strip().lower() == correct_answer.strip().lower():
                session["score"] = session.get("score", 0) + 1

        session["question_number"] = question_number + 1
        question_number = session["question_number"]

    if question_number >= len(questions):
        score = session.get("score", 0)
        total = len(questions)
        student_name = session.get("student_name", session.get("user_name", "Guest"))
        percentage = round((score / total) * 100, 2) if total else 0

        try:
            save_result(student_name, score, total)
        except Exception as e:
            print("Result save error:", e)

        session["final_score"] = score
        session["final_total"] = total
        session["final_percentage"] = percentage
        session["final_name"] = student_name
        return redirect(url_for("result"))

    question = questions[question_number]
    return render_template(
        "quiz.html",
        question=question,
        number=question_number + 1,
        total=len(questions),
        student_name=session.get("student_name", session.get("user_name", "Guest"))
    )


@app.route("/result")
def result():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "result.html",
        score=session.get("final_score", 0),
        total=session.get("final_total", 0),
        percentage=session.get("final_percentage", 0),
        student_name=session.get("final_name", session.get("user_name", "Guest"))
    )


@app.route("/history")
def history():
    if "user_id" not in session:
        flash("Please login to view quiz history.", "error")
        return redirect(url_for("login"))

    try:
        results = get_results()
    except Exception as e:
        return f"History database error: {e}"

    return render_template("history.html", results=results)


@app.route("/history/<int:result_id>")
def result_details(result_id):
    if "user_id" not in session:
        flash("Please login to view result details.", "error")
        return redirect(url_for("login"))

    result_row = get_result_by_id(result_id)
    if not result_row:
        flash("Result not found.", "error")
        return redirect(url_for("history"))

    return render_template("details.html", result=result_row)


@app.route("/restart")
def restart():
    for key in [
        "question_number", "score", "final_score", "final_total",
        "final_percentage", "final_name"
    ]:
        session.pop(key, None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
