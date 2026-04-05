import json

from app.models.event import Event, serialize_event
from app.models.url import Url
from app.models.user import User
from flask import Blueprint, jsonify, request

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
            return jsonify({"error": "'url_id' must be an integer", "status": 400}), 400
        query = query.where(Event.url_id == url_id)
    if event_type is not None:
        query = query.where(Event.event_type == event_type)

    return jsonify([serialize_event(event) for event in query]), 200


@events_bp.route("/", methods=["POST"])
def create_event():
    data = request.get_json()
    url_id = data.get("url_id")
    user_id = data.get("user_id")
    event_type = data.get("event_type")
    details = data.get("details")
    if not Url.get_or_none(Url.id == url_id):
        return jsonify({"error": f"URL with ID {url_id} not found", "status": 404}), 404
    if not User.get_or_none(User.id == user_id):
        return jsonify({"error": f"User with ID {user_id} not found", "status": 404}), 404
    if not event_type:
        return jsonify({"error": "Missing 'event_type' in request body", "status": 400}), 400
    if isinstance(details, dict):
        details = json.dumps(details)
    elif isinstance(details, str):
        try:
            json.loads(details)
        except Exception:
            return jsonify({"error": "'details' must be a JSON object or a JSON string", "status": 400, "details": details}), 400
    else:
        return jsonify({"error": "'details' must be a JSON object", "status": 400, "details": details}), 400
    event = Event.create(url_id=url_id, user_id=user_id,
                         event_type=event_type, details=details)
    return jsonify(serialize_event(event)), 201
