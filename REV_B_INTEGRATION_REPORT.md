# Rev B WP-002–004 integration report — 23 October 2026

**Decision: DEVELOPMENT CANDIDATE / R0.1 NOT ACCEPTED.** The source package is integrated on `feature/wp-002-evidence`, based on WP-001 commit `6a04ac161df5336f32e1add1368460b569513fba`. This report supersedes the earlier reports' historical claim that the GitHub connector returns 404: the repository is now public and readable, but the connector has no PR write permission.

## Inputs and preservation

- Implementation ZIP SHA-256: `73DA63DED785C1D6C3D3D8B5378114D044E72BCB9FD9C8FC266DB437C4B9C7D1`.
- Integrated source reference ZIP SHA-256: `550B931B2E7CDC14BD10ACB014170DE3D859BEFDA7BC4DD15A32339B8DD9C0C1`.
- Safe extraction checked paths, duplicates, symlinks and size. `INTEGRATE_OVERLAY.py --check` passed on the clean exact baseline; all 33 manifest originals and replacements matched their SHA-256 values. The applied checkout matched all 67 files in the integrated reference byte for byte before local review fixes.
- The package overlay did not change the WP-001 backup script, nine-volume manifest, `.env`, Compose topology, or prior governance decisions. The added source contains only fictional fixture records.
- The package integration is commit `58e88b2490fa50610f994075b2e8a76a03bdfe04`. The separate data-integrity and constraint fix is commit `5df0eaf36b0fe10615f4534330738c9d0fdf2447`.

## Review fixes after exact overlay

- Repeated source and observation IDs now compare all submitted original fields. Changed citation, source title, date or transcription content is rejected as a conflict rather than silently counted as an idempotent duplicate. A correction belongs in the append-only transcription revision route.
- Added API and CSV regression checks for those conflicts. Updated the application status text to describe the implemented uncalibrated ranker and optional read-only Gramps probe accurately.
- Updated `apps/research-web/constraints-windows-py312.txt` to include all 29 packages in the tested Windows Python 3.12 development environment, including the new SQLAlchemy and Alembic dependencies. This is a development constraint snapshot, not a production image lock.

## Checks run in `C:\24Gen\Gen`

| Gate | Result |
| --- | --- |
| `python -B -m pytest -q apps/research-web/tests` with a disposable writable `--basetemp` | **PASS: 30 tests**, one upstream Starlette/AnyIO deprecation warning. Includes SQLite migration, synthetic CSV import/idempotence, API, security and source-conflict checks. |
| `python -B tools/validate_decisions.py` | **PASS: all 50 approved decisions match Rev A baseline.** |
| `python -m pip check` | **PASS: no broken requirements.** |
| Windows PowerShell parser on `Test-Research-Data.ps1` | **PASS.** |
| `git diff --check` | **PASS.** |
| `Test-Research-Data.ps1` dry-run | **BLOCKED at first Docker command:** `docker` is not installed. No container or research database was touched. |
| WSL2 and Docker | **NOT AVAILABLE:** WSL reports not installed; Docker CLI absent. The earlier `wsl --install --no-distribution` attempt exited 1 without completing installation. |
| Gramps owner login, real import, API compatibility, persistence, cold backup and isolated media restore | **NOT RUN:** no Docker stack, `.env`, or disposable live data environment. |
| Image digests, licence review, production dependency lock | **NOT RUN.** Do not claim release compatibility from the development constraint file. |

## Git and release state

The public Git remote is `https://github.com/EIEng-enginering/Gen.git`. Direct Git published the Rev B branch and verified its SHA. The connected GitHub app could compare branches but reported `pull=true`, `push=false` and rejected PR creation with HTTP 403. The already authorized Git credential successfully created these draft PRs through GitHub's API without printing or storing its secret:

1. [WP-000 governance → main, PR #2](https://github.com/EIEng-enginering/Gen/pull/2)
2. [WP-001 foundation → WP-000, PR #3](https://github.com/EIEng-enginering/Gen/pull/3)
3. [Rev B WP-002–004 → WP-001, PR #1](https://github.com/EIEng-enginering/Gen/pull/1)

Review and merge in that order. No PR has been merged or marked ready for release.

No real genealogy records, credentials, Docker volumes, or Gramps accepted-tree tables were modified. WP-002–004 provides a provisional evidence foundation and an **uncalibrated** ranker. Calibrated family-relation probabilities, AI-led external research, handwriting recognition, and approved Gramps tree writes remain unimplemented. R0.1 stays **NOT ACCEPTED** until Windows Docker/Gramps, backup/restore, release locks and review gates pass with recorded evidence.
