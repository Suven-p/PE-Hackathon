from logging.config import dictConfig
import random
import socket
import string
import time
import uuid

from dotenv import load_dotenv
from flask import Flask, g, jsonify, request
from flask_cors import CORS
from peewee import InterfaceError, OperationalError
from werkzeug.exceptions import HTTPException
import csv
import os


from app.database import init_db
from app.errors import error_response
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


def get_log_filename():
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = None

    if not hostname:
        hostname = ''.join(random.choices(
            string.ascii_letters + string.digits, k=6))

    return f"application-{hostname}.log"


def create_app():
    load_dotenv()

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    log_dir = os.environ.get("LOG_DIR", os.path.join(project_root, "logs"))
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, get_log_filename())

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
                "filename": log_file,
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
    from prometheus_client import start_http_server, make_wsgi_app
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry import metrics
    from prometheus_client import make_wsgi_app
    from werkzeug.middleware.dispatcher import DispatcherMiddleware

    # Set up Prometheus metric reader
    reader = PrometheusMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)

    db.create_tables([User, Url, Event], safe=True)
    _migrate_schema(db)
    _insert_sample_data(db, app.logger)

    # Mount /metrics as a sub-application
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        '/prometheus': make_wsgi_app()
    })

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
            code = e.code or 500
            return error_response(
                e.description,
                code,
                error_code=f"http_{code}",
                retryable=code >= 500,
            )

        if isinstance(e, (OperationalError, InterfaceError)):
            app.logger.warning("Database unavailable: %s", e)
            return error_response(
                "Service temporarily unavailable",
                503,
                error_code="database_unavailable",
                retryable=True,
            )

        app.logger.error("Unhandled exception: %s", e)
        app.logger.exception(e)
        return error_response(
            "Internal server error",
            500,
            error_code="internal_server_error",
            retryable=True,
        )

    @app.before_request
    def start_timer():
        incoming_request_id = request.headers.get("X-Request-ID")
        g.request_id = incoming_request_id or str(uuid.uuid4())
        request.start_time = time.time()

    @app.after_request
    def log_request(response):
        response.headers["X-Request-ID"] = getattr(g, "request_id", "")
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
