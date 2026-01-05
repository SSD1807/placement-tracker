import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.secret_key = "super-secret-key"   # change later for production

# ---------------- FILE UPLOAD CONFIG ----------------
UPLOAD_FOLDER = os.path.join("uploads", "resumes")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------- DATABASE ----------------
DATABASE = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT UNIQUE
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            company_id INTEGER,
            status TEXT,
            deadline TEXT,
            resume_file TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("home.html")


# ---------------- REGISTER ----------------
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
            return "Email already exists"
        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials"

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    applications = conn.execute("""
        SELECT applications.id,
               companies.company_name,
               applications.status,
               applications.deadline,
               applications.resume_file
        FROM applications
        JOIN companies ON applications.company_id = companies.id
        WHERE applications.user_id = ?
    """, (session["user_id"],)).fetchall()
    conn.close()

    return render_template(
        "dashboard.html",
        applications=applications,
        user_name=session["user_name"]
    )


# ---------------- ADD APPLICATION ----------------
@app.route("/add-application", methods=["GET", "POST"])
def add_application():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        company_name = request.form["company_name"]
        status = request.form["status"]
        deadline = request.form["deadline"]

        # -------- RESUME UPLOAD --------
        resume = request.files.get("resume")
        resume_filename = None

        if resume and resume.filename != "":
            resume_filename = secure_filename(resume.filename)
            resume.save(
                os.path.join(app.config["UPLOAD_FOLDER"], resume_filename)
            )

        # -------- DATABASE --------
        conn = get_db_connection()

        # Insert company if not exists
        conn.execute(
            "INSERT OR IGNORE INTO companies (company_name) VALUES (?)",
            (company_name,)
        )

        company_id = conn.execute(
            "SELECT id FROM companies WHERE company_name = ?",
            (company_name,)
        ).fetchone()["id"]

        # Insert application
        conn.execute("""
            INSERT INTO applications
            (user_id, company_id, status, deadline, resume_file)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            company_id,
            status,
            deadline,
            resume_filename
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("add_application.html")


# ---------------- EDIT APPLICATION ----------------
@app.route("/edit-application/<int:id>", methods=["GET", "POST"])
def edit_application(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    if request.method == "POST":
        status = request.form["status"]
        deadline = request.form["deadline"]

        resume = request.files.get("resume")
        resume_filename = None

        if resume and resume.filename != "":
            resume_filename = secure_filename(resume.filename)
            resume.save(os.path.join(app.config["UPLOAD_FOLDER"], resume_filename))

            conn.execute("""
                UPDATE applications
                SET status = ?, deadline = ?, resume_file = ?
                WHERE id = ? AND user_id = ?
            """, (status, deadline, resume_filename, id, session["user_id"]))
        else:
            conn.execute("""
                UPDATE applications
                SET status = ?, deadline = ?
                WHERE id = ? AND user_id = ?
            """, (status, deadline, id, session["user_id"]))

        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))

    application = conn.execute("""
        SELECT applications.*, companies.company_name
        FROM applications
        JOIN companies ON applications.company_id = companies.id
        WHERE applications.id = ? AND applications.user_id = ?
    """, (id, session["user_id"])).fetchone()
    conn.close()

    return render_template("edit_application.html", application=application)


# ---------------- DELETE APPLICATION ----------------
@app.route("/delete-application/<int:id>")
def delete_application(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    conn.execute(
        "DELETE FROM applications WHERE id = ? AND user_id = ?",
        (id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
