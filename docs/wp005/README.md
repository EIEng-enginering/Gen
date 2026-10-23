# WP-005 Revision C — Versioned genealogical hypothesis graphs

**Status: locally tested development candidate, NOT release acceptance.**

## Purpose and data boundaries

The authoritative accepted genealogy tree remains in Gramps. WP-005 adds provisional **versioned alternative branches** to the separate research DB. The app does not contact the Gramps write API, make AI-initiated merges, assign Bayesian probabilities, or run autonomous external searches. Distinct appearances in historical records are not automatically asserted to be the same individual.

Each original `HypothesisSet` continues to require exactly one `other/unknown` option. The graph service associates each named option with a sequence of append-only `BranchRevision` snapshots containing explicitly proposed edges. A revision retains the evidence observations and researcher reasoning behind each edge. Research decisions are recorded in an append-only `BranchReview` ledger, independent of Gramps.

## New relational entities

- `hypothesis_branch_revisions`: one ordered snapshot per option; rationale, reviewer identity and creation timestamp; unique `(option_id, revision_number)`.
- `hypothesis_branch_edges`: one relation per snapshot; parent, sibling, spouse, same-person or household association; supporting and contradicting observation IDs; unique `(revision_id, edge_key)`.
- `hypothesis_branch_reviews`: append-only `research_supported`, `rejected`, or `deferred` judgement with reason and reviewer.

`HypothesisSet.version` is claimed by an atomic conditional SQL UPDATE for every branch revision/review. Stale writers receive HTTP 409. The original historical source/observation tables are not modified by revision 002.

## Available local endpoints

- `GET /api/v1/research/hypotheses/{id}/graph`: all options, latest graph revision per option, structural comparison, warnings, unknown branch and current set version.
- `POST /api/v1/research/hypotheses/{id}/options/{key}/revisions`: create one new frozen candidate graph. Must include `expected_set_version`, a reason and edges; unknown option must have no edges. Every cited observation must be registered locally.
- `GET /api/v1/research/hypotheses/{id}/options/{key}/revisions`: bounded complete revision history.
- `POST /api/v1/research/hypotheses/{id}/options/{key}/reviews`: append a research-only judgement; requires version match and reason.
- `GET /api/v1/research/hypotheses/{id}/options/{key}/reviews`: full bounded review history.

As in the earlier provisional research API, mutating calls require HTTP Basic credentials and `X-24Gen-Intent: research` from the loopback deployment.

### Example of a *synthetic* edge submission

After registering two synthetic observations and creating a hypothesis with `mother_a` and `other_unknown` options, submit:

```json
{
  "expected_set_version": 1,
  "rationale": "Test hypothesis, subject to original-document review",
  "edges": [
    {
      "edge_key": "relation-1",
      "from_observation_id": "<synthetic-registered-parent-observation-uuid>",
      "to_observation_id": "<synthetic-registered-child-observation-uuid>",
      "relationship_type": "biological_parent",
      "supporting_observation_ids": ["<synthetic-registered-source-observation-uuid>"],
      "contradicting_observation_ids": [],
      "reasoning": "Researcher reviewed the original register, subject to corroboration"
    }
  ]
}
```

Do not submit the placeholder strings literally. `GET .../graph` returns the incremented `version`, and all percentages remain `null`/unscored until separately certified calibrations exist.

## Safety/validation details

- Reject parent-chain cycles, duplicate or self-referential edges, absent observations, missing/duplicate identifiers and unverified client-authored probability fields.
- Flag source-origin double-counting, source cited both for and against the same relationship, unsupported links, census-only parentage assumptions, birth chronology conflict and unusual parent ages. These are warnings, **not** automatic evidence of a mistaken genealogy.
- Multiple appearances with the same original register/page are treated as one declared source group, not independent corroboration.
- Structural comparison reports common and distinctive asserted edges; it must not be represented as a posterior distribution over branches.
- The unknown option is kept even if a candidate is marked `research_supported`; a separate human-reviewed write adapter is required in a future package to mutate Gramps.

## Migration / rollback contract

1. Review the current Git baseline, stop research writers and make an independently verified backup of the research DB and Gramps media. Do not copy raw records or credentials into source control/OneDrive.
2. Test the migration against a disposable copy before touching records of interest.
3. On the intended machine with the research service available, execute the Alembic upgrade **manually**:

   ```powershell
   docker compose --env-file .env -f deploy/compose.yaml exec research_web alembic -c alembic.ini upgrade head
   ```

   Run this only after confirming the container working directory and Python path. The service boot gate intentionally refuses to upgrade a populated old schema automatically.
4. Inspect `alembic_version` and verify historical sources and observations survived unchanged. Run the workspace and request/auth tests.
5. Roll back code by Git revert if needed; DO NOT revert the database by deleting volumes. Revision 002 intentionally refuses a destructive downgrade if any branch history exists. Use a verified backup/restore in a **separate environment** if a full rollback is required.

## Validation executed in the ChatGPT container

- 40 Python unit/integration tests pass (31 existing + 9 new).
- Incremental SQLite upgrade 001 -> 002 preserves existing evidence and prevents destructive branch downgrade.
- Client API tests include stale-version collisions, chronology and source-origin warnings, unknown alternative, mutation guard and no Gramps writes.
- OpenAPI schema creation and browser JavaScript syntax check pass.
- Held-out CSV audit CLI refuses family/source leakage and refuses to convert ranking scores to probabilities.

**Still blocked:** Windows Docker/WSL2 and PostgreSQL live deployment; real Gramps owner/REST compatibility, cold backup plus isolated media restore; external matching gold-standard accuracy and calibrated probabilities; image lock/licence acceptance. Existing draft PRs #2 -> #3 -> #1 still need review/merge in dependency order.

## Packaging note

All test identifiers and sample records in this package are fictitious. No private family-history records, source images, tokens or `.env` files are included.
