# Combined WP-010 / WP-011 integration and acceptance report — 23 October 2026

**Status: integrated development candidate; R0.1 NOT ACCEPTED.** Code was committed and pushed for review. It was not deployed or merged. No live genealogy data, accepted Gramps object, provider website/API, billable service, populated PostgreSQL database, or backup volume was accessed or modified.

## Source, exact baseline, branch and PR

- Repository: `https://github.com/EIEng-enginering/Gen.git`; active checkout `C:\24Gen\Gen` outside OneDrive.
- User-supplied `24Gen_WP010_WP011_Combined_Codex_Ready.zip` SHA-256: `8441c5b4b6992ece1cadc55712bbc0002acc2fcdf2b6ace410b209fc6b2842b7`. The original ZIP was copied intact into the separate project inspection directory. All 20 entries passed path, duplicate, symlink and size screening; `SHA256SUMS.txt` matched all 19 other entries before extraction outside Git.
- The local clean parent `feature/wp-008-009-historic-readiness` and remote head both matched `9162283ba47f8d89b69f084835162dfe19bc0a7b`. The remote parent was rechecked before commit and had not moved. No reset, force-push, merge or existing-file overwrite was used to satisfy package checks.
- `APPLY_SAFE.py --verify-only` passed the exact commit, clean tree, 13 baseline/overlay hashes and patch preflight. The installer then applied its 13 paths on new branch `feature/wp-010-011-provenance-jobs`; no other source path was staged.
- Two reviewed corrections within the 13 manifest paths: a source family with only one attested member no longer claims a shared original; new regression tests cover that case and expired-lease reclaim with stale-token rejection. These two files intentionally differ from their original overlay hashes after application. The full suite was rerun after these changes.
- Exactly the 13 manifest paths were staged and passed `git diff --cached --check`. Implementation commit: `756a828693fda900329ef9a22334936ac2e37e9b`. Branch was pushed to `origin/feature/wp-010-011-provenance-jobs`.
- One [draft PR #7](https://github.com/EIEng-enginering/Gen/pull/7) targets the WP-008/009 branch and draft PR #6. Earlier draft dependency order remains #2 → #3 → #1 → #4 → #5 → #6 → #7. No PR was merged.

## Integrated files and behavior

| Scope | Manifest paths | Review result |
| --- | --- | --- |
| App and schema wiring | `apps/research-web/app/main.py`, `apps/research-web/app/research/models.py`, `apps/research-web/app/research/ui.py` | Registers new research-only routes, models and local UI panels. UI says provider tasks are staged only. |
| WP-010 provenance | `apps/research-web/app/research/source_families_api.py`, `apps/research-web/migrations/versions/20261023_006_original_source_families.py`, `docs/wp010/README.md` | Human-attested source families, unique member document assignment, transitive dependence warnings using membership/origin/checksum, immutable metadata-only cache receipts. Individual source documents remain intact. |
| WP-011 local tasks | `apps/research-web/app/research/task_queue_api.py`, `apps/research-web/migrations/versions/20261023_007_research_tasks.py`, `docs/wp011/README.md` | Idempotent job tasks, cents reservations, local-review-only finite leases, hashed lease tokens, idempotent completion, immutable provider policy metadata. The API contains no external provider client or paid executor. |
| Supplied and added tests | `apps/research-web/tests/test_wp010_source_families.py`, `test_wp011_tasks.py`, `test_wp010011_migrations.py`, `test_wp010011_metadata.py` in the same tests directory | Auth and research-intent denial, source family/copy grouping, idempotence, rights metadata, budget/lease/duplicate completion, provider-task denial, and migration safeguards. |

All Q01–Q50 decision files remain unchanged, including Q12 A+B, Q14 B, Q19 A+B+C. Source-provider rows record proposed access terms, rate caps and budgets; **they do not grant rights or run calls**. Task completion records a local reported cost only; it does not bill an external service. Local mutating routes use the existing basic-auth and `X-24Gen-Intent: research` guard. No Gramps accepted-tree mutation route was added.

### Source-independence integration limit

The new `POST /source-dependence/assess` returns one possible-original group when two documents are manually attested as copies, and tests cover transitive grouping without declaring other groups independent. The older hypothesis graph assessment still derives `distinct_declared_origin_groups` and duplicate warnings from each document's original `origin_group` text. It does **not** yet consume `original_source_members`. Consequently, a graph can display two declared groups even when WP-010's new endpoint groups those documents as one original. No calibrated support probability is produced, and the UI warns that declared groups do not prove independence. Integrating manual membership into graph evidence display/review is an outstanding issue before anyone treats counts as independent corroboration.

## Checks run on this Windows host

| Check | Observed result |
| --- | --- |
| Runtimes | Existing project virtual environment: Windows Python 3.12.14; Node v24.19.0. No dependency installation was needed. |
| Full automated tests | `python -B -m pytest -q -p no:cacheprovider apps/research-web/tests` with disposable `--basetemp`: **93 passed**, one upstream Starlette/AnyIO deprecation warning. Supplied package initially passed 91; two targeted regressions raised the final count to 93. |
| Approved decisions | `python -B tools/validate_decisions.py`: **PASS**, all Q01–Q50 match the approved Rev A baseline. This proves register preservation, not completion of all product requirements. |
| Dependencies and syntax | `python -m pip check`: **PASS**. All 62 Python application, migration, test and tool source files compiled in memory. Embedded workspace JavaScript extracted and passed `node --check`; `git diff --check` and staged whitespace check passed. |
| Authentication, rights and scheduling | Tests passed for missing mutation intent, family/member/cache/policy idempotency and collisions, duplicate-origin grouping, budget exhaustion, lease expiry/reclaim, stale token refusal, repeat completion and denial of manual/provider task claims. Static review found no HTTP client, provider network executor or Gramps write path in the two new API files. These tests are local SQLite/API checks, not live PostgreSQL concurrency or provider-rights approval. |
| Synthetic backup and migrations | A fresh SQLite database at revision 005 held one synthetic source document, one observation and one historical place. Its pre-upgrade backup matched byte-for-byte (backup SHA-256 `c177865bcb574f4f08a867d536c54cae35856a932fdda391329f2fc7d76d9adf`). Sequential 005→006→007 left old-table row counts at **1, 1, 1** and hashes unchanged after each step: source `7f8793292239aa0ed4599a52997efbcf03fa5958e917123a19d158a160f3b125`; observation `9a276f4eaa3e7e8bad63ea0a898908c9af778027730ecd9a59421e97f080e751`; place `17bf48eea0f2b1ac77d09f063777cfa4e16c0498d0604d65be7b3dc8f3738e7d`. New family, member, receipt, task and policy rows were inserted. Duplicate member/document and task/job-key rows plus invalid member FK were rejected. Populated 007→006 and 006→005 downgrades refused data loss. This is **not** a PostgreSQL result. |
| PostgreSQL | Windows `postgresql-x64-16` service answered `pg_isready -h 127.0.0.1 -p 5432`. `GEN_DB_URL` and `GEN_DB_PASSWORD` were absent. The existing service was not assumed to be a disposable project database. No login, migration, SQL write or concurrent reservation test was run there. |
| Docker / WSL2 / live Gramps | Docker CLI absent; WSL command returned not installed; no `GEN_GRAMPS_ACCESS_TOKEN` was set. Real owner login/import, service persistence, Gramps API checks and exact nine-volume cold backup plus isolated restore were **NOT RUN**. No Windows administrator-controlled Docker test host was available in this task. |
| Image and licence review | `deploy/compose.yaml` defaults to tag-based images (`grampsweb:latest`, `valkey:8-alpine`, `postgres:17-alpine`); `apps/research-web/Dockerfile` starts from `python:3.12-slim`. Deployable digests are not pinned or verified. The repository licence register requires separate review of code licences and historical-provider terms; no current third-party source permission was accepted by this integration. |
| CI | GitHub's PR-triggered workflow query surfaced no run for the implementation commit at inspection time. The Windows results above are the available test evidence. |

## Installation and acceptance work remaining

1. Review the stacked draft dependency chain, including this draft PR. Keep R0.1 unaccepted and the accepted Gramps tree write gate disabled.
2. On an administrator-controlled Windows test host, install/verify WSL2 and Docker Desktop, pin and record exact image digests, configure secrets outside OneDrive, and start the local-only Compose stack with synthetic or expressly approved disposable family records.
3. Back up and verify a separate disposable PostgreSQL copy at Alembic revision 005; upgrade manually through 006 and 007. Record source/document/observation counts and hashes, test new constraints and real concurrent job-budget reservations, and prove populated downgrade refusal. Never migrate the observed Windows service by assumption or automatically migrate a production genealogy database.
4. Test real Gramps login/import, person/family read shapes, restart persistence, and the documented exact nine-volume cold backup and isolated restore, including media checksums. Do not copy tokens, raw family data or backups into Git or synced support reports.
5. Reconcile WP-010 manually attested source families with the older graph's declared-origin warning/count display before relying on evidence-independence counts. Review each historical-provider licence/permission and implement audited rate/cost enforcement separately before any provider executor is considered.

The ZIP, extraction, disposable synthetic SQLite database/backup and test helper remain in the separate project inspection directory and are not part of PR #7. No real family data or credentials were disclosed in Git or this report.
