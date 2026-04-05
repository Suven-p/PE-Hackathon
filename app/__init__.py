from logging.config import dictConfig
import time

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import csv
import os

from app.database import init_db
from app.logger import JsonFormatter
from app.routes import register_routes
from app.models.user import User, set_user_sequence_value
from app.models.url import Url, set_url_sequence_value
from app.models.event import Event, set_event_sequence_value


def _migrate_schema(db):
    """Add missing columns to existing tables without dropping data."""
    migrations = [
        ("urls", "user_id",     "INTEGER"),
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


def _insert_sample_data(db, logger):
    should_initialize = os.environ.get(
        "DATABASE_INITIALIZE", "true").lower() == "true"
    if should_initialize:
        seed_directory = os.environ.get("DATABASE_SEED_DIRECTORY", "db_seed")
        if not os.path.isdir(seed_directory):
            logger.warning("Seed directory not found: %s", seed_directory)
            return

        with open(os.path.join(seed_directory, "users.csv"), "r") as f:
            reader = csv.DictReader(f)
            data = list(reader)  # read all rows into memory to get the count
            logger.info("Initializing database with %d users...", len(data))

            with db.atomic():
                User.insert_many(data).on_conflict_ignore().execute()
            set_user_sequence_value(db)

        with open(os.path.join(seed_directory, "urls.csv"), "r") as f:
            reader = csv.DictReader(f)
            data = list(reader)  # read all rows into memory to get the count
            logger.info("Initializing database with %d URLs...", len(data))

            with db.atomic():
                Url.insert_many(data).on_conflict_ignore().execute()
            set_url_sequence_value(db)

        with open(os.path.join(seed_directory, "events.csv"), "r") as f:
            reader = csv.DictReader(f)
            data = list(reader)  # read all rows into memory to get the count
            logger.info("Initializing database with %d events...", len(data))

            with db.atomic():
                Event.insert_many(data).on_conflict_ignore().execute()
            set_event_sequence_value(db)
    else:
        logger.info(
            "Database initialization skipped. Set DATABASE_INITIALIZE=true to enable.")


def create_app():
    load_dotenv()

    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "json": {
                "()": JsonFormatter,
            }
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "json",
                "filename": "logs/application.log",
            },
        },

        "root": {
            "level": "INFO",
            "handlers": ["console", "file"]
        }
    })

    app = Flask(__name__)
    app.url_map.strict_slashes = False
    CORS(app)

    init_db(app)

    from app import models  # noqa: F401 - registers models with Peewee
    from app.database import db
    from app.models.user import User
    from app.models.url import Url
    from app.models.event import Event
    db.create_tables([User, Url, Event], safe=True)
    _migrate_schema(db)
    _insert_sample_data(db, app.logger)

    register_routes(app)

    @app.route("/health")
    def health():
        try:
            db.execute_sql("SELECT 1")
            return jsonify({"status": "ok"}), 200
        except Exception:
            return jsonify({"status": "error"}), 503

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return jsonify({"error": e.description}), e.code
        app.logger.error("Unhandled exception: %s", e)
        app.logger.exception(e)
        return {"error": "Internal server error"}, 500

    @app.before_request
    def start_timer():
        request.start_time = time.time()

    @app.after_request
    def log_request(response):
        try:
            duration = (time.time() - request.start_time) * 1000

            app.logger.info(
                "%s %s %s %0.2fms",
                request.method,
                request.path,
                response.status_code,
                duration
            )
        except Exception as e:
            print("Error logging request: %s", e)

        return response

    return app
