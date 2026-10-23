# Detailed Database, Identity and Provenance Contract — Rev A

**Status:** intended contract for WP-002 migrations and technical validation. Not yet deployed. Each entity uses stable UUID; all user/AI derived content has creator, created_at, updated_at or append-only transaction fields. Use UTC for machine timestamps; historical dates must preserve their calendar and uncertain ranges.

## 1. Source provenance and historical assertions

Every imported source `SourceDocument` SHALL carry a repository/provider key, upstream immutable ID if available, original citation/reference, URL, asset rights, licence record, access mechanism (human/import/approved API), ingest timestamp, acquisition operator, capture checksum when bytes legitimately stored, original historical date string and structured interval. It SHALL be possible to reproduce its citation without a connection to the provider when allowed, or to link to the provider otherwise. The system does not store prohibited remote images. A `SourceDocument` is distinct from a `SourceObservation`: an image or census page can create multiple extracted observations, several independent name mentions and multiple relationship claims.

Store the exact OCR version, human-corrected transcription, crop/line coordinates and extraction model ID. Corrections are append-only: transcribed text V2 references V1, with editor/time/reason and an immutable original. Two transcriptions of the same GRO or census entry may be cross-provider duplicates. To avoid double-counting, the `evidence_origin_group` groups records derived from a common original, while preserving provider and transcription metadata. The correlation engine receives one independent evidentiary origin plus extraction uncertainty, not two independent votes.

Source classification axes are distinct: original/derivative/compiled document; primary/secondary/undetermined informant knowledge; direct/indirect/negative evidence relative to a question. They must not be collapsed into one generic reliability scalar. Evidence weighting is learned/justified, never based solely on an archive's prestige.

## 2. Date, place and name design

`HistoricalDate` representation: raw string, calendar, precision qualifier (exact/about/before/after/between/unknown), earliest_possible, latest_possible, enumeration/registration date separate from actual event date, parsing model/version, extraction confidence, literal provenance. Date arithmetic applies intervals not false precision; preserve baptisms distinct from births and burials distinct from deaths.

`HistoricalPlace` representation: literal original, historical gazetteer reference, jurisdiction name/type, alternate spelling, validity years, precision (address/parish/district/county/country), optional geometry with confidence, administrative membership by date and disputed/unknown boundaries. Do not map 1730 parish membership using only modern boundaries. Migration model accounts for roads, water crossings, employment and family movements rather than straight-line distance alone.

`HistoricalName`: verbatim given and surname, relationship to person, surname usage type (birth/married/alias/unknown), expanded abbreviation, variant derivation, script/transcription uncertainty and model output. Keep nonconformist, Welsh patronymic and other naming patterns extensible; do not assume a woman automatically changed surname.

## 3. Graph and identity model

A `PersonMention` is an appearance in a document, not necessarily a person; an `IdentityCluster` groups mentions hypothesised to represent one individual. Cluster members retain original mention IDs and independent source groups. An accepted Gramps person links by a versioned `ExternalObjectReference` to one or more confirmed mentions without absorbing unconfirmed clusters. Two hypotheses can reuse a mention differently but explicit mutual exclusion is stored in a `HypothesisChoiceSet`.

Relationship edges include: biological_parent, adoptive_parent, step_parent, marital_partner, household_member, witness, employer, apprenticeship, neighbour and other. For legal/biological distinctions, a person may have different legally social vs biological parents. Specify role and effective period; a spouse candidate and a father candidate are not interchangeable. Check cycles in biological ancestry (impossible) but do not ban all graph cycles in social relationships. A household membership cannot prove biological parentage. Couples and children form a family structure but a household can include lodgers, servants and visitors.

One research hypothesis is a graph snapshot plus evidence set, unknown assignments, candidate alternatives, model version and evaluation timestamp. Store competing graphs as immutable revisions with explicit choice-set exclusivity; preserve previously rejected alternatives and rejection reasons. Approval transfers an explicitly selected change to Gramps only after API precondition checks, not by changing identity cluster flags alone.

## 4. Probabilistic computing contracts

Pairwise linkage baseline: deterministic normalization -> blocking -> comparator features -> model likelihoods -> prior -> posterior -> calibration -> explanation. Name frequency and source completeness condition each prior. Comparators include names, baptism vs birth ranges, death constraints, parish and district, occupation, address, relatives, witness networks, record quality and duplicate origin. Missingness is not necessarily independent or neutral. Train/test split by families and underlying source networks, not randomly by record pairs.

Example of dependence: John Brown's father is named in the baptism image. FreeREG and FamilySearch may both repeat its transcription; they are not two independent testimonies. A family hypothesis combines the original record once, then accounts for alternate reading errors and the child's later appearance. If a family branch is evaluated using the same census evidence for several siblings, the posterior must not multiply that source's weight independently for each edge.

Graph-level inference includes latent person identity variables and relationship variables, factor constraints for dates and biology, alternative genealogies and an explicit unknown/noncandidate state. Workflows may return *unscored* if model calibration data is absent. Computation shall expose algorithm choice, random seed for approximate inference, convergence diagnostics, sensitivity to priors and evidence removal. For mutually exclusive exhaustive hypotheses, normalized probabilities sum to 1 within numeric tolerance; for incomplete sets add a genuine `other_unknown` state, never force certainty into the named alternatives.

Validation calculates: precision, recall, false-merge rate, false-split rate, relationship accuracy, expected calibration error, reliability bins, Brier score, log loss, abstention coverage, time-slice and county/surname-specific drift. Compare to a deterministic/no-AI baseline to establish incremental benefit. Probabilities must be labelled with model applicability and data-collection bias caveats. Do not call a calibrated identity posterior an established genealogical parentage percentage.

## 5. Gramps approval adapter, precise write protocol

Inputs: authenticated local reviewer identity, object handle + tree key, expected Gramps API version/revision snapshot, immutable proposed edit payload, linked observation IDs, hypothesis run ID, conflict warnings and independent backup reference. Refuse to operate if Gramps API unavailable, reviewer not recorded, source IDs missing, expected version stale, an impossible ancestry cycle exists or a protected person constraint is breached.

Transaction process: prepare proposal -> refetch current Gramps objects -> compute dry-run JSON diff -> request explicit approval -> send minimal REST update(s) -> fetch and verify -> write immutable audit event + API transaction ref. Multi-object write is not assumed atomic unless upstream explicitly guarantees it; on partial mutation flag manual reconciliation, do not retry duplicate writes. Any rollback uses Gramps supported transaction history/undo where safe, preceded by further current-state verification. Gramps API user token is server-held and redacted from logs. Never directly edit SQLite/Gramps internal tables.

## 6. PostgreSQL lifecycle and partitions

Alembic migration naming: `YYYYMMDD_NNN_slug`, down revisions where safe and irreversible migrations separately flagged; backups before destructive work; code supports one controlled backward-compatible rolling version. B-tree indexes on external references, job states, archival identifiers and graph IDs; trigram/GiST or appropriate indexing for surname/place search; controlled partitions for very large source mention tables. Use managed background workers for imports; large ingestion is chunked and idempotent with per-chunk error reports. Do not add massive national data without proven legal access, measured indexing and failed-job recovery.

## 7. Operational test cases that must survive a release

- Same John Smith named in two parishes; no accidental merge due solely to name and approximate age.
- Two websites transcribe the same original and produce conflicting spellings; independence correction avoids duplicated certainty.
- A child's parish baptism apparently contradicts later census birthplace; preserve both and propose reconciliation.
- 1841 age 42 is not interpreted as exact; household residents are not automatically father/son.
- Two plausible fathers, one unidentified; user sees the unknown hypothesis and can defer.
- Step/adoptive/biological parents are kept distinct.
- Repeated GEDCOM import does not double the accepted tree.
- LLM hallucinated citation ID is rejected.
- Changed upstream Gramps object triggers optimistic-concurrency failure, not silent overwrite.
- Interrupted import resumes idempotently without double charging or duplicated records.
