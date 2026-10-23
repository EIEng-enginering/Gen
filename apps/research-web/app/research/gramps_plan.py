"""Deterministic snapshot and conservative operation mapper; contains NO Gramps writes.

An operator-supplied Gramps handle is NOT verification that a person exists in the
accepted tree. Live read, revision recheck, duplicate detection, backup and a
separate future write gate are mandatory before any accepted-tree edit.
"""
import hashlib
import json

SUPPORTED = {'biological_parent', 'adoptive_parent', 'step_parent', 'spouse'}


def build_preview(group, option, revision, edges, bindings):
    if option.is_unknown:
        raise ValueError('An unidentified/unknown branch cannot be applied to Gramps')
    if not edges:
        raise ValueError('Selected branch has no explicit family relationships')
    edge_by_key = {e.edge_key: e for e in edges}
    handles = {b.edge_key: b for b in bindings}
    if set(edge_by_key) != set(handles):
        raise ValueError('Exactly one mapping is required for every branch edge')
    actions, warnings = [], []
    observation_handles = {}
    handle_owners = {}
    for key, edge in sorted(edge_by_key.items()):
        if edge.relationship_type not in SUPPORTED:
            raise ValueError('Unsupported relationship; identity merges and household associations cannot be proposed as Gramps writes')
        binding = handles[key]
        # A single observation cannot silently refer to different accepted people.
        for obs, handle in [(edge.from_observation_id, binding.from_handle),
                            (edge.to_observation_id, binding.to_handle)]:
            obs = str(obs)
            if obs in observation_handles and observation_handles[obs] != handle:
                raise ValueError('Inconsistent Gramps handle mapping across branch edges')
            if handle in handle_owners and handle_owners[handle] != obs:
                raise ValueError('Distinct research observations cannot silently collapse to one Gramps person')
            observation_handles[obs] = handle
            handle_owners[handle] = obs
        if not edge.supporting_observation_ids:
            raise ValueError('Unsourced relationship cannot enter an approval plan')
        if edge.contradicting_observation_ids:
            warnings.append('Contradictory evidence exists for edge '+key+'; resolve it before any future execution')
        actions.append({
            'edge_key': key,
            'action': 'propose_parent_child_link' if edge.relationship_type != 'spouse' else 'propose_spouse_link',
            'relationship_type': edge.relationship_type,
            'from_observation_id': str(edge.from_observation_id),
            'to_observation_id': str(edge.to_observation_id),
            'from_handle_claimed': binding.from_handle,
            'to_handle_claimed': binding.to_handle,
            'supporting_observation_ids': sorted(edge.supporting_observation_ids),
            'contradicting_observation_ids': sorted(edge.contradicting_observation_ids),
            'reasoning': edge.reasoning,
        })
    payload = {
        'contract_version': 'wp006.v1',
        'hypothesis_set_id': str(group.id), 'option_key': option.option_key,
        'branch_revision_id': str(revision.id),
        'branch_revision_number': revision.revision_number,
        'set_version': group.version,
        'actions': actions,
        'warnings': sorted(set(warnings)),
        'upstream_validation': 'NOT_PERFORMED',
        'accepted_tree_write': False,
        'required_future_checks': [
            'verify each Gramps person handle against authenticated live API',
            'capture and recheck upstream person/family change timestamps or ETags',
            'check for pre-existing or incompatible family relationships',
            'verify source revisions, signed approval, and current research group version',
            'verify complete backup and isolated restore before enabling any write',
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    payload['digest_sha256'] = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    return payload
