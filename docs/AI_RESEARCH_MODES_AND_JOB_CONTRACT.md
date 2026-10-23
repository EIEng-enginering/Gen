# AI Research Modes and Background Job Contract — Rev A

Three modes are compulsory under approved Q19 A+B+C. This applies to the same evidence store and person focus; switching modes preserves drafts and work history.

## Mode A: bounded autonomous

Receives exact research subject, root person, allowed depth, permitted providers, geographic/time period scope, maximum calls, maximum AI spend and maximum execution budget. Generates a cited plan with estimated value of information for each task, executes only allowed non-chargeable actions, records attempted/no-result searches, creates hypotheses and queues significant accepted-tree modifications for human review. When permissions, coverage, money or compute run out, it stops safely and reports missing data. No infinite expansion.

## Mode B: guided

Produces suggested searches and rationale, but execution of each source search is initiated by the user. The system may rank matches and summarize user-provided records, but cannot silently start autonomous follow-up chains. Paid acquisition still needs a separate confirmation.

## Mode C: conventional

User manually searches, filters, sorts, reads and edits approved genealogy information. AI may summarise selected documents on request, but never launches provider searches by itself.

## Durable state machine

`QUEUED -> RUNNING -> {COMPLETED | FAILED | PAUSED | CANCELLED | NEEDS_REVIEW | BLOCKED_SOURCE | BUDGET_EXCEEDED}`. Retry from FAILED is a new version with linked attempts; idempotency keys deduplicate repeat inputs. PAUSED and CANCELLED states must be enforced by the worker, not only UI display. Each external action stores provider permission key and an exact reason code; no manual-only provider search becomes an API request. Transition events are immutable, timestamped and actor-attributed.

## Suggested job output contract

`{job_id, mode, scope, provider_policy_ids, status, percent_complete|null, actions_count, sources_found, unique_observation_count, proposed_identity_count, hypothesis_ids, model_runs, costs, warnings, next_actions, audit_ref}`. Progress percentage is null when total work cannot be estimated. All costs distinguish estimated, authorised, invoiced and paid, with currency. Redact API tokens and living-person details from logs. Job requests carry explicit configurable limit objects.

## LLM tool allowlist

`search_local_sources`, `query_authorised_provider`, `get_observation`, `get_candidate_hypotheses`, `compare_evidence`, `propose_research_task`, `draft_approval_request`. Tools for modifying Gramps are not directly exposed to general LLM completions. Proposals are structured, schema-checked and cited. Transcribed webpages/documents are untrusted and must never supply system instructions.
