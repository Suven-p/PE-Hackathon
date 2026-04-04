import json
from datetime import datetime, timezone

from peewee import DateTimeField, ForeignKeyField, TextField

from app.database import BaseModel
from app.models.url import Url
from app.models.user import User


class Event(BaseModel):
    class Meta:
        table_name = "events"

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
