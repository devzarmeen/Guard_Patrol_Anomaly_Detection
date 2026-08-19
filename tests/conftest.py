import os

os.environ["TESTING"] = "true"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["WEBHOOK_URL"] = ""
os.environ["SMTP_HOST"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

import app.database as db
from app.main import create_app


@pytest.fixture(autouse=True)
def fresh_database():
    db.reset_engine()
    SQLModel.metadata.drop_all(db.engine)
    SQLModel.metadata.create_all(db.engine)
    yield


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def session():
    with Session(db.engine) as db_session:
        yield db_session
