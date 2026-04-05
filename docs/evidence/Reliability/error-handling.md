# Error Handling Contract

This project uses a unified JSON error response contract for API failures.

## Contract Shape

All non-2xx API responses must include:

- `error`: Human-readable failure message.
- `message`: Alias of `error` for compatibility.
- `error_code`: Stable machine-readable error identifier.
- `http_status`: HTTP status code as an integer.
- `status`: Alias of `http_status` for compatibility.
- `retryable`: Whether retrying may succeed (`true`/`false`).
- `request_id`: Correlation ID for tracing this request in logs.

Optional:

- `details`: Additional structured context for debugging invalid input.

## Canonical Behaviors

- `400`: Invalid payload, missing fields, malformed query params.
- `404`: Missing resources (user/url/short code).
- `410`: Inactive short links.
- `422`: Semantic type errors in request bodies.
- `500`: Unexpected server errors (safe message only).
- `503`: Service dependencies unavailable (e.g., database down).

## Example

```json
{
  "error": "Missing 'user_id' in request body",
  "message": "Missing 'user_id' in request body",
  "error_code": "missing_user_id",
  "http_status": 400,
  "status": 400,
  "retryable": false,
  "request_id": "31de8388-109f-4e4c-95bc-00f1f37f8d8a"
}
```

## Request ID Propagation

- If a client sends `X-Request-ID`, it is reused.
- Otherwise, the app generates one and returns it in the response header.
