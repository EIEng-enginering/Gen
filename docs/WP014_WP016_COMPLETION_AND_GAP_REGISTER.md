# 24 Gen — Original WP-000–016 Coding Completion and Gap Register

## Coding work complete in this handoff

WP-014 evidence comparison (local image preview only), WP-015 citation-grounded *deterministic* research guide (not an LLM), WP-016 read-only research operations dashboard. Combined change is intentionally schema-neutral, read-only with respect to Gramps, and network/billing-disabled. Existing Q01–Q50 requirements and versioned core evidence models are unchanged.

## Milestone status

- WP-000–013: development candidates in stacked draft pull requests, with Windows Python test evidence from Codex. Not merged or deployed as a release.
- WP-014–016: locally implemented and regression-tested; pending Codex integration, Windows tests, live PostgreSQL and UI checks.
- R0.1: **NOT ACCEPTED** until Docker/WSL2/Gramps login and imports, persistent volumes, nine-volume cold backup, isolated media restore, version/image/rights review and rollback are proven on an authorised host.

## Material user requirements not yet delivered in full

1. **Gramps accepted-tree write adapter:** real API compatibility, idempotent and reversible transactions under separate human approval; deliberately disabled now.
2. **Calibrated record linkage and genealogical probabilities:** current matching is heuristic and uncalibrated; needs independent gold-set benchmarks, false-merge thresholds, conditional dependence model, and unknown options.
3. **Legal record-provider connectors:** current source policies are metadata; actual approved API/bulk connectors, provider permissions, rate enforcement and audit have not been built.
4. **Handwritten-document recognition:** preserved manual transcription corrections exist; real local HTR and gated optional cloud HTR, quality review and document-image storage remain unbuilt.
5. **AI research:** current WP-015 is deterministic, not live LLM/agent inference; opt-in model adapters, grounding verification, spending/permission safeguards and workflow execution remain unbuilt.
6. **Full interactive genealogical UI:** current provisional appearance-tree views are not the complete accepted Gramps pedigree/descendant/fan/hourglass and evidence-linked map interface.
7. **Operations hardening:** Docker/WSL2 and PostgreSQL integration, concurrency, large-scale tests, restore, security, image licences and version pinning remain unaccepted.

**Never represent completion of 17 numbered code packages as delivery of all Q01–Q50 functionality.** Codex should report each unmet requirement with owners, reproducible tests and future implementation work packages.
