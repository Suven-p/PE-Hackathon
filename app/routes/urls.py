import json

from flask import Blueprint, jsonify, redirect, request

from app.models.event import get_events_for_url, log_event
from app.models.url import Url, UrlInactiveError, create_short_url, get_url_by_code, update_short_url
from app.models.user import User

urls_bp = Blueprint("urls", __name__)


def success(data, status=200):
    return jsonify({"status": "success", "data": data}), status


def error(message, status):
    return jsonify({"status": "error", "message": message}), status


def _url_response(url: Url) -> dict:
    return {
        "id": url.id,
        "short_code": url.short_code,
        "original_url": url.original_url,
        "title": url.title,
        "is_active": url.is_active,
        "user_id": url.user_id,
        "created_at": url.created_at.isoformat(),
        "updated_at": url.updated_at.isoformat() if url.updated_at else None,
    }


@urls_bp.route("/urls", methods=["GET"])
def list_urls():
    urls = Url.select().order_by(Url.created_at.desc())
    return success([_url_response(url) for url in urls])


@urls_bp.route("/shorten", methods=["POST"])
def shorten():
    data = request.get_json(silent=True)
    if not data or "url" not in data:
        return error("Missing 'url' in request body", 400)

    user = None
    if "user_id" in data:
        try:
            user = User.get_by_id(data["user_id"])
        except User.DoesNotExist:
            return error("User not found", 404)

    try:
        url = create_short_url(
            original_url=data["url"],
            user=user,
            title=data.get("title"),
        )
        log_event(url, "created", user=user, details={
            "short_code": url.short_code,
            "original_url": url.original_url,
        })
        return success(_url_response(url), 201)
    except ValueError as e:
        return error(str(e), 400)
    except Exception:
        return error("Internal server error", 500)


@urls_bp.route("/<short_code>", methods=["GET"])
def redirect_url(short_code):
    try:
        url = get_url_by_code(short_code)
        log_event(url, "redirected", details={"short_code": short_code})
        return redirect(url.original_url, code=302)
    except Url.DoesNotExist:
        return error("Short code not found", 404)
    except UrlInactiveError:
        return error("This short link has been deactivated", 410)
    except Exception:
        return error("Internal server error", 500)


@urls_bp.route("/<short_code>", methods=["PATCH"])
def update_url(short_code):
    data = request.get_json(silent=True)
    if not data or "user_id" not in data:
        return error("Missing 'user_id' in request body", 400)

    try:
        url = Url.get(Url.short_code == short_code)
    except Url.DoesNotExist:
        return error("Short code not found", 404)

    if url.user_id != data["user_id"]:
        return error("Forbidden: you do not own this short link", 403)

    try:
        user = User.get_by_id(data["user_id"])
        updated = update_short_url(
            url,
            original_url=data.get("url"),
            title=data.get("title"),
            is_active=data.get("is_active"),
        )
        log_event(updated, "updated", user=user, details={"short_code": short_code})
        return success(_url_response(updated))
    except ValueError as e:
        return error(str(e), 400)
    except Exception:
        return error("Internal server error", 500)


@urls_bp.route("/<short_code>/events", methods=["GET"])
def get_events(short_code):
    try:
        url = Url.get(Url.short_code == short_code)
    except Url.DoesNotExist:
        return error("Short code not found", 404)

    try:
        events = get_events_for_url(url)
        return success([
            {
                "event_type": e.event_type,
                "timestamp": e.timestamp.isoformat(),
                "details": json.loads(e.details) if e.details else None,
            }
            for e in events
        ])
    except Exception:
        return error("Internal server error", 500)
