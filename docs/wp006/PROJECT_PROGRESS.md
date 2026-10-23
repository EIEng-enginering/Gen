# 24 Gen whole-project implementation progress — 23 October 2026

## Evidence-based status

All 50 Q1–Q50 decisions are approved and present in versioned requirements. GitHub repository `EIEng-enginering/Gen` has four unmerged draft PRs stacked from WP-000 through WP-005 at the time of this assessment. The WP-006 implementation has been authored and locally tested but not pushed or merged.

| Workstream | Implemented candidate | Remaining before full approved scope |
|---|---|---|
| Requirements/governance | Q1–Q50, quality CI, API and migration contracts | Merge approval and operational governance |
| Windows foundation | Compose starter, Gramps container declaration, research web, configuration/backup scripts | Live Docker/WSL2 install, owner login, persistence, nine-volume backup and media restore, image locks |
| Historical evidence | Documents, preserved literal observations, citations and origin-group information, audit revisions | Large-scale authorised connectors, rights governance and real English source dataset validation |
| Record import | Limited manual CSV and repeat-import guards | Robust provider mapping, bulk ingestion, media/handwriting and error quarantine |
| Matching | Explainable heuristic candidate ranking, English-rule checks and benchmark CLI | Splink/LLM inference, held-out hard negatives, validated probability calibration |
| Alternative families | Versioned graph branches, explicit unknown, source and topology warnings, research reviews | Joint Bayesian family posterior, hypothesis scoring, graph-wide inference and calibration |
| Gramps approval bridge | WP-006 digest-locked preview + research-only approval, no writes | Verified live read mapping, human-approved transactional writer and rollback |
| Research UI | Local records workspace, comparisons, WP-006 approval form, basic tasks | Full interactive tree views, historical maps, document viewer, complete AI assistant |
| Automation | Queue records/modes/cost fields only | Worker execution, permitted source connectors, retries, limits, budgets, OCR/AI tools |
| Validation | 48 passing Python tests in this environment; database upgrade tests | Windows/Python 3.12, real PostgreSQL, Docker/Gramps, restore drill, licences, performance, calibration |

**Progress estimate (qualitative, not a verified percentage):** the project is through specification and several foundational programming increments, but considerably less than half of its eventual AI genealogy research capability is implemented, and no full release has passed operational acceptance. Code-complete does not mean installed, source-licensed or scientifically validated.

## Immediate execution order

1. Review draft PRs #2 (WP-000), #3 (WP-001), #1 (WP-002–004), #4 (WP-005) in that sequence. Do not rebase or merge without explicit repository-owner review.
2. Apply WP-006 to exact WP-005 commit on a separate review branch using the safe installer. Complete Windows 3.12 checks and open a *draft* stacked PR, not a release PR.
3. On an operator-controlled Windows machine, install/verify WSL2 and Docker and run the accepted-tree Gramps smoke and backup/restore gate with disposable genealogy records.
4. Establish a tested read-only Gramps person/family snapshot adapter, then design a separately gated write adapter; do not enable writes merely because WP-006 records human approvals.
5. In parallel, prioritise source-license-aware English record connectors, hard-negative matching benchmarks, calibrated inference, handwriting recognition and autonomous research, each in independently reviewable increments.
