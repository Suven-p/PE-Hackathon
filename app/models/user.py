from datetime import datetime, timezone

from peewee import CharField, DateTimeField

from app.database import BaseModel


class User(BaseModel):
    class Meta:
        table_name = "users"

    username = CharField(max_length=100, unique=False)
    email = CharField(max_length=255, unique=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
