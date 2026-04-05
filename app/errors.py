import uuid

from flask import g, jsonify, request


def _request_id() -> str:
    request_id = getattr(g, "request_id", None)
    if request_id:
        return request_id

    header_request_id = request.headers.get("X-Request-ID")
    if header_request_id:
        return header_request_id

    return str(uuid.uuid4())


def error_response(
    message: str,
    http_status: int,
    *,
    error_code: str,
    retryable: bool = False,
    details: dict | None = None,
):
    payload = {
        "error": message,
        "message": message,
        "error_code": error_code,
        "http_status": http_status,
        "status": http_status,
        "retryable": retryable,
        "request_id": _request_id(),
    }
    if details is not None:
        payload["details"] = details

    return jsonify(payload), http_status
