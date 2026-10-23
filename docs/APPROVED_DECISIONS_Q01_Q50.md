# Approved Decisions Register — Q01–Q50

**Baseline:** 2026-10-23.  All 50 are approved. Summaries below are faithful engineering restatements, not verbatim copies of each chat choice.

### Q01 — A

**Binding requirement:** England and Wales first, from earliest usable parish registers onward; international expansion later.

**Acceptance evidence:** English/Welsh country-specific datasets, place rules and source metadata; extension interface.

### Q02 — A

**Binding requirement:** GEDCOM imports plus manual entry and AI expansion from documented known ancestors.

**Acceptance evidence:** Import fixture with names, events, citations; no duplicate import; manual entry.

### Q03 — A

**Binding requirement:** AI may search, interpret and score; uncertain merges and relationships require user approval.

**Acceptance evidence:** No direct mutation of accepted tree from autonomous candidate results.

### Q04 — A

**Binding requirement:** Hybrid local Windows website/database and local processing with optional OpenAI cloud API.

**Acceptance evidence:** Application works with cloud AI disabled and never silently transmits records.

### Q05 — A

**Binding requirement:** Start with lawful free sources, authorised APIs, manual file imports; consider subscriptions/bulk data later.

**Acceptance evidence:** Provider capability and licence gate prevent prohibited automated access.

### Q06 — A

**Binding requirement:** Gramps Web as genealogy foundation; separate research database and AI modules.

**Acceptance evidence:** Accepted people persist in Gramps; research records stored separately.

### Q07 — A

**Binding requirement:** Prioritise civil BMD, censuses and parish registers, then probate, newspapers and specialist sources.

**Acceptance evidence:** Connector priorities and record schema cover the first three source classes.

### Q08 — A

**Binding requirement:** Research ancestors, siblings, spouses, descendants and surrounding households, expanding progressively.

**Acceptance evidence:** Expansion jobs use bounded breadth/depth, place and time constraints.

### Q09 — A

**Binding requirement:** Retain alternative relationships, complete hypothetical branches, probabilities, evidence and unknown options.

**Acceptance evidence:** Conflicting parent candidates coexist without destructive replacement.

### Q10 — A

**Binding requirement:** Integrated tree, document viewer, evidence comparison, candidate matches and AI research assistant.

**Acceptance evidence:** UX navigation accepts selected person and displays coordinated panes.

### Q11 — A

**Binding requirement:** Preserve original records or permitted links, transcriptions, citations, provenance and AI interpretations separately; immutable evidence.

**Acceptance evidence:** Original assertion remains unchanged after transcript correction.

### Q12 — A+B

**Binding requirement:** Use statistical/historical matching AND AI language-model analysis as separate evidence contributors.

**Acceptance evidence:** Traceable independent model outputs; AI cannot assert calibrated probabilities alone.

### Q13 — A

**Binding requirement:** Connected Bayesian/evidence-based relationship models calibrated with known cases, unknown option and contradictions.

**Acceptance evidence:** Alternatives and unknown normalise; held-out calibration report.

### Q14 — B

**Binding requirement:** Private local installation, basic password protection and standard backups; no elaborate user security initially.

**Acceptance evidence:** Loopback-only listener; password gate; recoverable data/media backup.

### Q15 — A

**Binding requirement:** Small focused pilot first; architecture allows incremental millions-scale processing with tested recovery.

**Acceptance evidence:** Index and batching plan; 100k synthetic stress benchmark; restore drill.

### Q16 — A

**Binding requirement:** Time-aware English county, parish, registration district, neighbours, boundaries and migration geography.

**Acceptance evidence:** Historical date-specific place resolution includes abolished/renamed districts.

### Q17 — A

**Binding requirement:** Historical name variants, phonetics, aliases, nicknames, maiden names and transcription errors preserved.

**Acceptance evidence:** Variant matcher compares differing spellings but returns original forms.

### Q18 — A

**Binding requirement:** Reconstruct and link households across censuses including departures, births, marriages and migration.

**Acceptance evidence:** 1841 vs 1851 census conventions enforced using fixture households.

### Q19 — A+B+C

**Binding requirement:** Expose three modes: autonomous research, AI-guided manual searches and conventional manual search with AI summaries.

**Acceptance evidence:** User can switch modes; progress persists; permissions consistent.

### Q20 — A

**Binding requirement:** Investigate conflicts, rank hypotheses and queue material accepted-tree modifications for approval.

**Acceptance evidence:** Conflicting candidates remain separate after review rejection.

### Q21 — A

**Binding requirement:** Explore parents, children, siblings, spouses, relatives and connected households in bounded provisional branches.

**Acceptance evidence:** Expansion stops at configurable generation, result and cost caps.

### Q22 — A

**Binding requirement:** Connected dependency-aware probabilistic family graph with historical constraints, unknowns and recalculation.

**Acceptance evidence:** No independent multiplication where evidence or events are shared.

### Q23 — A

**Binding requirement:** Prioritise research by expected uncertainty reduction, availability, cost and effort.

**Acceptance evidence:** Planner emits auditable ranked searches and budget rationale.

### Q24 — A

**Binding requirement:** On new evidence reevaluate affected connections; preserve past results and seek approvals for accepted-tree changes.

**Acceptance evidence:** Versioned hypotheses and impact/review queues.

### Q25 — A

**Binding requirement:** Interactive alternative trees, probabilities, source links, geography, timelines, and whole-branch comparisons.

**Acceptance evidence:** Comparative view includes 2 hypotheses and unknown relationship.

### Q26 — A

**Binding requirement:** Auto-search authorised APIs/licensed data; restricted sources get manual-assisted links/imports only.

**Acceptance evidence:** Policy registry blocks automatic queries to manual-only providers.

### Q27 — A

**Binding requirement:** Pilot family/county dataset, research licensed bulk sources in parallel, expand after validation.

**Acceptance evidence:** Pilot selection and licensed acquisition gate documented.

### Q28 — A

**Binding requirement:** Local handwriting recognition plus optional specialist cloud, AI extraction, original image and correction trail.

**Acceptance evidence:** Manual transcription edit never alters original image or prior run.

### Q29 — A

**Binding requirement:** Unified search catalogue with provider-specific observations, rights, IDs, URLs and provenance; avoid double counting.

**Acceptance evidence:** Two copies of same census observation deduplicated at evidence-family level.

### Q30 — A

**Binding requirement:** Background resumable jobs, caching, source throttling, budgets, cost reporting and paid-acquisition approval.

**Acceptance evidence:** Pause/resume, idempotent retry, budget exceed hard-stop.

### Q31 — A

**Binding requirement:** Multiple zoomable ancestor, descendant, hourglass, relationship and fan charts with optional AI overlays.

**Acceptance evidence:** All views preserve selected individual and navigate correctly.

### Q32 — A

**Binding requirement:** Accepted tree with toggleable visually distinct alternatives and complete hypothesis comparison.

**Acceptance evidence:** Conflicting branches and unknown category distinguishable without relying on colour.

### Q33 — A

**Binding requirement:** Integrated zoomable original image, editable AI transcription, linked citations, and side-by-side fact comparison.

**Acceptance evidence:** Correction is audit logged, original image immutable.

### Q34 — A

**Binding requirement:** Natural-language AI assistant and guided actions for cited research and proposed changes requiring approval.

**Acceptance evidence:** No assistant-origin accepted-tree write without reviewed action.

### Q35 — A

**Binding requirement:** Research dashboard tracks jobs, discoveries, misses, uncertainty, budgets, approvals; pause/resume/cancel.

**Acceptance evidence:** State changes and usage metrics are displayed accurately.

### Q36 — A

**Binding requirement:** ChatGPT prepares specs, modular code, tests and prompts; external coder integrates and reports validation.

**Acceptance evidence:** Work-package manifest, clear integration instructions and evidence template.

### Q37 — A

**Binding requirement:** Git increments, migrations, backups, compatibility checks and rollback preserving data.

**Acceptance evidence:** Rollback tested on representative data; no destructive auto-upgrade.

### Q38 — A

**Binding requirement:** Automated unit, integration, browser, genealogy, probability and backup/restore tests.

**Acceptance evidence:** Required checks enforceable as CI/acceptance gates.

### Q39 — A

**Binding requirement:** Windows Docker persistent installation, shortcuts, health checks and backups to project folder.

**Acceptance evidence:** Windows installation smoke test and local-only port binding.

### Q40 — A

**Binding requirement:** Incrementally merge independently validated work packages, releasing only with acceptance reports.

**Acceptance evidence:** No package is marked accepted before recorded tests.

### Q41 — A

**Binding requirement:** Apply Genealogical Proof Standard, source/information/evidence classifications and cited conflict resolution.

**Acceptance evidence:** Assessment distinguishes direct, indirect, negative and derivative evidence.

### Q42 — A

**Binding requirement:** Historically contextual consistency rules with impossible vs atypical and adoption/remarriage exceptions.

**Acceptance evidence:** Fixtures exercise known false positives and unusual legitimate families.

### Q43 — A

**Binding requirement:** Independently reviewed English genealogy gold-standard benchmarks, varied periods and hard negatives.

**Acceptance evidence:** Report precision, recall, false merges, missed links, relationship accuracy.

### Q44 — A

**Binding requirement:** Calibrate probabilities with held-out cases by time period, record class and surname; show uncertainty.

**Acceptance evidence:** Reliability diagrams/Brier score/coverage and abstention metrics.

### Q45 — A

**Binding requirement:** Log accepted/rejected examples with reasons; controlled retraining/evaluation/versioning/rollback.

**Acceptance evidence:** No model promotion unless independent holdout and regression gates pass.

### Q46 — A

**Binding requirement:** Continuously usable releases; foundation then records, AI matching, reconstruction and autonomous research.

**Acceptance evidence:** Each release starts and retains previous core functions.

### Q47 — A

**Binding requirement:** Integrate only via documented, versioned Gramps REST API; separate research DB; approved adapter writes.

**Acceptance evidence:** Contract tests prove no direct Gramps database writes.

### Q48 — A

**Binding requirement:** First Windows release: persistent Gramps, login, imports, research interface, health, backup/restore and shortcuts; live checkout/data outside OneDrive.

**Acceptance evidence:** Complete locally performed install and cold backup/restore drill required.

### Q49 — A

**Binding requirement:** Require traceability, automated regression, integrity/probability/security validation, rollback and acceptance report.

**Acceptance evidence:** Package gate rejects absent evidence or failed checks.

### Q50 — A

**Binding requirement:** Master Specification Rev A; 50-decision register; versioned schemas/APIs; modular prompts; traceability; PRs and history.

**Acceptance evidence:** Generated source docs and verification report cross-reference Q1-Q50.
