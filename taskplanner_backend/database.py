import sqlite3

DB = "tasks.db"

def connect():
    return sqlite3.connect(DB, check_same_thread=False)

def create_tables():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        deadline TEXT,
        importance INTEGER,
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        completed_at TEXT,
        duration_minutes REAL,
        completed_hour INTEGER,
        predicted_minutes REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fcm_token TEXT
    )
    """)

    conn.commit()
    conn.close()

def add_token(token):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO devices (fcm_token) VALUES (?)", (token,))
    conn.commit()
    conn.close()

def get_tokens():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT fcm_token FROM devices")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows
