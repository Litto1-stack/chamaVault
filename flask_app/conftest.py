"""Pytest config: puts this folder on sys.path and provides a freshly seeded app per test."""
import pytest

from app import create_app
from config import TestConfig
from seed import seed_demo


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        seed_demo()
        yield app


@pytest.fixture
def client(app):
    return app.test_client()
