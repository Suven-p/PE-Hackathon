"""
Error contract integration tests.
"""

import pytest

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


def test_user_create_missing_email_uses_error_contract(client):
    res = client.post("/users/", json={"username": "alice"})

    assert res.status_code == 400
    body = res.get_json()
    assert_error_contract(body, 400)
    assert body["error_code"] == "missing_required_fields"
    assert res.headers.get("X-Request-ID") == body["request_id"]


def test_url_create_missing_user_id_uses_error_contract(client):
    res = client.post("/urls", json={"original_url": "https://example.com", "title": "Example"})

    assert res.status_code == 400
    body = res.get_json()
    assert_error_contract(body, 400)
    assert body["error_code"] == "missing_user_id"


def test_short_code_not_found_uses_error_contract(client):
    res = client.get("/doesnotexist00")

    assert res.status_code == 404
    body = res.get_json()
    assert_error_contract(body, 404)
    assert body["error_code"] == "short_code_not_found"
