"""Optional, *read-only* Gramps API compatibility probe.

A live Gramps API token is configured separately by the operator and must never
be stored in the Git repository. No family-data mutation is supported here.
"""
import os
from urllib.parse import urlsplit
import httpx


def probe():
    base=os.getenv('GEN_GRAMPS_API_URL','http://grampsweb:5000/api').rstrip('/')
    parsed=urlsplit(base)
    # Prevent this adapter turning into an arbitrary-server proxy.
    if parsed.scheme!='http' or parsed.hostname not in ('grampsweb','localhost','127.0.0.1') or parsed.path!='/api':
        return {'status':'invalid_internal_endpoint','read_only':True}
    token=os.getenv('GEN_GRAMPS_ACCESS_TOKEN','').strip()
    if not token:
        return {'status':'token_not_configured','read_only':True,
                'note':'Owner login and exact upstream API compatibility must be tested locally'}
    try:
        # A JWT token is sent only to the fixed internal Gramps endpoint.
        # The token is NEVER included in diagnostics or exceptions.
        with httpx.Client(timeout=5.0,trust_env=False,follow_redirects=False) as client:
            r=client.get(base+'/metadata/',headers={'Authorization':'Bearer '+token})
        if r.status_code==401:return {'status':'upstream_unauthorised','read_only':True}
        if r.status_code!=200:return {'status':'upstream_http_error','upstream_status':r.status_code,'read_only':True}
        payload=r.json()
        return {'status':'connected_read_only','read_only':True,
                'upstream_metadata_keys':sorted(payload.keys())[:25] if isinstance(payload,dict) else [],
                'note':'No Gramps objects were written'}
    except (httpx.HTTPError,ValueError):
        return {'status':'unavailable','read_only':True}
