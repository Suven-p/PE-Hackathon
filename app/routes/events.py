from app.models.event import get_all_events, get_events_for_url, serialize_event
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
