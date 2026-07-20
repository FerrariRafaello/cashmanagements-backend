# IMPORTS
import os
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
from slowapi import Limiter

from app.main import app
from app.db.database import Base, get_db


# Use a separate test database
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rafaelloferrari@localhost:5432/cashmanagements_test"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def disable_rate_limit():
    with patch("app.middleware.security.limiter.enabled", False):
        yield


@pytest.fixture(scope="function")
def db():
    """Creates a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Creates a test client with the test database."""
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
