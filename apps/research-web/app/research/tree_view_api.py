"""WP-012/013: authenticated read-only family-chart and alternative comparison."""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app import main
from app.research.db import session
from app.research.models import Observation
from app.research.graph_api import hypothesis_graph
from app.research.tree_view import diagram, option_comparison

router = APIRouter(prefix='/api/v1/research', tags=['WP-012/013 Provisional visualisation'],
                   dependencies=[Depends(main.authenticate)])
DB = Annotated[Session, Depends(session)]


def prepared(group_id, db):
    graph = hypothesis_graph(group_id, db)
    ids = {UUID(str(edge[key])) for option in graph['options'] for edge in option['edges']
           for key in ('from_observation_id', 'to_observation_id')}
    if len(ids) > 300:
        raise HTTPException(422, 'Too many appearances to display at once')
    appearances = {str(o.id):o for o in db.scalars(select(Observation).where(Observation.id.in_(ids)))} if ids else {}
    return graph, appearances


@router.get('/hypotheses/{group_id}/tree-view')
def family_tree_view(group_id:UUID, db:DB, option_key:str|None=Query(None,min_length=1,max_length=100)):
    graph, appearances = prepared(group_id,db)
    options = graph['options']
    selection = next((o for o in options if o['option_key']==option_key),None) if option_key else (options[0] if options else None)
    if selection is None:
        raise HTTPException(404,'No matching branch option')
    try:
        result=diagram(selection,appearances)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    return {'hypothesis_set_id':str(group_id), 'title':graph['title'], 'set_version':graph['version'],
            'available_options':[{'key':o['option_key'],'description':o['description'],'is_unknown':o['is_unknown']}
                                 for o in options],
            'diagram':result,'accepted_tree_mutation_enabled':False,
            'warning':'This is a proposal diagram built from record appearances, not the accepted Gramps genealogy'}


@router.get('/hypotheses/{group_id}/compare-view')
def compare_family_tree_views(group_id:UUID, db:DB,
                              left:str=Query(min_length=1,max_length=100),
                              right:str=Query(min_length=1,max_length=100)):
    if left == right:
        raise HTTPException(422,'Select two different family alternatives')
    graph, appearances=prepared(group_id,db)
    opts={o['option_key']:o for o in graph['options']}
    if left not in opts or right not in opts:
        raise HTTPException(404,'One of the requested alternatives does not exist')
    try:
        ld,rd=diagram(opts[left],appearances),diagram(opts[right],appearances)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    return {'hypothesis_set_id':str(group_id), 'set_version':graph['version'],
            'left':ld, 'right':rd, 'comparison':option_comparison(opts[left],opts[right]),
            'other_or_unknown_available':any(o['is_unknown'] for o in opts.values()),
            'accepted_tree_mutation_enabled':False,
            'warning':'Neither diagram is proven; unscored evidence comparison only'}
