from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from database import *
from model import predict_duration, train_model
from push import send_push
import sqlite3

create_tables()

app = FastAPI()

# ------------------------------
# Request Models
# ------------------------------
class TaskIn(BaseModel):
    title: str
    deadline: str
    importance: int

class Token(BaseModel):
    fcm_token: str


# ------------------------------
# Add Task
# ------------------------------
@app.post("/tasks")
def add_task(t: TaskIn):
    hour = datetime.now().hour
    predicted = predict_duration(t.importance, hour)

    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tasks (title, deadline, importance, created_at, predicted_minutes)
        VALUES (?, ?, ?, ?, ?)
    """, (t.title, t.deadline, t.importance, datetime.now().isoformat(), predicted))
    conn.commit()
    conn.close()

    send_push("New Task Added", t.title)

    return {"status": "ok", "predicted_minutes": predicted}


# ------------------------------
# Get All Tasks
# ------------------------------
@app.get("/tasks")
def get_tasks():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, deadline, importance, status, created_at,
               completed_at, duration_minutes, predicted_minutes
        FROM tasks
    """)
    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "title": r[1],
            "deadline": r[2],
            "importance": r[3],
            "status": r[4],
            "created_at": r[5],
            "completed_at": r[6],
            "duration_minutes": r[7],
            "predicted_minutes": r[8]
        })

    return result


# ------------------------------
# Register Device Token
# ------------------------------
@app.post("/register")
def register(t: Token):
    add_token(t.fcm_token)
    return {"status": "registered"}


# ------------------------------
# Train Model
# ------------------------------
@app.post("/train")
def train():
    train_model()
    return {"status": "trained"}


# ------------------------------
# Reminder Check
# ------------------------------
@app.post("/reminders/check")
def check_reminders():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT title, deadline FROM tasks
        WHERE status='pending'
    """)
    tasks = cur.fetchall()
    conn.close()

    today = datetime.now().date()
    for title, deadline in tasks:
        due = datetime.fromisoformat(deadline).date()
        if due == today:
            send_push("Reminder", f"Task due today: {title}")

    return {"status": "done"}
