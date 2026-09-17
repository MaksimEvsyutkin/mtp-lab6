"""Database layer using SQLite for FastAPI application (Task Advanced 2)."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "app.db"


class Database:
    """SQLite Database manager for users and chat messages."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.db_path = str(db_path)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with Row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create tables if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'student',
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

            # Seed initial sample data if empty
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sample_users = [
                    ("maksim", "Евсюткин Максим Сергеевич", "admin", now),
                    ("alex", "Смирнов Алексей Игоревич", "student", now),
                    ("elena", "Кузнецова Елена Павловна", "teacher", now),
                    ("dmitry", "Васильев Дмитрий Олегович", "student", now),
                ]
                cursor.executemany(
                    "INSERT INTO users (username, full_name, role, created_at) VALUES (?, ?, ?, ?)",
                    sample_users,
                )
                conn.commit()

    def add_user(self, username: str, full_name: str, role: str = "student") -> Dict[str, Any]:
        """Insert a new user record."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, full_name, role, created_at) VALUES (?, ?, ?, ?)",
                (username.strip(), full_name.strip(), role.strip(), now),
            )
            user_id = cursor.lastrowid
            conn.commit()
            return {
                "id": user_id,
                "username": username.strip(),
                "full_name": full_name.strip(),
                "role": role.strip(),
                "created_at": now,
            }

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Retrieve all registered users."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, full_name, role, created_at FROM users ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]

    def add_message(self, author: str, content: str) -> Dict[str, Any]:
        """Insert a chat message."""
        now = datetime.now().strftime("%H:%M:%S")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (author, content, created_at) VALUES (?, ?, ?)",
                (author.strip(), content.strip(), now),
            )
            msg_id = cursor.lastrowid
            conn.commit()
            return {
                "id": msg_id,
                "author": author.strip(),
                "content": content.strip(),
                "created_at": now,
            }

    def get_recent_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent chat messages."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, author, content, created_at FROM messages ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in reversed(cursor.fetchall())]
