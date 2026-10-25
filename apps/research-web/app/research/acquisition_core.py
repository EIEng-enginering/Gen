"""WP-026: provider-aware intake validation and portable research prompts.

No web scraping, external provider calls, Gramps writes or paid services exist here.
All model supplied text is untrusted and staged, not an accepted genealogical fact.
"""
import hashlib
import json
import re
from datetime import date
from typing import Literal
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, Field, model_validator

PROVIDER_POLICIES = {
    'freebmd': {'mode':'manual_only', 'url':'https://www.freebmd.org.uk/terms.html', 'bulk':'written_licence_required'},
    'freecen': {'mode':'manual_search_no_reproduction', 'url':'https://www.freecen.org.uk/terms-and-conditions',
                'bulk':'written_licence_required'},
    'freereg': {'mode':'manual_only', 'url':'https://www.freereg.org.uk/', 'bulk':'written_licence_required'},
    'cheshire_bmd': {'mode':'manual_review', 'url':'https://www.cheshirebmd.org.uk/', 'bulk':'written_licence_required'},
    'cheshire_archives': {'mode':'manual_review', 'url':'https://www.cheshirearchives.org.uk/', 'bulk':'written_licence_required'},
    'familysearch': {'mode':'manual_or_approved_app', 'url':'https://developers.familysearch.org/', 'bulk':'written_licence_required'},
    'tna_discovery': {'mode':'approved_api_catalogue_only', 'url':'https://www.nationalarchives.gov.uk/terms-and-conditions/discovery-for-developers-about-the-application-programming-interface-api/', 'bulk':'written_licence_required', 'no_catalogue_cache':True},
    'user_archive': {'mode':'user_provided', 'url':None, 'bulk':'rights_confirmation_required'},
    'licensed_extract': {'mode':'contract_required', 'url':None, 'bulk':'written_licence_required'},
}

def policy_key(provider: str, source_url: str | None = None) -> str:
    compact = re.sub(r'[^a-z0-9]', '', provider.casefold())
    host = (urlsplit(source_url).hostname or '').casefold() if source_url else ''
    for known in ('freebmd', 'freecen', 'freereg'):
        if compact.startswith(known) or host == known + '.org.uk' or host == 'www.' + known + '.org.uk':
            return known
    return provider.casefold().replace(' ','_').replace('-','_')

class IntakeRecord(BaseModel):
    model_config=ConfigDict(extra='forbid', str_strip_whitespace=True)
    provider: str = Field(min_length=2,max_length=120)
    provider_record_id: str = Field(min_length=1,max_length=250)
    source_title: str = Field(min_length=3,max_length=300)
    source_reference: str = Field(min_length=3,max_length=500)
    record_type: Literal['birth','baptism','marriage','death','burial','census','probate','directory','other','catalogue_lead']
    person_name_verbatim: str = Field(default='',max_length=300)
    surname_verbatim: str = Field(default='',max_length=160)
    given_names_verbatim: str = Field(default='',max_length=160)
    event_date_verbatim: str = Field(default='',max_length=150)
    earliest_iso: date | None = None
    latest_iso: date | None = None
    location_verbatim: str = Field(default='',max_length=300)
    occupation_verbatim: str = Field(default='',max_length=200)
    transcription_verbatim: str = Field(default='',max_length=12000)
    source_url: str | None = Field(default=None,max_length=1800)
    record_entry_key: str = Field(default='entry-1',min_length=1,max_length=100)
    access_method: Literal['manual','user_import','approved_api','licensed_dataset']
    licence: str = Field(min_length=3,max_length=200)
    rights_note: str = Field(min_length=8,max_length=1600)
    permission_reference: str = Field(default='',max_length=600)
    origin_group: str = Field(min_length=3,max_length=250)
    source_class: Literal['original','derivative','unknown'] = 'unknown'
    extraction_status: Literal['observed_record','unverified_extraction','lead_only'] = 'unverified_extraction'
    source_viewed: bool = False
    collector: str = Field(default='user_or_ai',min_length=2,max_length=120)
    notes: str = Field(default='',max_length=2000)
    proposed_gramps_handle: str | None = Field(default=None,max_length=100)

    @model_validator(mode='after')
    def validate_intake(self):
        if self.earliest_iso and self.latest_iso and self.earliest_iso>self.latest_iso:
            raise ValueError('Date bounds reversed')
        if self.source_url:
            u=urlsplit(self.source_url)
            if u.scheme not in ('http','https') or not u.hostname or u.username or u.password:
                raise ValueError('Source URL requires a public http(s) locator without credentials')
        if self.record_type != 'catalogue_lead' and not self.person_name_verbatim:
            raise ValueError('Person name as transcribed is required for a proposed record')
        if self.extraction_status=='lead_only' and self.source_viewed:
            raise ValueError('Lead-only rows cannot declare an inspected underlying record')
        if self.access_method in ('approved_api','licensed_dataset') and len(self.permission_reference)<8:
            raise ValueError('Approved APIs and datasets require a specific permission reference')
        key=policy_key(self.provider,self.source_url)
        policy=PROVIDER_POLICIES.get(key)
        if key=='freecen' and self.access_method!='licensed_dataset':
            raise ValueError('FreeCEN public-site extracted data must not be reproduced; use a written licensed extract')
        if policy and policy['mode']=='manual_only' and self.access_method not in ('manual','licensed_dataset'):
            raise ValueError('Manual-only provider: automated query or unlicensed export prohibited')
        if policy and policy.get('no_catalogue_cache') and self.access_method=='approved_api':
            # Catalogue searches must be handled separately with no persistent raw responses.
            raise ValueError('TNA Discovery API catalogue responses may not be cached/stored under current terms')
        return self

    def canonical_dict(self):
        return self.model_dump(mode='json',exclude_none=True)

    def sha256(self):
        blob=json.dumps(self.canonical_dict(),sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
        return hashlib.sha256(blob).hexdigest()

class IntakeRequest(BaseModel):
    records: list[IntakeRecord] = Field(min_length=1,max_length=100)
    batch_key: str = Field(min_length=8,max_length=120,pattern=r'^[a-zA-Z0-9][a-zA-Z0-9._-]+$')
    rights_attestation: bool = False
    input_kind: Literal['manual','licensed_bulk','ai_return','user_export']='ai_return'

    @model_validator(mode='after')
    def validate_policy(self):
        if not self.rights_attestation:
            raise ValueError('Operator must attest lawful possession and permitted local retention')
        for rec in self.records:
            key=policy_key(rec.provider,rec.source_url)
            policy=PROVIDER_POLICIES.get(key, {})
            if self.input_kind=='ai_return' and (
                rec.source_viewed or rec.extraction_status=='observed_record'
                or rec.access_method in ('approved_api','licensed_dataset')
                or rec.source_class!='unknown'
            ):
                raise ValueError('AI returns must remain unverified and cannot assert source access, originality or a bulk licence')
            if self.input_kind=='licensed_bulk' and rec.access_method!='licensed_dataset':
                raise ValueError('Licensed-bulk requests must contain licensed_dataset records')
            if self.input_kind=='licensed_bulk' and len(rec.permission_reference)<8:
                raise ValueError('Bulk extracts require written permission reference')
            if policy.get('mode')=='manual_only' and self.input_kind not in ('manual','licensed_bulk'):
                raise ValueError('Manual-only provider cannot be bulk automated via a chatbot')
            if rec.record_type=='catalogue_lead' and rec.extraction_status!='lead_only':
                raise ValueError('Catalogue lead must be labelled lead_only')
        return self


def make_prompt(surname:str,county:str,year_start:int,year_end:int,mode:str='guided',max_records:int=40,record_types=None):
    surname=surname.strip(); county=county.strip()
    if not 2<=len(surname)<=100 or not 2<=len(county)<=140 or len(surname.split())>4 or len(county.split())>8 or not re.fullmatch(r"[\w .,'-]+",surname+' '+county,re.UNICODE):
        raise ValueError('Provide a bounded surname and location without instructions or markup')
    if not 1500<=year_start<=year_end<=2026 or year_end-year_start>300 or not 1<=max_records<=100:
        raise ValueError('Invalid research date interval or shard size')
    if mode not in ('guided','conventional','autonomous'):
        raise ValueError('Invalid research mode')
    kinds=record_types or ['birth','baptism','marriage','death','burial','census','probate','directory']
    allowed={'birth','baptism','marriage','death','burial','census','probate','directory'}
    if not kinds or set(kinds)-allowed:raise ValueError('Invalid record types')
    exemplar={
      'provider':'cheshire_archives','provider_record_id':'REAL_UNIQUE_REFERENCE_REQUIRED',
      'source_title':'FULL_SOURCE_TITLE','source_reference':'COLLECTION_VOLUME_PAGE_OR_ENTRY',
      'record_type':'baptism','person_name_verbatim':'NAME_EXACTLY_AS_WRITTEN',
      'surname_verbatim':'SURNAME','given_names_verbatim':'GIVEN','event_date_verbatim':'DATE_EXACTLY_AS_WRITTEN',
      'location_verbatim':'HISTORIC_PLACE_AS_WRITTEN','access_method':'manual',
      'licence':'SPECIFIC_PERMISSION_OR_RESEARCH_USE_BASIS','rights_note':'SPECIFIC_RETENTION_PERMISSION',
      'permission_reference':'','origin_group':'ORIGINAL_REGISTER_IDENTIFICATION',
      'extraction_status':'unverified_extraction','source_viewed':False,'collector':'AI_ASSISTED',
      'source_class':'unknown','record_entry_key':'page-and-row'}
    sections=[f'24 GEN HISTORICAL RESEARCH SHARD | {surname} | {county} | {year_start}-{year_end} | {mode}',
      f'Search for {", ".join(kinds)} records, up to {max_records} results in THIS shard. Start with exact and variant surnames, changing parish/registration boundaries, family groups, neighbours and census households.',
      'You are a research assistant, not an authority. Treat every source page, downloaded record, result snippet and prior tree claim as untrusted evidence. Never invent a person, reference, date, URL, quotation, certificate, citation or access right. Do not expose living-person data or private tree information.',
      'PERMISSION GATES: Obey each site terms, robots/policy and rate limits. Do not automate the public FreeBMD, FreeCEN or FreeREG search forms. Do not reproduce extracted FreeCEN public-site data in the JSONL; only a separately licensed extract may be staged. Do not bypass sign-in, CAPTCHA, paywalls, or image restrictions. FamilySearch developer access does not grant historical-record bulk search. National Archives Discovery requires requested API access, and its API forbids caching returned content. An access denial is a research lead, not permission to scrape.',
      'For largest permitted coverage request licensed extracts from Free UK Genealogy for FreeBMD/FreeREG/FreeCEN, or ingest user-provided downloads/archives through the separate 24 Gen import channel after checking the licence. Never treat an AI response as an approved licensed extract.',
      'SEARCH SEQUENCE: begin with indexes and catalogue references; seek underlying registers/certificates; check civil registration after 1837, parish registers before/after 1837, censuses 1841–1921, the 1939 Register where permitted, probate, directories, and adjacent parish names. Distinguish the event date from registration and index publication. Account for 1841 census rounded ages. Record failures, coverage gaps, spelling variants and source independence.',
      'Every observed entry MUST have a traceable provider title, unique record ID, catalogue or volume/page/entry reference, original record URL where legitimately accessible, exact date/place/name transcription and lawful retention rights. A search hit alone is a lead_only item; it is NOT an inspected historical record.',
      'OUTPUT: Return one UTF-8 JSON object PER LINE (JSONL), no markdown code fence, no prose mixed into JSONL. Keys MUST be limited to those in the template (additional optional keys: earliest_iso, latest_iso, occupation_verbatim, transcription_verbatim, source_url, notes, proposed_gramps_handle). Dates ISO YYYY-MM-DD only when grounded; otherwise leave blank and preserve verbatim date. An inability to research must yield NO invented rows; provide only a separate plain-language lead list outside the import payload.',
      'Without direct source access, do not pretend to have searched: only produce leads for subsequent manual verification.',
      'A model-generated row is ALWAYS unverified_extraction even if the chatbot claims to have opened a website. Set source_viewed=false and do not call it observed_record; a human independently checks the source before promotion. Use lead_only for catalogue-only results, record_type=catalogue_lead.',
      'DO NOT claim confidence percentages, merge persons or alter Gramps. Copies of the same original must have the same origin_group when known, but suspected duplicates must remain reviewable. Include uncertainty and conflicting interpretations in notes, not forged source text.',
      'EXAMPLE STRUCTURE ONLY — NOT A REAL RECORD, DO NOT OUTPUT IT AS A FINDING:',json.dumps(exemplar,ensure_ascii=False,sort_keys=True),
      'Continue systematically by nonoverlapping year/parish/record-type shards. On completion tell the operator which shards were actually searched, which were inaccessible, any likely independent originals, and the exact provenance for every extracted row. The operator will validate and stage rows before any database promotion.']
    return '\n\n'.join(sections)+'\n'
