import json
from datetime import datetime, timezone

from peewee import DateTimeField, IntegerField, TextField

from app.database import BaseModel
from app.utils.isPostgres import is_postgres

table_name = "events"


class Event(BaseModel):
    class Meta:
        table_name = table_name

    url_id = IntegerField(null=True)
    user_id = IntegerField(null=True)
    event_type = TextField()
    timestamp = DateTimeField(default=lambda: datetime.now(timezone.utc))
    details = TextField(null=True)  # stored as JSON string


# --- Business logic ---
def serialize_event(event: Event) -> dict:
    """Convert an Event instance to a dict for JSON serialization."""
    return {
        "id": event.id,
        "url_id": event.url_id,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "details": json.loads(event.details) if event.details else None,
    }


def _get_primary_key(value):
    if value is None:
        return None
    return getattr(value, "id", value)


def log_event(url, event_type: str, user=None, details: dict = None) -> None:
    """Record an event for a URL. Best-effort: never raises."""
    try:
        Event.create(
            url_id=_get_primary_key(url),
            user_id=_get_primary_key(user),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            details=json.dumps(details, default=str) if details else None,
        )
    except Exception as e:
        print(f"Error logging event: {e}")
        print(
            f"Failed to log event: url_id={_get_primary_key(url) if url is not None else 'N/A'}, event_type={event_type}, user_id={_get_primary_key(user) if user is not None else 'N/A'}, details={details}")


def get_events_for_url(url) -> list:
    """Return all events for a given URL, newest first."""
    url_id = _get_primary_key(url)
    events = Event.select().where(Event.url_id == url_id).order_by(Event.timestamp.desc())
    return list(events)


def get_all_events() -> list:
    """Return all events, newest first."""
    return list(Event.select().order_by(Event.timestamp.desc()))


def set_event_sequence_value(db):
    """Set the sequence value for the events table to max(id)+1. Safe to run multiple times."""
    if is_postgres(db):
        db.execute_sql(
            f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), (SELECT COALESCE(MAX(id), 0) FROM {table_name}) + 1, false)"
        )
    else:
        raise NotImplementedError(
            "Sequence management not implemented for this database type")
