# WP-013 — Alternative-branch comparison and shared-original evidence warnings

Status: development candidate, calibrated posterior model remains unimplemented.

## Scope

- Authenticated `GET /api/v1/research/hypotheses/{set_uuid}/compare-view?left=KEY&right=KEY`.
- Side-by-side interactive diagrams; options selected explicitly; no evidence-based probability inferred from graph structure.
- Structural difference summary (common/left-only/right-only proposed edge assertions) and explicit other/unknown option.
- **Critical WP-010 reconciliation**: graph `representation()` calls WP-010 conservative source `classification()` for referenced documents and passes it to `graph.assessment()`. WP-010 human-attested original source families, declared origins and matching checksums contribute to warning groups.
- Legacy `distinct_declared_origin_groups` retained unchanged for backwards compatibility but accompanied by `potential_original_group_count`, `possible_original_group_ids` and `independence_verified=false`.
- Shared-origin support/contradiction warnings and dependent documentary evidence are surfaced in JSON and the UI.

## Evidence meaning

A group is **only** a possible shared original, not proof that individual documents are reliable or that separate groups constitute independent corroboration. Do NOT use these numbers to calculate Bayesian support, multiply confidence percentages, infer family identity, or automatically merge people. An attested group can connect apparently distinct catalogue/provider entries. Evidence review is still required.

## Acceptance and safety

- Cross-catalogue human-attested sources count as ONE possible original when charted.
- Duplicate evidence warnings appear both in old graph endpoint and new comparison.
- Read-only endpoints; no new database tables or migrations.
- OpenAPI endpoints require existing Basic authentication; no public graph leakage.
- Accepted Gramps objects, production data and external providers remain untouched.
