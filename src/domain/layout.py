from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


SUPPORTED_COLUMNS = {
    "Date",
    "Provider",
    "Physician",
    "Facility",
    "Reason",
    "Summary",
    "Ref",
}


@dataclass
class LayoutSpec:
    columns: List[str] = field(
        default_factory=lambda: ["Date", "Provider", "Reason", "Ref"]
    )
    sort_by: List[Tuple[str, str]] = field(default_factory=lambda: [("Date", "asc")])
    group_by: Optional[str] = None
    unknown_columns: List[str] = field(default_factory=list)


def parse_layout_dsl(dsl: Optional[str]) -> LayoutSpec:
    if not dsl:
        return LayoutSpec()

    parts = [p.strip() for p in dsl.split(";") if p.strip()]
    columns: List[str] = []
    sort_by: List[Tuple[str, str]] = []
    group_by: Optional[str] = None
    unknown: List[str] = []

    for part in parts:
        if part.startswith("columns="):
            _, value = part.split("=", 1)
            requested = [c.strip() for c in value.split("|") if c.strip()]
            for col in requested:
                if col in SUPPORTED_COLUMNS:
                    columns.append(col)
                else:
                    unknown.append(col)
        elif part.startswith("sort="):
            _, value = part.split("=", 1)
            for token in value.split(","):
                token = token.strip()
                if not token:
                    continue
                if " " in token:
                    key, direction = token.split(" ", 1)
                    direction = direction.lower().strip()
                    if direction not in {"asc", "desc"}:
                        direction = "asc"
                else:
                    key, direction = token, "asc"
                sort_by.append((key.strip(), direction))
        elif part.startswith("group_by="):
            _, value = part.split("=", 1)
            group_by = value.strip() or None

    spec = LayoutSpec()
    spec.columns = columns or spec.columns
    spec.sort_by = sort_by or spec.sort_by
    spec.group_by = group_by
    spec.unknown_columns = unknown
    return spec
