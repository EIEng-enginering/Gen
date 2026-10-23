"""WP-006: human-controlled, non-executing Gramps change proposals."""
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator


class EndpointBinding(BaseModel):
    model_config = ConfigDict(extra='forbid')
    edge_key: str = Field(min_length=1, max_length=100)
    from_handle: str = Field(min_length=1, max_length=128, pattern=r'^[A-Za-z0-9_.:-]+$')
    to_handle: str = Field(min_length=1, max_length=128, pattern=r'^[A-Za-z0-9_.:-]+$')

    @model_validator(mode='after')
    def distinct(self):
        if self.from_handle == self.to_handle:
            raise ValueError('Two distinct observed people require distinct Gramps handles')
        return self


class PlanPreviewIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    hypothesis_set_id: UUID
    option_key: str = Field(min_length=1, max_length=100)
    expected_set_version: int = Field(ge=1)
    expected_revision_id: UUID
    bindings: list[EndpointBinding] = Field(min_length=1, max_length=75)

    @model_validator(mode='after')
    def unique_edges(self):
        names = [b.edge_key for b in self.bindings]
        if len(names) != len(set(names)):
            raise ValueError('Every branch edge requires exactly one binding')
        return self


class PlanCreateIn(PlanPreviewIn):
    idempotency_key: str = Field(min_length=12, max_length=128, pattern=r'^[A-Za-z0-9_-]+$')
    expected_preview_digest: str = Field(min_length=64, max_length=64, pattern=r'^[0-9a-f]{64}$')
    operator_note: str = Field(min_length=12, max_length=4000)


class PlanApprovalIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_set_version: int = Field(ge=1)
    expected_preview_digest: str = Field(min_length=64, max_length=64, pattern=r'^[0-9a-f]{64}$')
    confirmation: str = Field(min_length=20, max_length=100)
    rationale: str = Field(min_length=12, max_length=4000)
    decision: Literal['approve_for_future_validation','reject']
