import pytest
import asyncio
from app.storage.db import Database

@pytest.fixture
def test_db():
    """Provide a test database instance"""
    db = Database("sqlite:///:memory:")
    yield db
    db.close()

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
