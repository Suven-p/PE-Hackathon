# Failure Modes and Recovery Expectations

This runbook documents expected failure scenarios for the URL shortener service, how to detect them quickly, and the minimum recovery actions expected from the on-call engineer.

## Recovery Expectations

| Severity | Typical User Impact                               | Target RTO    | Target RPO    |
| -------- | ------------------------------------------------- | ------------- | ------------- |
| Sev-1    | Core API unavailable (5xx/502 on most requests)   | <= 15 minutes | <= 5 minutes  |
| Sev-2    | Partial degradation (elevated latency/error rate) | <= 30 minutes | <= 15 minutes |
| Sev-3    | Non-critical features degraded                    | <= 4 hours    | <= 1 hour     |

Notes:

- RTO (Recovery Time Objective): max acceptable time to restore service.
- RPO (Recovery Point Objective): max acceptable data loss window.

## Failure Mode Matrix

| Failure Mode                                     | Detection Signals                                                                                              | Likely Causes                                                                            | Immediate Mitigation                                                                                                                                         | Recovery Validation                                                            | Preventive Follow-up                                                                |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| Postgres authentication failure                  | App containers restart-looping, `FATAL: password authentication failed` in app logs, `/health` returns non-200 | DB password mismatch between app and postgres, stale compose volume with old credentials | Confirm `DATABASE_PASSWORD` and `POSTGRES_PASSWORD` alignment, reset stack if needed: `docker compose down -v --remove-orphans`, then `docker compose up -d` | `GET /health` returns `{\"status\":\"ok\"}` and create/read URL flow works     | Add startup check in deployment pipeline for DB connectivity before traffic cutover |
| Postgres unavailable/network failure             | `database_unavailable` 503 responses, DB connection errors in logs, rising 5xx                                 | DB instance down, networking outage, DNS/service resolution issue                        | Fail fast and serve structured 503s, restart DB service/container, verify credentials/network route                                                          | `GET /health` is healthy and error rate returns to baseline                    | Add DB uptime alerting and dependency health checks with paging thresholds          |
| App process/container crash                      | Container exits/restarts unexpectedly, request failures spike                                                  | Runtime exceptions, dependency startup race, image/runtime issue                         | Use restart policy (`restart: unless-stopped`), redeploy last known-good image/config, inspect logs                                                          | Container running stable for >= 10 minutes, health endpoint green              | Add canary deploy + rollback gate and crashloop alert                               |
| Reverse proxy upstream failure (502 Bad Gateway) | Nginx returns 502, app unreachable behind proxy                                                                | Backend app down, backend not listening, network issue in compose network                | Verify app service state, restart app service, confirm proxy upstream target/port                                                                            | Access through proxy (`http://localhost:5001/health`) returns healthy response | Add synthetic probe to proxy endpoint and alert on sustained 502s                   |
| Redis unavailable (non-core dependency)          | Redis connection errors in logs, feature degradation where Redis is used                                       | Redis service down or unreachable                                                        | Restart redis service and verify URL env/config; keep core URL CRUD running where possible                                                                   | Core API endpoints continue serving, Redis-dependent operations recover        | Define degraded-mode behavior and explicit fallback path in docs/code               |
| Bad input spike or malformed client traffic      | Increased 4xx rates, no corresponding 5xx increase, stable infra metrics                                       | Client bug, abusive traffic, malformed integrations                                      | Maintain graceful error responses (`400/422`) with error contract; rate-limit abusive sources if needed                                                      | 4xx pattern understood and 5xx remains controlled; no app crash                | Add dashboards splitting 4xx vs 5xx and API consumer diagnostics                    |
| Seed/config drift during startup                 | App startup logs indicate seed directory/migration/config mismatch                                             | Wrong `DATABASE_SEED_DIRECTORY`, unexpected env values, migration drift                  | Set `DATABASE_INITIALIZE=false` for runtime, correct env config, restart with known-good settings                                                            | App starts cleanly and tables/health checks are successful                     | Add environment validation checklist before deploy                                  |

## Standard Incident Response Flow

1. Declare incident and severity based on user impact.
2. Capture baseline evidence: health response, error rate, and service statuses.
3. Apply the fastest safe mitigation from the matrix.
4. Verify recovery with objective checks (`/health`, create/read URL path, logs stable).
5. Communicate recovery status and ETA updates.
6. Open follow-up tasks for prevention items.

## Operational Commands (Docker Compose)

```powershell
# Service status
docker compose ps

# Tail app logs
docker compose logs app --tail 100

# Tail postgres logs
docker compose logs postgres --tail 100

# Restart app tier
docker compose up -d app

# Hard reset when config/credential drift is suspected
docker compose down -v --remove-orphans
docker compose up -d
```

## Evidence Links

- Error contract and graceful failure behavior: [error-handling.md](error-handling.md), [graceful-failure.md](graceful-failure.md)
- Chaos restart proof: [chaos-restart.md](chaos-restart.md)
- Latest chaos artifact: [artifacts/chaos-restart-latest.md](artifacts/chaos-restart-latest.md)
