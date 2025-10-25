"""Integration tests for the complete medical summary pipeline."""

from __future__ import annotations

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from src.app.cli import main
from src.ingest.pdf_reader import extract_text_by_page
from src.domain.schema import Report


class TestIntegration:
    """Integration tests for the complete pipeline."""

    @pytest.fixture
    def sample_pdf_path(self):
        """Return path to sample PDF if it exists."""
        pdf_path = Path("Medical File.pdf")
        if pdf_path.exists():
            return str(pdf_path)
        pytest.skip("Medical File.pdf not found - skipping integration test")

    @pytest.fixture
    def sample_template_path(self):
        """Return path to sample template if it exists."""
        template_path = Path("Medical Summary.docx")
        if template_path.exists():
            return str(template_path)
        pytest.skip("Medical Summary.docx not found - skipping integration test")

    def test_pdf_text_extraction(self, sample_pdf_path):
        """Test that PDF text extraction works."""
        pages = extract_text_by_page(sample_pdf_path)

        assert len(pages) > 0
        assert isinstance(pages[0], str)
        assert len(pages[0]) > 100  # Should have substantial content

        # Check for expected content in first page
        first_page = pages[0].lower()
        assert any(
            keyword in first_page for keyword in ["claimant", "arthur", "miller"]
        )

    def test_end_to_end_pipeline(self, sample_pdf_path, sample_template_path, tmp_path):
        """Test the complete end-to-end pipeline."""
        output_docx = tmp_path / "test_output.docx"
        output_md = tmp_path / "test_output.md"

        # Mock sys.argv to simulate CLI call
        test_args = [
            "cli.py",
            "--pdf",
            sample_pdf_path,
            "--template",
            sample_template_path,
            "--out",
            str(output_docx),
            "--md-out",
            str(output_md),
            "--layout",
            "columns=Date|Provider|Reason|Ref; sort=Date asc",
        ]

        with patch("sys.argv", test_args):
            try:
                main()

                # Verify outputs were created
                assert output_docx.exists()
                assert output_md.exists()

                # Verify markdown content has expected structure
                md_content = output_md.read_text()
                assert "# Medical Summary" in md_content
                assert "RE: Arthur Miller" in md_content
                assert "SSN: 456-12-7890" in md_content
                assert "## Alleged impairments" in md_content
                assert "| Date | Provider | Reason | Ref |" in md_content

                # Verify DOCX file is not empty
                assert output_docx.stat().st_size > 1000  # Should be substantial

            except Exception as e:
                pytest.fail(f"End-to-end pipeline failed: {e}")

    def test_cli_missing_pdf(self, tmp_path):
        """Test CLI behavior with missing PDF file."""
        nonexistent_pdf = tmp_path / "nonexistent.pdf"
        output_docx = tmp_path / "output.docx"

        test_args = [
            "cli.py",
            "--pdf",
            str(nonexistent_pdf),
            "--template",
            "Medical Summary.docx",
            "--out",
            str(output_docx),
        ]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit):
                main()

    def test_cli_missing_template(self, sample_pdf_path, tmp_path):
        """Test CLI behavior with missing template file."""
        nonexistent_template = tmp_path / "nonexistent.docx"
        output_docx = tmp_path / "output.docx"

        test_args = [
            "cli.py",
            "--pdf",
            sample_pdf_path,
            "--template",
            str(nonexistent_template),
            "--out",
            str(output_docx),
        ]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit):
                main()

    def test_output_quality_validation(
        self, sample_pdf_path, sample_template_path, tmp_path
    ):
        """Test that output meets quality requirements."""
        output_md = tmp_path / "quality_test.md"

        test_args = [
            "cli.py",
            "--pdf",
            sample_pdf_path,
            "--template",
            sample_template_path,
            "--out",
            str(tmp_path / "quality_test.docx"),
            "--md-out",
            str(output_md),
        ]

        with patch("sys.argv", test_args):
            main()

            md_content = output_md.read_text()

            # Validate header completeness
            assert "RE: Arthur Miller" in md_content
            assert "SSN: 456-12-7890" in md_content
            assert "Title: T16" in md_content
            assert "DLI: 07/14/2022" in md_content
            assert "AOD: 07/01/2022" in md_content
            assert "Date of Birth: 05/21/1965" in md_content

            # Validate impairments section exists
            assert "## Alleged impairments" in md_content
            assert "Osteoarthrosis" in md_content or "Hip" in md_content

            # Validate timeline structure
            lines = md_content.split("\n")
            table_lines = [line for line in lines if "|" in line and "Pg" in line]
            assert len(table_lines) >= 5  # Should have multiple events

            # Validate page references are realistic (1-15)
            for line in table_lines:
                if "Pg" in line:
                    pg_part = line.split("Pg")[-1].strip().rstrip("|").strip()
                    try:
                        page_num = int(pg_part)
                        assert 1 <= page_num <= 15, (
                            f"Page number {page_num} outside expected range"
                        )
                    except ValueError:
                        pass  # Skip if can't parse page number

            # Validate clinical reasons (not just "Initial")
            clinical_keywords = [
                "pain",
                "evaluation",
                "consultation",
                "assessment",
                "therapy",
            ]
            has_clinical_reasons = any(
                keyword in md_content.lower() for keyword in clinical_keywords
            )
            assert has_clinical_reasons, (
                "Output should contain meaningful clinical reasons"
            )


if __name__ == "__main__":
    pytest.main([__file__])
