from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class Claimant(BaseModel):
    name: str
    ssn: str
    dob: Optional[date] = None
    aod: Optional[date] = None
    dli: Optional[date] = None
    title: Optional[str] = None
    last_grade_completed: Optional[str] = None
    attended_special_ed: Optional[bool] = None


class Event(BaseModel):
    date: date
    provider: str
    reason_raw: str
    reason_summary: Optional[str] = None
    ref_page: int
    physician: Optional[str] = None
    facility: Optional[str] = None


class Report(BaseModel):
    claimant: Claimant
    alleged_impairments: List[str] = Field(default_factory=list)
    events: List[Event] = Field(default_factory=list)
    age_at_aod: Optional[int] = None
    current_age: Optional[int] = None
