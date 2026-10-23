# Combined WP-012 / WP-013 integration and acceptance report — 23 October 2026

**Status: integrated development candidate; R0.1 NOT ACCEPTED.** The code was committed and pushed for review in one draft PR. It was not deployed or merged. No Gramps accepted-tree object, live genealogy database, source-provider service or backup volume was modified.

## Source, baseline, branch and PR

- Repository: `https://github.com/EIEng-enginering/Gen.git`; active checkout `C:\24Gen\Gen` outside OneDrive.
- User-supplied `24Gen_WP012_WP013_Combined_Codex_Ready.zip` SHA-256: `39d99580c0ed7b08ffb8f3a8e9f4453575216e9c8c3f1fb8271e786ab0b5db53`. The original ZIP was copied intact to the separate project inspection directory. All 17 ZIP entries passed path, duplicate, symlink and size screening; `SHA256SUMS.txt` matched all 16 other entries before extraction outside Git.
- The clean local `feature/wp-010-011-provenance-jobs` branch and remote head matched required SHA `51016ac5c19b338512df14f9cc093c87e3fbb181`. The remote parent was rechecked before commit. No reset, force-push, merge, or modified-file overwrite was used to satisfy preflight.
- `APPLY_SAFE.py --verify-only` passed the exact commit, clean tree, all 10 old/new path hashes and Git patch preflight. A new branch `feature/wp-012-013-provisional-visualization` was created from that parent, and the installer applied exactly its 10 paths with post-application hashes matching the supplied manifest. No package source correction was required.
- Exactly the 10 manifest paths were staged and passed `git diff --cached --check`. Implementation commit: `a9abc46ac39f0479a7501cd0d54b2a39a4773abf`. Branch pushed to `origin/feature/wp-012-013-provisional-visualization`.
- One [draft PR #8](https://github.com/EIEng-enginering/Gen/pull/8) targets `feature/wp-010-011-provenance-jobs`, draft PR #7. Earlier draft dependency sequence remains #2 → #3 → #1 → #4 → #5 → #6 → #7 → #8. None was merged during this integration.

## Integrated files and behavior

| Scope | Manifest paths | Review result |
| --- | --- | --- |
| App and graph wiring | `apps/research-web/app/main.py`, `apps/research-web/app/research/graph.py`, `apps/research-web/app/research/graph_api.py` | Adds read-only visualization routes. Graph assessment now uses WP-010 conservative source classification for referenced documents. Legacy declared-origin counts remain available but are marked unverified; new possible-original group count and warnings expose manually attested duplicates. |
| Bounded diagrams and API | `apps/research-web/app/research/tree_view.py`, `apps/research-web/app/research/tree_view_api.py` | Authenticated GET tree/compare endpoints display historical **record appearances**, not merged or confirmed people. Deterministic node positions, capped nodes/edges, cycle and unknown-observation refusal, explicit unknown option and structural difference summary. Responses keep calibrated probability null and accepted-tree mutation disabled. |
| Browser UI | `apps/research-web/app/research/ui.py` | Side-by-side SVG diagrams, option selectors, zoom, relationship detail list, contradiction marks and source-group warnings. Historical labels are assigned with `textContent` through DOM APIs; no historical data is inserted using `innerHTML`. |
| Tests and documentation | `apps/research-web/tests/test_wp012013_visualisation.py`, `docs/wp012/README.md`, `docs/wp012/WP012_WP013_ACCEPTANCE_GATES.md`, `docs/wp013/README.md` | Auth, deterministic layout, unknown option, comparison, malicious-text handling, read-only set version, and manual cross-catalogue shared-original checks; release gates documented. |

The WP-010 issue recorded in PR #7 is addressed for graph presentation: two documents manually attested as reproductions of one original now appear as **one possible** original group even when their older `origin_group` labels differ. The old `distinct_declared_origin_groups` value is retained for compatibility and is **not** evidence of independence. No Bayesian or calibrated probability is derived from either count. Individual source records are not merged or deleted. All Q01–Q50 decision documents remain unchanged.

## Checks run on this Windows host

| Check | Observed result |
| --- | --- |
| Runtimes | Existing project virtual environment: Windows Python 3.12.14; Node v24.19.0. No dependency installation was needed. |
| Full automated suite | `python -B -m pytest -q -p no:cacheprovider apps/research-web/tests` with disposable `--basetemp`: **98 passed**, one upstream Starlette/AnyIO deprecation warning. This includes existing WP-000–011 coverage and the supplied WP-012/013 visualization tests. |
| Approved decisions | `python -B tools/validate_decisions.py`: **PASS**, all Q01–Q50 match Rev A baseline. This verifies decision-register preservation, not completion of all product requirements. |
| Dependencies and syntax | `python -m pip check`: **PASS**. All 65 Python application, migration, test and tool source files compiled in memory. Embedded workspace JavaScript extracted and passed `node --check`. Git diff and staged whitespace checks passed. |
| API, graph and text safety | Automated tests passed for authenticated GET-only chart/compare responses, no graph version change after repeated reads, unknown alternative, deterministic coordinates, cycle/size refusal, cross-catalogue attested source grouping, null probability and `gramps_written=false`. Malicious label text remains text in the data response; UI uses DOM `textContent` for rendering. These are local API/static UI tests, not a full interactive browser or live Gramps test. No screenshot was captured because no live browser session with synthetic fixture data was available. |
| Schema and PostgreSQL | WP-012/013 adds **no migration or database write API**. The existing SQLite regression suite passed; no new schema migration was run. Windows PostgreSQL 16 responded to local `pg_isready`, but `GEN_DB_URL` and `GEN_DB_PASSWORD` were absent, and the observed service was not assumed to be an authorised disposable project database. No PostgreSQL login or SQL write was attempted. |
| Docker / WSL2 / Gramps | Docker CLI absent; WSL command returned not installed; no `GEN_GRAMPS_ACCESS_TOKEN` was configured. Live Gramps login/import/read, local-only deployment, service persistence, image digest and exact nine-volume cold backup plus isolated restore were **NOT RUN**. |
| Licence and image gates | No provider access or licence was exercised. Existing Compose defaults use tag-based images, including `grampsweb:latest`; deployable image digests and live licence review remain outstanding. |
| CI | GitHub's PR-triggered workflow query surfaced no run for implementation commit `a9abc46` at inspection time. The Windows checks above are the available test evidence. |

## Installation and acceptance work remaining

1. Review the stacked draft dependency chain. Keep PR #8 draft, R0.1 unaccepted, and accepted Gramps tree writes disabled until all relevant review and operational gates pass.
2. On an administrator-controlled Windows test host, install/verify WSL2 and Docker Desktop, pin exact deployable image digests, configure secrets outside OneDrive, and run the local-only Compose stack with synthetic or expressly approved disposable genealogy data.
3. If an explicitly disposable PostgreSQL project instance is available, run the previous migrations there with a verified backup and check the new chart endpoints against that instance. WP-012/013 introduces no schema revision. Never auto-migrate the observed Windows service or a production genealogy database.
4. Verify real Gramps owner login/import and GET-only API response shapes, restart persistence, and the documented exact nine-volume cold backup and isolated restore including media checksums. Review licences and distribution obligations before release.
5. Conduct an interactive browser accessibility and visual review on synthetic data, including zoom, keyboard navigation, narrow layouts and historical labels containing markup-like text. Capture screenshots there if useful; do not expose living-person names in artefacts.

The ZIP, extraction and temporary test artefacts remain in the separate project inspection directory and are not part of PR #8. No real family data, private genealogy images, credentials or unencrypted backups were disclosed in Git or this report.
