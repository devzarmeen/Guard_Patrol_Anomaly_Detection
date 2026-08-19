# System Architecture

## Layers

| Layer | Location | Responsibility |
|---|---|---|
| Dashboard | `frontend/` | Metrics, evaluation, thresholds, Leaflet map, anomaly table |
| HTTP API | `app/routes/`, `app/main.py` | Ingest, CRUD, pipeline triggers, config, evaluation, incidents |
| Detection | `app/detection/` | Features, rules, Isolation Forest, hybrid, check-ins, patrols, grouping |
| Evaluation | `app/evaluation/` | Precision, Recall, F1, FPR against labels |
| Services | `app/services/` | Pipeline orchestration, alerting, scheduler, ingest validation |
| Config | `config/*.yaml`, `app/config.py` | Thresholds and checkpoint coordinates |
| Persistence | `app/models.py`, `app/database.py` | SQLModel → SQLite or PostgreSQL/Supabase |

## Data flow

1. Events arrive via REST ingest (`/api/ingest/*`) or sample CSV load.
2. Rows are schema-validated (Pydantic) and quality-checked (`validation.py`).
3. Feature engineering computes time gaps, haversine distances, and speed.
4. The selected detector (`rule`, `isolation_forest`, or `hybrid`) scores GPS points.
5. Check-in and patrol rule engines run in parallel using the same YAML thresholds.
6. Anomalies are grouped into actionable events and persisted without duplicates.
7. High/Critical (and equivalent check-in/patrol) events generate email/webhook alerts.
8. Operators record true incident / false positive labels via `/api/incidents`.
9. `/api/evaluation` compares the three methods on those labels.

## Incremental vs batch

- **Incremental**: GPS rows with `processed = false` only. Suitable for streaming ingest. A `processing_cursors` row records last run time.
- **Batch**: All stored GPS, check-in, and patrol rows. Scheduler runs this on an interval for a full operational pass.
- Check-in missed detection uses wall-clock wait against `missed_after_minutes`, so batch/incremental both re-evaluate pending check-ins.

## Alert flow

Detection → risk score → `_should_alert` (config) → email and/or webhook → `alert_logs`. If SMTP/webhook env vars are missing, status is `skipped` and the API still succeeds.

## Database

Local default: `sqlite:///./data/app.db`. Production: set `DATABASE_URL` to the Supabase/Postgres connection string. `create_tables()` registers SQLModel metadata on startup.

## Frontend

Vite + React. API base URL: `VITE_API_BASE_URL` (default `http://127.0.0.1:8000`). Map: `react-leaflet` over OpenStreetMap tiles.
