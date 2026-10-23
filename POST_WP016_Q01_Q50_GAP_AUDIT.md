# Post-WP-016 Q01–Q50 gap audit

Date: 2026-10-23. Baseline: `6cb7532b688faeea94ef700580354db5db7fbe1e`; candidate branch: `feature/wp-014-016-evidence-assistant-ops`.

This audit compares the approved decisions in `docs/DECISIONS_Q01_Q50.json` with source and synthetic tests through WP-016. **Candidate** means code and synthetic tests exist, but installation and release gates remain open. **Partial** means material behavior is absent. **Unverified** means the decisive external or installed-system test was not run. No entry is an acceptance claim. WP labels below are proposed work owners, not approved work packages.

| Decision | Current evidence | Remaining gate / proposed owner |
|---|---|---|
| Q01 | English historical rule/place modules; candidate | Wider English/Welsh coverage, parish geography and extension fixtures; WP017 historical data |
| Q02 | GEDCOM importer and research API; candidate | Real Gramps import/manual entry, duplicate import verification; WP021 Gramps acceptance |
| Q03 | Candidate/review separation and no accepted-tree writer; candidate | End-to-end approval workflow with controlled accepted writes; WP021 |
| Q04 | Local research service, deterministic offline assistant; candidate | Installed local/cloud-disabled operation and opt-in transmission controls; WP020 AI / WP023 operations |
| Q05 | Provider policy and manual-only tasks; candidate | Rights-reviewed licensed connectors and ongoing licence checks; WP017 providers |
| Q06 | Gramps read/contract modules and separate research database; partial | Live Gramps persistence and approved adapter writes; WP021 |
| Q07 | Civil/census/parish source metadata; partial | Authorised first-priority connectors and real-source fixtures; WP017 |
| Q08 | Bounded graph/task concepts; partial | Full ancestor/household expansion with verified breadth/depth limits; WP019 graph |
| Q09 | Versioned alternative branches and unknowns; candidate | User-facing complete branch/probability comparison, calibrated scores; WP019/WP022 UX |
| Q10 | Research UI, evidence panel, assistant prototypes; partial | Coordinated person navigation and integrated document/tree UX; WP022 |
| Q11 | Source/original families, revisions, citations; candidate | Immutable permitted original image storage/link and live provenance audit; WP017/WP018 |
| Q12 | Historical matcher plus deterministic guide; partial | Independent statistical and real language-model outputs, traceability; WP019/WP020 |
| Q13 | Graph/calibration scaffolding; partial | Connected Bayesian model, unknown normalization and held-out calibration; WP019 |
| Q14 | Basic auth and backup scripts; unverified | Loopback installed service and exact-volume cold backup/isolated restore; WP023 |
| Q15 | Indexed schema and bounded queries; partial | 100k synthetic load, batching and recovery drill; WP023 |
| Q16 | Historical place tables/rules; partial | Date-specific county/parish/district boundary corpus and fixtures; WP017 |
| Q17 | Name matching rules; partial | Broad variants, aliases, phonetics and original-preserving benchmark; WP019 |
| Q18 | Historical linkage fixtures; partial | Longitudinal household reconstruction and convention-rich 1841/1851 validation; WP019 |
| Q19 | Three deterministic assistant modes; partial | Complete persistent progress, UI switching and permission parity; WP020/WP022 |
| Q20 | Review queues and conflicting branches; candidate | Human review to controlled accepted-tree action; WP021 |
| Q21 | Graph branches and task caps; partial | Generation/result/cost bounded exploratory expansion across all relative types; WP019 |
| Q22 | Versioned family graph; partial | Dependency-aware probability computation without shared-evidence multiplication; WP019 |
| Q23 | Task planner, budgets, deterministic suggestions; partial | Auditable expected-uncertainty/cost ranking on benchmark data; WP019 |
| Q24 | Versioned hypotheses and queues; candidate | Demonstrate complete affected-subgraph recalculation and acceptance workflow; WP019/WP021 |
| Q25 | Provisional visualization; partial | Interactive full-branch comparisons with calibrated scores, unknowns and geography; WP022 |
| Q26 | Policy registry blocks restricted automation; partial | Rights-cleared real API connectors, throttle and manual-assisted import; WP017 |
| Q27 | Pilot-oriented documents; partial | Select/validate pilot dataset and licensed acquisition gate; WP017 |
| Q28 | Editable literal transcripts and image preview; partial | Local handwriting recognition, opt-in cloud path, immutable image/run trail; WP018 OCR |
| Q29 | Original-source grouping and provenance; candidate | Real provider ingestion and duplicate census-family benchmark; WP017/WP019 |
| Q30 | Jobs, leases, budgets and idempotency tests; partial | Live worker, durable cache, pause/resume and payment approval end-to-end; WP023 |
| Q31 | Provisional views; partial | Ancestor/descendant/hourglass/relationship/fan zoom and navigation; WP022 |
| Q32 | Alternative branches in provisional UI; partial | Complete accepted/provisional comparison and accessible non-colour distinctions; WP022 |
| Q33 | Local File/Blob preview, transcript revisions, comparison; partial | Integrated zoomable permitted original, audit-linked correction and citation UX; WP018/WP022 |
| Q34 | Deterministic cited guide; partial | Real opt-in natural-language AI with bounded tools and reviewed actions; WP020 |
| Q35 | Read-only operations dashboard; partial | Working pause/resume/cancel controls and live usage accuracy; WP023 |
| Q36 | Manifested packages and integration reports; candidate | Continue independent review and acceptance evidence per package; ongoing governance |
| Q37 | Versioned migrations, backup scripts; unverified | Disposable PostgreSQL migration/rollback with original-row hashes and isolated restore; WP023 |
| Q38 | 112 Python tests; candidate | Browser, genealogy, probability, recovery and CI release gates; WP019/WP022/WP023 |
| Q39 | Compose/deployment files; unverified | Windows Docker install, persistent volumes, shortcuts, health and backup smoke; WP023 |
| Q40 | Stacked draft PR process; candidate | Review/merge decisions and release acceptance report; ongoing governance |
| Q41 | Source classifications and citations; partial | Full GPS assessment including negative/indirect/derivative evidence and conflict resolution; WP019 |
| Q42 | English consistency rules; partial | Broad period-aware exceptions and false-positive fixtures; WP019 |
| Q43 | Benchmark CLI/scaffolding; partial | Independently reviewed gold standard with precision/recall/error report; WP019 |
| Q44 | Calibration scaffolding; partial | Held-out stratified reliability, Brier, coverage and abstention report; WP019 |
| Q45 | Audit/review history; partial | Controlled training/evaluation/version rollback and promotion gates; WP019/WP020 |
| Q46 | Incremental candidate releases; unverified | Installed continuously usable release preserving prior functions; WP023 |
| Q47 | Read-only documented Gramps API integration; partial | Versioned live contract and approved write adapter, no direct DB writes; WP021 |
| Q48 | Deployment and backup materials; unverified | Real Windows login/import, persisted service, shortcuts, cold backup/restore; WP023 |
| Q49 | Decision validation and synthetic regression; partial | Enforced CI, integrity/probability/security, rollback and release acceptance; WP023 |
| Q50 | Versioned decisions, schemas, prompts and PR chain; candidate | Maintain complete traceability and verify release artifacts/history; ongoing governance |

## Release gates and reproducibility

- The 50 **decisions** remain approved; the implementation is a development candidate. `python -B tools/validate_decisions.py` passes all 50, which validates the decision register, not delivery of every requirement.
- WP-016 adds no migration. The `20261023_001`–`007` chain still needs testing against disposable PostgreSQL with row counts/hashes and non-destructive rollback behavior.
- Docker/WSL, a disposable authenticated Gramps instance, and an approved Windows installation host were unavailable in this run. No existing genealogy database was migrated or modified. No real family data was read, uploaded or disclosed.
- A synthetic browser screenshot and keyboard/screen-reader review are outstanding. Static UI script syntax and synthetic API/HTML tests pass, but do not replace an interactive accessibility check.
- R0.1 is **NOT ACCEPTED** pending the installed-system, recovery, rights, data-quality and user review gates above.
