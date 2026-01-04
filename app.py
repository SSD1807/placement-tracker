from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secretkey"

# ---------- CONFIG ----------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------- DATABASE ----------
def get_db_connection():
    conn = sqlite3.connect("database.db")
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
            company_name TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            company_id INTEGER,
            status TEXT,
            deadline TEXT,
            resume TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------- ROUTES ----------
@app.route("/")
def home():
    return render_template("home.html", user_name=session.get("user_name"))


# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Email already registered"

    return render_template("register.html")


# ---------- LOGIN ----------
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


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    applications = conn.execute("""
        SELECT applications.id, companies.company_name,
               applications.status, applications.deadline
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


# ---------- ADD APPLICATION ----------
@app.route("/add-application", methods=["GET", "POST"])
def add_application():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        company_name = request.form["company_name"]
        status = request.form["status"]
        deadline = request.form["deadline"]

        resume = request.files["resume"]
        resume_filename = resume.filename if resume else None

        if resume_filename:
            resume.save(os.path.join(app.config["UPLOAD_FOLDER"], resume_filename))

        conn = get_db_connection()

        conn.execute(
            "INSERT INTO companies (company_name) VALUES (?)",
            (company_name,)
        )

        company_id = conn.execute(
            "SELECT id FROM companies WHERE company_name = ?",
            (company_name,)
        ).fetchone()["id"]

        conn.execute("""
            INSERT INTO applications (user_id, company_id, status, deadline, resume)
            VALUES (?, ?, ?, ?, ?)
        """, (session["user_id"], company_id, status, deadline, resume_filename))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("add_application.html")


# ---------- EDIT APPLICATION ----------
@app.route("/edit-application/<int:app_id>", methods=["GET", "POST"])
def edit_application(app_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    if request.method == "POST":
        status = request.form["status"]
        deadline = request.form["deadline"]

        conn.execute(
            "UPDATE applications SET status = ?, deadline = ? WHERE id = ?",
            (status, deadline, app_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))

    app_data = conn.execute(
        "SELECT * FROM applications WHERE id = ?",
        (app_id,)
    ).fetchone()
    conn.close()

    return render_template("edit_application.html", app=app_data)


# ---------- DELETE APPLICATION ----------
@app.route("/delete-application/<int:app_id>")
def delete_application(app_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


# ---------- RUN ----------
if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
