from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os

app = Flask(__name__)
app.secret_key = "devops_super_secret_key"

os.makedirs("data", exist_ok=True)
DB_NAME = "data/tasks.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        if not conn.execute("SELECT id FROM users WHERE username = 'admin'").fetchone():
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                ("admin", generate_password_hash("admin123"))
            )

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )
        return render_template("login.html", success="Account created! Log in below.")
    except sqlite3.IntegrityError:
        return render_template("login.html", error="Username already taken.")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    status_filter = request.args.get("status", "All")
    with get_db() as conn:
        all_tasks = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? ORDER BY id DESC",
            (session["user_id"],)
        ).fetchall()

    tasks = [t for t in all_tasks if t["status"] == status_filter] if status_filter != "All" else all_tasks

    stats = {
        "total": len(all_tasks),
        "high": sum(1 for t in all_tasks if t["priority"] == "High Priority"),
        "progress": sum(1 for t in all_tasks if t["status"] == "In Progress"),
        "done": sum(1 for t in all_tasks if t["status"] == "Completed")
    }
    return render_template("dashboard.html", tasks=tasks, stats=stats, username=session["username"], current_filter=status_filter)

@app.route("/add", methods=["POST"])
def add_task():
    if "user_id" not in session:
        return redirect(url_for("login"))
    with get_db() as conn:
        conn.execute(
            "INSERT INTO tasks (user_id, title, priority, status) VALUES (?, ?, ?, ?)",
            (session["user_id"], request.form.get("title"), request.form.get("priority"), "In Progress")
        )
    return redirect(url_for("dashboard"))

@app.route("/toggle/<int:task_id>")
def toggle_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    with get_db() as conn:
        task = conn.execute(
            "SELECT status FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, session["user_id"])
        ).fetchone()
        if task:
            new_status = "Completed" if task["status"] == "In Progress" else "In Progress"
            conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    return redirect(url_for("dashboard"))

@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    with get_db() as conn:
        conn.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, session["user_id"])
        )
    return redirect(url_for("dashboard"))

@app.route("/api/health")
def health():
    return jsonify({"status": "healthy", "service": "taskops-web", "version": "2.0"})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)