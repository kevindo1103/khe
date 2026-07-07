"""Pydantic schemas for tenant profile endpoints (#155, #495)."""
from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator


class ComplianceProfileOut(BaseModel):
    legal_form: str | None = None
    has_employees: bool | None = None
    vat_period: str | None = None        # "month" | "quarter"
    fiscal_year_start: date | None = None
    model_config = ConfigDict(from_attributes=True)


class ComplianceProfileIn(BaseModel):
    legal_form: str | None = None
    has_employees: bool | None = None
    vat_period: str | None = None
    fiscal_year_start: date | None = None

    @field_validator("vat_period")
    @classmethod
    def _vat_period_enum(cls, v: str | None) -> str | None:
        if v is not None and v not in ("month", "quarter"):
            raise ValueError("vat_period must be 'month' or 'quarter'")
        return v
