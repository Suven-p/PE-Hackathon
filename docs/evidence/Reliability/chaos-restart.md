# Chaos Restart Proof

This evidence demonstrates restart resilience by intentionally killing the app container and verifying service recovery and data persistence.

## Implementation

- App container restart policy is set in [compose.yml](../../../compose.yml) using `restart: unless-stopped`.
- Reproducible script: [scripts/chaos-restart-proof.ps1](../../../scripts/chaos-restart-proof.ps1)
- Script output artifacts: [docs/evidence/Reliability/artifacts](artifacts)

## Verification Procedure

Run from repository root:

```powershell
./scripts/chaos-restart-proof.ps1
```

The script performs:

1. Reset compose state (`docker compose down -v --remove-orphans`) to remove stale service data.
2. Bring up required services (`app`, `nginx`, `postgres`, `redis`, `tempo`).
3. Wait for `/health` to return `{"status":"ok"}` via nginx.
4. Create a user and URL record.
5. Kill the current app container.
6. Wait for restart and health recovery.
7. Re-fetch the created URL record to prove persistence.
8. Write a timestamped artifact and refresh `chaos-restart-latest.md`.

## Success Criteria

- App container restarts after forced kill.
- Health endpoint returns to OK within timeout.
- Data created before kill remains retrievable after recovery.

## Latest Artifact

- [chaos-restart-latest.md](artifacts/chaos-restart-latest.md)
