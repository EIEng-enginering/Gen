"""Explicit provider execution *denial* boundary, no HTTP client or credentials.

Written permission, retention, cost and action need separate reviewed integration.
A catalogue appearing here grants no automated-query permission.
"""
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class ProviderCapability:
    key:str
    public_search:str
    service_type:Literal['manual_only','written_approval_required','user_supplied_file']
    can_server_query:bool=False
    permission_version:str='not_granted'
    permitted_retention:bool=False
    charge_authorised:bool=False

PROVIDERS={
 'freebmd_public':ProviderCapability('freebmd_public','https://www.freebmd.org.uk/search','manual_only'),
 'freecen_public':ProviderCapability('freecen_public','https://www.freecen.org.uk/','manual_only'),
 'freereg_public':ProviderCapability('freereg_public','https://www.freereg.org.uk/','manual_only'),
 'freeukgenealogy_bulk':ProviderCapability('freeukgenealogy_bulk','https://www.freeukgenealogy.org.uk/bulk-data-for-research','written_approval_required'),
 'national_archives_discovery_api':ProviderCapability('national_archives_discovery_api','https://www.nationalarchives.gov.uk/','written_approval_required'),
 'user_owned_export':ProviderCapability('user_owned_export','','user_supplied_file'),
}

def assess(provider:str,action:str,permission_id:str='',authorised_cost_cents:int=0)->dict:
    p=PROVIDERS.get(provider)
    if not p:
        return {'permitted':False,'reason':'Provider not registered; do not attempt network access.'}
    if action=='inspect_local_file' and provider=='user_owned_export':
        return {'permitted':True,'reason':'Local file review only; separate rights attestation required before import.'}
    return {'permitted':False,'reason':f'No automated provider action authorised for {provider}. '
            'A separate written permission, purpose, retention rule, account and budget approval are required.',
            'public_search_mode':p.service_type,'provider_queries_executed':0}
