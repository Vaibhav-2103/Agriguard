import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import Base, get_db
from backend.auth import hash_password, create_access_token
from backend.models import User

# Use an in-memory SQLite DB for tests
TEST_DATABASE_URL = "sqlite:///./test_agriguard.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_agriguard.db"):
        try:
            os.remove("./test_agriguard.db")
        except Exception:
            pass


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_farmer(db_session):
    user = db_session.query(User).filter(User.email == "test_farmer@test.com").first()
    if not user:
        user = User(
            name="Test Farmer",
            email="test_farmer@test.com",
            password_hash=hash_password("password123"),
            role="farmer",
            preferred_language="en"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def farmer_token(test_farmer):
    return create_access_token(data={"sub": str(test_farmer.id), "role": test_farmer.role, "name": test_farmer.name})


@pytest.fixture
def test_farmer2(db_session):
    user = db_session.query(User).filter(User.email == "farmer2@test.com").first()
    if not user:
        user = User(
            name="Farmer Two",
            email="farmer2@test.com",
            password_hash=hash_password("password123"),
            role="farmer",
            preferred_language="en"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def farmer2_token(test_farmer2):
    return create_access_token(data={"sub": str(test_farmer2.id), "role": test_farmer2.role, "name": test_farmer2.name})


@pytest.fixture
def test_expert(db_session):
    user = db_session.query(User).filter(User.email == "test_expert@test.com").first()
    if not user:
        user = User(
            name="Test Expert",
            email="test_expert@test.com",
            password_hash=hash_password("password123"),
            role="expert",
            preferred_language="en"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def expert_token(test_expert):
    return create_access_token(data={"sub": str(test_expert.id), "role": test_expert.role, "name": test_expert.name})
