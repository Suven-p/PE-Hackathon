"""
Integration tests for URL endpoints:
  POST   /urls
  GET    /urls
  GET    /urls/<id>
  PUT    /urls/<id>
  GET    /<short_code>   (redirect)
"""
import pytest

pytestmark = pytest.mark.usefixtures("clean_tables")


def create_user(client, username="alice", email="alice@example.com"):
    res = client.post("/users/", json={"username": username, "email": email})
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def create_url(client, user_id, original_url="https://example.com", title="Example"):
    res = client.post("/urls", json={
        "user_id": user_id,
        "original_url": original_url,
        "title": title,
    })
    assert res.status_code == 201, res.get_json()
    return res.get_json()


class TestCreateUrl:
    def test_success_returns_201(self, client):
        user = create_user(client)
        res = client.post("/urls", json={
            "user_id": user["id"],
            "original_url": "https://example.com",
            "title": "Example",
        })
        assert res.status_code == 201

    def test_response_contains_expected_fields(self, client):
        user = create_user(client)
        data = create_url(client, user["id"])
        for field in ("id", "user_id", "short_code", "original_url", "title", "is_active", "created_at"):
            assert field in data, f"Missing field: {field}"

    def test_is_active_defaults_to_true(self, client):
        user = create_user(client)
        data = create_url(client, user["id"])
        assert data["is_active"] is True

    def test_missing_original_url_returns_400(self, client):
        user = create_user(client)
        res = client.post("/urls", json={"user_id": user["id"], "title": "Test"})
        assert res.status_code == 400
        assert "error" in res.get_json()

    def test_invalid_url_returns_400(self, client):
        user = create_user(client)
        res = client.post("/urls", json={
            "user_id": user["id"],
            "original_url": "not-a-valid-url",
            "title": "Test",
        })
        assert res.status_code == 400

    def test_nonexistent_user_returns_404(self, client):
        res = client.post("/urls", json={
            "user_id": 99999,
            "original_url": "https://example.com",
            "title": "Test",
        })
        assert res.status_code == 404

    def test_missing_user_id_returns_400(self, client):
        res = client.post("/urls", json={
            "original_url": "https://example.com",
            "title": "Test",
        })
        assert res.status_code == 400

    def test_missing_title_returns_400(self, client):
        user = create_user(client)
        res = client.post("/urls", json={
            "user_id": user["id"],
            "original_url": "https://example.com",
        })
        assert res.status_code == 400


class TestListUrls:
    def test_empty_db_returns_empty_list(self, client):
        res = client.get("/urls")
        assert res.status_code == 200
        assert res.get_json() == []

    def test_returns_created_urls(self, client):
        user = create_user(client)
        create_url(client, user["id"], title="First")
        create_url(client, user["id"], original_url="https://other.com", title="Second")
        data = client.get("/urls").get_json()
        assert len(data) == 2

    def test_filter_by_user_id(self, client):
        user1 = create_user(client, username="alice", email="alice@example.com")
        user2 = create_user(client, username="bob", email="bob@example.com")
        create_url(client, user1["id"], title="Alice URL")
        create_url(client, user2["id"], title="Bob URL")

        res = client.get(f"/urls?user_id={user1['id']}")
        data = res.get_json()
        assert len(data) == 1
        assert data[0]["user_id"] == user1["id"]

    def test_invalid_user_id_filter_returns_400(self, client):
        res = client.get("/urls?user_id=notanint")
        assert res.status_code == 400


class TestGetUrl:
    def test_returns_correct_url(self, client):
        user = create_user(client)
        created = create_url(client, user["id"])
        res = client.get(f"/urls/{created['id']}")
        assert res.status_code == 200
        assert res.get_json()["id"] == created["id"]

    def test_nonexistent_id_returns_404(self, client):
        res = client.get("/urls/99999")
        assert res.status_code == 404
        assert "error" in res.get_json()


class TestUpdateUrl:
    def test_update_title_success(self, client):
        user = create_user(client)
        url = create_url(client, user["id"])
        res = client.put(f"/urls/{url['id']}", json={"title": "Updated Title"})
        assert res.status_code == 200
        assert res.get_json()["title"] == "Updated Title"

    def test_deactivate_url(self, client):
        user = create_user(client)
        url = create_url(client, user["id"])
        res = client.put(f"/urls/{url['id']}", json={"is_active": False})
        assert res.status_code == 200
        assert res.get_json()["is_active"] is False

    def test_nonexistent_id_returns_404(self, client):
        res = client.put("/urls/99999", json={"title": "X"})
        assert res.status_code == 404

    def test_empty_body_returns_400(self, client):
        user = create_user(client)
        url = create_url(client, user["id"])
        res = client.put(f"/urls/{url['id']}", data="", content_type="application/json")
        assert res.status_code == 400


class TestRedirect:
    def test_valid_code_returns_302(self, client):
        user = create_user(client)
        url = create_url(client, user["id"], original_url="https://example.com")
        res = client.get(f"/{url['short_code']}", follow_redirects=False)
        assert res.status_code == 302
        assert res.headers["Location"] == "https://example.com"

    def test_nonexistent_code_returns_404(self, client):
        res = client.get("/doesnotexist00")
        assert res.status_code == 404
        assert "error" in res.get_json()

    def test_inactive_url_returns_410(self, client):
        user = create_user(client)
        url = create_url(client, user["id"])
        client.put(f"/urls/{url['id']}", json={"is_active": False})
        res = client.get(f"/{url['short_code']}", follow_redirects=False)
        assert res.status_code == 410
        assert "error" in res.get_json()
