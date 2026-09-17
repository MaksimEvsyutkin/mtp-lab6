"""Integration tests for FastAPI application endpoints, forms, API and WebSockets."""

import unittest

try:
    from fastapi.testclient import TestClient
    from app.main import app
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


@unittest.skipUnless(HAS_FASTAPI, "FastAPI / TestClient dependencies not available")
class TestFastAPIApp(unittest.TestCase):
    """Integration test suite using TestClient."""

    @classmethod
    def setUpClass(cls) -> None:
        """Initialize TestClient."""
        cls.client = TestClient(app)

    def test_index_page(self) -> None:
        """Verify home page loads and displays lab title and variant."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Лабораторная работа №6", response.text)
        self.assertIn("Евсюткин Максим Сергеевич", response.text)
        self.assertIn("вариант 2", response.text)

    def test_greet_page_get(self) -> None:
        """Verify greeting page loads form (Task Medium 2)."""
        response = self.client.get("/greet")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<form", response.text)
        self.assertIn("name=\"username\"", response.text)

    def test_greet_page_post_success(self) -> None:
        """Verify POST submission with name generates greeting (Task Medium 2)."""
        response = self.client.post("/greet", data={"username": "Максим"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Привет, Максим!", response.text)

    def test_greet_page_post_empty_fallback(self) -> None:
        """Verify POST submission with empty name falls back gracefully."""
        response = self.client.post("/greet", data={"username": "   "})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Привет, незнакомец!", response.text)

    def test_table_page(self) -> None:
        """Verify HTML table displays SQLite users (Task Medium 4 & Advanced 2)."""
        response = self.client.get("/table")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<table>", response.text)
        self.assertIn("maksim", response.text)

    def test_chat_page(self) -> None:
        """Verify chat room page loads (Task Advanced 6)."""
        response = self.client.get("/chat")
        self.assertEqual(response.status_code, 200)
        self.assertIn("WebSocket Чат", response.text)
        self.assertIn("/ws/chat", response.text)

    def test_api_info_endpoint(self) -> None:
        """Verify /api/info returns JSON with student & task info (Task Medium 7)."""
        response = self.client.get("/api/info")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["lab"], 6)
        self.assertEqual(data["variant"], 2)
        self.assertEqual(data["author"], "Евсюткин Максим Сергеевич")
        self.assertEqual(data["group"], "221141")
        self.assertIn("tasks", data)

    def test_api_users_list(self) -> None:
        """Verify /api/users returns list of user objects (Task Medium 7 & Advanced 2)."""
        response = self.client.get("/api/users")
        self.assertEqual(response.status_code, 200)
        users = response.json()
        self.assertIsInstance(users, list)
        self.assertGreaterEqual(len(users), 4)
        self.assertTrue(any(u["username"] == "maksim" for u in users))

    def test_api_users_create(self) -> None:
        """Verify creating a user via POST /api/users (Task Advanced 2)."""
        new_user_data = {
            "username": "api_tester_unique",
            "full_name": "API Тестовый Пользователь",
            "role": "student",
        }
        response = self.client.post("/api/users", json=new_user_data)
        self.assertEqual(response.status_code, 201)
        created = response.json()
        self.assertEqual(created["username"], "api_tester_unique")
        self.assertEqual(created["full_name"], "API Тестовый Пользователь")

    def test_api_users_create_invalid(self) -> None:
        """Verify invalid user creation fails with 422."""
        response = self.client.post("/api/users", json={"username": "a"})  # too short
        self.assertEqual(response.status_code, 422)

    def test_api_messages_list(self) -> None:
        """Verify /api/messages returns message list."""
        response = self.client.get("/api/messages")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_websocket_chat(self) -> None:
        """Verify bi-directional communication over WebSocket (Task Advanced 6)."""
        with self.client.websocket_connect("/ws/chat") as websocket:
            payload = {"author": "Автотест", "text": "Тестовое сообщение через WebSocket"}
            websocket.send_json(payload)
            data = websocket.receive_json()
            self.assertEqual(data["author"], "Автотест")
            self.assertEqual(data["text"], "Тестовое сообщение через WebSocket")
            self.assertIn("timestamp", data)


if __name__ == "__main__":
    unittest.main()
