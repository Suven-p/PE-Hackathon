from datetime import datetime, timezone

from peewee import CharField, DateTimeField

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


def bulk_create_users(db, user_data_list):
    """Bulk create users from a list of dicts with 'username' and 'email' keys."""
    users_to_create = []
    imported = 0
    total = len(user_data_list)
    for data in user_data_list:
        username = data.get("username")
        email = data.get("email")
        if not username or not email:
            continue
        if len(username) > lengths["username"] or len(email) > lengths["email"]:
            continue
        users_to_create.append(data)

    if not users_to_create:
        return {"imported": 0, "total": total}

    with db.atomic():
        users = User.insert_many(
            users_to_create).on_conflict_ignore().returning(User.id).execute()
        imported = len(users)
    set_user_sequence_value(db)
    return {"imported": imported, "total": total}


def register_user(username: str, email: str) -> User:
    """Create and persist a new user. Raises ValueError for bad input."""
    if not username or not email:
        raise ValueError("Username and email are required")
    if len(username) > lengths["username"]:
        raise ValueError(
            f"Username too long. Must be at most {lengths['username']} characters")
    if len(email) > lengths["email"]:
        raise ValueError(
            f"Email too long. Must be at most {lengths['email']} characters")

    return User.create(username=username, email=email)


def update_user(id: int, username: str):
    """Update an existing user's username. Raises ValueError for bad input."""
    if not username:
        raise ValueError("Username is required")
    if len(username) > lengths["username"]:
        raise ValueError(
            f"Username too long. Must be at most {lengths['username']} characters")

    user = User.get_or_none(User.id == id)
    if not user:
        raise LookupError("User not found")

    user.username = username
    user.save()
    return user


def delete_user(id: int):
    """Delete a user by ID. Raises LookupError if user not found."""
    user = User.get_or_none(User.id == id)
    if not user:
        raise LookupError("User not found")
    user.delete_instance()


def set_user_sequence_value(db):
    """Set the sequence value for the users table to max(id)+1. Safe to run multiple times."""
    if is_postgres(db):
        db.execute_sql(
            f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), (SELECT COALESCE(MAX(id), 0) FROM {table_name}) + 1, false)"
        )
    else:
        raise NotImplementedError(
            "Sequence management not implemented for this database type")
