"""WP-008 offline Gramps OpenAPI contract inspection (never sends mutations).

An API document describes route availability, not compatibility of an authenticated
running instance, backup recoverability, or write authorization. No personal data
or tokens are retained. All production write operations remain intentionally absent.
"""
from __future__ import annotations
import re

REQUIRED_READ_PATHS = {
    'metadata': '/metadata/',
    'person': '/people/{handle}',
    'family': '/families/{handle}',
}
TEMPLATE = re.compile(r'\{[^{}]+\}')


def _normalise_route(route: str) -> str:
    route = '/' + route.strip().strip('/')
    if route.startswith('/api/'):
        route = route[4:]
    route = TEMPLATE.sub('{handle}', route)
    return route.rstrip('/') or '/'


def inspect_openapi(document: dict) -> dict:
    """Return a sparse, fail-closed read-only compatibility report."""
    if not isinstance(document, dict) or not isinstance(document.get('paths'), dict):
        raise ValueError('OpenAPI document must contain a paths object')
    version = document.get('openapi') or document.get('swagger')
    if not isinstance(version, str) or not version.startswith(('2.', '3.')):
        raise ValueError('Unsupported OpenAPI or Swagger document version')
    paths = document['paths']
    if len(paths) > 6000:
        raise ValueError('Too many route definitions')
    normalised = {}
    for raw, operations in paths.items():
        if not isinstance(raw, str) or not isinstance(operations, dict):
            continue
        normalised.setdefault(_normalise_route(raw), set()).update(
            verb.lower() for verb in operations if verb.lower() in {'get','post','put','patch','delete'}
        )
    checks = {}
    for key, route in REQUIRED_READ_PATHS.items():
        target = _normalise_route(route)
        checks[key] = 'get' in normalised.get(target, set())
    # The contract must be verified against the RUNNING instance; this is merely an offline hint.
    return {
        'input_document_version': version, 'read_routes': checks,
        'read_route_shape_complete': all(checks.values()),
        'live_instance_verified': False, 'response_shapes_verified': False,
        'api_token_verified': False, 'snapshot_atomic': False,
        'accepted_tree_write_enabled': False, 'future_write_eligible': False,
        'note': 'Offline contract check only; live authenticated tests and recovery gates are still required',
    }


def plan_readiness(plan, decision, validation, *, current: bool) -> dict:
    """Show gates for a plan, without ever interpreting a GET snapshot as a write permit."""
    approved = bool(decision and decision.decision == 'approve_for_future_validation')
    has_read = bool(validation and validation.plan_digest == plan.digest_sha256)
    result = validation.result_json if has_read and isinstance(validation.result_json, dict) else {}
    stable_read = bool(result.get('status') == 'READ_ONLY_OBSERVATION_COMPLETE'
                       and result.get('snapshot_sha256'))
    blockers = []
    if not approved: blockers.append('human_research_decision_missing')
    if not current: blockers.append('research_revision_or_support_changed')
    if not stable_read: blockers.append('gramps_live_read_validation_missing')
    blockers.extend([
        'gramps_write_api_unverified', 'upstream_atomic_concurrency_not_verified',
        'isolated_restore_not_verified', 'accepted_tree_write_adapter_not_implemented'
    ])
    return {
        'plan_id': str(plan.id), 'plan_digest': plan.digest_sha256,
        'research_review_approved': approved,
        'research_revision_current': bool(current),
        'latest_read_observation_available': stable_read,
        'snapshot_digest': result.get('snapshot_sha256') if stable_read else None,
        'execution_enabled': False, 'future_write_eligible': False,
        'blockers': blockers, 'note': 'A read-only observation is never a transaction precondition or a write authorization',
    }
