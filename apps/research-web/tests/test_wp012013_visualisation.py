"""WP-012/013: safe provisional tree and WP-010 source-independence reconciliation."""
import pytest
from uuid import uuid4
from test_graph_branches import client, observations, hypothesis, revision, parent, AUTH, WRITE
from app.research.tree_view import diagram, option_comparison


def add_attested_original(client, first, second):
    response=client.post('/api/v1/research/source-families',headers=WRITE,json={
        'family_key':'parish:synthetic:page-50',
        'description':'One original manuscript represented by two catalogues',
        'rationale':'The original archival shelfmark and scan folio were compared by the researcher.'})
    assert response.status_code==201,response.text
    fid=response.json()['id']
    for oid in (first,second):
        document=client.get('/api/v1/research/observations/'+oid,headers=AUTH).json()['document_id']
        result=client.post('/api/v1/research/source-families/'+fid+'/members',headers=WRITE,json={
            'document_id':document,
            'justification':'Researcher manually checked the same source manuscript and folio.'})
        assert result.status_code==201,result.text


def test_graphed_shared_originals_are_not_counted_as_distinct(client):
    ids=observations(client);hid=hypothesis(client,ids)
    add_attested_original(client,ids[0],ids[1])
    assert revision(client,hid,'mother_harriet',1,[parent(ids[0],ids[1],ids[:2])]).status_code==201
    graph=client.get('/api/v1/research/hypotheses/'+hid+'/graph',headers=AUTH).json()
    edge=graph['options'][0]['revision']['assessment']['edge_assessments'][0]
    assert edge['distinct_declared_origin_groups']==2  # legacy, not corrected or erased
    assert edge['potential_original_group_count']==1 # correct, conservative group
    assert edge['independence_verified'] is False
    assert any('WP-010' in warning for warning in edge['warnings'])
    tree=client.get('/api/v1/research/hypotheses/'+hid+'/tree-view',headers=AUTH).json()
    assert tree['diagram']['edge_assessments'][0]['potential_original_group_count']==1
    assert tree['diagram']['calibrated_probability'] is None
    assert not tree['diagram']['gramps_written']


def test_compare_provisional_branches_and_unknown(client):
    obs=observations(client);hid=hypothesis(client,obs)
    assert revision(client,hid,'mother_harriet',1,[parent(obs[0],obs[1],obs[:2])]).status_code==201
    root=f'/api/v1/research/hypotheses/{hid}'
    missing=client.get(root+'/tree-view',headers={})
    assert missing.status_code==401
    visual=client.get(root+'/tree-view?option_key=mother_harriet',headers=AUTH)
    assert visual.status_code==200,visual.text
    node_data=visual.json()['diagram']
    assert len(node_data['nodes'])==2 and len(node_data['links'])==1
    assert node_data['nodes'][0]['is_confirmed_person'] is False
    assert all(n['generation_for_layout_only']>=0 for n in node_data['nodes'])
    assert visual.json()['accepted_tree_mutation_enabled'] is False
    comparison=client.get(root+'/compare-view?left=mother_harriet&right=other_unknown',headers=AUTH)
    assert comparison.status_code==200,comparison.text
    result=comparison.json()
    assert result['other_or_unknown_available'] is True
    assert result['right']['nodes']==[] and result['right']['links']==[]
    assert result['comparison']['only_left'] and not result['comparison']['only_right']
    assert result['comparison']['probabilities_calibrated'] is False
    assert result['accepted_tree_mutation_enabled'] is False
    assert client.get(root+'/compare-view?left=other_unknown&right=other_unknown',headers=AUTH).status_code==422
    assert client.get(root+'/tree-view?option_key=madeup',headers=AUTH).status_code==404
    assert client.get(root+'/compare-view?left=mother_harriet&right=madeup',headers=AUTH).status_code==404
    assert client.get('/api/v1/research/hypotheses/'+str(uuid4())+'/tree-view',headers=AUTH).status_code==404


def test_visualization_get_does_not_edit_set_version(client):
    obs=observations(client);hid=hypothesis(client,obs)
    assert revision(client,hid,'mother_harriet',1,[parent(obs[0],obs[1],obs[:2])]).status_code==201
    root=f'/api/v1/research/hypotheses/{hid}'
    original=client.get(root+'/graph',headers=AUTH).json()['version']
    for _ in range(3):
        client.get(root+'/tree-view',headers=AUTH)
        client.get(root+'/compare-view?left=mother_harriet&right=other_unknown',headers=AUTH)
    assert client.get(root+'/graph',headers=AUTH).json()['version']==original


def test_diagram_stable_and_invalid_graph_fails_closed():
    from types import SimpleNamespace
    a,b=str(uuid4()),str(uuid4())
    e={'edge_key':'r1','from_observation_id':a,'to_observation_id':b,'relationship_type':'biological_parent',
       'supporting_observation_ids':[], 'contradicting_observation_ids':[],
       'canonical':['biological_parent',a,b]}
    option={'option_key':'a','description':'Candidate parent','is_unknown':False,
            'revision':{'revision_number':1,'assessment':{'warnings':[], 'edge_assessments':[]}},'edges':[e]}
    observations={a:SimpleNamespace(person_name_verbatim='<img onerror=alert(1)>',event_type='birth',
                                    event_date_verbatim='1800',location_verbatim='England'),
                  b:SimpleNamespace(person_name_verbatim='Person B',event_type='census',
                                    event_date_verbatim='1841',location_verbatim='England')}
    result=diagram(option,observations)
    assert result==diagram(option,observations)
    assert '<img onerror=alert(1)>' in [x['label'] for x in result['nodes']]
    assert all(x['calibrated_probability'] is None for x in [result])
    assert not any(x['is_confirmed_person'] for x in result['nodes'])
    reversed_edge={**e,'edge_key':'r2','from_observation_id':b,'to_observation_id':a}
    with pytest.raises(ValueError,match='Cyclic'):
        diagram({**option,'edges':[e,reversed_edge]},observations)
    with pytest.raises(ValueError,match='unknown historical observation'):
        diagram(option,{a:observations[a]})
    with pytest.raises(ValueError,match='maximum relationships'):
        diagram({**option,'edges':[e]*76},observations)
    assert option_comparison(option,{**option,'edges':[]})['only_left']


def test_workspace_contains_accessible_visual_controls_and_escaped_data(client):
    result=client.get('/workspace',headers=AUTH)
    assert result.status_code==200
    html=result.text
    assert 'Family alternative A' in html
    assert 'Family alternative B' in html
    assert 'family-zoom' in html
    assert 'createElementNS' in html and 'textContent' in html
    assert '.innerHTML' not in html
    assert 'WP-010' in html
