from app.models.event import Event, get_all_events, get_events_for_url, serialize_event
from flask import Blueprint, jsonify, request

from app.database import db

events_bp = Blueprint("events", __name__, url_prefix="/events")


@events_bp.route("/", methods=["GET"])
def list_events():
    url_id = request.args.get("url_id")
    if url_id is not None:
        try:
            url_id = int(url_id)
        except ValueError:
            return jsonify({"error": "'url_id' must be an integer", "status": 400}), 400
        events = get_events_for_url(url_id)
    else:
        events = get_all_events()
    return jsonify([serialize_event(event) for event in events]), 200


@events_bp.route("/", methods=["POST"])
def create_event():
    data = request.get_json()
    url_id = data.get("url_id")
    event_type = data.get("event_type")
    if not url_id or not event_type:
        return jsonify({"error": "Missing 'url_id' or 'event_type'", "status": 400}), 400
    try:
        url_id = int(url_id)
    except ValueError:
        return jsonify({"error": "'url_id' must be an integer", "status": 400}), 400
    event = Event.create(url_id=url_id, event_type=event_type)
    return jsonify(serialize_event(event)), 201
