# 24 Gen — Detailed Implementation Roadmap (Revision A)

**Strategy:** continuously operating product increments, contract-first integrations, human-approved data mutations. Dependencies below are mandatory unless explicitly revised. Time durations are not committed until the repository and developer environment are inspected. WP numbers 000–016 are the initial planning scheme.

| Stage | Work package | Deliverable | Dependencies | Exit gate | Release |
| --- | --- | --- | --- | --- | --- |
| Governance | WP-000 | Repo quality baseline, secrets exclusions, CI, requirements ledger, merge/rollback contract | Git access and repo inspection | Python tests and static checks green; safe baseline diff | pre-R0.1 |
| Foundation | WP-001 | Docker Gramps/Valkey/Celery, PostgreSQL and read-only passworded research homepage, scripts | WP-000 | Live Windows Docker and persistent-volume smoke; pending backup/restore verification | R0.1 candidate |
| Evidence | WP-002 | PostgreSQL relational model, migrations, source rights, audit | WP-001 | Migration upgrade/downgrade; immutable observation tests | R0.2 |
| Imports | WP-003 | GEDCOM/CSV/media and authorised source ingestion, de-duplication | WP-002 | Input quarantine and import-repeat idempotency | R0.2 |
| Matching | WP-004 | Historical normalisation, Splink-based mention matching and LLM review | WP-003 | Hard-negative precision/recall and evidence audit | R0.3 |
| Hypotheses | WP-005 | Graph model, alternative parentage/unknown and recalculation | WP-004 | Normalisation, dependence and contradiction tests | R0.4 |
| UI integration | WP-006 | Integrated review/approval mapping into Gramps API | WP-001,WP-005 | No unapproved Gramps changes; revision conflict test | R0.4 |
| Connectors | WP-007 | Provider capability, permissions and link-first framework | WP-002 | Manual-only automated request blocked | R0.2–0.5 |
| Normalisation | WP-008 | Provider-specific field and licence mapping | WP-007 | Literal values preserved, rights audit | R0.2–0.5 |
| HWR | WP-009 | Local handwriting OCR, optional gated cloud, correction trail | WP-003 | Verified immutable original and transcription version history | R0.5 |
| Deduplication | WP-010 | Canonical source families, cache and double-count protection | WP-003 | Duplicate-origin regression test | R0.2–0.5 |
| Jobs | WP-011 | Resumable queues, rate limits, budgets and approvals | WP-007 | Pause/retry/idempotent/cost cap tests | R0.5 |
| Tree UX | WP-012 | Interactive tree and navigation | WP-006 | Cross-view selection and accessibility tests | R0.4–1.0 |
| Alternate UX | WP-013 | Whole-branch comparison/confidence/unknown | WP-005,WP-012 | Non-colour alternate branches, score provenance | R0.4 |
| Evidence UX | WP-014 | Image, transcription and citation comparison | WP-003,WP-009 | Image zoom, correction history, conflicts | R0.5 |
| AI assistance | WP-015 | Structured AI chat and guided actions | WP-004,WP-007 | Source citations, no mutating tool without approval | R0.5 |
| Orchestration | WP-016 | Research dashboard, cost monitoring and approval queue | WP-011,WP-006 | Real queue state and action approval tests | R0.5–1.0 |

## Operating sequence and dependency controls

**Phase 0:** Inspect target Git repository and branch protections; document existing assets; resolve connection. Establish clean active checkout outside OneDrive. Apply WP-000 on a new branch, run tests and create review.  
**Phase 1:** Apply WP-001, install Docker Desktop/WSL2, create untracked secrets, start Gramps/worker/Valkey/research database/app. Perform real Windows integration test and persistent media + database recovery drill. Do not declare R0.1 complete until all gates pass.  
**Phase 2:** Define and migrate PostgreSQL research schema, provenance and sources; import a limited approved family/county dataset; freeze source policy per connector.  
**Phase 3:** Historical matching first with deterministic features and gold labels; then optional LLM reviewer; calibrate on held-out family networks.  
**Phase 4:** Dependent family-hypothesis engine with explicit unknown; review and approved Gramps write adapter; tree alternatives and evidence comparisons.  
**Phase 5:** Extend permitted connectors, local HWR, guided/autonomous agents and resource budgets; formal beta.  
**Phase 6:** Cross-version/large-volume load tests, resilience, false-merge review, data governance, release candidate acceptance and R1.0.

## Priority classifications

- **P0 data protection:** No AI accidental accepted-tree edits; no lost Gramps/media files; no exposure of web/db ports; no unauthorised automated source access; consistent backups.
- **P0 validation:** Original provenance preserved, false merge safeguards, model reliability must be labelled/calibrated.
- **P1 usability:** A persistent browser app, searchable imported data, person focus, document comparison and research history.
- **P1 performance:** Indexed matching, resumable jobs, licence-aware cache and scope limits.
- **P2 enrichment:** Specialist records, map expansion, multiple advanced tree layouts and broader languages.

## Performance engineering targets (provisional, benchmark required)

- Pilot: 1–10 families and a bounded county sample; log source coverage.
- Standard data: 100k synthetic mentions and 10k distinct identities in performance tests.
- Scale ambition: millions of records by partitioning/indexing/incremental linking; do not promise a specific response time before measurement.
- Background tasks: tolerate restarts without duplicate billing or repeated accepted-tree writes.
- Probabilities: calibration report across time period and record classes, with documented abstention on out-of-distribution cases.

## Acceptance evidence format

`ACCEPTANCE_REPORT.md`: package ID, base SHA, branch, date, host OS/Docker versions, commands, pass/fail tests, source files, DB snapshots/backup hash, image lock, screenshots, exceptions, release decision and reviewer. Any blocker fails release even if homepage is reachable.

## Repo access blocker

User-supplied repository `https://github.com/EIEng-enginering/Gen.git` was not accessible to connected GitHub account during preparation (404). No clone, push, branch or PR has been performed. The external coding agent must verify exact repository name, ownership and its credentials before treating existing files as replaceable.
