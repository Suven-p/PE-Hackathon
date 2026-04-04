from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
import csv
import os

from app.database import init_db
from app.routes import register_routes
from app.models.user import User, set_user_sequence_value
from app.models.url import Url, set_url_sequence_value
from app.models.event import Event, set_event_sequence_value


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
            db.execute_sql(
                f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {definition}")
        except Exception:
            pass  # column already exists or table doesn't exist yet — safe=True handles that


def _insert_sample_data(db):
    should_initialize = os.environ.get(
        "DATABASE_INITIALIZE", "false").lower() == "true"
    if should_initialize:
        seed_directory = os.environ.get("DATABASE_SEED_DIRECTORY", "db_seed")
        if not os.path.isdir(seed_directory):
            print(f"Seed directory not found: {seed_directory}")
            return

        with open(os.path.join(seed_directory, "users.csv"), "r") as f:
            reader = csv.DictReader(f)
            data = list(reader)  # read all rows into memory to get the count
            print(f"Initializing database with {len(data)} users...")

            with db.atomic():
                User.insert_many(data).on_conflict_ignore().execute()
            set_user_sequence_value(db)

        with open(os.path.join(seed_directory, "urls.csv"), "r") as f:
            reader = csv.DictReader(f)
            data = list(reader)  # read all rows into memory to get the count
            print(f"Initializing database with {len(data)} URLs...")

            with db.atomic():
                Url.insert_many(data).on_conflict_ignore().execute()
            set_url_sequence_value(db)

        with open(os.path.join(seed_directory, "events.csv"), "r") as f:
            reader = csv.DictReader(f)
            data = list(reader)  # read all rows into memory to get the count
            print(f"Initializing database with {len(data)} events...")

            with db.atomic():
                Event.insert_many(data).on_conflict_ignore().execute()
            set_event_sequence_value(db)
    else:
        print("Database initialization skipped. Set DATABASE_INITIALIZE=true to enable.")


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
    _insert_sample_data(db)

    register_routes(app)

    @app.route("/health")
    def health():
        try:
            db.execute_sql("SELECT 1")
            return jsonify({"status": "success", "data": {"db": "connected"}})
        except Exception:
            return jsonify({"status": "error", "message": "Database unreachable"}), 503

    @app.errorhandler(Exception)
    def handle_exception(e):
        print(f"Unhandled exception: {e}")
        return {"error": "Internal server error"}, 500

    return app
