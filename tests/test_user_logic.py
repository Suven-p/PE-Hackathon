"""
Unit tests for User business logic (app/models/user.py).
Only tests validation paths that raise before touching the database.
DB-dependent paths (duplicate email check, actual create) are covered
by integration tests in test_api_users.py.
"""
import pytest

from app.models.user import register_user, update_user


class TestRegisterUserValidation:
    def test_missing_username_raises(self):
        with pytest.raises(ValueError, match="required"):
            register_user(username="", email="a@example.com")

    def test_missing_email_raises(self):
        with pytest.raises(ValueError, match="required"):
            register_user(username="alice", email="")

    def test_username_too_long_raises(self):
        with pytest.raises(ValueError, match="Username too long"):
            register_user(username="a" * 101, email="a@example.com")

    def test_email_too_long_raises(self):
        with pytest.raises(ValueError, match="Email too long"):
            register_user(username="alice", email="a" * 256 + "@example.com")


class TestUpdateUserValidation:
    def test_missing_username_raises(self):
        with pytest.raises(ValueError, match="Username is required"):
            update_user(id=1, username="")

    def test_username_too_long_raises(self):
        with pytest.raises(ValueError, match="Username too long"):
            update_user(id=1, username="a" * 101)
