import subprocess
from pathlib import Path

import pytest


def test_cli_end_to_end(tmp_path: Path):
    """Test end-to-end CLI execution with open source models."""
    project_root = Path(__file__).resolve().parents[1]

    pdf_path = project_root / "Medical File.pdf"
    template_path = project_root / "Medical Summary.docx"
    out_path = tmp_path / "Medical_Summary.docx"

    assert pdf_path.exists(), "Medical File.pdf missing"
    assert template_path.exists(), "Medical Summary.docx missing"

    cmd = [
        "uv",
        "run",
        "python",
        "-m",
        "src.app.cli",
        "--pdf",
        str(pdf_path),
        "--template",
        str(template_path),
        "--out",
        str(out_path),
    ]
    subprocess.check_call(cmd, cwd=project_root)
    assert out_path.exists(), "Output DOCX not created"
