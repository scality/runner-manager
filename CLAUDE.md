# runner-manager

This is a **Python FastAPI service** that manages GitHub Actions self-hosted runners on cloud VMs. It:

- Provisions and deprovisions VMs across multiple cloud backends (AWS, GCP, vSphere, OpenStack, Docker, Scaleway)
- Processes GitHub webhook events (`workflow_job`) to scale runners up/down
- Uses **Redis** (via redis-om) for persistent model storage and **RQ** (Redis Queue) for background job processing
- Exposes a REST API for runner group management, health checks, and metrics

Key directories:

- `runner_manager/backend/` — cloud provider integrations, each extending `BaseBackend`
- `runner_manager/models/` — Pydantic/redis-om models (`Runner`, `RunnerGroup`, `Settings`)
- `runner_manager/routers/` — FastAPI route handlers (webhooks, health, metrics, runner_groups)
- `runner_manager/jobs/` — RQ background jobs (startup, workflow_job, healthcheck, leaks, reset)
- `runner_manager/clients/` — GitHub API client (githubkit)
- `tests/unit/` and `tests/api/` — pytest test suite

Tech stack: Python 3.11+, FastAPI, Pydantic v2, redis-om, RQ, Poetry, Trunk (ruff/black/pyright for lint/format/types).

No internal Scality shared libraries (no arsenal, vaultclient, etc.).
