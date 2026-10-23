# WP-014/015/016 integration and acceptance report

Date: 2026-10-23. Repository: `https://github.com/EIEng-enginering/Gen.git`. Parent branch `feature/wp-012-013-provisional-visualization` at `6cb7532b688faeea94ef700580354db5db7fbe1e` (draft PR #8). Candidate branch `feature/wp-014-016-evidence-assistant-ops`; package commit `ed96aea1e6909d07fdf0e3ea34900998b3e5366f`. Draft PR link and final documentation commit will be recorded in the PR and final handoff.

## Package and integration

- Source archive: `24Gen_WP014_WP015_WP016_Combined_Codex_Ready.zip`, SHA-256 `0ef6f8a5b805cf2ecf5820cc4dd53beb3e070d0b227839eb5f9bebb693f0523c`.
- Extracted outside Git after checking 22 entries for traversal, absolute paths, symlinks, duplicate case-insensitive names and size limits; all 21 entries in `SHA256SUMS.txt` matched.
- Confirmed the authorized repository, exact clean parent SHA, and open draft parent PR. `APPLY_SAFE.py --verify-only` passed. Applied through `APPLY_SAFE.py --apply` to a new branch. All 15 output file SHA-256 values match `MANIFEST.json`; the package commit contains exactly those 15 paths. No previous file was overwritten outside the manifest, and no migration was added.
- New scope: evidence dossier/comparison and local image preview; deterministic offline three-mode research guide; authenticated read-only operations dashboard; 14 supplied tests and package documentation. Existing basic auth and research mutation intent controls remain. No accepted Gramps object write, provider executor or external AI call is enabled.

## Verification on Windows

| Check | Result |
|---|---|
| Full project test suite, `python -B -m pytest -q -p no:cacheprovider apps/research-web/tests` with disposable temp base | **112 passed**, 1 upstream Starlette/AnyIO deprecation warning; 73.02 s. Previous verified branch had 98 tests. |
| `python -B tools/validate_decisions.py` | PASS, all Q01–Q50 approved decisions. |
| `python -m pip check` | PASS, no broken requirements. |
| Python source compile | PASS, 74 project files compiled in memory. |
| Embedded workspace JavaScript extracted from UI; `node --check` | PASS. |
| `git diff --check`; independent manifest hash comparison | PASS, all 15 package paths. |

Environment: Windows NT `10.0.26200.0`; project Python `3.12.14`; Node `v24.19.0`. The installed PostgreSQL 16 service answered `pg_isready` on `127.0.0.1:5432`, but no disposable database credentials or approved instance were provided. Docker CLI was unavailable; WSL did not start. `GEN_DB_URL`, `GEN_DB_PASSWORD`, and `GEN_GRAMPS_ACCESS_TOKEN` were absent.

## Contract and rights review

- Evidence API and assistant/dashboard endpoints require application basic authentication. Supplied synthetic tests include denial without credentials. The evidence compare operation reads 2–6 observations and returns citations, original-family dependence warnings, and `calibrated_probability: null`; it does not invent a calibrated score.
- Browser preview accepts a user-selected PNG/JPEG/WebP file under 20 MB through File/Blob object URLs and revokes the URL. New server code does not fetch, upload or store images. UI text is rendered through text nodes rather than injected HTML. A synthetic interactive screenshot, keyboard review and screen-reader check remain open.
- The assistant generates a deterministic offline guide with cited selected evidence and three mode labels. It contains no LLM invocation. Provider policy remains a planning/rights gate; it authorizes no restricted-source queries, fees or account use.
- Dashboard endpoints read counts, bounded job/review/audit summaries and provider policy. The inspected WP-014–016 code has no Gramps POST/PUT/PATCH/DELETE path and no outbound provider/model execution. This review does not certify an installed service or external integrations.
- No real genealogy records, credentials, original images or live databases were read, copied, migrated, uploaded or disclosed during integration.

## Outstanding acceptance gates

1. On an authorized disposable PostgreSQL instance, test the existing `20261023_001`–`007` migration chain, row-count/hash preservation, uniqueness/FK behavior, refusal of destructive downgrade, and backup/restore. WP-014–016 has no new migrations.
2. On an approved controlled Windows host with Docker/WSL and a disposable Gramps tree, verify login/import, persistence, loopback binding, nine-volume cold backup and isolated restore. Do not use the observed Windows PostgreSQL service as a disposable target.
3. Perform browser screenshot, keyboard and screen-reader review on synthetic data, followed by performance/load testing and licence/version review of deployable images.
4. Complete the material Q01–Q50 gaps itemized in `POST_WP016_Q01_Q50_GAP_AUDIT.md`, especially calibrated genealogy probabilities, authorized source connectors, OCR, opt-in real AI, approved Gramps writes, advanced pedigree UX and installed recovery.

**Disposition: development candidate; R0.1 NOT ACCEPTED.** Parent and this PR remain draft for human review. No merge or accepted-tree write is authorized by this report.
