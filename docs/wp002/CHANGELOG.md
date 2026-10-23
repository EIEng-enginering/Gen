# Development addendum Rev B / WP-002–004 starter

### Implemented
- Research source/observation/provenance persistence (no family tree writes)
- Alembic schema version 20261023_001 (frozen initial schema, guarded downgrade)
- Conservative boot-time schema gate (auto initialise blank only; reject unreviewed migrations)
- REST source registration/search, observation registration/search, append-only transcription revisions
- Uncalibrated match ranking and documented human review states
- Mutually exclusive candidate family hypotheses with explicit unknown and deliberately no numerical probabilities yet
- Research task management and API cost ceilings as records only (no hidden worker)
- Read-only Gramps API compatibility check guarded against arbitrary URLs
- Human CSV import (dry-run default) with idempotent keys and row errors
- English age/date rule helpers, independent benchmark holdout/check metrics
- Local no-CDN browser research workspace
- API OpenAPI JSON and 29 existing/new tests

### Preserved
- No change to Codex fixed WP-001 backup script or exact volume manifest
- No change to deployment Compose volumes, credentials or existing Gramps images
- No schema write inside Gramps; no external source scraping
- All 50 approved requirements remain binding

### Explicit release blockers
- Docker, WSL2, user login/import, Gramps JWT API compatibility, live backup, isolated media restore, version digests and Windows software acceptance untested
- Repository PR/merge permissions require permitted GitHub operator
- Full probabilistic family inference and AI automation remain future work
