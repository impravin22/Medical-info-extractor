from __future__ import annotations

from datetime import date
from typing import List, Literal, Any

from src.domain.schema import Claimant, Event, Report
from src.utils.dates import parse_date_strict
from src.llm.reason_summarizer import (
    extract_claimant_with_llm,
    extract_impairments_with_llm,
    extract_events_with_llm,
)
from src.llm.nebius_llm import (
    extract_claimant_with_llm_nebius,
    extract_impairments_with_llm_nebius,
    extract_events_with_llm_nebius,
)


def build_report(
    pages: List[str], llm_model: Any, backend: Literal["gemini", "nebius"] = "nebius", model_name: str = "NousResearch/Hermes-4-405B"
) -> Report:
    """Build report from PDF pages using LLM."""
    claimant = extract_claimant_header(pages, llm_model, backend, model_name)
    impairments = extract_impairments(pages, llm_model, backend, model_name)
    events = extract_events(pages, llm_model, backend, model_name)

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


def extract_claimant_header(
    pages: List[str], model: Any, backend: Literal["gemini", "nebius"] = "nebius", model_name: str = "NousResearch/Hermes-4-405B"
) -> Claimant:
    """Extract claimant from first few pages."""
    text = "\n".join(
        pages[:12]
    )  # Look at many pages to find all fields (DOB on pg 4, education on pg 9)
    
    if backend == "nebius":
        result = extract_claimant_with_llm_nebius(model, model_name, text)
    else:
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


def extract_impairments(
    pages: List[str], model: Any, backend: Literal["gemini", "nebius"] = "nebius", model_name: str = "NousResearch/Hermes-4-405B"
) -> List[str]:
    """Extract impairments from PDF."""
    text = "\n".join(pages[:12])  # Look at more pages to find impairments section
    
    if backend == "nebius":
        return extract_impairments_with_llm_nebius(model, model_name, text)
    else:
        return extract_impairments_with_llm(model, text)


def extract_events(
    pages: List[str], model: Any, backend: Literal["gemini", "nebius"] = "nebius", model_name: str = "NousResearch/Hermes-4-405B"
) -> List[Event]:
    """Extract medical events from pages."""
    events = []

    # Process ALL pages to capture all medical events
    print(f"Processing {len(pages)} pages for medical events...")
    for page_idx, page in enumerate(pages, start=1):
        # Skip only truly empty pages (very low threshold to ensure completeness)
        if len(page.strip()) < 10:
            continue
        
        # Progress indicator every 10 pages
        if page_idx % 10 == 0:
            print(f"  Processed {page_idx}/{len(pages)} pages...")

        if backend == "nebius":
            results = extract_events_with_llm_nebius(model, model_name, page, page_idx)
        else:
            results = extract_events_with_llm(model, page, page_idx)

        for item in results:
            try:
                if not item.get("date"):
                    continue

                evt_date = parse_date_strict(item["date"])

                # Accept all valid dates (no year filtering to ensure completeness)
                # Valid medical records can span decades
                if 1900 <= evt_date.year <= 2030:
                    events.append(
                        Event(
                            date=evt_date,
                            provider=item.get("provider", "Unknown"),
                            reason_raw=item.get("reason", ""),
                            ref_page=item.get("ref_page", page_idx),
                            facility=item.get("provider", "Unknown"),
                        )
                    )
            except Exception as e:
                # Log parsing errors but continue processing
                print(f"  Warning: Could not parse event on page {page_idx}: {e}")
                continue

    # Remove duplicates and sort - use date + provider + reason for more precise deduplication
    seen = set()
    unique = []
    for evt in events:
        # Use first 50 chars of reason to allow similar but not identical entries
        reason_key = evt.reason_raw[:50] if evt.reason_raw else ""
        key = (evt.date, evt.provider, reason_key)
        if key not in seen:
            seen.add(key)
            unique.append(evt)

    sorted_events = sorted(unique, key=lambda e: e.date)
    print(f"Extracted {len(sorted_events)} unique medical events from {len(pages)} pages")
    print(f"Date range: {sorted_events[0].date if sorted_events else 'N/A'} to {sorted_events[-1].date if sorted_events else 'N/A'}")
    return sorted_events  # Return ALL events, no limit
