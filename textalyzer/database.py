import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_data.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            input_text TEXT NOT NULL,
            result_summary TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()


def create_user(username, email, password_hash, salt):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, email, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, email, password_hash, salt, datetime.now().isoformat()),
        )
        conn.commit()
        return True, "Account created successfully. Please log in."
    except sqlite3.IntegrityError:
        return False, "That username is already taken."
    finally:
        conn.close()


def get_user_by_username(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row


def add_history(user_id, action_type, input_text, result_summary):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO history (user_id, action_type, input_text, result_summary, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, action_type, input_text, result_summary, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_history(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM history WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_corpus_excluding_user(user_id, limit=500):
    """Texts submitted by OTHER users, used as the comparison corpus for plagiarism checks."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT h.input_text, u.username, h.created_at
        FROM history h JOIN users u ON h.user_id = u.id
        WHERE h.user_id != ? AND h.action_type = 'analysis'
        ORDER BY h.created_at DESC LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return rows
