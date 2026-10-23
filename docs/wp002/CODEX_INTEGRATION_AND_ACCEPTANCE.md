# 24 Gen — WP-002/003/004 Codex integration and acceptance contract

**Release state: DEVELOPMENT CANDIDATE / NOT ACCEPTED.** This package is based on the actual WP-001 Codex snapshot and does not contain or change live genealogy data. Baseline reported branch `feature/wp-001-foundation`, full HEAD `6a04ac161df5336f32e1add1368460b569513fba` (23 October 2026). GitHub remote: `https://github.com/EIEng-enginering/Gen.git`.

## Highest priority: preserve completed work

1. Review the current repository and maintain the WP-000 / WP-001 branch ordering. Do not merge or reset any branch without review. Verify remote, HEAD, clean working tree and files.
2. Run the included `INTEGRATE_OVERLAY.py --repo C:\24Gen\Gen --check`, which compares the actual current files against the bundled source file hashes. It must refuse modified or unexpected source files. If it fails, review the conflicting file and reconcile manually—**never force-overlay**.
3. Create `feature/wp-002-evidence` based on the reviewed WP-001 branch (or its merged equivalent). Run `INTEGRATE_OVERLAY.py --repo C:\24Gen\Gen --apply`. Only after file-level review create a commit and draft PR to the correct parent branch. No forced pushes.
4. Keep the accepted Gramps tree, `.env`, genealogy media, GEDCOM, database volumes and credentials out of source control. No source content supplied by this package is actual family data.
5. Do not install to a user's live data until R0.1 backups, Gramps login/import and restoration are successfully exercised with disposable data.

## Implemented modules

- A versioned SQLAlchemy/PostgreSQL provisional evidence model and Alembic migration; initial empty databases initialise themselves, while existing schemas refuse silent upgrades.
- Source documents with provider IDs, original citation, access method, rights/licence and evidence-origin group.
- Person appearances (baptism, census, marriage, etc.), original verbatim transcription and append-only correction history.
- Local single-user authenticated research REST API with cross-origin write protection and audit trail.
- Idempotent CSV import with dry-run preview; synthetic parish demo input only.
- Bounded and explainable uncalibrated identity candidate ranker, explicit human review and no Gramps writes.
- Family alternatives requiring an `other/unknown` option; unsupported numerical probability claims rejected.
- Three research modes for task recording. Automated AI/online searching is NOT present and autonomous jobs stay paused until an authorised worker is implemented.
- Read-only Gramps metadata compatibility probe requiring an operator-held API token. It cannot write accepted persons or their families.
- A usable no-CDN research workspace for registered source documents, appearances, candidate matches, provisional hypotheses and research tasks.
- English 1841 age-rounding helper; chronology warning rules; offline benchmark precision/recall/ECE/Brier evaluation helpers.

## Local Python test commands

From repository root with Python 3.12 available:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r apps/research-web/requirements-dev.txt
$env:PYTHONPATH = 'apps/research-web'
.\.venv\Scripts\python.exe -m pytest -q apps/research-web/tests
.\.venv\Scripts\python.exe tools/validate_decisions.py
```

Tests are designed to use disposable SQLite databases, not the live PostgreSQL service; one migration test exercises create/import/re-import and destructive downgrade blocking. Review the warnings and all test outputs; do not mistake static test success for Windows/Docker acceptance.

## First actual Docker run

1. **Install and verify** Docker Desktop/WSL2, Docker Compose Linux mode, and the existing WP-001 start/configuration scripts. **Do not install images directly into OneDrive.**
2. Confirm `.env` is untracked, uses strong local admin credentials, and the `research_db` Docker volume is a disposable test database. Ensure a backup is taken if it contains any records.
3. Run `docker compose --env-file .env -f deploy/compose.yaml config`, build and start the stack; check that `research_web` initialises the research schema only when the database is empty. It must refuse automatic migration of a populated unversioned database. Verify Gramps and research app only publish ports on loopback.
4. Open `http://127.0.0.1:8765/workspace`; verify authentication and each tab. Open Gramps at `http://127.0.0.1:5055`, establish owner login, import disposable genealogy, restart and verify persistence.
5. Register a synthetic source and appearance; use a copy of `fixtures/english_parish_demo.csv` with the CSV import CLI to demonstrate preview and idempotent apply (first run creates rows, repeat adds none).
6. Validate API response to an attempted write without the `X-24Gen-Intent: research` header (must be HTTP 403). Verify `GET /api/v1/research/gramps-compatibility` reports missing token or read-only metadata only.
7. Execute an isolated cold backup and media restoration using **exactly nine** project-owned volumes and the Rev A.1 corrected backup script. Confirm OneDrive raw backups are rejected. Never test restore on live family records.
8. Capture commands, results, environment versions, image digests, migrations, restored-media checksum, commit SHA and PR URL in an acceptance report. R0.1 remains NOT ACCEPTED until those gates pass.

## Version and dependency policy

Python package versions used in requirements are development candidates. `constraints-windows-py312.txt` from WP-001 must be regenerated for the *new* dependencies after successful Windows installation; do not claim that the old snapshot covers this work. Docker images still use mutable development tags—pin tested digests after the live verification. Gramps REST API and frontend versions are independent: record both. Read Gramps API documentation at `https://www.grampsweb.org/development/backend/api/` (Swagger at `/api/swagger-ui`). Do not use direct writes to Gramps database tables.

## Historical/source safety

No automatic FreeBMD/FreeREG/FreeCEN scraping. API and bulk rights must be approved per source. Preserve original records and identical underlying source grouping; never count two transcriptions of the same register as independent evidence. Living people remain excluded from shared test fixtures. 1841 England/Wales census adult age and household information must not be mistaken for exact age or parentage proof.

## Exit criteria for this coding package

- Quality checks, tests and migration smoke tests pass on the actual integrated repository.
- Workspace and API survive real Docker restart with unchanged research records.
- Source provenance and transcription correction are preserved through repeated imports.
- Candidate scoring is correctly labelled "ranking, uncalibrated"; no automated merge writes.
- Gramps read-only probe reaches real API safely after an authorised local owner setup; token never logged.
- The R0.1 Gramps import and full media restore have been witnessed. Until then, classify this as an *integrated candidate*, not a release.

## Future packages, explicitly NOT in scope

Full historical UK bulk access, LLM fact extraction, handwriting recognition, probabilistic linkage calibration, relationship graph inference, autonomous external research, and Gramps write adapter with current-version optimistic concurrency. All remain required by Q1–Q50 and must not be misrepresented as implemented.
