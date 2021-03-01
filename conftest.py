import pytest

from app import app


@pytest.fixture
def client():
    yield app.test_client
