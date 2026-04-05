# Graceful Failure Evidence

This project enforces graceful-failure behavior for malformed requests and backend dependency outages.

## Guarantees

- Invalid input returns structured JSON error payloads.
- Unexpected service/database failures return `503` with a retryable indicator.
- API clients never receive Python stack traces in responses.

## Error Contract

All error responses include:

- `error`
- `message`
- `error_code`
- `http_status`
- `status`
- `retryable`
- `request_id`

## Demonstrated Failure Paths

- Invalid JSON body to `/users/` returns structured `400`.
- Invalid query value for `/urls?is_active=...` returns structured `400`.
- Invalid event details payload returns structured `400`.
- Simulated database outage while creating users returns structured `503` with `retryable=true`.

## Verification

Run:

```powershell
python -m pytest tests/test_graceful_failure.py -q
```

or as part of full suite:

```powershell
python -m pytest -q
```
