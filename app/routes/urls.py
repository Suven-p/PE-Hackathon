from flask import Blueprint, jsonify, redirect, request

from app.models.event import log_event
from app.models.url import Url, UrlInactiveError, create_short_url, delete_url, get_url_by_code, update_short_url
from app.models.user import User

urls_bp = Blueprint("urls", __name__)


def _url_response(url: Url) -> dict:
    return {
        "id": url.id,
        "user_id": url.user_id,
        "short_code": url.short_code,
        "original_url": url.original_url,
        "title": url.title,
        "is_active": url.is_active,
        "created_at": url.created_at.isoformat(),
        "updated_at": url.updated_at.isoformat() if url.updated_at else None,
    }


# --- URL endpoints ---

@urls_bp.route("/urls", methods=["POST"])
def create_url():
    data = request.get_json(silent=True)
    if not data or "original_url" not in data:
        return jsonify({"error": "Missing 'original_url' in request body"}), 400

    user = None
    if "user_id" in data:
        try:
            user = User.get_by_id(data["user_id"])
        except User.DoesNotExist:
            return jsonify({"error": "User not found"}), 404
    else:
        return jsonify({"error": "Missing 'user_id' in request body"}), 400

    try:
        url = create_short_url(
            original_url=data["original_url"],
            user=user,
            title=data.get("title"),
        )
        log_event(url, "created", user=user, details={
            "short_code": url.short_code,
            "original_url": url.original_url,
        })
        return jsonify(_url_response(url)), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@urls_bp.route("/urls", methods=["GET"])
def list_urls():
    user_id = request.args.get("user_id")
    is_active = request.args.get("is_active")
    query = Url.select().order_by(Url.created_at.desc())
    if user_id:
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({"error": "'user_id' must be an integer"}), 400
        query = query.where(Url.user_id == user_id)
    if is_active is not None:
        query = query.where(Url.is_active == (is_active.lower() == "true"))
    return jsonify([_url_response(url) for url in query]), 200


@urls_bp.route("/urls/<int:url_id>", methods=["GET"])
def get_url(url_id):
    try:
        url = Url.get_by_id(url_id)
        return jsonify(_url_response(url)), 200
    except Url.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404


@urls_bp.route("/urls/<int:url_id>", methods=["PUT"])
def update_url(url_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing request body"}), 400

    try:
        url = Url.get_by_id(url_id)
    except Url.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404

    is_active = data.get("is_active")
    if is_active and not isinstance(is_active, bool):
        return jsonify({"error": "'is_active' must be a boolean value"}), 400

    try:
        updated = update_short_url(
            url,
            original_url=data.get("original_url"),
            title=data.get("title"),
            is_active=data.get("is_active"),
        )
        log_event(updated, "updated", details={"url_id": url_id})
        return jsonify(_url_response(updated)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@urls_bp.route("/urls/<int:url_id>", methods=["DELETE"])
def delete_url_endpoint(url_id):
    try:
        url = delete_url(url_id)
        log_event(url, "deleted", details={
                  "url_id": url_id, "reason": "user_requested"})
        return jsonify({"message": "URL deleted"}), 200
    except LookupError as e:
        return jsonify({"error": str(e)}), 404


@urls_bp.route("/<short_code>", methods=["GET"])
def redirect_url(short_code):
    try:
        url = get_url_by_code(short_code)
        log_event(url, "redirected", details={"short_code": short_code})
        return redirect(url.original_url, code=302)
    except Url.DoesNotExist:
        return jsonify({"error": "Short code not found"}), 404
    except UrlInactiveError:
        return jsonify({"error": "This short link has been deactivated"}), 410
    except Exception:
        return jsonify({"error": "Internal server error"}), 500
