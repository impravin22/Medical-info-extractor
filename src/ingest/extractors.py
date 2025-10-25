from __future__ import annotations

from datetime import date
from typing import List

from src.domain.schema import Claimant, Event, Report
from src.utils.dates import parse_date_strict
from src.llm.reason_summarizer import (
    extract_claimant_with_llm,
    extract_impairments_with_llm,
    extract_events_with_llm,
)


def build_report(pages: List[str], llm_model) -> Report:
    """Build report from PDF pages using LLM."""
    claimant = extract_claimant_header(pages, llm_model)
    impairments = extract_impairments(pages, llm_model)
    events = extract_events(pages, llm_model)

    # Calculate ages
    age_at_aod = None
    current_age = None
    if claimant.dob and claimant.aod:
        age_at_aod = claimant.aod.year - claimant.dob.year
        if (claimant.aod.month, claimant.aod.day) < (
            claimant.dob.month,
            claimant.dob.day,
        ):
            age_at_aod -= 1

    if claimant.dob:
        today = date.today()
        current_age = today.year - claimant.dob.year
        if (today.month, today.day) < (claimant.dob.month, claimant.dob.day):
            current_age -= 1

    return Report(
        claimant=claimant,
        alleged_impairments=impairments,
        events=events,
        age_at_aod=age_at_aod,
        current_age=current_age,
    )


def extract_claimant_header(pages: List[str], model) -> Claimant:
    """Extract claimant from first few pages."""
    text = "\n".join(
        pages[:12]
    )  # Look at many pages to find all fields (DOB on pg 4, education on pg 9)
    result = extract_claimant_with_llm(model, text)

    # Parse dates from various field names
    dob = None
    aod = None
    dli = None

    for key in ["dob", "date_of_birth", "DOB", "Date of Birth"]:
        if result.get(key):
            try:
                dob = parse_date_strict(result[key])
                break
            except:
                pass

    for key in ["aod", "alleged_onset", "AOD", "Alleged onset"]:
        if result.get(key):
            try:
                aod = parse_date_strict(result[key])
                break
            except:
                pass

    for key in ["dli", "date_last_insured", "DLI", "Last Insured"]:
        if result.get(key):
            try:
                dli = parse_date_strict(result[key])
                break
            except:
                pass

    # Get other fields
    name = (
        result.get("name")
        or result.get("claimant_name")
        or result.get("Claimant")
        or ""
    )
    ssn = result.get("ssn") or result.get("SSN") or ""
    title = result.get("title") or result.get("Title") or result.get("claim_type") or ""
    grade = (
        result.get("last_grade_completed")
        or result.get("education")
        or result.get("Last Grade Completed")
        or ""
    )
    special_ed = (
        result.get("attended_special_ed")
        or result.get("special_education")
        or result.get("Special Ed")
        or False
    )

    if isinstance(special_ed, str):
        special_ed = special_ed.lower() in ["yes", "true", "y"]

    return Claimant(
        name=name,
        ssn=ssn,
        dob=dob,
        aod=aod,
        dli=dli,
        title=title,
        last_grade_completed=grade,
        attended_special_ed=special_ed,
    )


def extract_impairments(pages: List[str], model) -> List[str]:
    """Extract impairments from PDF."""
    text = "\n".join(pages[:12])  # Look at more pages to find impairments section
    return extract_impairments_with_llm(model, text)


def extract_events(pages: List[str], model) -> List[Event]:
    """Extract medical events from pages."""
    events = []

    # Process pages
    for page_idx, page in enumerate(pages[:15], start=1):
        if len(page.strip()) < 50:
            continue

        results = extract_events_with_llm(model, page, page_idx)

        for item in results:
            try:
                if not item.get("date"):
                    continue

                evt_date = parse_date_strict(item["date"])

                if 2020 <= evt_date.year <= 2024:
                    events.append(
                        Event(
                            date=evt_date,
                            provider=item.get("provider", "Unknown"),
                            reason_raw=item.get("reason", ""),
                            ref_page=item.get("ref_page", page_idx),
                            facility=item.get("provider", "Unknown"),
                        )
                    )
            except:
                continue

    # Remove duplicates and sort
    seen = set()
    unique = []
    for evt in events:
        key = (evt.date, evt.provider)
        if key not in seen:
            seen.add(key)
            unique.append(evt)

    return sorted(unique, key=lambda e: e.date)[:15]
