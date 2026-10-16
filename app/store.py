"""In-memory to-do storage.

Deliberately simple: data lives in memory and resets when the app restarts.
The project is about the pipeline, not the database.
"""

from threading import Lock

from app.models import Todo, TodoCreate, TodoUpdate


class TodoStore:
    """Thread-safe in-memory store for to-do items."""

    def __init__(self) -> None:
        self._items: dict[int, Todo] = {}
        self._next_id = 1
        self._lock = Lock()

    def list(self) -> list[Todo]:
        with self._lock:
            return sorted(self._items.values(), key=lambda t: t.id)

    def get(self, todo_id: int) -> Todo | None:
        with self._lock:
            return self._items.get(todo_id)

    def create(self, data: TodoCreate) -> Todo:
        with self._lock:
            todo = Todo(id=self._next_id, title=data.title.strip())
            self._items[todo.id] = todo
            self._next_id += 1
            return todo

    def update(self, todo_id: int, data: TodoUpdate) -> Todo | None:
        with self._lock:
            current = self._items.get(todo_id)
            if current is None:
                return None
            changes = data.model_dump(exclude_none=True)
            if "title" in changes:
                changes["title"] = changes["title"].strip()
            updated = current.model_copy(update=changes)
            self._items[todo_id] = updated
            return updated

    def delete(self, todo_id: int) -> bool:
        with self._lock:
            return self._items.pop(todo_id, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
            self._next_id = 1
