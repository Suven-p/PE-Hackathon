from datetime import datetime, timezone

from peewee import CharField, DateTimeField, PostgresqlDatabase

from app.database import BaseModel
from app.utils.isPostgres import is_postgres

lengths = {
    "username": 100,
    "email": 255,
}

table_name = "users"


class User(BaseModel):
    class Meta:
        table_name = table_name

    username = CharField(max_length=lengths["username"], unique=False)
    email = CharField(max_length=lengths["email"], unique=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))



def set_user_sequence_value(db):
    """Set the sequence value for the users table to max(id)+1. Safe to run multiple times."""
    if is_postgres(db):
        db.execute_sql(
            f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), (SELECT COALESCE(MAX(id), 0) FROM {table_name}) + 1, false)"
        )
    else:
        raise NotImplementedError(
            "Sequence management not implemented for this database type")
