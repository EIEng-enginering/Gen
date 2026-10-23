# WP-011 — Local supervised jobs, budgets, task leases and provider-policy metadata

**Scope:** bounded research scheduling **without** live job execution, external data acquisition, spend or Gramps mutations.

## Delivered

- `research_tasks`: durable job task keys, kinds (`local_review`, `manual_lookup`, `approved_api_request`), reservable cost in integer cents, status, attempt counter, hashed lease secret, lease expiry and idempotent completion key.
- `POST /api/v1/research/jobs/{job}/tasks`: idempotent planning with SQL row lock on the parent job (PostgreSQL), job-wide budget reservations and optimistic refusals if an operation would overspend.
- `GET /api/v1/research/jobs/{job}/tasks` and `/budget`: bounded task listing, reservations and remaining budget, with explicit execution disabled notice.
- `POST .../claim`: only supervised **local_review** tasks may be leased. No `manual_lookup` or `approved_api_request` execution is possible. Autonomous jobs remain paused when created under the existing API.
- `POST .../finish`: lease-token checks, expiry, exact completion idempotency, charge <= reserved budget, and audit trail. No actual monetary charge is made; charge amounts are local **reported** work cost only.
- `source_provider_policies`: immutable manual entries for access mode, licence/permission reference, per-day request cap, cooldown seconds and daily cents budget. All policies **report `execution_enabled: false`**, including policies labelled `approved_api`.
- Existing `jobs/{id}/control` pause, resume and cancel functionality remains; this release does not install a worker that runs provider calls. UI adds task staging and inspection.

## Explicit limitations and later hard gates

- **Not a production multi-worker queue:** PostgreSQL row locks should serialise reservations, but no live PostgreSQL concurrency test has been performed. SQLite tests do not demonstrate concurrency behaviour.
- **No automatic rate limiter/executor yet:** Limits are configured metadata, not enforcement of network calls. Do not connect external workers until reviewed provider connector code enforces all provider limits atomically and provides a full cancellation/resume/billing audit.
- No credentials, provider tokens, external HTTP requests, paid API calls, AI model execution or Gramps writes. The lease token is returned once and only its SHA-256 hash is stored.
- Incrementally reconcile task costs in a future ledger before enabling billable operations; floating `ResearchJob.spent_usd` remains legacy summary and is not authoritative for finance.

## Acceptance

- Run tests `test_wp011_tasks.py`, `test_wp010011_metadata.py` and migration tests; verify no endpoint can call a network provider.
- Run disposable PostgreSQL 006→007 migration, preserve old records, test constraints and populated downgrade refusal.
- Future external-worker acceptance requires rate and budget enforcement, true queue concurrency tests and no duplicate billing on retries.
