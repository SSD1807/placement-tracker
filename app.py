import os
import sqlite3
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ---------------- CONFIG ----------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "resumes")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------- DATABASE ----------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT UNIQUE NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            company_id INTEGER NOT NULL,
            application_type TEXT NOT NULL,
            stage TEXT NOT NULL,
            deadline DATE,
            resume_file TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)

    conn.commit()
    conn.close()

# ✅ FORCE DB CREATION ON STARTUP
create_tables()

# ---------------- HELPERS ----------------
def days_left(deadline):
    if not deadline:
        return None
    d = datetime.strptime(deadline, "%Y-%m-%d").date()
    return (d - date.today()).days

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("home.html")

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered"
        conn.close()
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))

        return "Invalid credentials"

    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    applications = conn.execute("""
        SELECT 
            applications.id,
            companies.company_name,
            applications.application_type,
            applications.stage,
            applications.deadline,
            applications.resume_file
        FROM applications
        JOIN companies ON applications.company_id = companies.id
        WHERE applications.user_id = ?
        ORDER BY applications.deadline
    """, (session["user_id"],)).fetchall()
    conn.close()

    enriched = []
    for app_row in applications:
        app_dict = dict(app_row)
        app_dict["days_left"] = days_left(app_row["deadline"])
        enriched.append(app_dict)

    return render_template(
        "dashboard.html",
        applications=enriched,
        user_name=session["user_name"]
    )

# ---------- ADD APPLICATION ----------
@app.route("/add-application", methods=["GET", "POST"])
def add_application():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        company_name = request.form["company_name"]
        application_type = request.form["application_type"]
        stage = request.form["stage"]
        deadline = request.form["deadline"]

        resume = request.files.get("resume")
        resume_filename = None

        if resume and resume.filename:
            resume_filename = secure_filename(resume.filename)
            resume.save(os.path.join(app.config["UPLOAD_FOLDER"], resume_filename))

        conn = get_db_connection()
        conn.execute(
            "INSERT OR IGNORE INTO companies (company_name) VALUES (?)",
            (company_name,)
        )
        company_id = conn.execute(
            "SELECT id FROM companies WHERE company_name = ?",
            (company_name,)
        ).fetchone()["id"]

        conn.execute("""
            INSERT INTO applications
            (user_id, company_id, application_type, stage, deadline, resume_file)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            company_id,
            application_type,
            stage,
            deadline,
            resume_filename
        ))

        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))

    return render_template("add_application.html")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
