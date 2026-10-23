"""WP-007 strictly read-only Gramps identity/family preflight.

No mutation methods. One bounded request per required person/family handle.
No real Gramps data or bearer tokens are copied into local audit logs.
This is NOT a write authorization or guaranteed upstream concurrency token.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
import re
from urllib.parse import urlsplit

import httpx

HANDLE = re.compile(r'^[A-Za-z0-9_.:-]{1,128}$')
MAX_FAMILIES = 50
MAX_PEOPLE = 150
MAX_BYTES = 1024 * 1024


class UpstreamBlocked(Exception):
    """An intentionally generic diagnostic: never contains token, URL, or private data."""
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def upstream_url():
    url = os.getenv('GEN_GRAMPS_API_URL', 'http://grampsweb:5000/api')
    try:
        p = urlsplit(url)
        port = p.port
    except ValueError:
        raise UpstreamBlocked('unsupported_local_upstream') from None
    if (p.scheme != 'http' or p.hostname not in ('grampsweb', '127.0.0.1', 'localhost')
        or p.username or p.password or p.query or p.fragment or p.path.rstrip('/') != '/api'
        or (p.hostname == 'grampsweb' and port not in (None, 5000))):
        raise UpstreamBlocked('unsupported_local_upstream')
    return url.rstrip('/')


def make_client():
    return httpx.Client(timeout=httpx.Timeout(5.0), trust_env=False, follow_redirects=False)


def _get(client, base, relative, token):
    # relative paths are constructed only from a validated handle or fixed literals.
    try:
        with client.stream('GET', base + '/' + relative, headers={
            'Authorization': 'Bearer ' + token,
            'Accept': 'application/json',
        }) as response:
            if response.status_code == 401 or response.status_code == 403:
                raise UpstreamBlocked('upstream_auth_denied')
            if response.status_code == 404:
                raise UpstreamBlocked('upstream_object_not_found')
            if response.status_code != 200:
                raise UpstreamBlocked('upstream_http_error')
            if response.headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
                raise UpstreamBlocked('upstream_unexpected_content_type')
            chunks, size = [], 0
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > MAX_BYTES:
                    raise UpstreamBlocked('upstream_response_too_large')
                chunks.append(chunk)
            try:
                obj = json.loads(b''.join(chunks))
            except (ValueError, UnicodeError):
                raise UpstreamBlocked('upstream_invalid_json') from None
            if not isinstance(obj, dict):
                raise UpstreamBlocked('upstream_unexpected_shape')
            return obj
    except (httpx.HTTPError, OSError):
        raise UpstreamBlocked('upstream_connection_error') from None


def _family_handles(person):
    result = set()
    for key in ('family_list', 'parent_family_list'):
        value = person.get(key)
        if not isinstance(value, list):
            raise UpstreamBlocked('person_missing_family_references')
        for family in value:
            if not isinstance(family, str) or HANDLE.fullmatch(family) is None:
                raise UpstreamBlocked('person_invalid_family_reference')
            result.add(family)
    return result


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=True).encode('utf-8')).hexdigest()


def _extract_person(person, expected):
    if person.get('handle') != expected:
        raise UpstreamBlocked('upstream_person_handle_mismatch')
    family_handles = sorted(_family_handles(person))
    # A 'change' value is not assumed to be an atomic compare-and-swap token.
    token = person.get('change')
    return {'handle': expected, 'gramps_id': person.get('gramps_id'),
            'family_handles': family_handles,
            'change_hint': str(token) if token is not None else None}


def _extract_family(family, expected):
    if family.get('handle') != expected:
        raise UpstreamBlocked('upstream_family_handle_mismatch')
    children = family.get('child_ref_list')
    if not isinstance(children, list):
        raise UpstreamBlocked('family_missing_child_references')
    refs = []
    for child in children:
        if not isinstance(child, dict) or not isinstance(child.get('ref'), str):
            raise UpstreamBlocked('family_invalid_child_reference')
        if HANDLE.fullmatch(child['ref']) is None:
            raise UpstreamBlocked('family_invalid_child_reference')
        refs.append(child['ref'])
    for key in ('father_handle', 'mother_handle'):
        if family.get(key) is not None and (not isinstance(family[key], str)
                                               or HANDLE.fullmatch(family[key]) is None):
            raise UpstreamBlocked('family_invalid_parent_handle')
    return {'handle': expected, 'father': family.get('father_handle'),
            'mother': family.get('mother_handle'), 'children': sorted(set(refs)),
            'change_hint': str(family.get('change')) if family.get('change') is not None else None}


def read_plan_snapshot(preview):
    """Read and fingerprint only; does NOT assign write eligibility.

    Returns a minimal report. Callers must not surface individual Gramps objects,
    names, tokens, or the raw upstream metadata. Any unsupported shape blocks.
    """
    base = upstream_url()
    token = os.getenv('GEN_GRAMPS_ACCESS_TOKEN', '').strip()
    if not token:
        raise UpstreamBlocked('token_not_configured')
    actions = preview.get('actions')
    if not isinstance(actions, list) or not actions or len(actions) > 75:
        raise UpstreamBlocked('invalid_plan_actions')
    required = set()
    for action in actions:
        if action.get('action') not in ('propose_parent_child_link', 'propose_spouse_link'):
            raise UpstreamBlocked('unsupported_action')
        for field in ('from_handle_claimed','to_handle_claimed'):
            value = action.get(field)
            if not isinstance(value, str) or HANDLE.fullmatch(value) is None:
                raise UpstreamBlocked('invalid_handle')
            required.add(value)
    if len(required) > MAX_PEOPLE:
        raise UpstreamBlocked('too_many_people')
    with make_client() as client:
        metadata = _get(client, base, 'metadata/', token)
        # Metadata is used as a shape-checked reachability probe; not a verified schema version.
        people = {}
        for handle in sorted(required):
            people[handle] = _extract_person(_get(client, base, 'people/'+handle, token), handle)
        families_set = set()
        for p in people.values():
            families_set.update(p['family_handles'])
        if len(families_set) > MAX_FAMILIES:
            raise UpstreamBlocked('too_many_related_families')
        families = {}
        for handle in sorted(families_set):
            families[handle] = _extract_family(_get(client, base, 'families/'+handle, token), handle)
    findings = []
    for action in actions:
        first, second = action['from_handle_claimed'], action['to_handle_claimed']
        exists = False
        if action['action'] == 'propose_spouse_link':
            exists = any({fam['father'], fam['mother']} == {first, second} for fam in families.values())
        else:
            exists = any(first in (fam['father'],fam['mother']) and second in fam['children'] for fam in families.values())
        # Relationship type and existing family structure need live manual review.
        findings.append({'edge_key':action['edge_key'],
                         'observed_upstream_status':'already_linked' if exists else 'not_seen_in_related_families',
                         'needs_manual_review': True})
    change_hints = all(p['change_hint'] is not None for p in people.values()) and all(
        f['change_hint'] is not None for f in families.values())
    relevant_snapshot = {'people':people, 'families':families,
                         'metadata_keys': sorted(metadata.keys())[:40],
                         'plan_digest': preview['digest_sha256']}
    return {
        'status': 'READ_ONLY_OBSERVATION_COMPLETE',
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'plan_digest':preview['digest_sha256'],
        'snapshot_sha256': _digest(relevant_snapshot),
        'people_checked': len(people), 'related_families_checked':len(families),
        'upstream_change_hints_present':change_hints,
        'findings': findings,
        'mutation_performed':False,
        'execution_enabled':False,
        'future_write_eligible':False,
        'limitations':[
            'Read snapshot is non-atomic: upstream objects can change immediately afterwards',
            'Upstream change hints are NOT proven compare-and-swap tokens',
            'No approval for live mutation, duplicate resolution, merge or Gramps commit',
            'Requires a disposable authenticated Gramps API test and isolated full restore',
        ],
    }
