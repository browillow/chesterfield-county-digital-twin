"""Executable first-wave contracts. Numeric strings preserve exact source precision."""

from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Bootstrap(Contract):
    api_version: Literal["v1"] = "v1"
    active_release_id: str | None = None
    has_baseline: bool = False
    capabilities: list[str] = Field(default_factory=list)


class SessionRequest(Contract):
    secret: str = Field(min_length=32, max_length=128)


class SessionResponse(Contract):
    csrf_token: str


class Measurement(Contract):
    claim_class: Literal["reported", "calculated", "inference", "hypothesis", "scenario"]
    value_state: Literal["observed", "suppressed", "unavailable", "not_applicable"]
    value: str | None = None
    reason: str | None = None
    unit: str = Field(min_length=1)
    universe: str = Field(min_length=1)
    geography_id: str = Field(min_length=1)
    geography_vintage: str = Field(min_length=1)
    reference_period: str = Field(min_length=1)
    synthetic: bool = False

    @model_validator(mode="after")
    def validate_value(self):
        if self.value_state == "observed":
            try:
                if self.value is None or not Decimal(self.value).is_finite():
                    raise ValueError("Observed measurements require a finite numeric string")
            except InvalidOperation as exc:
                raise ValueError("Observed measurements require a finite numeric string") from exc
        elif self.value is not None or not self.reason or not self.reason.strip():
            raise ValueError("Non-observed measurements require null value and a reason")
        return self
