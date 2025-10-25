from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

from src.domain.layout import LayoutSpec
from src.domain.schema import Event, Report


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|")


def render_report_to_markdown(
    report: Report, out_path: str, layout: LayoutSpec
) -> None:
    lines: List[str] = []
    h = report.claimant
    lines.append("# Medical Summary")
    lines.append("")

    # Line 1: RE, SSN, Title, DLI - use extracted data only
    title_part = f"Title: {h.title}" if h.title else ""
    dli_part = f"DLI: {h.dli.strftime('%m/%d/%Y')}" if h.dli else ""
    line1_parts = [f"RE: {h.name}", f"SSN: {h.ssn}", title_part, dli_part]
    lines.append("  ".join(p for p in line1_parts if p))

    # Line 2: AOD, DOB, Ages - compute from extracted data only
    aod = h.aod.strftime("%m/%d/%Y") if h.aod else ""
    dob = h.dob.strftime("%m/%d/%Y") if h.dob else ""

    age_at_aod = ""
    current_age = ""

    if h.aod and h.dob:
        age_at_aod = str(
            (h.aod.year - h.dob.year)
            - (1 if (h.aod.month, h.aod.day) < (h.dob.month, h.dob.day) else 0)
        )

    if h.dob:
        today = datetime.today().date()
        current_age = str(
            (today.year - h.dob.year)
            - (1 if (today.month, today.day) < (h.dob.month, h.dob.day) else 0)
        )

    lines.append(
        f"AOD: {aod}  Date of Birth: {dob}  Age at AOD: {age_at_aod}  Current Age: {current_age}"
    )

    # Line 3: Education - use extracted data only
    if h.last_grade_completed or h.attended_special_ed is not None:
        grade = h.last_grade_completed or ""
        special_ed = ""
        if h.attended_special_ed is True:
            special_ed = "Yes"
        elif h.attended_special_ed is False:
            special_ed = "No"

        lines.append(
            f"Last Grade Completed: {grade}  Attended Special Ed Classes: {special_ed}"
        )

    lines.append("")
    lines.append(f"Last Updated: {datetime.today().strftime('%A, %B %d, %Y')}")
    lines.append("")

    if report.alleged_impairments:
        lines.append("## Alleged impairments")
        for imp in report.alleged_impairments:
            lines.append(f"- {_md_escape(imp)}")
        lines.append("")

    # Table
    lines.append("| " + " | ".join(layout.columns) + " |")
    lines.append("| " + " | ".join(["---"] * len(layout.columns)) + " |")
    for evt in report.events:
        row = []
        for col in layout.columns:
            if col == "Date":
                row.append(evt.date.strftime("%m/%d/%Y"))
            elif col == "Provider":
                row.append(_md_escape(evt.provider))
            elif col == "Physician":
                row.append(_md_escape(evt.physician or ""))
            elif col == "Facility":
                row.append(_md_escape(evt.facility or ""))
            elif col == "Reason":
                row.append(_md_escape(evt.reason_raw))
            elif col == "Summary":
                row.append(_md_escape(evt.reason_summary or evt.reason_raw))
            elif col == "Ref":
                row.append(f"Pg {evt.ref_page}")
            else:
                row.append("")
        lines.append("| " + " | ".join(row) + " |")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
