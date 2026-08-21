import pytest
import sys
import os
from datetime import datetime, timezone
from uuid import uuid4

# Add the parent directory to path so app module can be found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.database import Base, get_db
from app.models import User, RoleEnum
import bcrypt

# Use PostgreSQL for testing (supports UUID natively)
# Make sure to create test database: CREATE DATABASE test_userdb;
DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:Dinidu2005@localhost:5432/test_userdb")

engine = create_engine(DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override database dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db_session():
    """Create a clean database session for each test"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user"""
    hashed = bcrypt.hashpw("TestPassword123!".encode("utf-8"), bcrypt.gensalt())
    user = User(
        id=uuid4(),
        name="Test User",
        email="test@example.com",
        password_hash=hashed.decode("utf-8"),
        role=RoleEnum.customer,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_admin(db_session):
    """Create a test admin user"""
    hashed = bcrypt.hashpw("AdminPassword123!".encode("utf-8"), bcrypt.gensalt())
    admin = User(
        id=uuid4(),
        name="Test Admin",
        email="admin@example.com",
        password_hash=hashed.decode("utf-8"),
        role=RoleEnum.admin,
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture(scope="function")
def test_inactive_user(db_session):
    """Create an inactive test user"""
    hashed = bcrypt.hashpw("InactivePassword123!".encode("utf-8"), bcrypt.gensalt())
    user = User(
        id=uuid4(),
        name="Inactive User",
        email="inactive@example.com",
        password_hash=hashed.decode("utf-8"),
        role=RoleEnum.customer,
        is_active=False,
        deleted_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def auth_headers(test_user, client):
    """Get authentication headers for test user"""
    response = client.post("/api/v1/users/login", json={
        "email": "test@example.com",
        "password": "TestPassword123!"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def admin_headers(test_admin, client):
    """Get authentication headers for admin user"""
    response = client.post("/api/v1/users/login", json={
        "email": "admin@example.com",
        "password": "AdminPassword123!"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def refresh_token(test_user, client):
    """Get refresh token for test user"""
    response = client.post("/api/v1/users/login", json={
        "email": "test@example.com",
        "password": "TestPassword123!"
    })
    return response.json()["refresh_token"]