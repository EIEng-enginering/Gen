# WP-002 / WP-003 / WP-004 starter — Research evidence foundation

Status: **CODE READY FOR REVIEW, LIVE DEPLOYMENT NOT VERIFIED**.

## Scope implemented
- PostgreSQL research schema with a first Alembic migration, source documents,
  observations, immutable transcription history, audit events, identity candidate
  review, competing family hypotheses with exactly one unknown alternative,
  and research-task records.
- Protected REST endpoints and a usable local evidence research workspace.
- Human-provided CSV preview/import CLI with idempotent source and observation keys.
- Explainable *uncalibrated* candidate-ranking heuristic, never misrepresented
  as a verified identity or parentage probability.
- Work queue records across 3 approved research modes (no background execution yet).
- Strictly **NO writes to Gramps** and **NO automated external search**.

## Scope NOT implemented / not accepted
- Gramps REST adapter writes/approval workflow, calibrated Bayesian posterior,
  probabilistic family network inference, population matching, integrated HTR,
  external-source connectors, background worker, paid API calls and public hosting.
- Automatic upgrading of the existing accepted family tree.
- Live Windows/Docker startup, Gramps installation and restore acceptance.

## Data and evidence rules
- Source references and licence/access mechanisms are required.
- Upstream citations are preserved verbatim. Shared original-group IDs must be
  assigned for derivatives of the same historic record to avoid evidence inflation.
- A census entry is an appearance, not a confirmed individual. Census household
  co-occurrence does not imply biological parentage.
- Candidate `ranking_score` is for ordering review, **not a probability**.
- Explicit `other/unknown` option is mandatory for every mutually-exclusive
  family hypothesis set; uncalibrated options have null probability.
- Research approval only changes local candidate *review status*, never Gramps.

## Developer quick start (disposable local SQLite tests)
```bash
python -m pip install -r apps/research-web/requirements-dev.txt
python -m pytest -q apps/research-web/tests
```

## Docker startup
`research_web` container starts with `alembic upgrade head` before serving.
Its database lives in the existing `research_postgres` named Docker volume. To
avoid race conditions, run **one** research_web replica during migration.

## CSV import
CSV columns are documented by `fixtures/english_parish_demo.csv`; all sample
names/records are fictional and cannot establish genealogy.

Preview without writes inside the app container:
```bash
docker compose --env-file .env -f deploy/compose.yaml exec research_web \
  python -m app.research.importer /app/fixtures/english_parish_demo.csv
```
If fixtures are not mounted in the container, copy an authorised CSV into the
container or run the importer locally with an explicitly configured test DB.
Do not use `--apply` until the file is validated and licensing permits storage.

## Configuration
Passwords and API credentials belong in the existing `.env` only, not Git.
Research web remains bound to 127.0.0.1 via existing Compose port mapping.
Backup script must be reviewed again before any real data is ingested.
