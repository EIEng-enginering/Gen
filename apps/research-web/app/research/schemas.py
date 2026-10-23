"""Explicit input validation; never treat model-asserted sources as verified."""
from datetime import date
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator

AccessMethod=Literal['manual','user_import','approved_api','licensed_dataset']


class DocumentIn(BaseModel):
    provider: str = Field(min_length=1,max_length=120)
    provider_record_id: str = Field(min_length=1,max_length=250)
    title: str = Field(min_length=1,max_length=300)
    reference: str = Field(min_length=1,max_length=500)
    original_url: str|None=None
    access_method: AccessMethod='user_import'
    licence: str = Field(min_length=1,max_length=200)
    rights_note: str=''
    origin_group: str=Field(min_length=1,max_length=250)
    document_kind: str='undetermined'
    source_class: str='undetermined'
    metadata_json: dict[str,Any] = Field(default_factory=dict)

    @field_validator('original_url')
    @classmethod
    def validate_url(cls,value):
        if value and not value.lower().startswith(('https://','http://')):
            raise ValueError('Only http or https original URLs are permitted')
        return value


class ObservationIn(BaseModel):
    observation_key: str=Field(min_length=1,max_length=100)
    event_type: str=Field(min_length=1,max_length=50)
    person_name_verbatim: str=Field(min_length=1,max_length=300)
    surname_verbatim: str=''
    given_names_verbatim: str=''
    event_date_verbatim: str=''
    earliest_iso: date|None=None
    latest_iso: date|None=None
    location_verbatim: str=''
    historical_place_ref: str|None=None
    occupation_verbatim: str=''
    transcription_verbatim: str=''
    additional_json: dict[str,Any]=Field(default_factory=dict)

    @model_validator(mode='after')
    def bounds(self):
        if self.earliest_iso and self.latest_iso and self.earliest_iso>self.latest_iso:
            raise ValueError('earliest_iso must not exceed latest_iso')
        return self


class RevisionIn(BaseModel):
    text: str=Field(min_length=1,max_length=200000)
    reason: str=Field(min_length=3,max_length=500)
    model_id: str|None=None


class HypothesisOptionIn(BaseModel):
    option_key: str=Field(min_length=1,max_length=100)
    description: str=Field(min_length=1,max_length=600)
    subject_observation_id: UUID|None=None
    related_observation_id: UUID|None=None
    is_unknown: bool=False
    calibrated_probability: float|None=Field(default=None,ge=0,le=1)
    model_id: str|None=None
    evidence_observation_ids: list[UUID]=Field(default_factory=list)
    reasoning: str=''


class HypothesisIn(BaseModel):
    title: str=Field(min_length=1,max_length=250)
    subject_description: str=Field(min_length=1,max_length=500)
    relation_type: str=Field(min_length=1,max_length=50)
    options: list[HypothesisOptionIn]=Field(min_length=2,max_length=30)

    @model_validator(mode='after')
    def check_options(self):
        keys=[x.option_key for x in self.options]
        if len(keys)!=len(set(keys)):
            raise ValueError('Duplicate option keys')
        if sum(x.is_unknown for x in self.options)!=1:
            raise ValueError('Exactly one unknown/other alternative is required')
        probs=[x.calibrated_probability for x in self.options]
        if any(p is not None for p in probs):
            # A string called 'model_id' is not evidence of independent model
            # calibration. Never accept user- or LLM-authored confidence numbers.
            raise ValueError('Numerical relationship probabilities are unavailable until a verified calibration registry is implemented')
        return self


class JobIn(BaseModel):
    mode: Literal['autonomous','guided','conventional']='guided'
    objective: str=Field(min_length=1,max_length=500)
    cost_limit_usd: float=Field(default=0,ge=0,le=10000)


class JobUpdate(BaseModel):
    action: Literal['pause','resume','cancel']


class DecisionIn(BaseModel):
    decision: Literal['accept_as_research','reject','defer']
    reason: str=Field(min_length=3,max_length=2000)
