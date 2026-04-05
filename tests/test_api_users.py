"""
Integration tests for User endpoints:
  POST   /users/
  POST   /users/bulk
  GET    /users/
  GET    /users/<id>
  PUT    /users/<id>
"""
import io
import pytest

pytestmark = pytest.mark.usefixtures("clean_tables")


def create_user(client, username="alice", email="alice@example.com"):
    res = client.post("/users/", json={"username": username, "email": email})
    assert res.status_code == 201, res.get_json()
    return res.get_json()


class TestCreateUser:
    def test_success_returns_201(self, client):
        res = client.post("/users/", json={"username": "alice", "email": "alice@example.com"})
        assert res.status_code == 201

    def test_response_contains_expected_fields(self, client):
        data = create_user(client)
        for field in ("id", "username", "email", "created_at"):
            assert field in data, f"Missing field: {field}"

    def test_username_and_email_are_stored_correctly(self, client):
        data = create_user(client, username="bob", email="bob@example.com")
        assert data["username"] == "bob"
        assert data["email"] == "bob@example.com"

    def test_missing_username_returns_400(self, client):
        res = client.post("/users/", json={"email": "a@example.com"})
        assert res.status_code == 400
        assert "error" in res.get_json()

    def test_missing_email_returns_400(self, client):
        res = client.post("/users/", json={"username": "alice"})
        assert res.status_code == 400

    def test_duplicate_email_returns_400(self, client):
        create_user(client, email="dup@example.com")
        res = client.post("/users/", json={"username": "other", "email": "dup@example.com"})
        assert res.status_code == 400
        assert "error" in res.get_json()

    def test_empty_body_returns_400(self, client):
        res = client.post("/users/", data="", content_type="application/json")
        assert res.status_code == 400


class TestListUsers:
    def test_empty_db_returns_empty_list(self, client):
        res = client.get("/users/")
        assert res.status_code == 200
        assert res.get_json() == []

    def test_returns_created_users(self, client):
        create_user(client, username="alice", email="alice@example.com")
        create_user(client, username="bob", email="bob@example.com")
        data = client.get("/users/").get_json()
        assert len(data) == 2

    def test_pagination_per_page(self, client):
        for i in range(5):
            create_user(client, username=f"user{i}", email=f"user{i}@example.com")
        data = client.get("/users/?page=1&per_page=2").get_json()
        assert len(data) == 2

    def test_pagination_invalid_page_returns_400(self, client):
        res = client.get("/users/?page=abc")
        assert res.status_code == 400


class TestGetUser:
    def test_returns_correct_user(self, client):
        user = create_user(client)
        res = client.get(f"/users/{user['id']}")
        assert res.status_code == 200
        assert res.get_json()["id"] == user["id"]

    def test_nonexistent_id_returns_404(self, client):
        res = client.get("/users/99999")
        assert res.status_code == 404
        assert "error" in res.get_json()


class TestUpdateUser:
    def test_update_username_success(self, client):
        user = create_user(client)
        res = client.put(f"/users/{user['id']}", json={"username": "alice_updated"})
        assert res.status_code == 200
        assert res.get_json()["username"] == "alice_updated"

    def test_nonexistent_id_returns_404(self, client):
        res = client.put("/users/99999", json={"username": "x"})
        assert res.status_code == 404

    def test_missing_username_returns_400(self, client):
        user = create_user(client)
        res = client.put(f"/users/{user['id']}", json={"username": ""})
        assert res.status_code == 400


class TestBulkCreateUsers:
    def _make_csv(self, rows):
        lines = ["username,email"] + [f"{r['username']},{r['email']}" for r in rows]
        return io.BytesIO("\n".join(lines).encode("utf-8"))

    def test_bulk_import_success(self, client):
        csv_file = self._make_csv([
            {"username": "alice", "email": "alice@example.com"},
            {"username": "bob", "email": "bob@example.com"},
        ])
        res = client.post("/users/bulk", data={"file": (csv_file, "users.csv")},
                          content_type="multipart/form-data")
        assert res.status_code == 201
        data = res.get_json()
        assert data["imported"] == 2

    def test_missing_file_returns_400(self, client):
        res = client.post("/users/bulk", content_type="multipart/form-data")
        assert res.status_code == 400

    def test_csv_without_required_headers_returns_400(self, client):
        csv_file = io.BytesIO(b"name,mail\nalice,alice@example.com")
        res = client.post("/users/bulk", data={"file": (csv_file, "users.csv")},
                          content_type="multipart/form-data")
        assert res.status_code == 400
