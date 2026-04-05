# Chaos Restart Proof

- Timestamp: 2026-04-05T07:47:07.7151557-02:30
- Runner: DESKTOP-BP7DQ5L

## Tooling

- docker compose: Docker Compose version v5.1.1

## Startup

Running: docker compose down -v --remove-orphans
Running: docker compose up -d app nginx postgres redis tempo
- Initial health: ok

## Data Setup

- Created user id: 1
- Created url id: 1

## Chaos Action

- App container before kill: e77be5a2099992d47200dcc09a29cfe348c21d47c3788da92a282b3aedeac59e
- StartedAt before kill: 2026-04-05T10:17:27.502858497Z
- Running: docker kill e77be5a2099992d47200dcc09a29cfe348c21d47c3788da92a282b3aedeac59e

- App container after recovery: fc696136b100df91983e0cdbe41cc8c208c7b83b1836b290a00b95d3a871f9ab
- StartedAt after recovery: 2026-04-05T10:17:26.196787207Z
- Recovery detected: yes

## Post-Recovery Validation

- URL fetch after restart: success
- Persisted url id: 1
- Verdict: PASS
