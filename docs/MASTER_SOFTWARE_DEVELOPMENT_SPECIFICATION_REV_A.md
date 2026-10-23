# 24 Gen — Master Software Development Specification

**Revision:** A (approved requirements baseline)  
**Date:** 23 October 2026  
**Project:** AI Genealogy Research and Probabilistic Family Reconstruction  
**Repository:** https://github.com/EIEng-enginering/Gen.git  
**Project deliverable directory (Windows):** `C:\Users\Admin\OneDrive - Enhance Integration Engineering\Company\006 Calculation Methods\24 Gen`  
**Preferred active source checkout:** `C:\24Gen\Gen` (adjust after checking disk and permissions)  
**Runtime:** Docker-managed volumes outside OneDrive.  
**Status:** All 50 product decisions approved; software releases and services not yet acceptance-tested.

## 1. Executive specification and baseline

24 Gen shall be a local-first genealogy research and evidence-assessment system, initially designed for England and Wales. It shall preserve accepted family-history records in Gramps Web and store independent source observations, possible identities, alternative relationships, hypothesis graphs and model outcomes in a custom research system. The website shall support conventional search, AI-guided searches and bounded autonomous research. Competing explanations must remain visible, even when one explanation leads. Original sources and confidence calculations must remain traceable. Future internet hosting and worldwide extension must not require changing the core data meaning.

### 1.1 Decision authority and hierarchy

Binding product decisions are in `APPROVED_DECISIONS_Q01_Q50.md` and the machine-readable JSON register. Q12 combines A+B, Q14 is B, and Q19 combines A+B+C. Stage Nine Q41–Q45 and Stage Ten Q46–Q50 are approved option A. In conflicts, explicit approvals supersede inferred choices; legal requirements and data integrity gates supersede convenience; any proposed reinterpretation requires a documented change request.

### 1.2 Scope and non-goals

Included eventually: English/Welsh BMD, parish and census records; import and export; historical geography; document images, text recognition, confidence-aware record linkage; Bayesian relationship hypotheses; interactive family trees and evidence review; job monitoring, AI assistant and external connectors; audit and recovery.

Not included in initial release: unrestricted scraping of third-party genealogy sites, purchasing restricted datasets without permission, nationwide population reconstruction, public cloud hosting, automatic accepted-tree merges, an unsupervised inference system that reports arbitrary percentages, DNA interpretation, or a production mobile app. These can be proposed later through revised requirements.

### 1.3 Release outcomes

- R0.1: persistent Gramps Web and a basic locally password-protected research workspace; validated installation, import, health, backup and restore.
- R0.2: separate evidence database, source/provenance catalogue, permitted uploads, rights rules and duplicate management.
- R0.3: auditable record linkage (statistical and AI), historical constraints, candidate review.
- R0.4: alternative family graphs, dependent probabilities, review queue, graphical comparison.
- R0.5: all three research modes, approved connectors, handwriting recognition, costs and resumable jobs.
- R1.0: integrated, documented and independently benchmarked system with regression, calibration and recovery evidence.

The provided WP-001 is a **foundation candidate**: a runnable scaffold requiring live Windows Docker testing. It is not certified as R0.1.

## 2. Engineering principles and constraints

1. Non-destructive data handling: observation is not interpretation; uncertainty is not a committed genealogical fact.
2. User-approval boundary: external data and AI cannot create accepted Gramps relationships without a reviewed, logged action.
3. Evidence provenance: record locator, archive, reference, access mechanism, licence, capture date, original bytes/hash or URL, derivatives and transformations are retained.
4. Source independence: duplicate transcriptions derived from one original do not increase evidential weight independently.
5. Human-readable reasoning: every identity/relationship suggestion explains supporting and contradicting facts.
6. No numerical false precision: percentages require identifiable models, calibration evidence and applicability checks. Otherwise display qualitative status or "not calibrated".
7. Rights respecting ingestion: no website scraping contrary to provider rules, automation blocked unless authorised.
8. Local first: published ports bound to 127.0.0.1; cloud AI disabled by default and opt-in per action/source.
9. Recoverability: backups include genealogy data, custom research data and original images; verify restore on isolated destination.
10. Maintainability: modular services, versioned contracts, small additive changes, no unreviewed modification of Gramps internals.

## 3. Logical architecture and responsibility map

| Subsystem | Owns | External boundary |
| --- | --- | --- |
| Gramps Web | Accepted people, families, events, citations, tree editing, GEDCOM/Gramps import/export | Documented authenticated REST API only |
| 24 Gen Research API | Research users/configuration, ingestion metadata, research workflow, candidate and hypothesis reads/writes | REST `/api/v1/*`, migrations |
| Evidence Store | Raw source metadata, images, immutable observations, transcriptions/corrections, licence constraints | Content-addressed media and relational tables |
| Identity Resolution | Candidate blocking, feature extraction, probabilistic linkage and LLM reviewer outputs | Job and result contracts |
| Family Graph | Alternative parent/spouse/household structures, correlations, unknown state, inference provenance | Hypothesis API, versioned model |
| Research Planner | Research mode, provider gates, priority scheduling, limits, hints, progress | Queue and provider adapters |
| Approval Adapter | Two-phase preview/validate/review then approved Gramps mutation | Documented Gramps REST API only |
| Browser UI | Person selection, accepted/provisional visuals, viewer, conversations, approvals, jobs | 24 Gen API + Gramps Web links/allowed API |
| Operations | Windows launcher, Docker Compose, secrets, backups, CI and release locks | Persistent volumes and release manifests |

### 3.1 Hosting topology and ports

Windows 10/11 with Docker Desktop + WSL2 Linux containers. Gramps Web hosted at `127.0.0.1:5055`; 24 Gen Research at `127.0.0.1:8765`; both may be overridden with conflict checks. Redis-compatible broker for Gramps Celery remains on the private Compose network. Separate PostgreSQL is used by the custom research engine. Do not expose PostgreSQL, Valkey or internal worker ports. On first run Gramps creates its own owner account, separate from the initial 24 Gen research login. Revisit unified authentication after the first working release.

### 3.2 Data ownership, cross-system IDs and transactions

Gramps handle references are stored in an `external_object_reference` mapping alongside tree ID, type, Gramps version and last synchronised revision. Research IDs are stable UUIDs. Never assume handles are globally unique across different trees. Accepted relationship approval must use a staged operation: (1) re-fetch current Gramps object; (2) compare expected version/hash; (3) validate duplicate/person/relationship constraints; (4) backup/snapshot state; (5) send authorised REST operation; (6) fetch and verify result; (7) record transaction/compensating action in approval log. On API failure, mark uncertain and retain pending work; do not replay mutating requests blindly.

### 3.3 APIs and auth

24 Gen uses versioned routes and OpenAPI definitions. Authentication initially by local account/password, TLS unnecessary only while strict loopback binding remains in force. Never transmit local Basic credentials outside loopback; future internet access requires HTTPS, sessions, CSRF safeguards, modern identity/auth design and living-person privacy review. Gramps remains separately authenticated until a documented safe integration is verified. AI tools use least-privilege read actions and a separate user-confirmed mutation service. API calls to Gramps use server-held credentials, never embedded in JavaScript.

## 4. Physical research data model — proposed Rev A contract

At WP-002 implement PostgreSQL via Alembic migrations. Illustrative table-level contracts below; migration naming and SQL types are normative once the WP-002 contract is frozen. Dates support ranges and approximate uncertainty, not fabricated point dates.

| Table | Required fields / rules |
| --- | --- |
| `source_repository` | id UUID, name, country, base_uri, access_class, licence_version, attribution, permitted_uses, policy_reviewed_at |
| `source_document` | id, source_repository_id, external_id, archive_reference, canonical_url, record_class, event_period, place_ref, access_licence, rights_status, acquired_at, content_sha256 nullable, parent_source_id nullable |
| `document_asset` | id, source_document_id, kind (original, thumbnail, OCR output), SHA-256, mime_type, restricted flag, storage key, capture timestamp; never alter original |
| `transcription_run` | id, document_id, model name/version, input_hash, run_time, text, confidence metadata, human_corrected_version_id nullable |
| `source_observation` | id, document_id, event_claim_type, literal_name, literal_date, literal_place, literal_relation, linked person mention, extraction span, uncertainty, original text; append-only |
| `person_mention` | id, document_id, observation_id, literal name, given/surname components, sex-as-reported nullable, occupation, birth/date intervals, role-in-record |
| `place_historical` | id, spelling, jurisdiction type, parent, valid_from/to, geometry source, boundary_version, alternate names |
| `identity_cluster` | id, candidate mention set, status (proposed/reviewed/accepted/rejected), model/run provenance; not automatically Gramps person |
| `pairwise_match` | id, mentions A/B, features, statistical posterior, language-model report ref, calibration version, model applicability, explanation, decision, independent source groups |
| `family_hypothesis` | id, root research person, graph snapshot/version, status, prior/posterior nullable, unknown mass, evaluation_run, created_by, comparison group |
| `relationship_hypothesis` | id, hypothesis_id, endpoint identity IDs, relation type, chronological rules, posterior nullable, evidence link set, contradiction link set |
| `evidence_assessment` | id, hypothesis/claim, evidence set with same-origin grouping, independence model, source quality, conflict narrative, GPS checklist |
| `research_job` | id, mode, person target, query plan, provider, state, priority, idempotency_key, created/started/finished, error, progress, cost estimate/spend |
| `provider_access_policy` | provider, mechanism, automated_allowed, rate/volume terms, content retention, PII constraints, licence reference, expiry, operator approval |
| `approval_request` | id, proposed change payload, expected Gramps revision, reason, evidence digest, requester, reviewer, reviewed_at, decision, Gramps transaction ID |
| `model_run` | id, code/model digest, dataset snapshot, calibration curve reference, configuration, data lineage, runtime, quality report |
| `audit_event` | id, actor, action, target type/id, old/new hash, timestamp, causal job, irreversible flag; append-only |
| `external_object_reference` | research UUID, tree identifier, Gramps type, Gramps handle, API version, last observed revision/hash |

### 4.1 Key invariants

- Unique `(source_repository_id, external_id)` where upstream identifiers are stable; otherwise compound fingerprints with collision manual review.
- Source duplicates may point to the same original, but transcriptions remain separable; never hard-delete conflicting representations.
- Identity clusters and family hypotheses never imply automatic source truth or Gramps mutations.
- Immutable asset hashes and append-only observations; correction is a new derivative linked to old version.
- Every probability reports model, date, dataset applicability, evidence grouping and whether calibrated.
- Alternative parent candidates must include an unknown/unidentified possibility when exhaustive search cannot be established.
- All relationships have role semantics (biological, adoptive, step, marital, household, witness, neighbour) with distinguishable representations.
- Every job stores provider authority, permitted method, idempotency and budget information.

### 4.2 Genealogy exchange and source inheritance

GEDCOM 7 is the interchange target where supported; ingest GEDCOM 5.5.1 and Gramps XML after format detection. Imports are staged in quarantine; preview duplicate candidates, unsupported tags, lost multimedia and citation mappings before commit. Preserve the uploaded original and import manifest. Retain one-to-many crosswalk from external IDs to research IDs; any reimport uses fingerprint checks. Never interpret loss of family link on a GEDCOM export as evidence against its existence in the source tree.

## 5. Historical English research engine

### 5.1 Record priority and period-specific treatment

1. Civil registration from 1837: index references distinguish birth/marriage/death registration from underlying event and certificate evidence. Preserve quarterly indexes and registration districts.
2. Census: 1841 household relationships cannot simply be inferred from co-residence; adult ages typically rounded down to five years. 1851+ includes relationships and age/birthplace with known reporting inaccuracies. 1939 Register is not a normal decennial census.
3. Parish baptisms/marriages/burials: examine mother/father, witnesses, residence, cleric, parish location, banns and nonconformity where source permits.
4. Future additions: probate, newspapers, military, electoral, tax, directories, apprenticeship, land, institutions and other historical resources, subject to licences.

### 5.2 Geography and naming

Historical place matching requires gazetteer crosswalk, validity periods for parish/county/registration district, uncertain boundaries, migration edges and distance/time-based travel checks. Name features preserve literal spellings and include surnames at birth and marriage, aliases, transcription substitutions, diminutives, phonetic similarity and frequency-aware common-name penalties. Never normalise away the original transcript.

### 5.3 Household and family networks

Follow each individual across enumeration years using household composition and changing occupancy. Household co-location alone cannot establish biological relationship; represent inferred household edges separately. Grouped matching considers siblings, neighbours, witnesses, occupations, addresses, known departures and deaths; evaluate improbable cross-record chains using graph consistency. Resolve one ambiguous common-name match using family-level evidence instead of rigid exact-name equality.

## 6. Entity resolution, AI reasoning and genealogical probability

### 6.1 Separate tasks; different outputs

- `record_mentions_same_person` evaluates a pair (or cluster) of references to identity. Statistical linkage engine produces scored comparisons and assumptions.
- `relationship_is_correct` evaluates specified child/parent/spouse/household edge and dependent family network. Its probability need not equal the pairwise identity score.
- `hypothesis_graph_is_correct` compares mutually exclusive candidate genealogies, with unmodelled/unknown mass. This is neither product of pairwise scores nor direct language-model "confidence".

### 6.2 Statistical linkage implementation

Candidate blocking by temporal, geographic, surname, household and source feature filters; fail-open broader search for hard cases to avoid recall collapse. Employ Splink/Fellegi-Sunter style conditional feature weights as a baseline. Train/calibrate on non-overlapping adjudicated cases, document missingness mechanisms and record-dependent error structure. Use explicit controls for high-frequency surnames, duplicated entries and aliases. Expose comparison factors and retain run reproducibility.

### 6.3 LLM contribution (Q12 A+B)

AI can propose candidate search terms, read extracted text, interpret historically plausible exceptions, identify contradictions, and write cited explanations. It may return structured `claims`, `supporting_observation_ids`, `conflicting_observation_ids`, `historical_rule_ids`, `alternatives`, `unknowns`, and `uncertainties`. Reject any claim citing a nonexistent ID. LLM output is untrusted until schema-validated and grounded in stored evidence; it cannot fabricate provenance or directly set final posterior. Prompt injection from webpages and transcriptions must be treated as data, not instructions. Unverified AI summaries are marked as suggestions.

### 6.4 Connected probability model (Q22)

Represent identity, parentage, marriage, time/location and shared-record-origin as connected factors. Avoid treating multiple transcriptions of one original as independent. Evaluate alternate graphs via exact inference for small connected components, approximate sampling/message passing where justified for larger graphs. Include priors reflecting record availability, name frequency and place/period. Calibrated posteriors across mutually exclusive candidate sets must sum to 1 only if the hypothesis set is exhaustive, otherwise retain an explicit other/unknown category. Posterior displayed only when calibration applicability is supported. Explanations show priors, relevant evidence, dependence corrections, alternative sensitivity and major contradictions.

### 6.5 Mathematical evaluation and guardrails

Required benchmark statistics: pairwise precision/recall/F1, cluster B-cubed or equivalent, false merge rate, false split rate, relationship precision/recall, abstention/coverage, Brier score, log loss, calibration error and subgroup drift by source/century/surname prevalence. Treat false merges as particularly costly (do not mandate an arbitrary numeric threshold before benchmarks). Separate training, calibration and holdout by family/source network to prevent leakage. Use bootstrap uncertainty where appropriate. Verify human-labelled truth provenance and disagreement resolution.

### 6.6 Research expansion and active information gathering

Generate bounded tasks across ancestors, siblings, children, spouses and neighbours. Each search plan must explain expected information gain, source availability, permission, cost, expected time and current priority. Maintain budget caps, depth caps, time caps, provider throttle, failed-query cache and revisitation triggers after new evidence. Autonomous mode can produce proposals but cannot perform paid purchases or accepted-tree mutations without a corresponding explicit approval.

## 7. Provider connectivity, rights and handwriting

Each connector registers a policy describing authentication, base URL, allowed actions, manual-only status, robots/terms, rights, caching retention, rate limits, paid use and audit. `manual_only` prohibits automated server-side searches, even if technically possible. A source provider can be searchable by the user with outbound link and document import without being machine-queryable. Planned first sources: GRO, FreeBMD, FreeREG, FreeCEN, FamilySearch (only approved API functions), National Archives Discovery, and imported PDF/JPG/PNG/TIFF/CSV/GEDCOM. Paid sources require permissions, and family-history licence constraints must be documented before metadata/media are retained.

HWR/OCR workflow: capture image, quality check, segmentation, run Kraken or equivalent local model, optional cloud specialist only after explicit consent, field extraction with confidence intervals, human side-by-side correction, immutable original and derivative versioning. OCR may be poor on difficult handwriting; never silently equate transcription with original record. Never send images of living people to cloud without permission.

## 8. User experience and accessible visualisation

### 8.1 Screen map

- Home: focused person and current tree, recently reviewed evidence, research suggestions, cost summary.
- People/Tree: ancestor, descendant, hourglass, relationship and fan charts; pan/zoom; timeline; person search; confidence overlays.
- Hypotheses: accepted versus candidate tree; multiple complete branch comparison with unknown; visually distinguishable line types in addition to colour.
- Records: source catalogue, filter by original archive, dates, places, rights, keywords, status and duplication family.
- Document Review: zoomable image, transcription, original literal text, edit history, field mappings, side-by-side person facts.
- Research: three modes; bounded search authorisation; search log and suggestion queue.
- AI Chat: explain cited candidates, plan authorised searches, propose structured actions; show whether AI cloud is enabled.
- Jobs/Costs: progress, cancellation/pause/resume, API quota, costs, blocked sources, pending approvals and error reports.
- Administration: local account/password, secret and model configuration, data backups, audit logs, import and recovery.

### 8.2 UX invariants

Accepted tree remains visually distinct from hypotheses. Probability labels include date/model quality and readable basis. Never display fabricated certainty. Every source has direct navigation to its original (where permitted). No AI result can silently replace an accepted person. Keyboard focus, screen-reader labels and non-colour-only status coding are mandatory. Selected person/branch persists across views. Research dashboard status updates must come from actual job state, not simulated progress.

## 9. Operational workflows, resilience and data protection

### 9.1 Normal user workflows

A. Import existing tree -> quarantine -> duplicate preview -> mapped import -> user review -> accepted Gramps tree -> backup.
B. Select known relative -> choose research mode -> query authorised sources / suggest manual lookups -> ingest references -> produce observations and candidate identities -> independent score and AI analysis -> review candidate.
C. Open alternative father candidates -> compare records, chronology, parish locations -> request missing search -> approve selected relationship -> adapter reconciles Gramps updates and audits transaction.
D. Upload parish scan -> local HWR -> editable transcript -> corrected observations -> rerun affected hypotheses -> propose changes; originals remain unchanged.

### 9.2 Security baseline Q14 B

Use loopback-only published ports, local password for research web and Gramps owner account, no auto-publication or UPnP; secrets live in untracked `.env`, not documents or logs. Assume local machine access determines baseline trust. Because the chosen baseline is deliberately simple, internet exposure requires a separate security upgrade before deployment: HTTPS, CSRF, encryption/retention controls, multi-user permissions and living-person protections. Living-person data and passwords shall not be included in sample fixtures. Log redaction prevents raw tokens, full records and passwords in job logs.

### 9.3 Backups and restoration

Consistent backup must include Gramps users, secrets, indexes, accepted Gramps data and media plus the independent research database and document originals. Implement both an application-level Gramps XML export and a stopped-service complete volume archive; using one without media is inadequate. Research PostgreSQL uses `pg_dump` for hot logical backup or stopped-service volume snapshot. Backups may be exported to the named OneDrive directory **only after reviewing who can access it**. Encrypt sensitive archives when practical. Include SHA-256 manifest. Recovery rehearsal must restore into a new isolated stack, prove file hashes and accept a sample search/edit; never blindly overwrite the only live database during testing.

### 9.4 Revisions and schema changes

Custom DB changes use Alembic and backwards-compatibility windows; Gramps database is never hand-edited. Each work package declares minimum supported versions, migration preconditions, rollback semantics and backup obligations. Git feature branch -> tests -> review -> merge, with human approval. Pin dependencies and container image digests in release lock file; no `latest` as release-grade image. Monitor licensing implications of Gramps Web's AGPL in derivative or network-facing modifications.

## 10. API contracts (Rev A conceptual)

All custom resource APIs will use `/api/v1` with consistent error envelope `{code,message,correlation_id,details?}`, OAuth/sessions only after dedicated auth design, pagination and cursors, ETags for optimistic concurrency, UTC timestamps ISO-8601. Do not expose Gramps credentials to browser. Proposed endpoints after WP-001 scaffold:

| Method/path | Function | Change authority |
| --- | --- | --- |
| `GET /health` | Minimal liveness, no secret data | Anonymous loopback |
| `GET /api/v1/status` | Authenticated service readiness (no secrets) | User |
| `GET /api/v1/features` | Accurate implemented/deferred feature list | User |
| `GET /api/v1/people/{id}/candidates` | Candidate references with support and uncertainty | Read |
| `GET /api/v1/documents/{id}` | Evidence metadata/licence and permitted links | Read |
| `POST /api/v1/imports` | Staged, validated user-supplied file | Authenticated write |
| `POST /api/v1/research/jobs` | Bounded provider-authorised task with idempotency key | Authenticated action |
| `POST /api/v1/jobs/{id}/pause|resume|cancel` | Control actual background job | Authenticated action |
| `GET /api/v1/hypotheses/{id}/compare` | Evidence and whole-branch contrasts | Read |
| `POST /api/v1/approvals` | Create a request, NOT mutate Gramps | Authenticated action |
| `POST /api/v1/approvals/{id}/apply` | Human-approved, revision-checked Gramps API mutation | Privileged, separately tested |

WP-001 intentionally only implements the first three endpoints and a read-only starter homepage. All other endpoints remain contract designs until implemented and verified. Gramps API contract negotiation must happen against the running `/api/swagger-ui` rather than hard-coded assumptions.

## 11. Verification and acceptance gates

### 11.1 Gates for every work package

- `requirements`: mapping from changed files to Q identifiers and acceptance conditions.
- `source`: no secret/historical private data in commits; no destructive overwrite of existing repository code.
- `static`: syntax/type/style/secret-scan where available; provider data-use policy checks.
- `unit`: deterministic fixtures, expected results for happy/negative cases, non-regression.
- `integration`: API contract, dependencies, migration up/down and idempotency as appropriate.
- `system`: browser smoke, local host access, Gramps login/import flow, preservation of existing data.
- `genealogy`: false match/merge and source-provenance audits as relevant.
- `probability`: calibration/sensitivity/independence reports as relevant.
- `recoverability`: full backup, media restore and isolated restore drill for DB-changing packages.
- `release`: dependency digest, changelog, risks and signed/recorded acceptance report.

### 11.2 Minimum test fixtures

Include intentionally ambiguous common English surnames, 1841 rounded ages, 1851 household relationships, conflicting baptism father names, remarriage/step relationships, parish boundary changes, illegible handwritten document, duplicated census transcription from two websites, an imported GEDCOM duplicate and a missing/unknown parent. Each fixture must document its expected interpretation and possible legitimate alternatives. No real living person's sensitive data in public fixtures.

### 11.3 Initial R0.1 acceptance (future, not yet met)

R0.1 passes only if on the actual Windows machine: clean Docker start; Gramps owner creation; accepted GEDCOM and Gramps imports tested; login; 24 Gen research homepage; both health checks; shutdown/restart persistent data; database/media backup including manifest; isolated restore verification; Windows shortcut working; `127.0.0.1` only; Docker image versions pinned; logs inspected. Record observable evidence with command output/screenshots and hashes.

## 12. Work-package authoring and Git policy

Each package has an ID, branch name, baseline commit, manifest, dependency/compatibility list, implementation intent, allowed/forbidden files, source overlay/patch, migration notes, smoke and regression tests, installation steps, rollback steps, known gaps and exact evidence required. Coding agent must inspect target repository before changes and avoid overwriting unrelated content. Do not apply an overlay without a diff review and a fresh feature branch. Prefer commits of small logical units and PR review. If connected repository remains inaccessible (currently GitHub 404), work offline with handoff ZIP; do not claim push or PR creation.

Proposed identifiers: WP-000 repository governance/CI and WP-001 first local Gramps and research scaffold. WP-001 depends on WP-000 and does not itself satisfy R0.1 until the onsite acceptance checklist has passed. WP-002+ add DB migrations and provenance before probabilistic inference. See `DETAILED_IMPLEMENTATION_ROADMAP.md` and each work-package manifest.

## 13. Required documentation, decision change and unresolved assumptions

Change management: each modified decision gets a revision record with impact on API/data/tests and an acceptance decision; never silently reinterpret Q12, Q14 or Q19. Technical assumptions requiring verification: GitHub organisation access and target branch; actual Windows Docker privileges and available disk; precise Gramps/Valkey image digests; Gramps owner/tree name; source licence access; existing GEDCOM files; geographic pilot; cloud AI opt-in. None blocks creation of the initial implementation package, but each must be resolved before claiming live installation or the corresponding data integration.

### 13.1 Final baseline rule

The approved decision register is the product requirements contract. The architecture and contracts here are an implementation proposal created to fulfil it. Revisions to engineering detail are allowed through controlled review, but not destructive reinterpretation of the approved functional intent.
