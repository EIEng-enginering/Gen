# WP-008: Gramps API contract check and execution readiness (safe, non-writing)

Status: DEVELOPMENT CANDIDATE. **R0.1 still NOT ACCEPTED.**

## Delivered

- Authenticated `POST /api/v1/research/gramps/contracts/review` checks a locally supplied OpenAPI 2.0/3.x JSON export, never calls external URLs. Input is capped at 1 MiB; reports only whether GET `/metadata/`, `/people/{handle}`, `/families/{handle}` are declared.
- Authenticated `GET /api/v1/research/gramps/plans/{plan_id}/execution-readiness` reports prior human research review, current plan validation, and most recent read-only observation. **Always execution disabled**.
- `GET /api/v1/research/gramps/execution-policy` explicitly disallows writes.
- Unit/API/security tests (auth, oversized payload, incomplete contract, readiness fail-closed).

## Important limitations

* OpenAPI documentation is not proof that the running Gramps API implements response fields or concurrency semantics. Validate its `/api/swagger-ui` and authenticated GETs using an isolated disposable instance.
* Read snapshots are non-atomic, cannot be treated as compare-and-swap, and expire immediately as concurrency evidence.
* None of these endpoints sends a Gramps mutation. The existing GET-only Gramps WP-007 adapter remains unchanged.
* **WP-008 does NOT permit live accepted-tree changes**, even when all returned GET checks are true.

Sources: https://www.grampsweb.org/development/backend/api/ ; https://www.grampsweb.org/development/backend/queries/ ; https://www.grampsweb.org/user-guide/data-model/
