from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from app.database import init_db
from app.routes import register_routes


def _migrate_schema(db):
    """Add missing columns to existing tables without dropping data."""
    migrations = [
        ("urls", "user_id",     "INTEGER REFERENCES users(id)"),
        ("urls", "title",       "VARCHAR(255)"),
        ("urls", "is_active",   "BOOLEAN NOT NULL DEFAULT TRUE"),
        ("urls", "updated_at",  "TIMESTAMP"),
    ]
    for table, column, definition in migrations:
        try:
            db.execute_sql(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {definition}")
        except Exception:
            pass  # column already exists or table doesn't exist yet — safe=True handles that


def create_app():
    load_dotenv()

    app = Flask(__name__)
    CORS(app)

    init_db(app)

    from app import models  # noqa: F401 - registers models with Peewee
    from app.database import db
    from app.models.user import User
    from app.models.url import Url
    from app.models.event import Event
    db.create_tables([User, Url, Event], safe=True)
    _migrate_schema(db)

    register_routes(app)

    @app.route("/health")
    def health():
        try:
            db.execute_sql("SELECT 1")
            return jsonify(status="ok", db="connected")
        except Exception:
            return jsonify(status="error", db="unreachable"), 503

    return app
