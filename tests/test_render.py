from pathlib import Path

from src.domain.layout import parse_layout_dsl
from src.domain.schema import Claimant, Event, Report
from src.render.docx_writer import render_report_to_docx
from datetime import date


def test_render_basic(tmp_path: Path):
    report = Report(
        claimant=Claimant(
            name="John Doe",
            ssn="***-**-1234",
            dob=date(1980, 1, 2),
            aod=date(2020, 1, 1),
        ),
        events=[
            Event(
                date=date(2020, 1, 2), provider="Clinic", reason_raw="Visit", ref_page=1
            ),
        ],
    )
    out = tmp_path / "out.docx"
    spec = parse_layout_dsl(None)
    render_report_to_docx(report, out, spec)
    assert out.exists()
