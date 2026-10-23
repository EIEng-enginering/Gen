# WP-007 — Authenticated read-only Gramps person/family checks

**Status:** candidate implementation for the combined WP-006 + WP-007 release. **No accepted-tree writes.** The public Gramps Web API documentation describes authenticated `GET /api/people/{handle}`, `GET /api/families/{handle}`, and `GET /api/metadata/`; the running instance's `/api/swagger-ui` is authoritative for its installed version. See https://www.grampsweb.org/development/backend/api/ and https://www.grampsweb.org/development/backend/queries/.

## Implemented

- Preserve all WP-006 immutable previews, source requirements, review/audit and digest-confirmed human approval logic.
- For a **currently approved** (not rejected, not stale) WP-006 plan, optionally use a local configured JWT to issue only Gramps `GET` requests for the plan's claimed person handles and all directly related family handles.
- Refuse external/custom upstream URL hosts, userinfo, query strings, redirects, unrecognised object response formats, unsupported relationship operations, unknown handles, oversized responses, missing token, and inaccessible objects.
- Inspect whether proposed parent-child/spouse relationships *already appear* in observed Gramps family references. This is merely a finding, not a proof that applying changes is safe. No Gramps `POST`, `PUT`, `PATCH`, `DELETE`, transaction, object creation, family merging, or undo is implemented.
- Store a reduced SHA-256 fingerprint and sparse findings in the *local* research DB (`gramps_read_validations`) using Alembic revision `20261023_004`, along with an audit entry. Do **not** store upstream names, dates, living-person details, full person/family records, credentials, or token values.
- Expose a basic manual read-validation interface from the existing Gramps dry-run review tab. The UI requires a previously created and approved plan UUID.

## Routes

| Verb | API endpoint | Effect |
|---|---|---|
| `POST` | `/api/v1/research/gramps/plans/{plan_id}/read-validate` | GET-only Gramps query; write **local** audit result only. Requires local HTTP Basic and `X-24Gen-Intent: research`. |
| `GET` | `/api/v1/research/gramps/plans/{plan_id}/read-validations` | Recent local read-validation history (last 25). Requires local HTTP Basic. |

A successful preflight always returns `execution_enabled: false` and `future_write_eligible: false`. A full backup, real Gramps API compatibility review, atomic upstream concurrency semantics, person identity verification, and transactional rollback are **still untested and are required prior to any future write adapter**. Gramps change timestamps/hints are *not* assumed to be compare-and-swap tokens.

## Environment

- `GEN_GRAMPS_API_URL` default `http://grampsweb:5000/api` (may only point at local/internal Gramps endpoint).
- `GEN_GRAMPS_ACCESS_TOKEN` short-lived read-capable JWT configured on the local host. Never commit it or put it in OneDrive or logs. Tokens may expire and must be refreshed manually pending a vetted credential flow.
- Maintain password protection for local app. Do not expose direct HTTP Basic to the public internet.

## Migration

Backup the **disposable** PostgreSQL research database first. Test Alembic `20261023_003 → 20261023_004` against a disposable copy; existing tables/evidence must remain intact. Downgrade from 004 to 003 is blocked when any preflight has been recorded. Never migrate actual live family research without verified backups/restore.

## Tests and integration

Run the full Python suite from repository root with `PYTHONPATH=.;apps/research-web` on Windows and `PYTHONPATH=.:apps/research-web` on Linux. Validate all 50 decisions. A `MockTransport` simulates the Gramps service in automated tests; this is **not** a substitute for real Windows Docker/Gramps validation. The attached package is intentionally grounded against the immutable WP-005 commit; apply WP-006 and WP-007 together only when that baseline matches exactly.

## Limitations and next implementation

- No complete Gramps family topology consistency, biological/adoptive type conversion, household/relation identity inference, or full genealogical proof is implemented.
- No calibration of family probabilities or automatically learned model is implemented.
- Read-only results are ephemeral observations; upstream can change at any moment, and snapshots alone do not authorise any subsequent mutation.
- No licence to scrape sites is conferred. No user data should enter tests, developer support bundles, Git or cloud AI inadvertently.
