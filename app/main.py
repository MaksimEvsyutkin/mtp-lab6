"""FastAPI web application implementing Variant 2 tasks.

Tasks implemented:
- Medium 2: Form submission page (name -> greeting) at /greet
- Medium 4: Data table page displaying SQLite records at /table
- Medium 7: FastAPI endpoints returning JSON at /api/info and /api/users
- Advanced 2: SQLite database integration (users and messages)
- Advanced 6: Real-time WebSocket chat room at /chat and /ws/chat
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Form, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.database import Database
from app.websocket import ConnectionManager

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="Лабораторная работа №6 — Веб-программирование",
    description="Реализация варианта 2 (FastAPI, SQLite, Jinja2, WebSockets)",
    version="1.0.0",
)

# Mount static assets and Jinja2 templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Database and WebSocket connection manager singletons
db = Database()
ws_manager = ConnectionManager()


# Pydantic schemas for API endpoints
class UserCreate(BaseModel):
    """Request payload for user creation."""

    username: str = Field(..., min_length=2, max_length=50, description="Уникальный логин")
    full_name: str = Field(..., min_length=2, max_length=100, description="ФИО пользователя")
    role: str = Field("student", description="Роль пользователя (student/teacher/admin)")


class UserResponse(BaseModel):
    """User response model."""

    id: int
    username: str
    full_name: str
    role: str
    created_at: str


# ============================================================================
# HTML Web Pages (Jinja2)
# ============================================================================


@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request) -> HTMLResponse:
    """Render the home page detailing all completed Variant 2 tasks."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "active_tab": "home"},
    )


@app.get("/greet", response_class=HTMLResponse)
async def greet_page_get(request: Request) -> HTMLResponse:
    """Render the greeting form page (Task Medium 2)."""
    return templates.TemplateResponse(
        "greet.html",
        {"request": request, "active_tab": "greet", "greeting": None, "username": ""},
    )


@app.post("/greet", response_class=HTMLResponse)
async def greet_page_post(request: Request, username: str = Form(...)) -> HTMLResponse:
    """Process greeting form submission (Task Medium 2)."""
    clean_name = username.strip()
    greeting_message = f"Привет, {clean_name}!" if clean_name else "Привет, незнакомец!"
    return templates.TemplateResponse(
        "greet.html",
        {
            "request": request,
            "active_tab": "greet",
            "greeting": greeting_message,
            "username": clean_name,
        },
    )


@app.get("/table", response_class=HTMLResponse)
async def table_page(request: Request) -> HTMLResponse:
    """Render HTML table displaying database records (Task Medium 4 & Advanced 2)."""
    users = db.get_all_users()
    return templates.TemplateResponse(
        "table.html",
        {"request": request, "active_tab": "table", "users": users},
    )


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request) -> HTMLResponse:
    """Render real-time WebSocket chat room page (Task Advanced 6)."""
    messages = db.get_recent_messages(limit=50)
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "active_tab": "chat", "messages": messages},
    )


# ============================================================================
# REST API Endpoints (Task Medium 7 & Advanced 2)
# ============================================================================


@app.get("/api/info")
async def get_lab_info() -> Dict[str, Any]:
    """Return JSON metadata describing the lab work and student (Task Medium 7)."""
    return {
        "lab": 6,
        "title": "Веб-программирование на Python (FastAPI)",
        "author": "Евсюткин Максим Сергеевич",
        "group": "221141",
        "variant": 2,
        "tasks": {
            "medium_2": "Страница с формой: имя -> приветствие (/greet)",
            "medium_4": "Страница с таблицей данных (/table)",
            "medium_7": "FastAPI endpoint возвращает JSON (/api/info)",
            "advanced_2": "FastAPI с базой данных SQLite (/api/users, /table)",
            "advanced_6": "Приложение чат на WebSockets (/chat, /ws/chat)",
        },
        "status": "success",
    }


@app.get("/api/users", response_model=List[UserResponse])
async def list_users() -> List[Dict[str, Any]]:
    """Retrieve list of all users from SQLite database (Task Medium 7 & Advanced 2)."""
    return db.get_all_users()


@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate) -> Dict[str, Any]:
    """Add a new user to the SQLite database (Task Advanced 2)."""
    try:
        new_user = db.add_user(
            username=user.username,
            full_name=user.full_name,
            role=user.role,
        )
        return new_user
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка добавления пользователя: {exc}",
        )


@app.get("/api/messages")
async def list_recent_messages(limit: Optional[int] = 50) -> List[Dict[str, Any]]:
    """Retrieve recent chat messages from SQLite database."""
    safe_limit = max(1, min(limit or 50, 100))
    return db.get_recent_messages(limit=safe_limit)


# ============================================================================
# WebSocket Endpoint (Task Advanced 6)
# ============================================================================


@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket) -> None:
    """Handle bi-directional WebSocket connections for live group chat (Task Advanced 6)."""
    await ws_manager.connect(websocket)
    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                msg_payload = json.loads(raw_data)
                author = str(msg_payload.get("author", "Аноним")).strip() or "Аноним"
                text = str(msg_payload.get("text", "")).strip()
            except (json.JSONDecodeError, AttributeError):
                author = "Аноним"
                text = raw_data.strip()

            if not text:
                continue

            saved_msg = db.add_message(author=author, content=text)
            await ws_manager.broadcast(
                author=saved_msg["author"],
                text=saved_msg["content"],
                timestamp=saved_msg["created_at"],
            )
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
