# Reliability Evidence

## Tier 1

| Criterion         | Description                                                        | Evidence                                                                                                                                                             |
| ----------------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| health endpoint   | A working `GET /health` endpoint is available.                     | [Route implementation](../../../app/__init__.py) · [CI test passed](https://github.com/Suven-p/PE-Hackathon/actions/runs/23995183756)                                |
| unit test present | The repository includes unit tests and pytest collection succeeds. | [tests/](https://github.com/Suven-p/PE-Hackathon/tree/main/tests) · [CI run #2](https://github.com/Suven-p/PE-Hackathon/actions/runs/23995183756)                    |
| CI runs test      | CI workflow is configured to execute tests automatically.          | [ci.yml](https://github.com/Suven-p/PE-Hackathon/blob/main/.github/workflows/ci.yml) · [CI run #2](https://github.com/Suven-p/PE-Hackathon/actions/runs/23995183756) |

---

## Tier 2

| Criterion                            | Description                                         | Evidence                                                                                                                                       |
| ------------------------------------ | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| automated test coverage at least 50% | Automated test coverage reaches at least 50%.       | 74% — see [coverage.png](coverage.png)                                                                                                         |
| integration tests present            | Integration/API tests exist and are detectable.     | [tests/](https://github.com/Suven-p/PE-Hackathon/tree/main/tests) · 42 integration tests across test_api_health, test_api_urls, test_api_users |
| error handling                       | Error handling behavior for failures is documented. | [Error contract doc](error-handling.md) · [Contract integration tests](../../../tests/test_error_contract.py)                                  |

---

## Tier 3

| Criterion                            | Description                                                   | Evidence                                                                                                                                                |
| ------------------------------------ | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| automated test coverage at least 70% | Automated test coverage reaches at least 70%.                 | 74% — see [coverage.png](coverage.png)                                                                                                                  |
| graceful failure behavior            | Invalid input paths return clean structured errors.           | [Graceful failure doc](graceful-failure.md) · [Integration tests](../../../tests/test_graceful_failure.py)                                              |
| chaos restart proof                  | Evidence shows service restart behavior after forced failure. | [Chaos restart doc](chaos-restart.md) · [Proof script](../../../scripts/chaos-restart-proof.ps1) · [Latest artifact](artifacts/chaos-restart-latest.md) |
| failure modes documented             | Failure modes and recovery expectations are documented.       | [Failure mode runbook](failure-modes.md)                                                                                                                |
