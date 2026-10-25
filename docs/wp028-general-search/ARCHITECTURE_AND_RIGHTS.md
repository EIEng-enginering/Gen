# WP-028 — General Historical Search & Correlation (development candidate)

## Architecture decision

Use a **versioned materialized index inside the existing PostgreSQL research database**, not Elasticsearch or an unapproved external source crawler. The index is a derivative projection of immutable `observations`, `source_documents`, and quarantined `staged_evidence`. It can be rebuilt and never replaces the original source document or the accepted Gramps person tree. Alternative evaluated: a separate search engine would increase dependency burden, security surface, and recovery scope without a measured advantage at the pilot scale. PostgreSQL indexes need a separate real `EXPLAIN ANALYZE` benchmark.

## Schema and search behavior

Migration `20261025_010` adds `general_search_mentions` with a unique source-kind/source-id key; indexed normalized surname/year, soundex/year, county/year and status. Original name, place, record class, source reference, reviewed status and licence remain displayed. Normalized keys are **derivative search aids** and do not overwrite source spellings.

`POST /api/v1/research/general/index/sync` processes 1–500 existing records per call with source-ID cursor; the supplied `tools/reindex_general_search.py` performs a bounded resumable sweep. After any later import, start a new sweep from the beginning because UUID identifiers are random. The projection is idempotent; old observations never disappear. Indexing is not a rights grant. Do not enable automatic migrations on production.

`GET /api/v1/research/general/search` retrieves at most 100 indexed results per page by exact/declared variant, phonetic or prefix surname (or county). `GET /api/v1/research/general/mentions/{id}/correlations` compares a capped 250-record pool and preserves unknown/unmatched alternatives. All scores are clearly labelled uncalibrated retrieval heuristics. It does **not** prove identity, family relationships, or biological parentage; no Gramps write adapter is present. Result counts never claim external-collection completeness. Corpus coverage is explicit.

`GET /general-search` serves a standalone accessible browser page with a source-aware result list and side-by-side candidate reasoning. It renders record text with DOM `textContent`, not `innerHTML`.

## Provider-policy matrix (review date: 2026-10-25)

| Provider/channel | Access condition | This increment |
|---|---|---|
| User-owned exports | Operator confirms rights; retain only the permitted fields | Existing WP-026 quarantine and human review |
| FreeBMD public search | Manual browser searches; automated form requests prohibited | Manual lead only; network disabled |
| FreeCEN/FreeREG public interfaces | Site restrictions; no inferred automated API rights | Manual lead only; network disabled |
| Free UK Genealogy extracts | Written approved scope/licence and possible charges | Licensed file adapter only AFTER approval; no purchase |
| The National Archives Discovery API | Contact Archives; the API terms prohibit caching its output | No connector and no returned-result cache |
| FamilySearch or subscription sites | Provider-specific permissions/records; site access does not grant API rights | Manual import of separately permitted exports only |

Permission policies are data, not an exemption to Terms of Use. `general_provider_policy.py` always rejects automated network queries; no HTTP client is imported.

## Design limitations and next measured steps

- This initial search covers *locally indexed* reviewed observations and quarantined leads only. It does not search the user's 1,629-person Gramps database as a unified indexed corpus. The existing WP-025 Guest picker is still separate. A cross-search adapter should convert bounded Guest **GET-only** context into temporary, **uncited** UI clues and must never persist living-person data without explicit authority.
- Full married-name, alias, historical jurisdiction transition, address, occupational, and household-specific scoring require richer typed mention and household tables. Soundex is coarse; it is not sufficient to disambiguate common surnames.
- Incremental indexing is resumable within a sweep; reindex from the beginning after future imports because UUIDs do not have insertion order. Add insert-time write-through or persistent (created_at, UUID) checkpoints after database benchmarking.
- The 100,000-record benchmark tests synthetic materialized index speed on SQLite/Linux. It does not establish PostgreSQL, Windows, production ingest or million-record service levels.
- The system has no calibrated probabilities, adjudicated held-out truth, live provider connector, HTR/OCR model, autonomous worker or accepted-tree edit. Do not silently describe them as implemented.
- Provider requests, credentials, cloud AI spending and accepted-tree writes remain disabled.

## Decision traceability (Q1–Q50 unchanged)

| Approved decisions | Implemented contribution / next gap |
|---|---|
| Q03, Q07–Q11 | Source-preserving index of local documents and observations |
| Q12 A+B, Q13 | Deterministic features and optional **separately coded** AI interpretation; calibration unbuilt |
| Q14 B | Existing basic local HTTP authentication retained |
| Q16–Q18 | Place label/county and surname variants; historical time-varying geography and households still required |
| Q19 A+B+C, Q20 | Browser search and reviewable candidates; bounded autonomy still disabled absent permission |
| Q21–Q25 | Explicit unknown and no silent accepted-tree changes; entire hypothesis recomputation still separate |
| Q26–Q30 | Rights denials, local bulk ingestion & resumable index; provider execution and quotas still incomplete |
| Q33–Q35 | Search display and source citations; full diagrams/operations elsewhere in repo |
| Q41–Q45 | Source-duplication warnings, abstention; benchmark truth set and probabilistic calibration outstanding |
| Q46–Q50 | Tested incremental overlay, migration gate, exact SHA protection and PR review |

## Release gates

**R0.1 NOT ACCEPTED** until reviewed live Windows Docker/Gramps/PostgreSQL installation, source rights, nonempty app-linked media recovery, image locks/licences, original-source evidence quality and review-chain merges are demonstrated. This package is a development candidate only.
