# WP-006: controlled Gramps change plans (Revision A)

**Status:** development candidate, NO accepted-tree writes; R0.1 remains NOT ACCEPTED.

## Rationale and boundary

The accepted Gramps genealogy database is authoritative. WP-006 builds a local, non-executing workflow from one reviewed, versioned research hypothesis to a verifiable proposed change plan. It does **not** merge people, create families, issue mutations to the Gramps API, claim that any supplied Gramps handle exists, or calculate family probabilities. Neither research assistants nor autonomous jobs can write to Gramps.

## Capabilities programmed

- Authenticated preview from the current version of one selected hypothesis option and its exact branch revision.
- Require explicit mapping of **every** proposed edge to two Gramps person handles. Supported relationship proposals: biological/adoptive/step parent and spouse. Reject same-person and household relationship writes.
- Require source observations for every edge and carry contradictory evidence forward as warnings. Reuse an observation with conflicting person handles or collapse distinct observations into one handle -> reject.
- Deterministic SHA-256 digest of the ordered proposal, original observations, evidence, version, and claimed handles. Unknown/unidentified option is deliberately not exportable.
- Only a current `research_supported` human review enables recording a proposal; merely previewing needs no such decision.
- Idempotency key prevents duplicate plans; conflicting reuse is rejected; optimistic set-version checks prevent stale edits and approvals.
- Explicit human decision with an exact digest confirmation phrase. Both approval and rejection are audit-logged and append-only. **Approval permits future validation only, NOT execution.**
- Browser 'Gramps review (dry-run)' tab alongside the existing research workspace.
- Separate Alembic migration `20261023_003` and a downgrade guard to preserve populated review history.

## API endpoints

All endpoints need HTTP Basic configured for the local installation. POST endpoints require `X-24Gen-Intent: research`, and browser cross-origin mutations are denied by the existing guard.

| Method | Path | Side effect |
|---|---|---|
| GET | `/api/v1/research/gramps/compatibility` | Read-only metadata probe if token configured |
| POST | `/api/v1/research/gramps/plans/preview` | None |
| POST | `/api/v1/research/gramps/plans` | Writes *only* immutable research plan and audit record |
| GET | `/api/v1/research/gramps/plans/{plan_id}` | None |
| POST | `/api/v1/research/gramps/plans/{plan_id}/decisions` | Writes *only* human decision and audit record |

### Illustrative preview request

The UUIDs and handles below are placeholders and MUST NOT be applied as real genealogy identities.

```json
{
  "hypothesis_set_id": "00000000-0000-0000-0000-000000000001",
  "option_key": "candidate_parent",
  "expected_set_version": 3,
  "expected_revision_id": "00000000-0000-0000-0000-000000000002",
  "bindings": [{"edge_key": "parent-1", "from_handle": "CLAIMED_PARENT_HANDLE", "to_handle": "CLAIMED_CHILD_HANDLE"}]
}
```

Preview returns `digest_sha256`, exact actions, `upstream_validation: NOT_PERFORMED`, `accepted_tree_write: false`. A `POST /plans` adds `idempotency_key`, `operator_note` and `expected_preview_digest` to this request. It requires the specific branch's latest research review to be `research_supported`.

An approval is a `POST /plans/{id}/decisions` with `expected_set_version` from `set_version_after_creation`, the full digest, a rationale, and the exact phrase `APPROVE PLAN <digest first 12 hex chars>`. Rejection requires `REJECT PLAN <digest first 12 hex chars>`.

## Subsequent work required before actual Gramps writes

1. Test an authenticated read-only Gramps API on disposable Docker services. Capture actual endpoint schemas, Gramps person/family handles, change tokens and duplicate-family semantics. The current integration only probes `/api/metadata/` and cannot verify identities.
2. Implement a **separate**, explicitly disabled-by-default execution adapter. Re-read all upstream objects and their revisions immediately before changes; require complete Gramps + media backups and isolated recovery evidence.
3. Detect existing parent/child and spousal families in the accepted tree; never auto-merge people or overwrite records. Enforce an operator-approved action list and one-time execution ID against retries.
4. Verify transactional/compensating rollback behavior through disposable failure-injection tests. Gramps API semantics must be measured, not assumed.
5. Add end-to-end Windows Docker, PostgreSQL migration and authentic family import/backup/restore checks before R0.1 or Gramps-write acceptance.

## Cautions

- Historical observations may refer to the same individual; this early contract intentionally rejects mapping different observation IDs onto one accepted-tree handle because there is not yet an independently approved identity-resolution table. Later revisions may add a separate verified mapping phase.
- Review does not equal genealogical proof, and a valid graph is not a calibrated probability.
- Do not commit credentials, real living-person details, genealogy media or backups.
