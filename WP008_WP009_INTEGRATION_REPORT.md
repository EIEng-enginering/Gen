# Combined WP-008 / WP-009 integration report — 23 October 2026

**Status: integrated development candidate; R0.1 NOT ACCEPTED.** This work was committed and pushed for review. It was not deployed or merged. No accepted Gramps family-tree mutation, real genealogy-data import, populated production database migration, or backup-volume operation was performed.

## Source, baseline, branch and installation

- Existing repository: `https://github.com/EIEng-enginering/Gen.git`; active checkout: `C:\24Gen\Gen` outside OneDrive.
- User-supplied package: `24Gen_WP008_WP009_Combined_Codex_Ready.zip`, SHA-256 `728C264168067428D0DCCC9EAC906C242FC2B5ECEB0C7AA4F1C933AD1923969E`. The original ZIP was copied intact to the separate project deliverables directory for inspection. ZIP paths, duplicates, symbolic links, and size were checked before extraction; 20 safe entries contained 13 source overlay paths.
- The clean parent branch `feature/wp-006-007-controlled-gramps-review` matched required commit `c54a49d46a569b43af77f42a4db921529545a820`, also the head of draft PR #5. No WP-008/009 remote branch existed at preflight.
- `APPLY_SAFE.py --verify-only` passed the exact Git baseline and all 13 baseline/overlay file checks. `git apply --check SOURCE_CHANGES.patch` also passed. A new branch `feature/wp-008-009-historic-readiness` was created from that exact commit, and the installer applied 13 paths without overwriting a modified worktree.
- The supplied WP-009 browser form converted blank optional year inputs to `0`, which the API rejects. The integrated UI omits blank optional years; this one-line correction is the only intentional departure from the package overlay. Tests were rerun afterward.
- Exactly the 13 manifest paths were staged and checked. Implementation commit: `208dcdbb1c04cd8be0c52a06af159f604ee350c5`; branch pushed to `origin/feature/wp-008-009-historic-readiness`.
- One [draft PR #6](https://github.com/EIEng-enginering/Gen/pull/6) targets the WP-006/007 branch. Earlier drafts remain unmerged and are reviewed in dependency order #2 → #3 → #1 → #4 → #5 → #6. No force-push, reset, merge, or accepted-tree write occurred.

## Integrated files and behavior

| Area | Files | Result |
| --- | --- | --- |
| App wiring and data model | `apps/research-web/app/main.py`, `apps/research-web/app/research/models.py` | Registers WP-008/009 routes and the source-linked `HistoricalPlace` model. |
| Gramps offline contract | `apps/research-web/app/research/gramps_contract.py`, `apps/research-web/app/research/gramps_contract_api.py` | Authenticated, 1 MiB bounded local OpenAPI 2/3 inspection; read-only plan readiness and execution-policy GET. Both report accepted-tree writes disabled. No schema upload is forwarded to Gramps. |
| Historical place and triage | `apps/research-web/app/research/historical_api.py`, `apps/research-web/app/research/historical_linkage.py`, `apps/research-web/app/research/ui.py` | Manual source-backed historical labels, year-filtered search, bounded candidate retrieval, transparent heuristic ranking, census-age uncertainty, and browser controls. The register has no preloaded authoritative place data. Rankings are not probabilities or identity proof. |
| Schema | `apps/research-web/migrations/versions/20261023_005_historical_places.py` | Creates `historical_places` with source FK, evidence fields, interval checks and source/key uniqueness. Refuses downgrade when place evidence exists. |
| Tests | `apps/research-web/tests/test_wp008_contract.py`, `apps/research-web/tests/test_wp009_historical.py`, `apps/research-web/tests/test_wp009_migration.py` | Offline contract/auth/gate, place API and triage, census-age, and disposable migration coverage. |
| Package documentation | `docs/wp008/README.md`, `docs/wp009/README.md` | Development scope, API and remaining gates. |

The POST that registers a historical place writes only to the separate research database behind the existing authentication and research-intent guard. There is no Gramps write adapter or accepted-tree mutation route. The WP-007 Gramps client remains GET-only. The existing 50 approved decision documents were not edited.

## Verification on this Windows host

| Check | Observed result |
| --- | --- |
| Runtime | Existing project virtual environment: Windows Python 3.12.14; Node v24.19.0. No dependency installation was required. |
| Full automated suite | `python -B -m pytest -q -p no:cacheprovider apps/research-web/tests` with disposable `--basetemp`: **81 passed**, one upstream Starlette/AnyIO deprecation warning. The complete suite passed before and after the UI correction. |
| Approved requirements | `python -B tools/validate_decisions.py`: **PASS**, all Q01–Q50 match the approved Rev A baseline. This validates register preservation, not full implementation of every requirement. |
| Dependencies and source | `python -m pip check`: **PASS**. All 54 Python application/test/tool source files compiled in memory: **PASS**. Embedded workspace JavaScript extracted and checked with `node --check`: **PASS**. |
| API and Gramps policy | Automated authenticated tests passed for Swagger 2.0 and OpenAPI 3.x structure, authentication, 1 MiB limit, missing-plan response and `GET /api/v1/research/gramps/execution-policy`. The policy returns `accepted_tree_mutation_enabled: false`. This is offline/mocked verification, not a live Gramps compatibility check. |
| UI | Automated authenticated `/workspace` test returned 200 and found the new historical controls; embedded JavaScript syntax passed. No full browser interaction or live Gramps UI test was run. |
| Disposable migration | SQLite test upgraded revision 004→005 with one synthetic old `SourceDocument` row; that row remained after upgrade. The test added one synthetic historical-place row and confirmed a populated downgrade to 004 was refused, leaving both rows accessible. This is **not** a PostgreSQL migration result. |
| Package and Git integrity | Safe installer exact-baseline and 13-path preflight passed; patch preflight passed; staged paths exactly matched `MANIFEST.json`; `git diff --cached --check` passed. The UI correction means that one integrated file intentionally differs from its overlay hash after installation. |
| PostgreSQL availability | Windows service `postgresql-x64-16` was running; `pg_isready -h 127.0.0.1 -p 5432` returned accepting connections. `GEN_DB_URL`, `GEN_DB_PASSWORD` and project `.env` were absent. The service was not treated as an authorised disposable 24 Gen database. No login, PostgreSQL migration, SQL write or rollback was attempted. |
| Docker / WSL2 / Gramps | Docker CLI absent. `wsl --list --quiet` reported Windows Subsystem for Linux not installed. No `GEN_GRAMPS_ACCESS_TOKEN` was configured. Live Gramps owner login, actual OpenAPI export, person/family read shapes, restart persistence, image digest, nine-volume backup and isolated restore were **NOT RUN**. |
| CI | The GitHub commit-workflow query surfaced no PR-triggered run for implementation commit `208dcdb` at inspection time. Local Windows checks above are the available test evidence. |

## Installation and acceptance work remaining

1. Review and merge the draft dependency chain only after each PR's review gates pass. PR #6 must remain draft while these live gates are outstanding. Do not mark R0.1 accepted from the local tests.
2. On an administrator-controlled Windows test host, install/verify WSL2 and Docker Desktop, pin and record container image digests, and bring up the documented Compose stack with synthetic or expressly authorised disposable family data. Confirm local bindings, service versions and persistent volumes. Keep raw unencrypted backups outside OneDrive.
3. Provision an explicitly disposable PostgreSQL copy at revision `20261023_004`, after a verified backup. Upgrade manually to `20261023_005`; record Alembic version and old/new row counts and hashes. Insert a synthetic sourced place, verify constraints and indexed searches, then verify populated downgrade refusal. Do not migrate an unknown or populated production database automatically.
4. On the authorised Gramps test instance, export its actual OpenAPI specification and run the authenticated, read-only contract and person/family GET checks. Review response shapes, expired/denied auth behavior, source data minimisation and restart persistence. An offline schema match or prior read snapshot cannot authorise a later tree write.
5. Verify the documented cold backup and isolated restore for all required Gramps/media/research volumes, including media checksums. Review image licences and production dependency locks. Reassess R0.1 only after this evidence is captured and reviewed.

No real family records, existing PostgreSQL rows, accepted Gramps objects, Docker volumes, credentials or private genealogy files were added to Git or the report. The ZIP and temporary test artefacts remain in the project deliverables inspection directory and are not part of PR #6.
