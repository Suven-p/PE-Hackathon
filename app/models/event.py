import json
from datetime import datetime, timezone

from peewee import DateTimeField, ForeignKeyField, PostgresqlDatabase, TextField

from app.database import BaseModel
from app.models.url import Url
from app.models.user import User
from app.utils.isPostgres import is_postgres

table_name = "events"


class Event(BaseModel):
    class Meta:
        table_name = table_name

    url = ForeignKeyField(Url, backref="events")
    user = ForeignKeyField(User, backref="events", null=True)
    event_type = TextField()
    timestamp = DateTimeField(default=lambda: datetime.now(timezone.utc))
    details = TextField(null=True)  # stored as JSON string


# --- Business logic ---

def log_event(url: Url, event_type: str, user=None, details: dict = None) -> None:
    """Record an event for a URL. Best-effort: never raises."""
    try:
        Event.create(
            url=url,
            user=user,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            details=json.dumps(details, default=str) if details else None,
        )
    except Exception:
        pass


def get_events_for_url(url: Url) -> list:
    """Return all events for a given URL, newest first."""
    return list(Event.select().where(Event.url == url).order_by(Event.timestamp.desc()))


def set_event_sequence_value(db):
    """Set the sequence value for the events table to max(id)+1. Safe to run multiple times."""
    if is_postgres(db):
        db.execute_sql(
            f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), (SELECT COALESCE(MAX(id), 0) FROM {table_name}) + 1, false)"
        )
    else:
        raise NotImplementedError(
            "Sequence management not implemented for this database type")
