# WP-016 — Research Operations and Approval Dashboard

**Status: local, read-only operational visibility.** This package does not add a new execution worker. Actions such as pause, resume and cancel remain in the existing guarded WP-002 job-control APIs.

## Implemented

- `GET /api/v1/research/ops/dashboard`: bounded project counts, research-job/task state totals, last 15 jobs, last 15 audit events (without sensitive `details_json`), source-provider policy metadata and clear disabled execution flags.
- `GET /api/v1/research/ops/reviews?limit=50`: unreviewed provisional branch revisions and Gramps research-only change plans. Bounded windows flag possible truncation.
- `GET /api/v1/research/ops/jobs/{job_id}`: queue statuses and cents, all-task aggregate budget sums, last 200 task summaries, no lease tokens, no source-record payloads. This shows **reported** cost, not charges billed by a provider.
- `/workspace` **Operations dashboard**: summary panels, provider policy indicators, human review queue and job budget inspection.

## Boundaries

Research-task rows remain local metadata. Provider permission declarations do not grant access. No rate limiter or provider worker was added. Costs only reflect reservations/reported local completions; those figures are not reconciled against outside invoices. Basic authentication and existing local-only deployment rules remain. No accepted-tree write route is introduced.

## Remaining validation

PostgreSQL concurrency/budget contention tests, UI keyboard/accessibility checks, hundreds-of-thousands-of-rows performance test, real worker recovery, rate/cost controls in any future external executor, reliable queue status reconciliation with worker sessions and operational observability. Installation is not release acceptance.

## Tests

`tests/test_wp016_operations.py`: authentication, counts, job cents/reservations, missing jobs, research-only pending reviews, provider policy and audit-data minimisation.
