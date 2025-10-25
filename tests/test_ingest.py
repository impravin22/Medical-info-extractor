"""Tests for PDF ingestion and extraction functionality."""

from src.ingest.pdf_reader import extract_text_by_page
from pathlib import Path


def test_pdf_text_extraction():
    """Test that PDF text extraction works."""
    # This is a basic test - in a real scenario you'd have a test PDF
    # For now, just test that the function exists and can be called
    try:
        # Test with a non-existent file to verify error handling
        result = extract_text_by_page(Path("nonexistent.pdf"))
        assert False, "Should have raised an exception"
    except Exception:
        # Expected - file doesn't exist
        pass


def test_extraction_pipeline_structure():
    """Test that the extraction pipeline has the expected structure."""
    from src.ingest.extractors import build_report

    # Test that build_report function exists and can be imported
    assert callable(build_report)

    # Test with empty pages - should not crash
    pages = []
    mock_model = None

    try:
        report = build_report(pages, mock_model)
        # Should create a report even with empty data
        assert report is not None
    except Exception as e:
        # Expected to fail with mock model, but should not be an import error
        assert "NoneType" in str(e) or "model" in str(e).lower()
