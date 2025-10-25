"""Tests for LLM-based extraction functionality."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch
from datetime import date

from src.ingest.extractors import (
    build_report,
    extract_claimant_header_llm,
    extract_alleged_impairments_llm,
    extract_events_llm,
)
from src.domain.schema import Claimant, Event, Report


class TestLLMExtraction:
    """Test LLM-based extraction functions."""

    def test_extract_claimant_header_llm_success(self):
        """Test successful claimant header extraction."""
        mock_model = Mock()
        pages = ["Claimant: Arthur Miller | SSN: 456-12-7890 | Claim type: T16"]

        with patch("src.ingest.extractors.extract_claimant_with_llm") as mock_extract:
            mock_extract.return_value = {
                "name": "Arthur Miller",
                "ssn": "456-12-7890",
                "dob": "05/21/1965",
                "aod": "07/01/2022",
                "dli": "07/14/2022",
                "title": "T16",
                "last_grade_completed": "12",
                "attended_special_ed": False,
            }

            result = extract_claimant_header_llm(pages, mock_model)

            assert isinstance(result, Claimant)
            assert result.name == "Arthur Miller"
            assert result.ssn == "456-12-7890"
            assert result.dob == date(1965, 5, 21)
            assert result.aod == date(2022, 7, 1)
            assert result.dli == date(2022, 7, 14)
            assert result.title == "T16"
            assert result.last_grade_completed == "12"
            assert result.attended_special_ed is False

    def test_extract_claimant_header_llm_invalid_dates(self):
        """Test claimant header extraction with invalid dates."""
        mock_model = Mock()
        pages = ["Claimant: Arthur Miller"]

        with patch("src.ingest.extractors.extract_claimant_with_llm") as mock_extract:
            mock_extract.return_value = {
                "name": "Arthur Miller",
                "ssn": "456-12-7890",
                "dob": "invalid-date",
                "aod": None,
                "dli": None,
                "title": "T16",
                "last_grade_completed": None,
                "attended_special_ed": None,
            }

            result = extract_claimant_header_llm(pages, mock_model)

            assert result.name == "Arthur Miller"
            assert result.dob is None  # Invalid date should be None
            assert result.aod is None
            assert result.dli is None

    def test_extract_alleged_impairments_llm(self):
        """Test impairments extraction."""
        mock_model = Mock()
        pages = ["Medical conditions: hip pain, arthritis"]

        with patch(
            "src.ingest.extractors.extract_impairments_with_llm"
        ) as mock_extract:
            mock_extract.return_value = [
                "Osteoarthrosis and allied disorders",
                "Hip, neck and back pain",
                "Body numbness and weakness",
            ]

            result = extract_alleged_impairments_llm(pages, mock_model)

            assert len(result) == 3
            assert "Osteoarthrosis and allied disorders" in result
            assert "Hip, neck and back pain" in result

    def test_extract_events_llm(self):
        """Test events extraction."""
        mock_model = Mock()
        # Make page long enough to pass the 100 character filter
        pages = [
            "Willow Creek Medical Center 01/19/2023 Initial evaluation for hip pain and mobility assessment with detailed clinical notes and treatment plan recommendations."
        ]

        with patch("src.ingest.extractors.extract_events_with_llm") as mock_extract:
            mock_extract.return_value = [
                {
                    "date": "01/19/2023",
                    "provider": "Willow Creek Medical Center",
                    "reason": "Hip pain evaluation",
                    "ref_page": 1,
                }
            ]

            result = extract_events_llm(pages, mock_model)

            assert len(result) == 1
            event = result[0]
            assert isinstance(event, Event)
            assert event.date == date(2023, 1, 19)
            assert event.provider == "Willow Creek Medical Center"
            assert event.reason_raw == "Hip pain evaluation"
            assert event.ref_page == 1

    def test_extract_events_llm_invalid_date(self):
        """Test events extraction with invalid dates."""
        mock_model = Mock()
        pages = ["Some medical text"]

        with patch("src.ingest.extractors.extract_events_with_llm") as mock_extract:
            mock_extract.return_value = [
                {
                    "date": "invalid-date",
                    "provider": "Test Provider",
                    "reason": "Test reason",
                    "ref_page": 1,
                }
            ]

            result = extract_events_llm(pages, mock_model)

            assert len(result) == 0  # Invalid date should be filtered out

    def test_extract_events_llm_date_range_filter(self):
        """Test events extraction filters dates outside 2020-2024 range."""
        mock_model = Mock()
        pages = ["Old medical record"]

        with patch("src.ingest.extractors.extract_events_with_llm") as mock_extract:
            mock_extract.return_value = [
                {
                    "date": "01/19/2019",  # Too old
                    "provider": "Test Provider",
                    "reason": "Test reason",
                    "ref_page": 1,
                },
                {
                    "date": "01/19/2025",  # Too new
                    "provider": "Test Provider",
                    "reason": "Test reason",
                    "ref_page": 1,
                },
            ]

            result = extract_events_llm(pages, mock_model)

            assert len(result) == 0  # Both dates should be filtered out

    def test_extract_events_llm_deduplication(self):
        """Test events extraction deduplicates by date + provider."""
        mock_model = Mock()
        # Make pages long enough to pass the 100 character filter
        pages = [
            "Medical records with detailed clinical notes and comprehensive patient assessment documentation for treatment planning.",
            "Additional medical records with extensive clinical documentation and patient care notes for comprehensive evaluation.",
            "Further medical records containing detailed clinical assessments and treatment documentation for patient care.",
        ]

        with patch("src.ingest.extractors.extract_events_with_llm") as mock_extract:
            # Return same date/provider multiple times
            mock_extract.side_effect = [
                [
                    {
                        "date": "01/19/2023",
                        "provider": "Test Provider",
                        "reason": "Reason 1",
                        "ref_page": 1,
                    }
                ],
                [
                    {
                        "date": "01/19/2023",
                        "provider": "Test Provider",
                        "reason": "Reason 2",
                        "ref_page": 2,
                    }
                ],
                [
                    {
                        "date": "01/20/2023",
                        "provider": "Test Provider",
                        "reason": "Reason 3",
                        "ref_page": 3,
                    }
                ],
            ]

            result = extract_events_llm(pages, mock_model)

            # Should deduplicate to 2 unique events (different dates)
            assert len(result) == 2
            dates = [event.date for event in result]
            assert date(2023, 1, 19) in dates
            assert date(2023, 1, 20) in dates

    def test_build_report_integration(self):
        """Test full report building integration."""
        mock_model = Mock()
        pages = ["Test medical document"]

        with (
            patch("src.ingest.extractors.extract_claimant_header_llm") as mock_claimant,
            patch(
                "src.ingest.extractors.extract_alleged_impairments_llm"
            ) as mock_impairments,
            patch("src.ingest.extractors.extract_events_llm") as mock_events,
        ):
            mock_claimant.return_value = Claimant(
                name="Arthur Miller",
                ssn="456-12-7890",
                dob=date(1965, 5, 21),
                aod=date(2022, 7, 1),
                dli=date(2022, 7, 14),
                title="T16",
            )
            mock_impairments.return_value = ["Hip pain and arthritis"]
            mock_events.return_value = [
                Event(
                    date=date(2023, 1, 19),
                    provider="Test Provider",
                    reason_raw="Test reason",
                    ref_page=1,
                )
            ]

            result = build_report(pages, mock_model)

            assert isinstance(result, Report)
            assert result.claimant.name == "Arthur Miller"
            assert len(result.alleged_impairments) == 1
            assert len(result.events) == 1
            assert result.events[0].provider == "Test Provider"


if __name__ == "__main__":
    pytest.main([__file__])
