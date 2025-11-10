from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

from database import create_tables, connect, add_token
from model import predict_duration, train_model
from push import send_push

# Initialize Database
create_tables()

# Create App
app = FastAPI()

# CORS Setup (allow frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # You can restrict this to your domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------- MODELS -----------

class TaskIn(BaseModel):
    title: str
    deadline: str
    importance: int

class Token(BaseModel):
    fcm_token: str


# ----------- ROUTES -----------

@app.get("/")
def home():
    return {"message": "TaskPlanner Backend Running ✅"}


# ✅ Add Task
@app.post("/tasks")
def add_task(t: TaskIn):
    hour = datetime.now().hour
    predicted = predict_duration(t.importance, hour)

    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tasks (title, deadline, importance, status, created_at, predicted_minutes)
        VALUES (?, ?, ?, 'pending', ?, ?)
    """, (t.title, t.deadline, t.importance, datetime.now().isoformat(), predicted))
    conn.commit()
    conn.close()

    # Push Notification
    send_push("New Task Added", t.title)

    return {"status": "ok", "predicted_minutes": predicted}


# ✅ Get All Tasks
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


# ✅ Register Device Token
@app.post("/register")
def register_token(t: Token):
    add_token(t.fcm_token)
    return {"status": "registered"}


# ✅ Train ML Model
@app.post("/train")
def train():
    train_model()
    return {"status": "trained"}


# ✅ Reminder Check (Auto push)
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
        try:
            due = datetime.fromisoformat(deadline).date()
            if due == today:
                send_push("Reminder", f"Task due today: {title}")
        except:
            continue

    return {"status": "done"}


# ✅ REQUIRED FOR RENDER DEPLOYMENT
# Render launches using:  uvicorn app:app --host 0.0.0.0 --port 10000

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
