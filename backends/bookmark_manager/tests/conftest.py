import os
import tempfile

# Configure environment BEFORE importing the app
_tmp = tempfile.NamedTemporaryFile(suffix=".db", prefix="test_temp_", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("RATELIMIT_STORAGE_URI", "memory://")

import fakeredis  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402
from sqlmodel.pool import StaticPool  # noqa: E402

# Inject fakeredis as the module's Redis client — the lazy get_redis() helper
# will return whatever set_redis() last installed.
from app.redis_client import set_redis  # noqa: E402

set_redis(fakeredis.FakeRedis(decode_responses=True))

# Stub Celery .delay() so tests don't require a running broker. We're not
# testing the worker here, only that the task gets enqueued.
import app.tasks  # noqa: E402

app.tasks.fetch_bookmark_metadata.delay = lambda *args, **kwargs: None  # type: ignore[method-assign]

from app.database import get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.security import create_access_token, hash_password  # noqa: E402


@pytest.fixture(name="session")
def session_fixture(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    # Make Celery tasks use the same engine as the API for testability.
    # tasks.py does `from app.database import engine`, so we rebind the name
    # in the tasks module rather than mutating app.database.
    monkeypatch.setattr("app.tasks.engine", engine, raising=False)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="user")
def user_fixture(session):
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash=hash_password("testpass123"),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="user_token")
def user_token_fixture(user):
    return create_access_token(subject=user.username)


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(user_token):
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture(name="other_user")
def other_user_fixture(session):
    user = User(
        email="other@example.com",
        username="otheruser",
        password_hash=hash_password("otherpass123"),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="other_auth_headers")
def other_auth_headers_fixture(other_user):
    token = create_access_token(subject=other_user.username)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def clear_redis():
    """Clear the fake Redis between tests so blocklist state doesn't leak."""
    from app.redis_client import get_redis

    get_redis().flushdb()
    yield
