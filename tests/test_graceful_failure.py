"""
Graceful failure integration tests.
"""

import pytest
from peewee import OperationalError

import app.routes.users as users_routes

pytestmark = pytest.mark.usefixtures("clean_tables")


def assert_error_contract(payload, status_code):
    assert payload["http_status"] == status_code
    assert payload["status"] == status_code
    assert isinstance(payload["error"], str)
    assert isinstance(payload["message"], str)
    assert payload["message"] == payload["error"]
    assert isinstance(payload["error_code"], str)
    assert isinstance(payload["retryable"], bool)
    assert isinstance(payload["request_id"], str)
    assert payload["request_id"]


def test_invalid_json_body_returns_clean_400(client):
    res = client.post("/users/", data="{", content_type="application/json")

    assert res.status_code == 400
    payload = res.get_json()
    assert_error_contract(payload, 400)
    assert payload["error_code"] == "http_400"


def test_invalid_query_param_returns_clean_400(client):
    res = client.get("/urls?is_active=maybe")

    assert res.status_code == 400
    payload = res.get_json()
    assert_error_contract(payload, 400)
    assert payload["error_code"] == "invalid_is_active"


def test_invalid_event_details_returns_clean_400(client):
    create_user = client.post("/users/", json={"username": "alice", "email": "alice@example.com"})
    user = create_user.get_json()
    create_url = client.post(
        "/urls",
        json={
            "user_id": user["id"],
            "original_url": "https://example.com",
            "title": "Example",
        },
    )
    url = create_url.get_json()

    res = client.post(
        "/events/",
        json={
            "url_id": url["id"],
            "user_id": user["id"],
            "event_type": "clicked",
            "details": 123,
        },
    )

    assert res.status_code == 400
    payload = res.get_json()
    assert_error_contract(payload, 400)
    assert payload["error_code"] == "invalid_details"


def test_database_outage_returns_clean_503(client, monkeypatch):
    def raise_db_error(*_args, **_kwargs):
        raise OperationalError("database is down")

    monkeypatch.setattr(users_routes, "register_user", raise_db_error)

    res = client.post("/users/", json={"username": "alice", "email": "alice@example.com"})

    assert res.status_code == 503
    payload = res.get_json()
    assert_error_contract(payload, 503)
    assert payload["error_code"] == "database_unavailable"
    assert payload["retryable"] is True
