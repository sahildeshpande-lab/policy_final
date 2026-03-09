import sqlite3
from pathlib import Path

import uuid


DB_PATH = Path("conversation_history.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn




def create_tables():
    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        thread_id TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id)
            REFERENCES users(user_id)
            ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversation_messages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id TEXT NOT NULL,
        user_message TEXT,
        assistant_message TEXT,
        policies_used TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (thread_id)
            REFERENCES conversations(thread_id)
            ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()




def create_user(user_id: str, email: str, name: str | None = None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO users (user_id, email, name)
    VALUES (?, ?, ?)
    """, (user_id, email, name))

    conn.commit()
    conn.close()


def get_user_by_email(email: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, email, name
        FROM users
        WHERE email = ?
    """, (email,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "user_id": row["user_id"],
            "email": row["email"],
            "name": row["name"]
        }
    return None

def create_conversation(user_id: str, thread_id: str, title: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO conversations (user_id, thread_id, title)
    VALUES (?, ?, ?)
    """, (user_id, thread_id, title))

    conn.commit()
    conn.close()


def add_message(
    thread_id: str,
    user_message: str,
    assistant_message: str,
    policies_used: list[str] | None = None
):
    conn = get_connection()
    cursor = conn.cursor()

    policies_text = ",".join(policies_used) if policies_used else None

    cursor.execute("""
    INSERT INTO conversation_messages (
        thread_id,
        user_message,
        assistant_message,
        policies_used
    )
    VALUES (?, ?, ?, ?)
    """, (thread_id, user_message, assistant_message, policies_text))

    conn.commit()
    conn.close()


def get_conversation_messages(thread_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT user_message, assistant_message, created_at
    FROM conversation_messages
    WHERE thread_id = ?
    ORDER BY created_at ASC
    """, (thread_id,))

    rows = cursor.fetchall()
    conn.close()
    return rows

def login_or_create_user(email: str, name: str | None = None):
    user = get_user_by_email(email)

    if user:
        return user

    user_id = str(uuid.uuid4())
    create_user(user_id, email, name)

    return {
        "user_id": user_id,
        "email": email,
        "name": name
    }



def list_conversations(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT conversation_id, thread_id, title, created_at
    FROM conversations
    WHERE user_id = ?
    ORDER BY created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()
    return rows

def update_conversation_title(thread_id: str, title: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE conversations
    SET title = ?
    WHERE thread_id = ?
    """, (title, thread_id))

    conn.commit()
    conn.close()

def get_conversation_messages(thread_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_message, assistant_message, created_at
        FROM conversation_messages
        WHERE thread_id = ?
        ORDER BY created_at ASC
    """, (thread_id,))

    rows = cursor.fetchall()
    conn.close()

    messages = []
    for row in rows:
        messages.append({
            "user_message": row[0],
            "assistant_message": row[1],
            "created_at": row[2]
        })

    return messages

def get_user_conversations(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT thread_id, title, created_at
        FROM conversations
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "thread_id": row[0],
            "title": row[1],
            "created_at": row[2]
        }
        for row in rows
    ]



if __name__ == "__main__":
    create_tables()
    print(" SQLite conversation history database initialized")
