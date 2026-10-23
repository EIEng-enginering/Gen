# WP-006 local verification summary — 23 October 2026

Baseline: `feature/wp-005-versioned-hypotheses` at `f4297df70465e82d89139a2ecef158d57bd5f6ae` (verified against offline Git bundle and remote PR #4).

- Python 3.13 container: `PYTHONPATH=.:apps/research-web pytest -q apps/research-web/tests` **48 PASS** (13 environment/dependency deprecation warnings).
- All Q01–Q50 decision register validation: **PASS**.
- Python compilation: **PASS**.
- Browser JavaScript `node --check`: **PASS**.
- SQLite migration 002 → 003 and old-document retention: **PASS**; populated downgrade refused.
- Auth, idempotency, preview digest, wrong-version rejection, human approval phrase, no accepted-Gramps mutation: **PASS**.
- Live Windows Docker / WSL2 / PostgreSQL / Gramps source APIs / backup and restore: **NOT RUN** (this environment has no Docker CLI or Gramps stack).
- Container-installed dependencies differ from pinned Windows production requirements; Windows Python 3.12 testing is **NOT RUN** on this host.

`R0.1` acceptance: **NOT ACCEPTED**. WP-006 is a candidate for a draft review stacked on WP-005, not a production release.
