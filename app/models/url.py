import secrets
import string
from datetime import datetime, timezone

from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField, IntegrityError, PostgresqlDatabase

from app.database import BaseModel
from app.models.user import User
from app.utils.isPostgres import is_postgres

table_name = "urls"


class Url(BaseModel):
    class Meta:
        table_name = table_name
        indexes = (
            (("short_code",), True),  # UNIQUE index — also speeds up lookups
        )

    user = ForeignKeyField(User, backref="urls", null=True)
    short_code = CharField(max_length=10, unique=True)
    original_url = CharField(max_length=2048)
    title = CharField(max_length=255, null=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))


# --- Business logic (separated so it can be unit tested without Flask) ---

def generate_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def is_valid_url(url: str) -> bool:
    return (url.startswith("http://") or url.startswith("https://")) and len(url) <= 2048


def create_short_url(original_url: str, user=None, title: str = None) -> "Url":
    """Create and persist a short URL. Raises ValueError for bad input."""
    if not original_url or not is_valid_url(original_url):
        raise ValueError("URL must start with http:// or https://")

    for _ in range(5):
        code = generate_short_code()
        try:
            return Url.create(
                short_code=code,
                original_url=original_url,
                user=user,
                title=title,
                updated_at=datetime.now(timezone.utc),
            )
        except IntegrityError:
            continue

    raise RuntimeError("Could not generate a unique short code, please retry")


class UrlInactiveError(Exception):
    pass


def get_url_by_code(short_code: str) -> "Url":
    """Look up a URL by short code. Raises Url.DoesNotExist if not found, UrlInactiveError if inactive."""
    url = Url.get(Url.short_code == short_code)
    if not url.is_active:
        raise UrlInactiveError(short_code)
    return url


def update_short_url(url: "Url", original_url: str = None, title: str = None, is_active: bool = None) -> "Url":
    """Update a URL's fields. Only the owner should call this."""
    if original_url is not None:
        if not is_valid_url(original_url):
            raise ValueError("URL must start with http:// or https://")
        url.original_url = original_url
    if title is not None:
        url.title = title
    if is_active is not None:
        url.is_active = is_active
    url.updated_at = datetime.now(timezone.utc)
    url.save()
    return url


def set_url_sequence_value(db):
    """Set the sequence value for the urls table to max(id)+1. Safe to run multiple times."""
    if is_postgres(db):
        db.execute_sql(
            f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), (SELECT COALESCE(MAX(id), 0) FROM {table_name}) + 1, false)"
        )
    else:
        raise NotImplementedError(
            "Sequence management not implemented for this database type")
