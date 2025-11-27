# Salt XC Quote Hub — Backend (FastAPI)

FastAPI service (Python 3.12) that fronts Postgres/Cloud SQL for pipeline, quotes, overhead, storage, roles, and metadata. Auth is enforced via Firebase ID tokens; all callers must present a valid Bearer token.

## Features
- Auth: Firebase Admin verification plus role guard (`admin`, `pm`, `user`).
- Pipeline: CRUD with automatic project code sequencing and changelog.
- Quotes: Bulk replace + per-user storage of full quote payloads.
- Overhead: Employee CRUD with allocations.
- Storage: User key/value store (JSONB) keyed by Firebase UID.
- Metadata: Client list, rate card map, and client category map served via `/api/metadata/pipeline`.
- Healthcheck: `/health` for readiness probes.

## Configuration
- Env precedence: `.env.production` > `.env` > process env vars.
- Key settings (see `.env.example`):
  - `DATABASE_URL` or `POSTGRES_*` (+ optional `CLOUD_SQL_CONNECTION_NAME` socket path).
  - `POSTGRES_SSL` (set to `false` for local non-SSL connections).
  - `FB_PROJECT_ID`, `FB_CLIENT_EMAIL`, `FB_PRIVATE_KEY` (escaped with `\\n`).
  - `CORS_ORIGINS` (comma-separated; defaults to `*` if unset).
  - `API_PREFIX` (default `/api`), `PORT` (default `5010`).

## Running Locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in values
uvicorn app.main:app --reload --port 5010
```
Requires a reachable Postgres instance with the expected schema (see `cloudsql_schema.sql` in the frontend repo for reference).

## Deployment Notes
- Expose port `5010`.
- Ensure the service has access to Postgres/Cloud SQL and Firebase service account credentials.
- CORS should include the frontend origins (e.g., `http://localhost:3000` or your deployed host).
