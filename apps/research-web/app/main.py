"""24 Gen local authenticated provisional research service.

Research writes stay in the provisional database; Gramps tree access is read-only.
Candidate ranking is uncalibrated and no autonomous research worker is installed.
"""
import html
import os
import secrets
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI(title="24 Gen Research Foundation", version="0.1.0-candidate")
security = HTTPBasic()


def authenticate(credentials: Annotated[HTTPBasicCredentials, Depends(security)]) -> str:
    user = os.environ.get('GEN_ADMIN_USER', '')
    password = os.environ.get('GEN_ADMIN_PASSWORD', '')
    if not user or not password or password.startswith('REPLACE_'):
        raise HTTPException(status_code=503, detail='Local admin credentials are not configured')
    valid = secrets.compare_digest(credentials.username.encode('utf-8'), user.encode('utf-8'))
    valid &= secrets.compare_digest(credentials.password.encode('utf-8'), password.encode('utf-8'))
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid local credentials',
            headers={'WWW-Authenticate': 'Basic realm="24 Gen Local"'},
        )
    return user


def database_check() -> bool:
    """Connection-only check against the configured research database."""
    try:
        from sqlalchemy import text
        from app.research.db import engine
        with engine().connect() as conn:
            return conn.scalar(text('SELECT 1')) == 1
    except Exception:
        return False


@app.get('/health', include_in_schema=False)
def health() -> dict:
    # No secrets, genealogy records or detailed infrastructure exposed to unauthenticated callers.
    return {'status': 'up', 'component': 'research_web'}


@app.get('/api/v1/status')
def status_page(_: Annotated[str, Depends(authenticate)]) -> dict:
    return {'service': '24 Gen Research', 'stage': 'WP-002 provisional evidence candidate (pending R0.1 acceptance)',
            'research_database_connected': database_check(),
            'gramps_integration': 'optional_read_only_handle_preflight_not_live_verified',
            'autonomous_search': 'not_implemented'}


@app.get('/api/v1/features')
def feature_page(_: Annotated[str, Depends(authenticate)]) -> dict:
    return {
        'implemented': ['local_password_gate', 'provisional_evidence_workspace',
                        'manual_csv_import', 'uncalibrated_candidate_ranker',
                        'versioned_provisional_family_graphs', 'dry_run_gramps_change_plans', 'research_only_human_approval', 'read_only_gramps_handle_and_family_preflight',
                        'offline_gramps_contract_review', 'non_executable_write_readiness',
                        'source_cited_historical_place_registry','english_census_aware_candidate_triage',
                        'health_endpoint', 'research_database_connectivity_check'],
        'provided_by_gramps_web': ['family_tree_UI', 'Gramps_import_and_export',
                                    'person_and_event_management'],
        'planned_not_implemented': ['automated_research_ingestion', 'calibrated_record_linkage', 'record_linkage', 'full_population_record_linkage',
                                    'LLM_analysis', 'calibrated_probability_graph',
                                    'autonomous_jobs', 'Gramps_API_write_adapter'],
    }


@app.get('/', response_class=HTMLResponse)
def home(_: Annotated[str, Depends(authenticate)]) -> HTMLResponse:
    gramps = os.getenv('GRAMPS_PUBLIC_URL', 'http://127.0.0.1:5055')
    if not gramps.startswith('http://127.0.0.1:'):
        # Do not reflect an arbitrary external URL into the dashboard.
        gramps = 'http://127.0.0.1:5055'
    url = html.escape(gramps, quote=True)
    content = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>24 Gen Research Foundation</title>
    <style>
    body{{font:16px system-ui,Segoe UI,Arial,sans-serif;background:#f5f7f9;color:#182434;margin:0}}
    header{{background:#173654;color:white;padding:24px max(24px,calc((100vw - 960px)/2))}}
    main{{max-width:960px;margin:35px auto;padding:0 24px}}
    article{{background:white;border:1px solid #d5dde5;border-radius:12px;padding:24px;margin:18px 0}}
    h1{{margin:0;font-size:1.8rem}}h2{{font-size:1.2rem;margin:0 0 10px}}
    .label{{color:#58687b;font-size:0.9rem}}a{{color:#065e94}}a:focus{{outline:3px solid #e59f32}}
    .notice{{border-left:4px solid #bf8730;padding-left:12px}}
    code{{background:#eef2f6;padding:2px 5px;border-radius:3px}}
    </style></head><body><header><h1>24 Gen</h1>
    <p>Local research workspace — foundation candidate</p></header><main>
    <article><h2>Accepted family tree</h2><p>Gramps Web owns confirmed people,
    families, events and citations. Set up the Gramps owner account before import.</p>
    <p><a href="{url}" target="_blank" rel="noopener noreferrer">Open Gramps Web</a></p></article>
    <article><h2>Research system status</h2><p>Authentication and research database
    infrastructure are available; probabilistic matching and AI features are planned,
    <strong>not yet implemented</strong>.</p>
    <p><a href="/workspace">Open evidence research workspace</a></p><p><a href="/api/v1/status">View status JSON</a> ·
    <a href="/api/v1/features">View feature status JSON</a></p></article>
    <article class="notice"><h2>Important data controls</h2>
    <p>Do not store real genealogy data until the live backup and restore gates pass.
    The provisional evidence schema and manual record import are present. The
    Gramps write adapter and autonomous research are not implemented. This page does not change the accepted tree.</p></article>
    <p class="label">WP-002–004: provisional evidence candidate · loopback deployment only</p></main></body></html>"""
    return HTMLResponse(content=content)

# WP-002 onwards: a separate *provisional* evidence research data plane.
# No Gramps write adapter is enabled here.
from app.research.api import router as research_router
from app.research.ui import router as workspace_router
from app.research.graph_api import router as graph_router
app.include_router(research_router)
app.include_router(graph_router)
app.include_router(workspace_router)

# WP-006: read-only Gramps compatibility and human-reviewed dry-run plans.
from app.research.gramps_plan_api import router as gramps_plan_router
app.include_router(gramps_plan_router)

# WP-007: GET-only Gramps person/family fingerprint and human-controlled preflight.
from app.research.gramps_live_read_api import router as gramps_live_read_router
app.include_router(gramps_live_read_router)

# WP-008: Gramps schema review and non-executable readiness gates.
from app.research.gramps_contract_api import router as gramps_contract_router
app.include_router(gramps_contract_router)

# WP-009: source-linked historical places and bounded English identity triage.
from app.research.historical_api import router as historical_router
app.include_router(historical_router)

# WP-010/011: source provenance dependence and local supervised task staging.
# No external provider execution, billable calls or Gramps writes are enabled.
from app.research.source_families_api import router as source_family_router
from app.research.task_queue_api import router as task_queue_router
app.include_router(source_family_router)
app.include_router(task_queue_router)

# WP-012/013: bounded, read-only provisional chart and alternative views.
from app.research.tree_view_api import router as tree_view_router
app.include_router(tree_view_router)
