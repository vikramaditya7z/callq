"""Deterministic orchestration and API tests for V2.4."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.api.analysis import analyze_earnings_call
from backend.api.v2_analysis import analyze_v2
from backend.main import app
from backend.models.analysis import EarningsAnalysisRequest, EarningsAnalysisResponse
from backend.models.v2_analysis import (
    Calculation,
    EvidenceRef,
    FinancialFact,
    HistoricalTranscript,
    InterpretationItem,
    V2AnalysisRequest,
    V2ExtractionResponse,
    V2InterpretationResponse,
)
from backend.services.gemini_service import GeminiAPIError
from backend.services.v2_analysis_service import (
    V2AnalysisServiceError,
    build_v2_source_documents,
    run_v2_analysis,
)
from backend.services.v2_extraction_service import V2ExtractionServiceError
from backend.services.v2_interpretation_service import V2InterpretationServiceError


TRANSCRIPT = "Operator: " + ("Management discussed revenue growth and demand. " * 8)


def verified_extraction(include_historical: bool = False) -> V2ExtractionResponse:
    """Build verified V2.1 output for orchestration tests."""
    facts = [
        FinancialFact(
            fact_id="revenue_current",
            metric_key="revenue",
            reported_value="$1.20 billion",
            unit="USD",
            period="Q3 2025",
            period_type="quarterly",
            evidence=EvidenceRef(
                source_id="current",
                exact_quote="Management discussed revenue growth and demand.",
                start_offset=10,
                end_offset=58,
            ),
        )
    ]
    if include_historical:
        facts.append(
            FinancialFact(
                fact_id="revenue_historical",
                metric_key="revenue",
                reported_value="$1.00 billion",
                unit="USD",
                period="Q3 2024",
                period_type="quarterly",
                evidence=EvidenceRef(
                    source_id="historical_1_prior-quarter",
                    exact_quote="Management discussed revenue growth and demand.",
                    start_offset=10,
                    end_offset=58,
                ),
            )
        )
    return V2ExtractionResponse(financial_facts=facts)


def grounded_thesis() -> V2InterpretationResponse:
    """Build minimal V2.3 output compatible with the verified extraction."""
    return V2InterpretationResponse(
        bull_items=[
            InterpretationItem(
                claim="Revenue trend improved.",
                why_it_matters="The reported trend supports stronger business momentum.",
                supporting_fact_ids=["revenue_current"],
                calculation_ids=[],
                evidence_refs=[
                    EvidenceRef(
                        source_id="current",
                        exact_quote="Management discussed revenue growth and demand.",
                        start_offset=10,
                        end_offset=58,
                    )
                ],
            )
        ]
    )


class V24PipelineTests(unittest.TestCase):
    """Verify stage orchestration with deterministic mocked service boundaries."""

    def test_valid_current_transcript(self) -> None:
        request = V2AnalysisRequest(current_transcript=TRANSCRIPT)
        extraction = verified_extraction()

        with patch(
            "backend.services.v2_analysis_service.extract_v2_facts",
            return_value=extraction,
        ), patch(
            "backend.services.v2_analysis_service.generate_v2_interpretation",
            return_value=grounded_thesis(),
        ):
            response = run_v2_analysis(request)

        self.assertEqual(response.source_documents[0].source_id, "current")
        self.assertEqual(response.facts.financial_facts[0].fact_id, "revenue_current")
        self.assertEqual(response.coverage.source_count, 1)

    def test_current_and_historical_transcript(self) -> None:
        request = V2AnalysisRequest(
            current_transcript=TRANSCRIPT,
            historical_transcripts=[
                HistoricalTranscript(label="Prior Quarter", transcript=TRANSCRIPT)
            ],
        )
        extraction = verified_extraction(include_historical=True)

        with patch(
            "backend.services.v2_analysis_service.extract_v2_facts",
            return_value=extraction,
        ), patch(
            "backend.services.v2_analysis_service.generate_v2_interpretation",
            return_value=grounded_thesis(),
        ):
            response = run_v2_analysis(request)

        self.assertEqual(response.coverage.source_count, 2)
        self.assertEqual(response.coverage.valid_calculation_count, 2)
        self.assertEqual(response.calculations[0].input_fact_ids, [
            "revenue_current", "revenue_historical"
        ])

    def test_source_ids_are_stable(self) -> None:
        request = V2AnalysisRequest(
            current_transcript=TRANSCRIPT,
            historical_transcripts=[
                HistoricalTranscript(label="Prior Quarter", transcript=TRANSCRIPT)
            ],
        )

        first_ids = [source.source_id for source in build_v2_source_documents(request)]
        second_ids = [source.source_id for source in build_v2_source_documents(request)]

        self.assertEqual(first_ids, ["current", "historical_1_prior-quarter"])
        self.assertEqual(first_ids, second_ids)

    def test_interpretation_receives_verified_facts_and_calculations(self) -> None:
        request = V2AnalysisRequest(
            current_transcript=TRANSCRIPT,
            historical_transcripts=[
                HistoricalTranscript(label="Prior Quarter", transcript=TRANSCRIPT)
            ],
        )
        extraction = verified_extraction(include_historical=True)

        def assert_interpretation_inputs(facts, guidance, observations, calculations):
            self.assertEqual(facts, extraction.financial_facts)
            self.assertTrue(all(calculation.status == "valid" for calculation in calculations))
            return grounded_thesis()

        with patch(
            "backend.services.v2_analysis_service.extract_v2_facts",
            return_value=extraction,
        ), patch(
            "backend.services.v2_analysis_service.generate_v2_interpretation",
            side_effect=assert_interpretation_inputs,
        ):
            run_v2_analysis(request)

    def test_invalid_evidence_stops_before_interpretation(self) -> None:
        request = V2AnalysisRequest(current_transcript=TRANSCRIPT)

        with patch(
            "backend.services.v2_analysis_service.extract_v2_facts",
            side_effect=V2ExtractionServiceError("unverifiable evidence"),
        ), patch(
            "backend.services.v2_analysis_service.generate_v2_interpretation",
        ) as interpretation_mock:
            with self.assertRaises(V2AnalysisServiceError):
                run_v2_analysis(request)

        interpretation_mock.assert_not_called()

    def test_invalid_interpretation_reference_is_rejected(self) -> None:
        request = V2AnalysisRequest(current_transcript=TRANSCRIPT)

        with patch(
            "backend.services.v2_analysis_service.extract_v2_facts",
            return_value=verified_extraction(),
        ), patch(
            "backend.services.v2_analysis_service.generate_v2_interpretation",
            side_effect=V2InterpretationServiceError("unknown fact reference"),
        ):
            with self.assertRaises(V2AnalysisServiceError):
                run_v2_analysis(request)


class V24ApiTests(unittest.TestCase):
    """Verify additive V2 API behavior and preserved V1.5 routing."""

    def test_provider_errors_become_controlled_api_errors(self) -> None:
        with patch(
            "backend.api.v2_analysis.run_v2_analysis",
            side_effect=GeminiAPIError("socket details must not leak"),
        ), self.assertRaises(HTTPException) as raised:
            analyze_v2(V2AnalysisRequest(current_transcript=TRANSCRIPT))

        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(
            raised.exception.detail,
            "V2 AI provider failed to return a valid response.",
        )

    def test_invalid_request_returns_validation_error(self) -> None:
        with self.assertRaises(ValueError):
            V2AnalysisRequest(current_transcript="short")

    def test_v2_route_is_registered(self) -> None:
        paths = {route.path for route in app.routes}

        self.assertIn("/analyze/v2", paths)

    def test_v15_analyze_route_remains_unaffected(self) -> None:
        v15_response = EarningsAnalysisResponse(
            executive_summary=["Summary"], positives=["Positive"], negatives=["Negative"],
            risks=["Risk"], opportunities=["Opportunity"], management_outlook="Outlook",
            themes=["Theme"], financial_metrics=[], guidance=[],
            management_signals={
                "overall_tone": "neutral", "positive_signals": [], "watch_signals": []
            },
        )
        with patch("backend.api.analysis.analyze_transcript", return_value=v15_response):
            response = analyze_earnings_call(EarningsAnalysisRequest(transcript=TRANSCRIPT))

        self.assertEqual(response.executive_summary, ["Summary"])


class Python39CompatibilityTests(unittest.TestCase):
    """Ensure V2.4 source uses syntax accepted by Python 3.9."""

    def test_v24_source_parses_with_python_39_grammar(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        v24_files = [
            repository_root / "backend/models/v2_analysis.py",
            repository_root / "backend/services/v2_analysis_service.py",
            repository_root / "backend/api/v2_analysis.py",
        ]

        for source_file in v24_files:
            with self.subTest(source_file=source_file):
                ast.parse(
                    source_file.read_text(encoding="utf-8"),
                    filename=str(source_file),
                    feature_version=(3, 9),
                )


if __name__ == "__main__":
    unittest.main()
