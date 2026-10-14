from app.models import TodoCreate, TodoUpdate
from app.store import TodoStore


def test_ids_increment() -> None:
    store = TodoStore()
    first = store.create(TodoCreate(title="a"))
    second = store.create(TodoCreate(title="b"))
    assert (first.id, second.id) == (1, 2)


def test_update_only_changes_given_fields() -> None:
    store = TodoStore()
    todo = store.create(TodoCreate(title="keep me"))
    updated = store.update(todo.id, TodoUpdate(done=True))
    assert updated is not None
    assert updated.title == "keep me"
    assert updated.done is True


def test_update_missing_returns_none() -> None:
    assert TodoStore().update(42, TodoUpdate(done=True)) is None


def test_clear_resets_ids() -> None:
    store = TodoStore()
    store.create(TodoCreate(title="x"))
    store.clear()
    assert store.list() == []
    assert store.create(TodoCreate(title="y")).id == 1
