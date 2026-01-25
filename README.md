# 📌 Placement & Internship Tracking System

## 🌐 Live Demo
https://placement-tracker-ys81.onrender.com/

A backend-driven web application built using **Python and Flask** that helps students efficiently track internship and placement applications, manage deadlines, and monitor application status in one centralized platform.

This project is designed as a **real-world, scalable system**, not just an academic demo.

---

## 🚀 Features

- User Registration & Login (Session-based authentication)
- Secure Password Hashing
- Add, Edit, Delete job/internship applications
- Track application status:
  - Applied
  - Interview
  - Rejected
- Deadline tracking for applications
- Resume upload support (PDF)
- User-specific dashboard
- Role-ready architecture (Admin / Student – extendable)
- Clean and minimal UI
- SQLite database (easily scalable to PostgreSQL)

---

## 🛠️ Tech Stack

### Backend
- Python 3
- Flask
- SQLite
- Werkzeug (Password hashing)

### Frontend
- HTML
- CSS (Minimal UI, no JavaScript frameworks)

### Tools
- VS Code
- Git & GitHub

---

## 🧱 Project Structure

placement_tracker/
│
├── app.py # Main Flask application
├── database.db # SQLite database (ignored in Git)
├── requirements.txt # Project dependencies
├── README.md # Project documentation
├── .gitignore
│
├── templates/
│ ├── home.html
│ ├── login.html
│ ├── register.html
│ ├── dashboard.html
│ ├── add_application.html
│ ├── edit_application.html
│
├── static/
│ └── style.css
│
├── uploads/
│ └── resumes/


---

## 🔄 Application Flow

1. User registers and logs in
2. Session is created and user is redirected to the dashboard
3. User can:
   - Add applications
   - Edit or delete applications
   - Upload resume
   - Track deadlines and status
4. All data is securely stored in the database
5. Each user can only access their own data

---

## 🗃️ Database Design

### Tables

#### users
- id
- name
- email
- password (hashed)

#### companies
- id
- company_name

#### applications
- id
- user_id
- company_id
- status
- deadline
- resume_file

---

## 🔐 Security Practices

- Passwords are stored using Werkzeug password hashing
- Sessions are used instead of passing user data in URLs
- Database queries use parameterized SQL (prevents SQL injection)
- Sensitive files and folders are ignored using `.gitignore`

---

## 📈 Future Improvements

- Migrate database from SQLite to PostgreSQL
- Email reminders for upcoming deadlines
- Admin dashboard for analytics
- Deployment using Docker
- Role-based access control (Admin / Student)
- Resume versioning
- API-based backend

---

## 🧠 Learning Outcomes

- Understanding backend request–response lifecycle
- Flask routing and template rendering
- Database schema design and relationships
- Session management and authentication
- Secure password handling
- Real-world CRUD application design
- Git and GitHub workflow

---

## 👤 Author

**Shreeyan Das**  
B.Tech CSE Student  
KIIT University  

---

## 📜 License

This project is for educational and learning purposes.

---

## ✅ Status

- ✔ Core backend completed
- ✔ Authentication implemented
- ✔ CRUD operations functional
- ✔ Deployement done successfully 

---

## 🔗 Note

Deployment is intentionally deferred to allow further optimization and additional project development before final production release.

---

## ⭐ Support

If you like this project, give it a ⭐ on GitHub — it motivates future improvements!
