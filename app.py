from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "devops_secret_key"
DB_NAME = "tasks.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                env TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == "admin" and request.form.get("password") == "admin123":
            session["user"] = "admin"
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid credentials (use admin / admin123)")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        tasks = conn.execute("SELECT id, title, env, status FROM tasks").fetchall()
    return render_template("dashboard.html", tasks=tasks)

@app.route("/add", methods=["POST"])
def add_task():
    if "user" not in session:
        return redirect(url_for("login"))
    title = request.form.get("title")
    env = request.form.get("env")
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO tasks (title, env, status) VALUES (?, ?, ?)", (title, env, "Running"))
    return redirect(url_for("dashboard"))

@app.route("/toggle/<int:task_id>")
def toggle_task(task_id):
    if "user" not in session:
        return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        curr = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if curr:
            new_status = "Completed" if curr[0] == "Running" else "Running"
            conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    return redirect(url_for("dashboard"))

@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    if "user" not in session:
        return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return redirect(url_for("dashboard"))

@app.route("/api/health")
def health():
    return jsonify({"status": "healthy", "service": "taskops-web"})

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)