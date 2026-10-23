"""Strict typed requests for versioned, provisional family graph changes."""
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator

Relation = Literal['biological_parent', 'adoptive_parent', 'step_parent',
                   'spouse', 'sibling', 'same_person', 'household_association']

class EdgeIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    edge_key: str = Field(min_length=1, max_length=100)
    from_observation_id: UUID
    to_observation_id: UUID
    relationship_type: Relation
    supporting_observation_ids: list[UUID] = Field(default_factory=list, max_length=50)
    contradicting_observation_ids: list[UUID] = Field(default_factory=list, max_length=50)
    reasoning: str = Field(min_length=10, max_length=4000)

    @model_validator(mode='after')
    def not_self(self):
        if self.from_observation_id == self.to_observation_id:
            raise ValueError('Self relationship is invalid')
        if len(set(self.supporting_observation_ids)) != len(self.supporting_observation_ids):
            raise ValueError('Duplicate supporting evidence')
        if len(set(self.contradicting_observation_ids)) != len(self.contradicting_observation_ids):
            raise ValueError('Duplicate contradicting evidence')
        if set(self.supporting_observation_ids) & set(self.contradicting_observation_ids):
            raise ValueError('Same observation cannot support and contradict one assertion')
        return self

class RevisionIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_set_version: int = Field(ge=1)
    rationale: str = Field(min_length=10, max_length=5000)
    edges: list[EdgeIn] = Field(default_factory=list, max_length=75)

    @model_validator(mode='after')
    def unique_keys(self):
        keys = [e.edge_key for e in self.edges]
        if len(keys) != len(set(keys)):
            raise ValueError('Duplicate edge keys')
        return self

class BranchReviewIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    decision: Literal['research_supported','rejected','deferred']
    reason: str = Field(min_length=10, max_length=5000)
    expected_set_version: int = Field(ge=1)
