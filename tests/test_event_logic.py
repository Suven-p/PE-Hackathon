"""
Unit tests for Event business logic (app/models/event.py).
serialize_event and _get_primary_key are pure functions — no DB needed.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.models.event import _get_primary_key, serialize_event


class TestGetPrimaryKey:
    def test_none_returns_none(self):
        assert _get_primary_key(None) is None

    def test_integer_returns_integer(self):
        assert _get_primary_key(5) == 5

    def test_object_with_id_returns_id(self):
        obj = MagicMock()
        obj.id = 42
        assert _get_primary_key(obj) == 42

    def test_string_without_id_returns_string(self):
        assert _get_primary_key("abc") == "abc"


class TestSerializeEvent:
    def _make_event(self, details=None, timestamp=None):
        import json
        event = MagicMock()
        event.id = 1
        event.url_id = 10
        event.user_id = 2
        event.event_type = "redirected"
        event.timestamp = timestamp or datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        event.details = json.dumps(details) if details is not None else None
        return event

    def test_basic_fields_are_present(self):
        event = self._make_event()
        result = serialize_event(event)
        assert result["id"] == 1
        assert result["url_id"] == 10
        assert result["user_id"] == 2
        assert result["event_type"] == "redirected"

    def test_details_are_deserialized_from_json(self):
        event = self._make_event(details={"short_code": "abc123"})
        result = serialize_event(event)
        assert result["details"] == {"short_code": "abc123"}

    def test_null_details_returns_none(self):
        event = self._make_event(details=None)
        result = serialize_event(event)
        assert result["details"] is None

    def test_timestamp_is_iso_format(self):
        ts = datetime(2024, 6, 1, 9, 30, 0, tzinfo=timezone.utc)
        event = self._make_event(timestamp=ts)
        result = serialize_event(event)
        assert result["timestamp"] == ts.isoformat()
