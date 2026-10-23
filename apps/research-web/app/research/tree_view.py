"""WP-012/013 bounded, deterministic diagrams of *record appearances*.

Records are NEVER implicitly merged into people; levels are diagram positions,
not ancestry proof. No posterior probability is inferred from layout or counts.
"""
from collections import defaultdict

PARENT = {'biological_parent', 'adoptive_parent', 'step_parent'}
MAX_NODES = 150
MAX_EDGES = 75


def diagram(option, observations):
    """Project a stored option onto safe, sortable SVG coordinates and text labels."""
    edges = option['edges']
    if len(edges) > MAX_EDGES:
        raise ValueError('Diagram exceeds maximum relationships')
    identifiers = sorted({str(e[k]) for e in edges for k in ('from_observation_id','to_observation_id')})
    if len(identifiers) > MAX_NODES:
        raise ValueError('Diagram exceeds maximum appearances')
    parent_edges = defaultdict(set)
    for e in edges:
        if e['relationship_type'] in PARENT:
            parent_edges[str(e['from_observation_id'])].add(str(e['to_observation_id']))
    level = {key: 0 for key in identifiers}
    # Bounded Bellman-Ford style propagation. The upstream graph validator rejects
    # directed cycles; still stop for bad imported or future persisted rows.
    for _ in range(len(identifiers)):
        modified = False
        for source, children in sorted(parent_edges.items()):
            for target in sorted(children):
                if level[target] <= level[source]:
                    level[target] = level[source] + 1
                    modified = True
        if not modified:
            break
    else:
        if parent_edges:
            raise ValueError('Cyclic genealogy graph cannot be drawn as ancestry')
    rows = defaultdict(list)
    for ident in identifiers:
        rows[level[ident]].append(ident)
    node_coordinates = {}
    width = max(760, max((len(v) * 218 for v in rows.values()), default=760))
    for generation, entries in sorted(rows.items()):
        offset = (width - len(entries) * 218) // 2
        for i, oid in enumerate(entries):
            node_coordinates[oid] = (offset + i * 218 + 12, 42 + generation * 118)
    nodes = []
    for oid in identifiers:
        record = observations.get(oid)
        if record is None:
            raise ValueError('Diagram references an unknown historical observation')
        x, y = node_coordinates[oid]
        nodes.append({'id':oid, 'label':record.person_name_verbatim,
                      'event_type':record.event_type, 'date_as_written':record.event_date_verbatim,
                      'place_as_written':record.location_verbatim,
                      'is_confirmed_person':False, 'generation_for_layout_only':level[oid],
                      'x':x, 'y':y})
    links = [{'edge_key':e['edge_key'], 'source_id':str(e['from_observation_id']),
              'target_id':str(e['to_observation_id']), 'relationship_type':e['relationship_type'],
              'style':'solid' if e['relationship_type'] in PARENT else 'dashed',
              'evidence_count':len(e['supporting_observation_ids']),
              'has_contradiction':bool(e['contradicting_observation_ids'])} for e in edges]
    return {'option_key':option['option_key'], 'description':option['description'],
            'is_unknown':option['is_unknown'], 'revision_number':(
                option['revision']['revision_number'] if option['revision'] else None),
            'nodes':nodes, 'links':links, 'width':width,
            'height':max(190, (max(rows) + 1) * 118 + 32) if rows else 190,
            'warnings':option['revision']['assessment']['warnings'] if option['revision'] else [],
            'edge_assessments':(option['revision']['assessment']['edge_assessments']
                                if option['revision'] else []),
            'interpretation':'Record appearances, not proven individual people',
            'calibrated_probability':None, 'gramps_written':False}


def option_comparison(left, right):
    """Deterministic comparison of structural assertions, not posterior odds."""
    le = {tuple(e['canonical']) for e in left['edges']}
    re = {tuple(e['canonical']) for e in right['edges']}
    return {'common': [list(x) for x in sorted(le & re)],
            'only_left': [list(x) for x in sorted(le - re)],
            'only_right': [list(x) for x in sorted(re - le)],
            'unknown_candidate_included':bool(left['is_unknown'] or right['is_unknown']),
            'probabilities_calibrated':False,
            'warning':'Comparison of provisional assertions only; source evidence is not proven independent.'}
