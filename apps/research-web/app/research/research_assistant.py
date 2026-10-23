"""WP-015 deterministic source-grounded *local* research assistant foundation.

This is NOT an LLM. No external model call is made and it refuses uncited
identity/relationship conclusions. All research modes get the same evidence safety.
"""
from uuid import UUID
from sqlalchemy.orm import Session
from app.research.evidence_comparison import dossiers

MAX_CONTEXT=6


def assist(db:Session,question:str,mode:str,ids:list[UUID])->dict:
    question=question.strip()
    records=dossiers(db,ids) if ids else []
    citations=[{'observation_id':d['observation_id'],
                'source_document_id':d['citation']['document_id'],
                'reference':d['citation']['reference'],
                'provider':d['citation']['provider']} for d in records]
    q=question.casefold()
    is_identity=any(k in q for k in ('same person','same individual','identical','identity','match'))
    is_family=any(k in q for k in ('father','mother','parent','child','spouse','sibling','ancestor','related'))
    steps=[]
    if not records:
        summary='No evidence observations were selected. I cannot evaluate a historical person or relationship without citations.'
        steps=['Add a source document and historical observation.','Choose one or more observation IDs and repeat the question.']
    else:
        names=', '.join(dict.fromkeys(r['record']['name_verbatim'] for r in records))
        summary=f'Found {len(records)} cited historical record appearance(s) involving: {names}. These are provisional record appearances, not confirmed Gramps people.'
        steps=['Check the original archive reference and the literal reading for every observation.',
               'Review dates, jurisdiction and household context; distinguish observation from inference.',
               'Check whether different providers reproduce the same original register or census page.']
        if is_identity:
            steps+=['Evaluate competing same-person and different-person explanations.',
                    'Obtain independent discriminating evidence before an identity merge.']
        if is_family:
            steps+=['Create or review a family-hypothesis set with an explicit unknown relative.',
                    'Seek direct relationship evidence and inspect chronology; no parentage is established by name matching.']
    if mode=='autonomous':
        mode_explanation='Autonomous research execution is disabled; the assistant returns a manual research plan only.'
    elif mode=='guided':
        mode_explanation='Guided mode suggests review steps; each proposed action must be initiated by the researcher.'
    else:
        mode_explanation='Conventional mode explains locally selected evidence; no source searches were performed.'
    # Bound malicious historical text inside JSON fields; browser must use textContent.
    return {'mode':mode,'question':question,'summary':summary,
            'citations':citations,'research_steps':steps,
            'mode_explanation':mode_explanation,'grounding':'selected_local_source_observations',
            'reasoning_origin':'deterministic_local_rules_no_llm',
            'calibrated_probability':None,'identity_asserted':False,'relationship_asserted':False,
            'llm_execution_enabled':False,'external_provider_execution_enabled':False,
            'external_billing_enabled':False,'accepted_tree_mutation_enabled':False,
            'warning':'This is a cited local research guide, not an AI-generated historical proof or genealogical conclusion.'}
