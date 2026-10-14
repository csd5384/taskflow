from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app, store


@pytest.fixture
def client() -> Iterator[TestClient]:
    store.clear()
    with TestClient(app) as test_client:
        yield test_client
    store.clear()
