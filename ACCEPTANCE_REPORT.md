# WP-000 / WP-001 acceptance report — 23 October 2026

**Decision:** **NOT ACCEPTED**. These commits stage the first work packages in the exact target repository's local clone. They do not establish a working Windows Docker installation or R0.1 release.

| Check | Status | Evidence |
| --- | --- | --- |
| Target baseline and overlay conflicts | **PASS** | Direct Git clone of `EIEng-enginering/Gen` reported no commits or tracked paths; commits and branches are recorded in `BASELINE_REPORT.md`. The GitHub connector still returns 404. |
| Q01–Q50 decision register | **PASS** | `python -B tools/validate_decisions.py` printed `PASS: all 50 approved decisions match Rev A baseline`. |
| Python source compilation | **PASS** | `python -B -m compileall -q tools apps/research-web/app apps/research-web/tests` completed. |
| Python unit/API/static Compose tests | **PASS** | `python -B -m pytest -q apps/research-web/tests`: **8 passed**, one upstream Starlette/AnyIO deprecation warning. Includes two new manifest checks. |
| Python dependency consistency | **PASS** | `python -m pip check`: `No broken requirements found.` The Windows Python 3.12 dependency snapshot is a development constraint file, not a release image lock. |
| PowerShell syntax | **PASS** | Windows PowerShell parser found no errors in the five `deploy/windows/*.ps1` files. |
| Backup OneDrive destination guard | **PASS** | Executed preflight with a OneDrive backup path; script rejected it before Docker operations. |
| Backup volume rejection | **PASS, simulated** | Fake Docker responses with only eight volumes, and then with a wrong ownership label, were both rejected before the script attempted to stop the stack. No real volumes were accessed. |
| Docker Compose config/build/start and loopback binding | **NOT RUN** | Docker Desktop and CLI unavailable; no daemon or WSL2. Source-level Compose checks are not a live network test. |
| Gramps owner login, GEDCOM/Gramps import and persistence | **NOT RUN** | No running Gramps or disposable import fixture. |
| Cold backup and isolated restore with media | **NOT RUN** | No Docker volumes or isolated restore stack. Backup script is a review candidate; recoverability is unproven. |
| Image/API/licence release locks | **NOT RUN** | Gramps, Valkey, PostgreSQL, Python and Alpine helper image digests remain development placeholders; live compatibility and licence review remain outstanding. |

## Changed files and rollback

WP-000: `.gitattributes`, `.gitignore`, `.github/workflows/quality.yml`, `README_WP000.md`, `tools/validate_decisions.py`, and the 13 versioned `docs/` files.

WP-001: `.env.example`, `apps/research-web/`, `deploy/compose.yaml`, and `deploy/windows/`. The corrective commit adds `deploy/backup-volumes.json`, `apps/research-web/tests/test_backup_manifest.py`, and `apps/research-web/constraints-windows-py312.txt`; it replaces the backup script and restore checklist.

No database migration or live data change occurred. Before merge, rollback is branch deletion or reset to the recorded baseline. After merge, use a normal Git revert; never delete Docker volumes as a source rollback.

## Remaining gates

Install WSL2 and Docker Desktop on the intended Windows host, then test Compose and image versions. Use disposable genealogy data for owner setup, import, persistence, cold backup and isolated media restore. Pin tested image digests and verify relevant licences. Confirm the GitHub App's organization access for PR review. Keep R0.1 **NOT ACCEPTED** until every live gate is evidenced.
