# WP-010 — Source-origin dependence, duplicate-evidence defence and cache receipts

**Scope:** research-database evidence only. No accepted-tree writes, automatic merges, downloaded data or third-party website access.

## Delivered

- `original_source_families` and `original_source_members`: human-attested assertions that catalogue items originate from one underlying manuscript/page. Individual `source_documents` and citations stay immutable and independently addressable.
- Provenance grouping combines manual group membership, matching `origin_group` hints, and identical SHA-256 checksums using transitive components. This intentionally errs towards warning of dependence; it does not infer that ungrouped sources are independent.
- `POST /api/v1/research/source-dependence/assess` accepts 1–100 known document IDs and returns potentially dependent evidence groups, without probabilities or identity merges.
- `GET /api/v1/research/documents/{id}/possible-copies` returns bounded exact-origin/checksum candidates for human review.
- `POST /api/v1/research/source-families`, `POST /api/v1/research/source-families/{id}/members`: explicit local-auth + `X-24Gen-Intent: research` controls, idempotent stable keys, no silent changes or remapping.
- `source_cache_receipts`: immutable acquisition metadata for a registered source, including rights basis, checksum and optional expiry. **No raw source image, licensed webpage, cookie, credential or private family data is cached in this table.** This is not an external source content cache.
- Historical source document records are never merged, and agreement between webpages that reproduce one original must not count as independent confirmations.

## Not provided

- Automatic licence decisions; unrestricted third-party scraping; source content downloads; trusted global catalogues; proven independence; deletion or rewriting of original records; Bayesian linkage or calibrated probability.

## Acceptance

- Tests in `test_wp010_source_families.py`, `test_wp010011_metadata.py`, `test_wp010011_migrations.py` pass.
- Run Alembic 005→006 on a **disposable** research database after a verified backup. Confirm old source/observation counts and hashes; prove that downgrade refuses populated source-family/cache rows.
- Auth, idempotence, conflicting membership and transitive origin-group warnings must pass.
