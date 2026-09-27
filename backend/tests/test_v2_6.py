"""End-to-end validation and hardening integration tests for V2.6."""

from __future__ import annotations

from decimal import Decimal
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.api.analysis import analyze_earnings_call
from backend.api.v2_analysis import analyze_v2
from backend.models.analysis import EarningsAnalysisRequest, EarningsAnalysisResponse
from backend.models.v2_analysis import (
    Calculation,
    EvidenceGap,
    EvidenceRef,
    FinancialFact,
    GuidanceFact,
    HistoricalTranscript,
    InterpretationItem,
    QualitativeObservation,
    SourceDocument,
    V2AnalysisRequest,
    V2AnalysisResponse,
    V2ExtractionResponse,
    V2InterpretationResponse,
)
from backend.services.gemini_service import GeminiAPIError, GeminiConfigurationError
from backend.services.v2_analysis_service import (
    V2AnalysisServiceError,
    V2CalculationPipelineError,
    run_v2_analysis,
)
from backend.services.v2_extraction_service import V2ExtractionServiceError
from backend.services.v2_interpretation_service import (
    InterpretationValidationError,
    V2InterpretationServiceError,
)


CURRENT_TRANSCRIPT = (
    "Operator: Welcome to the Q3 2025 earnings call. "
    "Revenue was $1.20 billion, up from last year. "
    "Gross margin was 65 percent for the quarter. "
    "Management expects revenue between $1.30 billion and $1.40 billion for the upcoming fourth quarter. "
    "Enterprise demand in North America remained resilient throughout the period. "
    "We are maintaining disciplined capital allocation and operational rigor."
)

HISTORICAL_TRANSCRIPT = (
    "Operator: Welcome to the Q3 2024 earnings call. "
    "Revenue was $1.00 billion during the prior year period. "
    "Gross margin was 60 percent for the quarter. "
    "Management expected modest growth across all key segments. "
    "Enterprise demand in North America was stable."
)


def mock_extraction_output(include_historical: bool = False) -> V2ExtractionResponse:
    """Mock a raw structured output from Gemini for extraction."""
    facts = [
        FinancialFact(
            fact_id="fact_rev_curr",
            metric_key="revenue",
            reported_value="$1.20 billion",
            unit="USD",
            period="Q3 2025",
            period_type="quarterly",
            evidence=EvidenceRef(
                source_id="current",
                exact_quote="Revenue was $1.20 billion, up from last year.",
            ),
        ),
        FinancialFact(
            fact_id="fact_margin_curr",
            metric_key="gross_margin",
            reported_value="65 percent",
            unit="percent",
            period="Q3 2025",
            period_type="quarterly",
            evidence=EvidenceRef(
                source_id="current",
                exact_quote="Gross margin was 65 percent for the quarter.",
            ),
        ),
    ]
    guidance = [
        GuidanceFact(
            fact_id="guidance_rev_q4",
            metric_key="revenue",
            guidance_value="$1.30 billion to $1.40 billion",
            unit="USD",
            period="Q4 2025",
            evidence=EvidenceRef(
                source_id="current",
                exact_quote="Management expects revenue between $1.30 billion and $1.40 billion for the upcoming fourth quarter.",
            ),
        )
    ]
    observations = [
        QualitativeObservation(
            observation_id="obs_demand_curr",
            category="demand",
            statement="Enterprise demand in North America remained resilient.",
            evidence=EvidenceRef(
                source_id="current",
                exact_quote="Enterprise demand in North America remained resilient throughout the period.",
            ),
        )
    ]

    if include_historical:
        facts.extend([
            FinancialFact(
                fact_id="fact_rev_hist",
                metric_key="revenue",
                reported_value="$1.00 billion",
                unit="USD",
                period="Q3 2024",
                period_type="quarterly",
                evidence=EvidenceRef(
                    source_id="historical_1_prior-year-q3",
                    exact_quote="Revenue was $1.00 billion during the prior year period.",
                ),
            ),
            FinancialFact(
                fact_id="fact_margin_hist",
                metric_key="gross_margin",
                reported_value="60 percent",
                unit="percent",
                period="Q3 2024",
                period_type="quarterly",
                evidence=EvidenceRef(
                    source_id="historical_1_prior-year-q3",
                    exact_quote="Gross margin was 60 percent for the quarter.",
                ),
            ),
        ])

    return V2ExtractionResponse(
        financial_facts=facts,
        guidance=guidance,
        qualitative_observations=observations,
    )


def mock_interpretation_output() -> V2InterpretationResponse:
    """Mock a raw structured interpretation output without numeric claims."""
    return V2InterpretationResponse(
        bull_items=[
            InterpretationItem(
                claim="Revenue expanded with resilient enterprise demand.",
                why_it_matters="Strong top-line expansion indicates healthy market traction.",
                supporting_fact_ids=["fact_rev_curr"],
                calculation_ids=[],
                evidence_refs=[
                    EvidenceRef(
                        source_id="current",
                        exact_quote="Revenue was $1.20 billion, up from last year.",
                    )
                ],
            )
        ],
        bear_items=[
            InterpretationItem(
                claim="Capital allocation and operational rigor required ongoing attention.",
                why_it_matters="Management focus on rigor implies potential cost pressures.",
                supporting_fact_ids=["obs_demand_curr"],
                calculation_ids=[],
                evidence_refs=[
                    EvidenceRef(
                        source_id="current",
                        exact_quote="Enterprise demand in North America remained resilient throughout the period.",
                    )
                ],
            )
        ],
        watch_items=[
            InterpretationItem(
                claim="Future revenue guidance depends on continued pipeline execution.",
                why_it_matters="Meeting the guided range is crucial for sustaining investor confidence.",
                supporting_fact_ids=["guidance_rev_q4"],
                calculation_ids=[],
                evidence_refs=[
                    EvidenceRef(
                        source_id="current",
                        exact_quote="Management expects revenue between $1.30 billion and $1.40 billion for the upcoming fourth quarter.",
                    )
                ],
            )
        ],
        evidence_gaps=[
            EvidenceGap(
                gap_id="gap_intl_demand",
                description="International demand breakdown was not disclosed in the transcript.",
                related_fact_ids=["fact_rev_curr"],
                related_calculation_ids=[],
            )
        ],
    )


class V26EndToEndValidationTests(unittest.TestCase):
    """V2.6 end-to-end integration and hardening test suite."""

    def test_1_current_transcript_only(self) -> None:
        """1. Validate full pipeline with current transcript only."""
        request = V2AnalysisRequest(current_transcript=CURRENT_TRANSCRIPT)
        raw_extraction = mock_extraction_output(include_historical=False)
        raw_interpretation = mock_interpretation_output()

        with patch(
            "backend.services.v2_extraction_service.generate_structured_response",
            return_value=raw_extraction.model_dump(),
        ), patch(
            "backend.services.v2_interpretation_service.generate_structured_response",
            return_value=raw_interpretation.model_dump(),
        ):
            response = run_v2_analysis(request)

        self.assertIsInstance(response, V2AnalysisResponse)
        self.assertEqual(len(response.source_documents), 1)
        self.assertEqual(response.source_documents[0].source_id, "current")
        self.assertEqual(response.coverage.source_count, 1)
        self.assertEqual(response.coverage.financial_fact_count, 2)
        self.assertEqual(response.coverage.guidance_count, 1)
        self.assertEqual(response.coverage.qualitative_observation_count, 1)
        # Guidance calculations should be generated (midpoint + width)
        self.assertEqual(len(response.calculations), 2)
        calc_types = [c.calculation_type for c in response.calculations]
        self.assertIn("guidance_midpoint", calc_types)
        self.assertIn("guidance_range_width", calc_types)

    def test_2_current_and_historical_transcript(self) -> None:
        """2. Validate full pipeline with current + historical transcript."""
        request = V2AnalysisRequest(
            current_transcript=CURRENT_TRANSCRIPT,
            historical_transcripts=[
                HistoricalTranscript(label="Prior Year Q3", transcript=HISTORICAL_TRANSCRIPT)
            ],
        )
        raw_extraction = mock_extraction_output(include_historical=True)
        raw_interpretation = mock_interpretation_output()

        with patch(
            "backend.services.v2_extraction_service.generate_structured_response",
            return_value=raw_extraction.model_dump(),
        ), patch(
            "backend.services.v2_interpretation_service.generate_structured_response",
            return_value=raw_interpretation.model_dump(),
        ):
            response = run_v2_analysis(request)

        self.assertEqual(len(response.source_documents), 2)
        self.assertEqual(response.coverage.source_count, 2)
        self.assertEqual(response.coverage.financial_fact_count, 4)
        # 2 comparisons for revenue (abs, pct) + 3 comparisons for gross_margin (abs, pct, margin_change) + 2 guidance calcs = 7 calcs
        self.assertEqual(len(response.calculations), 7)
        self.assertEqual(response.coverage.valid_calculation_count, 7)
        self.assertEqual(response.coverage.unavailable_calculation_count, 0)

    def test_3_valid_financial_facts_extraction(self) -> None:
        """3. Validate financial facts content and metadata."""
        request = V2AnalysisRequest(current_transcript=CURRENT_TRANSCRIPT)
        raw_extraction = mock_extraction_output()

        with patch(
            "backend.services.v2_extraction_service.generate_structured_response",
            return_value=raw_extraction.model_dump(),
        ), patch(
            "backend.services.v2_interpretation_service.generate_structured_response",
            return_value=mock_interpretation_output().model_dump(),
        ):
            response = run_v2_analysis(request)

        rev_fact = next(f for f in response.facts.financial_facts if f.metric_key == "revenue")
        self.assertEqual(rev_fact.reported_value, "$1.20 billion")
        self.assertEqual(rev_fact.unit, "USD")
        self.assertEqual(rev_fact.period, "Q3 2025")

        margin_fact = next(f for f in response.facts.financial_facts if f.metric_key == "gross_margin")
        self.assertEqual(margin_fact.reported_value, "65 percent")
        self.assertEqual(margin_fact.unit, "percent")

    def test_4_evidence_references_resolve_correctly(self) -> None:
        """4. Verify evidence exact quote offsets are resolved deterministically."""
        request = V2AnalysisRequest(current_transcript=CURRENT_TRANSCRIPT)
        raw_extraction = mock_extraction_output()

        with patch(
            "backend.services.v2_extraction_service.generate_structured_response",
            return_value=raw_extraction.model_dump(),
        ), patch(
            "backend.services.v2_interpretation_service.generate_structured_response",
            return_value=mock_interpretation_output().model_dump(),
        ):
            response = run_v2_analysis(request)

        for fact in response.facts.financial_facts:
            quote = fact.evidence.exact_quote
            start = fact.evidence.start_offset
            end = fact.evidence.end_offset
            self.assertIsNotNone(start)
            self.assertIsNotNone(end)
            self.assertEqual(CURRENT_TRANSCRIPT[start:end], quote)

    def test_5_deterministic_calculations_reach_interpretation(self) -> None:
        """5. Verify calculations are passed to the interpretation stage."""
        request = V2AnalysisRequest(
            current_transcript=CURRENT_TRANSCRIPT,
            historical_transcripts=[
                HistoricalTranscript(label="Prior Year Q3", transcript=HISTORICAL_TRANSCRIPT)
            ],
        )
        raw_extraction = mock_extraction_output(include_historical=True)

        with patch(
            "backend.services.v2_extraction_service.generate_structured_response",
            return_value=raw_extraction.model_dump(),
        ), patch(
            "backend.services.v2_interpretation_service.generate_structured_response"
        ) as mock_interp_gen:
            def fake_interp(prompt, schema):
                self.assertIn('"calculations":', prompt)
                self.assertIn("percentage_change", prompt)
                self.assertIn("absolute_change", prompt)
                return mock_interpretation_output().model_dump()

            mock_interp_gen.side_effect = fake_interp
            response = run_v2_analysis(request)

        self.assertGreater(len(response.calculations), 0)

    def test_6_numeric_claims_require_calculation_provenance(self) -> None:
        """6. Numeric claims without valid calculation provenance are rejected."""
        request = V2AnalysisRequest(current_transcript=CURRENT_TRANSCRIPT)
        raw_extraction = mock_extraction_output()

        # Interpretation returns claim with numbers but without calculation_ids
        unprovenanced_interpretation = V2InterpretationResponse(
            bull_items=[
                InterpretationItem(
                    claim="Revenue jumped by 20.0 percent year over year.",
                    why_it_matters="Accelerating growth.",
                    supporting_fact_ids=["fact_rev_curr"],
                    calculation_ids=[],  # Missing calculation provenance for 20.0 percent
                    evidence_refs=[
                        EvidenceRef(
                            source_id="current",
                            exact_quote="Revenue was $1.20 billion, up from last year.",
                        )
                    ],
                )
            ]
        )

        with patch(
            "backend.services.v2_extraction_service.generate_structured_response",
            return_value=raw_extraction.model_dump(),
        ), patch(
            "backend.services.v2_interpretation_service.generate_structured_response",
            return_value=unprovenanced_interpretation.model_dump(),
        ):
            with self.assertRaises(V2AnalysisServiceError) as ctx:
                run_v2_analysis(request)
            self.assertIn("interpretation reference validation failed", str(ctx.exception).lower())

    def test_7_invalid_evidence_is_rejected(self) -> None:
        """7. Hallucinated evidence quote not in transcript is rejected."""
        request = V2AnalysisRequest(current_transcript=CURRENT_TRANSCRIPT)
        hallucinated_extraction = V2ExtractionResponse(
            financial_facts=[
                FinancialFact(
                    fact_id="fact_fake",
                    metric_key="revenue",
                    reported_value="$99.9 billion",
                    unit="USD",
                    evidence=EvidenceRef(
                        source_id="current",
                        exact_quote="This quote does not exist in the earnings transcript at all.",
                    ),
                )
            ]
        )

        with patch(
            "backend.services.v2_extraction_service.generate_structured_response",
            return_value=hallucinated_extraction.model_dump(),
        ):
            with self.assertRaises(V2AnalysisServiceError) as ctx:
                run_v2_analysis(request)
            self.assertIn("extraction evidence validation failed", str(ctx.exception).lower())

    def test_8_incompatible_historical_comparisons_become_unavailable(self) -> None:
        """8. Incompatible metrics produce 'unavailable' calculations with reasons."""
        request = V2AnalysisRequest(
            current_transcript=CURRENT_TRANSCRIPT,
            historical_transcripts=[
                HistoricalTranscript(label="Prior Year Q3", transcript=HISTORICAL_TRANSCRIPT)
            ],
        )
        # Extraction with mismatched units: USD vs EUR, with period_type present
        mismatched_extraction = V2ExtractionResponse(
            financial_facts=[
                FinancialFact(
                    fact_id="rev_usd",
                    metric_key="revenue",
                    reported_value="$1.20 billion",
                    unit="USD",
                    period="Q3 2025",
                    period_type="quarterly",
                    evidence=EvidenceRef(
                        source_id="current",
                        exact_quote="Revenue was $1.20 billion, up from last year.",
                    ),
                ),
                FinancialFact(
                    fact_id="rev_eur",
                    metric_key="revenue",
                    reported_value="€1.00 billion",
                    unit="EUR",
                    period="Q3 2024",
                    period_type="quarterly",
                    evidence=EvidenceRef(
                        source_id="historical_1_prior-year-q3",
                        exact_quote="Revenue was $1.00 billion during the prior year period.",
                    ),
                ),
            ]
        )

        with patch(
            "backend.services.v2_extraction_service.generate_structured_response",
            return_value=mismatched_extraction.model_dump(),
        ), patch(
            "backend.services.v2_interpretation_service.generate_structured_response",
            return_value=V2InterpretationResponse().model_dump(),
        ):
            response = run_v2_analysis(request)

        self.assertGreater(response.coverage.unavailable_calculation_count, 0)
        unavail_calc = next(c for c in response.calculations if c.status == "unavailable")
        self.assertIsNotNone(unavail_calc.reason)
        self.assertIn("incompatible", unavail_calc.reason.lower())

    def test_9_bull_bear_watch_references_remain_valid(self) -> None:
        """9. Interpretation referencing nonexistent fact ID is rejected."""
        request = V2AnalysisRequest(current_transcript=CURRENT_TRANSCRIPT)
        raw_extraction = mock_extraction_output()
        invalid_ref_interpretation = V2InterpretationResponse(
            bull_items=[
                InterpretationItem(
                    claim="Revenue was strong.",
                    why_it_matters="Good performance.",
                    supporting_fact_ids=["nonexistent_fact_id_12345"],
                    calculation_ids=[],
                    evidence_refs=[
                        EvidenceRef(
                            source_id="current",
                            exact_quote="Revenue was $1.20 billion, up from last year.",
                        )
                    ],
                )
            ]
        )

        with patch(
            "backend.services.v2_extraction_service.generate_structured_response",
            return_value=raw_extraction.model_dump(),
        ), patch(
            "backend.services.v2_interpretation_service.generate_structured_response",
            return_value=invalid_ref_interpretation.model_dump(),
        ):
            with self.assertRaises(V2AnalysisServiceError) as ctx:
                run_v2_analysis(request)
            self.assertIn("interpretation reference validation failed", str(ctx.exception).lower())

    def test_10_missing_optional_fields_do_not_break_response(self) -> None:
        """10. Omission of nullable/optional fields validates cleanly in Pydantic."""
        minimal_extraction = V2ExtractionResponse(
            financial_facts=[
                FinancialFact(
                    fact_id="fact_min",
                    metric_key="revenue",
                    reported_value="$1.20 billion",
                    unit=None,
                    period=None,
                    period_type=None,
                    evidence=EvidenceRef(
                        source_id="current",
                        exact_quote="Revenue was $1.20 billion, up from last year.",
                        start_offset=None,
                        end_offset=None,
                    ),
                )
            ],
            guidance=[],
            qualitative_observations=[],
        )
        minimal_interpretation = V2InterpretationResponse(
            bull_items=[],
            bear_items=[],
            watch_items=[],
            evidence_gaps=[],
        )

        request = V2AnalysisRequest(current_transcript=CURRENT_TRANSCRIPT)
        with patch(
            "backend.services.v2_extraction_service.generate_structured_response",
            return_value=minimal_extraction.model_dump(),
        ), patch(
            "backend.services.v2_interpretation_service.generate_structured_response",
            return_value=minimal_interpretation.model_dump(),
        ):
            response = run_v2_analysis(request)

        self.assertIsInstance(response, V2AnalysisResponse)
        self.assertIsNone(response.facts.financial_facts[0].unit)
        self.assertIsNone(response.facts.financial_facts[0].period)
        # Verify JSON dump and re-parse works cleanly
        dumped = response.model_dump()
        revalidated = V2AnalysisResponse.model_validate(dumped)
        self.assertEqual(revalidated.facts.financial_facts[0].fact_id, "fact_min")

    def test_11_v2_failures_produce_controlled_errors(self) -> None:
        """11. Service exceptions map to controlled HTTP 500 / 502 status codes."""
        request = V2AnalysisRequest(current_transcript=CURRENT_TRANSCRIPT)

        # 11a: Gemini configuration error -> 500
        with patch(
            "backend.api.v2_analysis.run_v2_analysis",
            side_effect=GeminiConfigurationError("API key missing"),
        ):
            with self.assertRaises(HTTPException) as ctx:
                analyze_v2(request)
            self.assertEqual(ctx.exception.status_code, 500)
            self.assertIn("not configured", ctx.exception.detail)

        # 11b: Gemini API / network error -> 502
        with patch(
            "backend.api.v2_analysis.run_v2_analysis",
            side_effect=GeminiAPIError("Timeout"),
        ):
            with self.assertRaises(HTTPException) as ctx:
                analyze_v2(request)
            self.assertEqual(ctx.exception.status_code, 502)
            self.assertIn("AI provider failed", ctx.exception.detail)

        # 11c: Calculation pipeline error -> 502
        with patch(
            "backend.api.v2_analysis.run_v2_analysis",
            side_effect=V2CalculationPipelineError("Calculation failed"),
        ):
            with self.assertRaises(HTTPException) as ctx:
                analyze_v2(request)
            self.assertEqual(ctx.exception.status_code, 502)
            self.assertIn("calculation pipeline failed", ctx.exception.detail)

        # 11d: Analysis validation error -> 502
        with patch(
            "backend.api.v2_analysis.run_v2_analysis",
            side_effect=V2AnalysisServiceError("Validation failed"),
        ):
            with self.assertRaises(HTTPException) as ctx:
                analyze_v2(request)
            self.assertEqual(ctx.exception.status_code, 502)
            self.assertIn("could not be validated", ctx.exception.detail)

    def test_12_v1_5_analyze_remains_unaffected(self) -> None:
        """12. Calling V1.5 /analyze route remains completely functional and unaffected."""
        v15_request = EarningsAnalysisRequest(transcript=CURRENT_TRANSCRIPT)
        v15_mock_response = {
            "executive_summary": ["Executive summary point 1."],
            "positives": ["Revenue expanded."],
            "negatives": ["Cost discipline required."],
            "risks": ["Supply chain variability."],
            "opportunities": ["Enterprise expansion."],
            "management_outlook": "Management remains cautiously optimistic.",
            "themes": ["Revenue Growth", "Cost Discipline"],
            "financial_metrics": [
                {
                    "name": "Revenue",
                    "value": "$1.20 billion",
                    "change": "up 20%",
                    "period": "Q3 2025",
                }
            ],
            "guidance": [
                {
                    "metric": "Revenue",
                    "value": "$1.30B - $1.40B",
                    "period": "Q4 2025",
                    "context": "Full year ramp",
                }
            ],
            "management_signals": {
                "overall_tone": "Constructive",
                "positive_signals": ["Strong enterprise bookings"],
                "watch_signals": ["Supply constraints"],
            },
        }

        with patch(
            "backend.services.analysis_service.generate_structured_response",
            return_value=v15_mock_response,
        ):
            v15_result = analyze_earnings_call(v15_request)

        self.assertIsInstance(v15_result, EarningsAnalysisResponse)
        self.assertEqual(v15_result.financial_metrics[0].name, "Revenue")
        self.assertEqual(v15_result.guidance[0].metric, "Revenue")
        self.assertEqual(v15_result.management_signals.overall_tone, "Constructive")


if __name__ == "__main__":
    unittest.main()
