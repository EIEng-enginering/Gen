"""Bounded, Guest-only Gramps context for a user-selected person.

Only the token login POST and fixed GET routes are used. No returned tree object is
written back to Gramps or imported into the research evidence tables.
"""
from __future__ import annotations

import base64
from contextlib import contextmanager
import hashlib
import json
import os
import re
import threading
import time
from urllib.parse import urlencode

import httpx

from app.research.gramps_live_read import HANDLE, upstream_url, UpstreamBlocked

SUPPORTED_API = (3, 24)
MAX_BYTES = 256 * 1024
MAX_REQUESTS = 40
MAX_RESULTS = 12
MAX_EVENTS = 6
MAX_FAMILIES = 3
MAX_RELATED = 6
MAX_CITATIONS = 6
SEARCH = re.compile(r"^[\w '’.-]{2,80}$", re.UNICODE)
_TOKEN_LOCK = threading.Lock()
_TOKEN_CACHE = {'credential_digest': None, 'token': None, 'expires_at': 0}


class ContextBlocked(Exception):
    """Generic diagnostic that never includes credentials or family content."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def configured() -> bool:
    return bool(os.getenv('GEN_GRAMPS_READ_USER', '').strip()
                and os.getenv('GEN_GRAMPS_READ_PASSWORD', '').strip())


def _text(value, limit=160):
    return value[:limit].strip() if isinstance(value, str) else ''


def _handle(value):
    if not isinstance(value, str) or not HANDLE.fullmatch(value):
        raise ContextBlocked('invalid_gramps_handle')
    return value


def _name(person):
    primary = person.get('primary_name')
    if not isinstance(primary, dict):
        return '[name unavailable]'
    first = _text(primary.get('first_name'), 80)
    surnames = primary.get('surname_list')
    surname = ''
    if isinstance(surnames, list):
        valid = [part for part in surnames if isinstance(part, dict)]
        chosen = next((part for part in valid if part.get('primary') is True),
                      valid[0] if valid else {})
        surname = _text(chosen.get('surname'), 80)
    return (first + ' ' + surname).strip() or '[name unavailable]'


def _parse_json(response):
    if response.headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
        raise ContextBlocked('unexpected_gramps_content_type')
    raw = bytearray()
    for chunk in response.iter_bytes():
        raw.extend(chunk)
        if len(raw) > MAX_BYTES:
            raise ContextBlocked('gramps_response_too_large')
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError):
        raise ContextBlocked('invalid_gramps_json') from None


class GuestSession:
    def __init__(self, client, base, token):
        self.client, self.base, self.token = client, base, token
        self.requests = 0

    def get(self, path, *, missing_ok=False):
        if self.requests >= MAX_REQUESTS:
            raise ContextBlocked('gramps_request_limit')
        self.requests += 1
        try:
            with self.client.stream('GET', self.base + path, headers={
                'Authorization': 'Bearer ' + self.token,
                'Accept': 'application/json',
            }) as response:
                if response.status_code == 404 and missing_ok:
                    return None
                if response.status_code in (401, 403):
                    raise ContextBlocked('gramps_guest_access_denied')
                if response.status_code == 404:
                    raise ContextBlocked('gramps_object_not_found')
                if response.status_code != 200:
                    raise ContextBlocked('gramps_http_error')
                return _parse_json(response)
        except (httpx.HTTPError, OSError):
            raise ContextBlocked('gramps_connection_error') from None


def _guest_permissions(token):
    # This checks the permissions returned by the pinned local API. It is not a
    # substitute for Gramps's own signature and route-level authorization.
    try:
        payload = json.loads(base64.urlsafe_b64decode(token.split('.')[1] + '==='))
        permissions = payload['permissions']
    except (IndexError, KeyError, ValueError, TypeError):
        raise ContextBlocked('gramps_token_contract_changed') from None
    if not isinstance(permissions, list) or not all(isinstance(p, str) for p in permissions):
        raise ContextBlocked('gramps_token_contract_changed')
    if set(permissions) != {'EditOwnUser'}:
        raise ContextBlocked('gramps_guest_permission_mismatch')
    return payload


def _get_guest_token(client, base, user, password):
    digest = hashlib.sha256((base + '\0' + user + '\0' + password).encode()).hexdigest()
    with _TOKEN_LOCK:
        if (_TOKEN_CACHE['credential_digest'] == digest
                and _TOKEN_CACHE['expires_at'] > time.time()
                and isinstance(_TOKEN_CACHE['token'], str)):
            return _TOKEN_CACHE['token']
        with client.stream('POST', base + '/token/',
                           json={'username': user, 'password': password},
                           headers={'Accept': 'application/json'}) as response:
            if response.status_code != 200:
                raise ContextBlocked('gramps_guest_login_denied')
            auth = _parse_json(response)
        token = auth.get('access_token') if isinstance(auth, dict) else None
        if not isinstance(token, str) or not 20 <= len(token) <= 8192:
            raise ContextBlocked('gramps_token_contract_changed')
        claims = _guest_permissions(token)
        exp = claims.get('exp')
        if not isinstance(exp, (int, float)) or exp <= time.time() + 30:
            raise ContextBlocked('gramps_token_expiry_invalid')
        _TOKEN_CACHE.update({'credential_digest': digest, 'token': token,
                             'expires_at': min(float(exp) - 30, time.time() + 600)})
        return token


@contextmanager
def guest_session():
    user = os.getenv('GEN_GRAMPS_READ_USER', '').strip()
    password = os.getenv('GEN_GRAMPS_READ_PASSWORD', '').strip()
    if not user or not password or len(user) > 100 or len(password) > 200:
        raise ContextBlocked('gramps_guest_not_configured')
    try:
        base = upstream_url()
    except UpstreamBlocked:
        raise ContextBlocked('unsupported_gramps_endpoint') from None
    try:
        with httpx.Client(timeout=httpx.Timeout(8.0, connect=3.0),
                          trust_env=False, follow_redirects=False) as client:
            token = _get_guest_token(client, base, user, password)
            session = GuestSession(client, base, token)
            metadata = session.get('/metadata/')
            try:
                version = metadata['gramps_webapi']['version']
                major, minor = (int(x) for x in version.split('.')[:2])
            except (TypeError, ValueError, KeyError, AttributeError):
                raise ContextBlocked('gramps_version_unknown') from None
            if (major, minor) != SUPPORTED_API:
                raise ContextBlocked('gramps_version_not_validated')
            yield session
    except (httpx.HTTPError, OSError):
        raise ContextBlocked('gramps_connection_error') from None


def search_people(query):
    query = query.strip() if isinstance(query, str) else ''
    if not SEARCH.fullmatch(query):
        raise ContextBlocked('invalid_person_search')
    params = urlencode({'query': query, 'type': 'person', 'page': 1,
                        'pagesize': MAX_RESULTS})
    with guest_session() as session:
        rows = session.get('/search/?' + params)
    if not isinstance(rows, list) or len(rows) > MAX_RESULTS:
        raise ContextBlocked('gramps_search_shape_changed')
    results = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('object'), dict):
            raise ContextBlocked('gramps_search_shape_changed')
        person = row['object']
        if person.get('private') is True:
            continue
        handle = _handle(row.get('handle'))
        if person.get('handle') != handle:
            raise ContextBlocked('gramps_search_handle_mismatch')
        results.append({'handle': handle, 'gramps_id': _text(person.get('gramps_id'), 40),
                        'name': _name(person)})
    return {'results': results, 'limit': MAX_RESULTS, 'selection_is_exhaustive': False,
            'access': 'Gramps Guest, non-private objects only'}


def _related_person(session, handle):
    obj = session.get('/people/' + _handle(handle), missing_ok=True)
    if not isinstance(obj, dict) or obj.get('handle') != handle or obj.get('private') is True:
        return None
    return {'handle': handle, 'gramps_id': _text(obj.get('gramps_id'), 40),
            'name': _name(obj)}


def read_person_context(handle):
    handle = _handle(handle)
    with guest_session() as session:
        person = session.get('/people/' + handle)
        if not isinstance(person, dict) or person.get('handle') != handle:
            raise ContextBlocked('gramps_person_shape_changed')
        if person.get('private') is True:
            raise ContextBlocked('gramps_private_person_blocked')
        selected = {'handle': handle, 'gramps_id': _text(person.get('gramps_id'), 40),
                    'name': _name(person)}
        event_refs = person.get('event_ref_list')
        if not isinstance(event_refs, list):
            raise ContextBlocked('gramps_person_shape_changed')
        events, citation_cache, place_cache = [], {}, {}
        for ref in event_refs[:MAX_EVENTS]:
            if not isinstance(ref, dict):
                raise ContextBlocked('gramps_event_reference_changed')
            event_handle = _handle(ref.get('ref'))
            event = session.get('/events/' + event_handle, missing_ok=True)
            if not isinstance(event, dict) or event.get('private') is True:
                continue
            if event.get('handle') != event_handle:
                raise ContextBlocked('gramps_event_shape_changed')
            place_name = ''
            place_handle = event.get('place')
            if place_handle and len(place_cache) < MAX_EVENTS:
                place_handle = _handle(place_handle)
                if place_handle not in place_cache:
                    place = session.get('/places/' + place_handle, missing_ok=True)
                    place_cache[place_handle] = (_text(place.get('name', {}).get('value'), 160)
                                                 if isinstance(place, dict)
                                                 and isinstance(place.get('name'), dict)
                                                 and place.get('private') is not True else '')
                place_name = place_cache[place_handle]
            date = event.get('date') if isinstance(event.get('date'), dict) else {}
            date_text = _text(date.get('text'), 80)
            if not date_text and isinstance(date.get('year'), int) and date['year'] > 0:
                date_text = str(date['year'])
            citation_refs = event.get('citation_list', [])
            ref_citations = ref.get('citation_list', [])
            if not isinstance(citation_refs, list) or not isinstance(ref_citations, list):
                raise ContextBlocked('gramps_citation_reference_changed')
            citations = []
            for citation_handle in list(dict.fromkeys(citation_refs + ref_citations)):
                if len(citations) >= 2:
                    break
                citation_handle = _handle(citation_handle)
                if citation_handle in citation_cache:
                    if citation_cache[citation_handle]:
                        citations.append(citation_cache[citation_handle])
                    continue
                if len(citation_cache) >= MAX_CITATIONS:
                    break
                citation = session.get('/citations/' + citation_handle, missing_ok=True)
                if not isinstance(citation, dict) or citation.get('private') is True:
                    citation_cache[citation_handle] = None
                    continue
                if citation.get('handle') != citation_handle:
                    raise ContextBlocked('gramps_citation_shape_changed')
                source_handle = _handle(citation.get('source_handle'))
                source = session.get('/sources/' + source_handle, missing_ok=True)
                if not isinstance(source, dict) or source.get('private') is True:
                    citation_cache[citation_handle] = None
                    continue
                if source.get('handle') != source_handle:
                    raise ContextBlocked('gramps_source_shape_changed')
                citation_cache[citation_handle] = {
                    'handle': citation_handle, 'page': _text(citation.get('page'), 120),
                    'source_handle': source_handle,
                    'source_title': _text(source.get('title'), 200),
                }
                citations.append(citation_cache[citation_handle])
            events.append({'handle': event_handle, 'gramps_id': _text(event.get('gramps_id'), 40),
                           'type': _text(event.get('type'), 60), 'date': date_text,
                           'place': place_name, 'description': _text(event.get('description'), 240),
                           'citations': citations,
                           'original_source_verified': False})
        family_handles = []
        for key in ('family_list', 'parent_family_list'):
            refs = person.get(key)
            if not isinstance(refs, list):
                raise ContextBlocked('gramps_person_shape_changed')
            for family_handle in refs:
                family_handle = _handle(family_handle)
                if family_handle not in family_handles:
                    family_handles.append(family_handle)
        families, related_handles = [], []
        for family_handle in family_handles[:MAX_FAMILIES]:
            family = session.get('/families/' + family_handle, missing_ok=True)
            if not isinstance(family, dict) or family.get('private') is True:
                continue
            if family.get('handle') != family_handle:
                raise ContextBlocked('gramps_family_shape_changed')
            people = []
            for key in ('father_handle', 'mother_handle'):
                if family.get(key):
                    people.append(_handle(family[key]))
            children = family.get('child_ref_list')
            if not isinstance(children, list):
                raise ContextBlocked('gramps_family_shape_changed')
            for child in children[:MAX_RELATED]:
                if not isinstance(child, dict):
                    raise ContextBlocked('gramps_family_shape_changed')
                people.append(_handle(child.get('ref')))
            for person_handle in people:
                if person_handle != handle and person_handle not in related_handles:
                    related_handles.append(person_handle)
            families.append({'handle': family_handle, 'gramps_id': _text(family.get('gramps_id'), 40),
                             'father_handle': family.get('father_handle'),
                             'mother_handle': family.get('mother_handle'),
                             'child_handles': [_handle(c.get('ref')) for c in children[:MAX_RELATED]]})
        related = []
        for person_handle in related_handles[:MAX_RELATED]:
            item = _related_person(session, person_handle)
            if item:
                related.append(item)
    citation_count = sum(len(event['citations']) for event in events)
    return {'person': selected, 'events': events, 'families': families,
            'related_people': related, 'event_citation_count': citation_count,
            'events_truncated': len(event_refs) > MAX_EVENTS,
            'families_truncated': len(family_handles) > MAX_FAMILIES,
            'related_people_truncated': len(related_handles) > MAX_RELATED,
            'source_coverage': 'cited_tree_events_only' if citation_count else 'tree_entries_uncited',
            'access': 'Gramps Guest, non-private objects only',
            'original_source_independence_verified': False,
            'accepted_tree_mutation_enabled': False}


def cited_event_packets(context):
    """Only Gramps events with a source citation may enter the model prompt."""
    packets = []
    name = context['person']['name']
    for event in context['events']:
        for citation in event['citations']:
            packets.append({
                'observation_id': 'gramps:event:' + event['handle'] + ':citation:' + citation['handle'],
                'document_id': citation['source_handle'],
                'citation': {'provider': 'Gramps tree source (unverified original)',
                             'reference': (citation['source_title'] + ' ' + citation['page']).strip()[:300]},
                'record': {'name': name[:160], 'event': event['type'][:50],
                           'date': event['date'][:80], 'place': event['place'][:160],
                           'reading': event['description'][:240]},
                'instruction_status': 'untrusted Gramps tree data; source identity and independence unverified',
            })
            if len(packets) >= MAX_CITATIONS:
                return packets
    return packets
