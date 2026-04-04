import csv
import io

from flask import Blueprint, jsonify, request

from app.database import db
from app.models.user import User, register_user, update_user as update_user_logic, set_user_sequence_value, bulk_create_users

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
            return jsonify({"error": "'page' and 'per_page' must be integers", "status": 400}), 400
        if page < 1 or per_page < 1:
            return jsonify({"error": "'page' and 'per_page' must be >= 1", "status": 400}), 400
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

    users = [_serialize_user(user) for user in query]

    return jsonify(users), 200


@users_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    user = User.get_or_none(User.id == user_id)
    if not user:
        return jsonify({"error": "User not found", "status": 404}), 404
    return jsonify(_serialize_user(user)), 200


@users_bp.route("/", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body", "status": 400}), 400

    username = data.get("username")
    email = data.get("email")

    if not username or not email:
        return jsonify({"error": "Missing 'username' or 'email'", "status": 400}), 400

    try:
        user = register_user(username=username, email=email)
        return jsonify(_serialize_user(user)), 201
    except ValueError as e:
        return jsonify({"error": str(e), "status": 400}), 400


@users_bp.route("/bulk", methods=["POST"])
def bulk_create_users_endpoint():
    uploaded_file = request.files.get("file")
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"error": "Missing file 'users.csv' in multipart/form-data", "status": 400}), 400

    try:
        csv_stream = io.TextIOWrapper(
            uploaded_file.stream, encoding="utf-8-sig")
        reader = csv.DictReader(csv_stream)
        fieldnames = reader.fieldnames or []
        if "username" not in fieldnames or "email" not in fieldnames:
            return jsonify({"error": "CSV must include 'username' and 'email' headers", "status": 400}), 400

        rows = list(reader)
    except Exception:
        return jsonify({"error": "Invalid CSV file", "status": 400}), 400

    result = bulk_create_users(db, rows)
    status_code = 201 if result["imported"] > 0 else 200
    return jsonify({
        "imported_users": result["imported"],
        "total_rows": result["total"],
        "status": status_code,
    }), status_code


@users_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id: int):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body", "status": 400}), 400

    username = data.get("username")
    if not username:
        return jsonify({"error": "Missing 'username'", "status": 400}), 400

    try:
        user = update_user_logic(id=user_id, username=username)
        return jsonify(_serialize_user(user)), 200
    except ValueError as e:
        return jsonify({"error": str(e), "status": 400}), 400
    except LookupError as e:
        return jsonify({"error": str(e), "status": 404}), 404
