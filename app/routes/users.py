import csv
import io

from app.models.event import log_event
from flask import Blueprint, jsonify, request

from app.database import db
from app.errors import error_response
from app.models.user import User, register_user, update_user as update_user_logic, bulk_create_users, delete_user as delete_user_logic

users_bp = Blueprint("users", __name__, url_prefix="/users")


def _serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@users_bp.route("/", methods=["GET"])
def list_users():
    page = request.args.get("page")
    per_page = request.args.get("per_page")

    query = User.select().order_by(User.id.asc())

    # Handle pagination parameters if provided.
    if page is not None or per_page is not None:
        try:
            page = int(page) if page is not None else 1
            per_page = int(per_page) if per_page is not None else 10
        except ValueError:
            return error_response(
                "'page' and 'per_page' must be integers",
                400,
                error_code="invalid_pagination",
            )
        if page < 1 or per_page < 1:
            return error_response(
                "'page' and 'per_page' must be >= 1",
                400,
                error_code="invalid_pagination",
            )
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

    users = [_serialize_user(user) for user in query]

    return jsonify(users), 200


@users_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    user = User.get_or_none(User.id == user_id)
    if not user:
        return error_response("User not found", 404, error_code="user_not_found")
    return jsonify(_serialize_user(user)), 200


@users_bp.route("/", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data:
        return error_response("Invalid JSON body", 400, error_code="invalid_json")

    username = data.get("username")
    email = data.get("email")

    if not username or not email:
        return error_response(
            "Missing 'username' or 'email'",
            400,
            error_code="missing_required_fields",
        )

    if not isinstance(username, str) or not isinstance(email, str):
        return error_response(
            "username and email must be strings",
            422,
            error_code="invalid_field_type",
        )

    try:
        user = register_user(username=username, email=email)
        log_event(None, "user_registered", user.id, details={
                  "user_id": user.id, "user": _serialize_user(user)})
        return jsonify(_serialize_user(user)), 201
    except ValueError as e:
        return error_response(str(e), 400, error_code="invalid_user_payload")


@users_bp.route("/bulk", methods=["POST"])
def bulk_create_users_endpoint():
    uploaded_file = request.files.get("file")
    if not uploaded_file:
        return error_response(
            "Missing file 'file' in multipart/form-data",
            400,
            error_code="missing_file",
        )

    try:
        csv_stream = io.TextIOWrapper(
            uploaded_file.stream, encoding="utf-8-sig")
        reader = csv.DictReader(csv_stream)
        fieldnames = reader.fieldnames or []
        if "username" not in fieldnames or "email" not in fieldnames:
            return error_response(
                "CSV must include 'username' and 'email' headers",
                400,
                error_code="invalid_csv_headers",
            )

        rows = list(reader)
    except Exception:
        return error_response("Invalid CSV file", 400, error_code="invalid_csv")

    result = bulk_create_users(db, rows)
    log_event(None, "bulk_user_import", details={
              "imported": result["imported"], "total": result["total"]})
    status_code = 201 if result["imported"] > 0 else 200
    return jsonify({"imported": result["imported"], "total": result["total"]}), status_code


@users_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id: int):
    data = request.get_json()
    if not data:
        return error_response("Invalid JSON body", 400, error_code="invalid_json")

    username = data.get("username")
    if not username:
        return error_response("Missing 'username'", 400, error_code="missing_username")

    try:
        user = update_user_logic(id=user_id, username=username)
        log_event(None, "user_updated", user_id, details={
                  "user_id": user.id, "user": _serialize_user(user)})
        return jsonify(_serialize_user(user)), 200
    except ValueError as e:
        return error_response(str(e), 400, error_code="invalid_user_payload")
    except LookupError as e:
        return error_response(str(e), 404, error_code="user_not_found")


@users_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id: int):
    try:
        delete_user_logic(user_id)
        log_event(None, "user_deleted", user_id, details={"user_id": user_id})
        return jsonify({"message": "User deleted", "status": 200}), 200
    except LookupError as e:
        return error_response(str(e), 404, error_code="user_not_found")
