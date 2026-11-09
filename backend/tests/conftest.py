import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import app


@pytest.fixture(autouse=True)
def test_database():
    test_engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def enable_sqlite_foreign_keys(
        dbapi_connection,
        connection_record,
    ):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=test_engine)

    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    def override_get_db():
        with TestingSessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    # Seed the three original sample parts for each test.
    with TestingSessionLocal() as db:
        db.add_all([
            models.Part(
                id=1,
                name="LED Bulb 9W",
                category="electrical",
                quantity=50,
            ),
            models.Part(
                id=2,
                name="PVC Pipe 1/2 inch",
                category="plumbing",
                quantity=30,
            ),
            models.Part(
                id=3,
                name="Electrical Outlet",
                category="electrical",
                quantity=20,
            ),
        ])
        db.commit()

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()