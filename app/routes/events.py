import json

from app.models.event import Event, serialize_event
from app.models.url import Url
from app.models.user import User
from flask import Blueprint, jsonify, request
from app.errors import error_response

events_bp = Blueprint("events", __name__, url_prefix="/events")


@events_bp.route("/", methods=["GET"])
def list_events():
    url_id = request.args.get("url_id")
    event_type = request.args.get("event_type")

    query = Event.select().order_by(Event.timestamp.desc())
    if url_id is not None:
        try:
            url_id = int(url_id)
        except ValueError:
            return error_response("'url_id' must be an integer", 400, error_code="invalid_url_id")
        query = query.where(Event.url_id == url_id)
    if event_type is not None:
        query = query.where(Event.event_type == event_type)

    return jsonify([serialize_event(event) for event in query]), 200


@events_bp.route("/", methods=["POST"])
def create_event():
    data = request.get_json()
    if not data:
        return error_response("Invalid JSON body", 400, error_code="invalid_json")

    url_id = data.get("url_id")
    user_id = data.get("user_id")
    event_type = data.get("event_type")
    details = data.get("details")
    if not Url.get_or_none(Url.id == url_id):
        return error_response(
            f"URL with ID {url_id} not found",
            404,
            error_code="url_not_found",
        )
    if not User.get_or_none(User.id == user_id):
        return error_response(
            f"User with ID {user_id} not found",
            404,
            error_code="user_not_found",
        )
    if not event_type:
        return error_response(
            "Missing 'event_type' in request body",
            400,
            error_code="missing_event_type",
        )
    if isinstance(details, dict):
        details = json.dumps(details)
    elif isinstance(details, str):
        try:
            json.loads(details)
        except Exception:
            return error_response(
                "'details' must be a JSON object or a JSON string",
                400,
                error_code="invalid_details",
                details={"raw_details": details},
            )
    else:
        return error_response(
            "'details' must be a JSON object",
            400,
            error_code="invalid_details",
            details={"raw_details": details},
        )
    event = Event.create(url_id=url_id, user_id=user_id,
                         event_type=event_type, details=details)
    return jsonify(serialize_event(event)), 201
