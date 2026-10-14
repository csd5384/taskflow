"""FastAPI application: JSON API under /api plus a tiny web UI at /."""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse

from app.models import Todo, TodoCreate, TodoUpdate
from app.store import TodoStore

# The pipeline bakes the commit SHA into the Docker image (see Dockerfile).
# /health reports it, so you can verify WHICH version is live after a deploy.
APP_VERSION = os.getenv("APP_VERSION", "dev")
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Taskflow", version=APP_VERSION)
store = TodoStore()


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check used by the deploy smoke test."""
    return {"status": "ok", "version": APP_VERSION}


@app.get("/api/todos")
def list_todos() -> list[Todo]:
    return store.list()


@app.post("/api/todos", status_code=status.HTTP_201_CREATED)
def create_todo(data: TodoCreate) -> Todo:
    return store.create(data)


@app.get("/api/todos/{todo_id}")
def get_todo(todo_id: int) -> Todo:
    todo = store.get(todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="To-do not found")
    return todo


@app.patch("/api/todos/{todo_id}")
def update_todo(todo_id: int, data: TodoUpdate) -> Todo:
    todo = store.update(todo_id, data)
    if todo is None:
        raise HTTPException(status_code=404, detail="To-do not found")
    return todo


@app.delete("/api/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int) -> Response:
    if not store.delete(todo_id):
        raise HTTPException(status_code=404, detail="To-do not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
