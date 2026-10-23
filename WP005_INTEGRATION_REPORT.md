# WP-005 integration report — 23 October 2026

**Decision: development candidate; R0.1 NOT ACCEPTED.**

## Source and Git state

- Applied the supplied `APPLY_SAFE.py` to the clean exact baseline `6a299b1f26cbadf350a6a58297b07027d5822f66` in `C:\24Gen\Gen`, outside OneDrive. It created `feature/wp-005-versioned-hypotheses` and staged all 14 manifest paths. The original WP-002–004 branch and three earlier draft PRs were not reset or merged.
- WP-005 package SHA-256: `9F84A181FC35149B183DADD1D3C80A92603C6D4626BDE4694B65A6B248A38CAD`.
- Full integrated source reference ZIP SHA-256: `5103B7445B7D188BCE141E793F9689E8A6CE2A61B954CB65C685C69115C88C3B`.
- The 79 reference files were present in the applied checkout. Eight raw hashes differed because of Windows line endings; `git diff --no-index` reported no content changes for those files. The installer independently verified all 14 baseline and replacement hashes and the exact patch.

## Windows validation

| Gate | Result |
| --- | --- |
| Python environment | Existing project virtual environment, Python 3.12.14; `pip check` passed. |
| Full Python suite | **40 passed**, one Starlette/AnyIO deprecation warning. Includes disposable SQLite migration 001 → 002, old-record retention, downgrade refusal with branch history, version conflicts, evidence and authentication guards. |
| Q01–Q50 | Validator passed all 50 approved decisions. |
| Python compile and API schema | `compileall` passed; all three WP-005 OpenAPI route patterns present. |
| Browser panel | Extracted script passed `node --check`; authenticated `/workspace` test returned 200, included the graph comparison panel and a Content Security Policy header. |
| Patch quality | `git diff --cached --check` passed. |
| Security and licensing review | No new requirements, outbound provider calls, accepted Gramps write adapter, or client-authored probability field added. Existing mutable container image tags and production dependency/licence review remain release blockers. |
| Live Docker/Gramps/PostgreSQL/backup restore | **NOT RUN:** Docker CLI and WSL2 are not installed on this host. No live database, Gramps owner account, GEDCOM import, nine-volume backup, or isolated media restore was accessed. |

The graph API stores provisional research branches and review history in the separate research schema. It does not alter the authoritative Gramps tree or produce calibrated family probabilities. Local SQLite tests do not establish PostgreSQL, Docker, or recovery compatibility.

## Remaining gates

Review the draft PR stack in order: WP-000 #2, WP-001 #3, WP-002–004 #1, then this WP-005 branch. On a disposable Windows Docker host, verify PostgreSQL migration from a backed-up 001 database, Gramps owner login and persistence, auth guards, nine-volume cold backup, isolated media restore, image digests, and licence checks. Record independent evidence before any R0.1 acceptance decision.
