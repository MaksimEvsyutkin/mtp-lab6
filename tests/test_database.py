"""Unit tests for SQLite database manager (Task Advanced 2)."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database import Database


class TestDatabaseManager(unittest.TestCase):
    """Test suite for Database operations."""

    def setUp(self) -> None:
        """Create a temporary database file for isolated testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_app.db"
        self.db = Database(db_path=self.db_path)

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_init_db_seeds_initial_users(self) -> None:
        """Verify that newly initialized database contains seed users."""
        users = self.db.get_all_users()
        self.assertGreaterEqual(len(users), 4)

        usernames = [u["username"] for u in users]
        self.assertIn("maksim", usernames)
        self.assertIn("alex", usernames)
        self.assertIn("elena", usernames)
        self.assertIn("dmitry", usernames)

    def test_add_user_success(self) -> None:
        """Verify inserting a new user record."""
        new_user = self.db.add_user(
            username="ivan_test",
            full_name="Иванов Иван Иванович",
            role="student",
        )
        self.assertIsNotNone(new_user["id"])
        self.assertEqual(new_user["username"], "ivan_test")
        self.assertEqual(new_user["full_name"], "Иванов Иван Иванович")
        self.assertEqual(new_user["role"], "student")
        self.assertIn("created_at", new_user)

        # Check that user is in all_users list
        all_users = self.db.get_all_users()
        found = any(u["username"] == "ivan_test" for u in all_users)
        self.assertTrue(found)

    def test_add_duplicate_username_raises_error(self) -> None:
        """Verify that inserting duplicate username raises IntegrityError."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.add_user(
                username="maksim",  # Already seeded
                full_name="Дубликат Максим",
                role="student",
            )

    def test_add_and_retrieve_messages(self) -> None:
        """Verify inserting and fetching chat messages."""
        msg1 = self.db.add_message(author="Тестер", content="Сообщение 1")
        msg2 = self.db.add_message(author="Максим", content="Сообщение 2")

        self.assertEqual(msg1["author"], "Тестер")
        self.assertEqual(msg1["content"], "Сообщение 1")
        self.assertEqual(msg2["author"], "Максим")
        self.assertEqual(msg2["content"], "Сообщение 2")

        recent = self.db.get_recent_messages(limit=10)
        self.assertGreaterEqual(len(recent), 2)
        contents = [m["content"] for m in recent]
        self.assertIn("Сообщение 1", contents)
        self.assertIn("Сообщение 2", contents)

    def test_get_recent_messages_limit(self) -> None:
        """Verify message limit constraint."""
        for i in range(10):
            self.db.add_message(author="User", content=f"Msg {i}")

        limited = self.db.get_recent_messages(limit=5)
        self.assertEqual(len(limited), 5)


if __name__ == "__main__":
    unittest.main()
