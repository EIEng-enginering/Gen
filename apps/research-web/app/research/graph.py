"""Conservative, explainable graph checks for alternative English family histories.

No inference that two observations are a person, and no assignment of posterior
probabilities. This code validates the *internal topology* of a proposed branch.
The genealogy/evidence may still be wrong even when these checks pass.
"""
from collections import defaultdict
from datetime import date

SYMMETRIC = {'spouse', 'sibling', 'same_person', 'household_association'}
PARENT = {'biological_parent', 'adoptive_parent', 'step_parent'}


def canonical_edge(edge):
    a, b = str(edge.from_observation_id), str(edge.to_observation_id)
    if edge.relationship_type in SYMMETRIC:
        a, b = sorted((a, b))
    return edge.relationship_type, a, b


def validate_topology(edges):
    """Raise ValueError for duplicated assertions or directed ancestry loops."""
    seen = set()
    directed = defaultdict(set)
    for edge in edges:
        a, b = str(edge.from_observation_id), str(edge.to_observation_id)
        if a == b:
            raise ValueError('An observation cannot form a relationship with itself')
        key = canonical_edge(edge)
        if key in seen:
            raise ValueError('Duplicate relationship asserted in one branch')
        seen.add(key)
        if edge.relationship_type in PARENT:
            directed[a].add(b)
    states = {}

    def visit(node):
        if states.get(node) == 1:
            raise ValueError('Directed ancestry cycle in this branch')
        if states.get(node) == 2:
            return
        states[node] = 1
        for other in directed[node]:
            visit(other)
        states[node] = 2

    for node in list(directed):
        visit(node)
    return True


def birth_year(record):
    """Only a recorded *birth* year is used as a proxy, never baptism/census."""
    if record.event_type != 'birth' or not record.earliest_iso or not record.latest_iso:
        return None
    lower, upper = int(record.earliest_iso[:4]), int(record.latest_iso[:4])
    return lower if lower == upper else None


def assessment(edges, observations, documents, source_groups=None):
    """Display warnings and source lineage without falsely claiming independence."""
    # WP-013 source grouping is conservative. A group's distinct key means
    # "not currently linked", never "verified independent".
    source_groups = source_groups or []
    possible_origin = {str(doc_id): group['group_id']
                       for group in source_groups for doc_id in group['document_ids']}
    warnings = []
    seen_warnings = set()
    edge_results = []
    for edge in edges:
        evidence = list(dict.fromkeys([*edge.supporting_observation_ids, *edge.contradicting_observation_ids]))
        origins = {}
        for raw_id in evidence:
            observation = observations[str(raw_id)]
            doc = documents[str(observation.document_id)]
            origins.setdefault(doc.origin_group, []).append(str(raw_id))
        supporting_origins = {documents[str(observations[str(x)].document_id)].origin_group for x in edge.supporting_observation_ids}
        contradicting_origins = {documents[str(observations[str(x)].document_id)].origin_group for x in edge.contradicting_observation_ids}
        unique_documents = {str(documents[str(observations[str(x)].document_id)].id) for x in evidence}
        grouped_evidence = defaultdict(list)
        for raw_id in evidence:
            doc = documents[str(observations[str(raw_id)].document_id)]
            grouped_evidence[possible_origin.get(str(doc.id), str(doc.id))].append(str(raw_id))
        support_candidates = {possible_origin.get(str(observations[str(x)].document_id),
                                                  str(observations[str(x)].document_id))
                              for x in edge.supporting_observation_ids}
        contradict_candidates = {possible_origin.get(str(observations[str(x)].document_id),
                                                     str(observations[str(x)].document_id))
                                 for x in edge.contradicting_observation_ids}
        local = []
        if any(len(ids) > 1 for ids in origins.values()):
            local.append('Multiple cited observations share one declared original-source group; do not double-count them')
        if supporting_origins & contradicting_origins:
            local.append('Supporting and contradicting citations share an original-source group; inspect the underlying document')
        if any(len({str(observations[str(oid)].document_id) for oid in ids}) > 1
               for ids in grouped_evidence.values()):
            local.append('WP-010 indicates possibly dependent original documents across catalogue entries; do not count as independent corroboration')
        if support_candidates & contradict_candidates:
            local.append('Support and contradiction may derive from one original source under WP-010 provenance grouping')
        if not edge.supporting_observation_ids:
            local.append('No supporting observations cited for this relationship')
        if edge.relationship_type in PARENT:
            parent = observations[str(edge.from_observation_id)]
            child = observations[str(edge.to_observation_id)]
            pyear, cyear = birth_year(parent), birth_year(child)
            if pyear is not None and cyear is not None:
                if pyear > cyear:
                    local.append('Chronology conflict: proposed parent birth recorded after child birth')
                elif cyear - pyear < 12 or cyear - pyear > 70:
                    local.append('Unusual recorded parent/child birth interval: investigate relationship type and record errors')
        if supporting_origins and all(observations[str(x)].event_type == 'census' for x in edge.supporting_observation_ids):
            local.append('Census-only citation: shared household does not prove biological kinship')
        if edge.contradicting_observation_ids:
            local.append('Contradictory evidence recorded; research reconciliation required')
        for message in local:
            if message not in seen_warnings:
                seen_warnings.add(message)
                warnings.append(message)
        edge_results.append({
            'edge_key': edge.edge_key,
            'distinct_declared_origin_groups': len(origins),
            'declared_origin_groups': sorted(origins),
            'potential_original_group_count': len(grouped_evidence),
            'possible_original_group_ids': sorted(grouped_evidence),
            'independence_verified': False,
            'warnings': local,
        })
    return {'edge_assessments': edge_results, 'warnings': warnings,
            'calibration_status': 'unscored', 'probability': None,
            'evidence_warning': ('Conservatively grouped possible shared originals; neither distinct origin keys '
                                 'nor different documents establish independent corroboration'),
            'independence_verified': False,
            'source_family_integration': 'WP-010 conservative grouping'}


def compare_options(options):
    """Compare candidate branch *assertions*, not genealogical probabilities."""
    keys = {o['option_key']: {tuple(x['canonical']) for x in o['edges']} for o in options}
    if not keys:
        return {'common_edges': [], 'distinct_edges_by_option': {}}
    common = set.intersection(*keys.values())
    return {'common_edges': [list(x) for x in sorted(common)],
            'distinct_edges_by_option': {k: [list(e) for e in sorted(v - common)] for k, v in keys.items()},
            'warning': 'Comparison is structural; no family probability is asserted'}
