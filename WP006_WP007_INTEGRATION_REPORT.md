# Combined WP-006 / WP-007 integration report — 23 October 2026

**Decision: development candidate; R0.1 NOT ACCEPTED.** Code was integrated for review, not deployed. No accepted Gramps tree mutation, real genealogy-data import, live database migration, or backup-volume operation was performed.

## Source, branch and installation state

- User-supplied package: `24Gen_WP006_WP007_Combined_Codex_Ready.zip`, SHA-256 `02F65F7CEFFBFA41CEE8F946C7A5B552BF32A52F91EDD0EB56A7CB8F85EA6658`; 25 ZIP entries, including 19 overlay files. Paths, duplicates, symbolic links and uncompressed size were checked before extraction. The original ZIP was copied to the separate OneDrive deliverables workspace for preservation; the active Git checkout remained `C:\24Gen\Gen` outside OneDrive.
- Exact clean parent: `feature/wp-005-versioned-hypotheses` at `f4297df70465e82d89139a2ecef158d57bd5f6ae`. The remote had no WP-006/WP-007 branch before integration. No baseline reset, merge, or existing-file overwrite was used to satisfy the package checks.
- The supplied `APPLY_SAFE.py` initially refused the Windows checkout because `git rev-parse --show-toplevel` returned forward slashes while `Path.resolve()` returned backslashes. Its **extracted staging copy only** was corrected to compare resolved `Path` objects. Repeated `--verify-only` then passed the exact parent and all 19 baseline/overlay hashes; the supplied `COMBINED_CHANGES.patch` passed `git apply --check`.
- Applied both work packages once on `feature/wp-006-007-controlled-gramps-review`. Exactly the 19 manifest paths were staged and checked. Code commit: `8ad4f2768e64ecbbc083172039acabc3d3081503`. Published branch: `origin/feature/wp-006-007-controlled-gramps-review`.
- One stacked [draft PR #5](https://github.com/EIEng-enginering/Gen/pull/5) targets `feature/wp-005-versioned-hypotheses`. Earlier drafts remain in review order [#2](https://github.com/EIEng-enginering/Gen/pull/2) → [#3](https://github.com/EIEng-enginering/Gen/pull/3) → [#1](https://github.com/EIEng-enginering/Gen/pull/1) → [#4](https://github.com/EIEng-enginering/Gen/pull/4) → #5. None was merged as part of this integration.

## Integrated behavior and data boundary

WP-006 records deterministic previews, claimed handle mappings, source evidence, version-bound plan digests, and explicit research-plan decisions in the separate research database. The decision allows future *read validation* only. WP-007 sends bounded Gramps **GET** requests for approved current plans, records sparse findings and a snapshot digest locally, and always returns execution disabled. The outbound Gramps client code contains `GET` only; no accepted-tree POST, PUT, PATCH or DELETE path was added. Local POST endpoints can create research plans, decisions and read-validation audit rows. The original 50 approved decision documents were not modified.

## Checks run on this Windows host

| Check | Result |
| --- | --- |
| Project Python | Windows Python **3.12.14** in existing `C:\24Gen\Gen\.venv`; no dependency installation was needed. |
| Full automated suite | **70 passed, one warning** (upstream Starlette/AnyIO deprecation), using `python -B -m pytest -q -p no:cacheprovider apps/research-web/tests` with a disposable workspace base temp. |
| Approved requirements | `python -B tools/validate_decisions.py` passed Q01–Q50. This confirms decision-register preservation, not completion of every product feature. |
| Dependencies | Project virtual environment `python -m pip check` passed; the combined package changed no requirements file. Production dependency and image locks remain unaccepted. |
| Source compilation | `compileall -q` passed for application, tests and tools. |
| OpenAPI / browser | All five combined plan/read-validation route patterns exist. Authenticated `/workspace` returned 200 with the Gramps dry-run panel and Content Security Policy. Embedded JavaScript passed `node --check` on Node **24.19.0**. |
| Patch integrity | Installer verified all 19 hashes, Git patch preflight passed, staged paths equaled the manifest, and `git diff --cached --check` passed. |
| Disposable migration tests | SQLite automated tests exercised 002→003→004, retention of older source and plan rows, and refusal of destructive downgrade when approval or read-validation history exists. This does **not** establish PostgreSQL behavior. |
| Docker / WSL2 | **NOT RUN:** Docker CLI is missing; `wsl --status` reports WSL not installed; this shell has no Windows administrator token. No Compose stack, nine-volume inventory, container image digest, or Gramps backup/restore was tested. |
| PostgreSQL | Windows service `postgresql-x64-16` was observed running and `pg_isready -h 127.0.0.1 -p 5432` returned accepting connections. `GEN_DB_URL`, `GEN_DB_PASSWORD` and a 24 Gen `.env` were absent. This service was **not** treated as a disposable project database; no login, migration, SQL write or rollback was attempted. |
| Live Gramps | **NOT RUN:** no Docker Gramps stack or `GEN_GRAMPS_ACCESS_TOKEN` was configured. Automated Gramps tests use `MockTransport`; no actual owner login, person/family response shape, handle existence, persistence or accepted-tree change was verified. |
| CI | No workflow run was surfaced for the initial code commit during inspection; local Windows results above are the evidence available at this point. |

The [official Gramps Web API documentation](https://www.grampsweb.org/development/backend/api/) says each running instance serves its interactive specification at `/api/swagger-ui`. The [manual query documentation](https://www.grampsweb.org/development/backend/queries/) demonstrates bearer-token access to metadata. The installed instance's person/family routes and response shapes remain unverified here.

## Installation and acceptance work still required

1. On an administrator-controlled Windows test host, enable WSL2 and Docker Desktop, pin and record container image digests, and start the documented Compose stack with **synthetic or expressly approved disposable data**. Keep checkout, secrets, databases and volumes outside OneDrive. Confirm local-only bindings and actual service versions.
2. Create and verify a full research database plus Gramps/media backup before any migration. Run Alembic revisions `20261023_003` and `20261023_004` manually on a **disposable PostgreSQL copy** of revision 002. Record `alembic_version`, old/new row counts and data hashes; verify populated downgrade refusal without deleting volumes.
3. Verify Gramps owner login, actual `/api/swagger-ui` schema, short-lived read token, person/family/metadata GET response shapes, existing-link findings, auth failures and restart persistence. Do not copy tokens or living-person details into logs, Git, this report or support bundles. A read snapshot must not be treated as future write approval.
4. Run the documented exact nine-volume cold backup and isolated restore including media checksums. Inspect licences and production dependency locks. Review drafts #2, #3, #1, #4 and #5 in dependency order. Keep all PRs draft until their relevant review gates pass; do not enable Gramps accepted-tree writes or mark R0.1 accepted from these local tests.

No real family records, existing PostgreSQL rows, Gramps accepted-tree objects, Docker volumes or credentials were changed by this integration.
