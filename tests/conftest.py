# Set before create_app() so load_dotenv() inside won't override them.
# To run integration tests locally: createdb hackathon_test
import os

os.environ["DATABASE_INITIALIZE"] = "false"
os.environ["DATABASE_SSL"] = "false"
os.environ.setdefault("DATABASE_NAME", "hackathon_test")
os.environ.setdefault("DATABASE_HOST", "localhost")
os.environ.setdefault("DATABASE_PORT", "5432")
os.environ.setdefault("DATABASE_USER", "postgres")
os.environ.setdefault("DATABASE_PASSWORD", "postgres")

import pytest

from app import create_app
from app.database import db
from app.models.event import Event
from app.models.url import Url
from app.models.user import User


@pytest.fixture(scope="session")
def app():
    """Create a single Flask app instance for the entire test session."""
    application = create_app()
    application.config["TESTING"] = True
    yield application


@pytest.fixture(scope="session")
def client(app):
    """Flask test client — reused across all tests."""
    return app.test_client()


@pytest.fixture()
def clean_tables(app):
    """Wipe all rows before each integration test. Not autouse — unit tests don't need DB."""
    with app.app_context():
        db.connect(reuse_if_open=True)
        Event.delete().execute()
        Url.delete().execute()
        User.delete().execute()
    yield
