from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import app_settings

load_dotenv()


def _build_engine():
    settings = app_settings()
    url = settings["database_url"]
    connect_args = {}
    kwargs: dict = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        if url in {"sqlite://", "sqlite:///:memory:"}:
            kwargs["poolclass"] = StaticPool
    return create_engine(url, connect_args=connect_args, **kwargs)


engine = _build_engine()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def test_connection() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def create_tables() -> None:
    from app import models as _models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def reset_engine() -> None:
    """Rebuild the engine after DATABASE_URL changes (tests)."""
    global engine
    engine.dispose()
    engine = _build_engine()
    os.environ.setdefault("TESTING", "true")
