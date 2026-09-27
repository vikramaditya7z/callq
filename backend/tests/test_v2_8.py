"""Deterministic unit tests for V2.8 real-world evaluation, failure taxonomy, and V3 synthesis."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from backend.eval.fixtures_loader import (
    FixtureGroundTruth,
    TranscriptFixture,
    load_fixture_file,
    load_fixtures_from_directory,
)
from backend.eval.models import (
    BenchmarkCase,
    CaseEvaluationResult,
    DiagnosticFinding,
    EvaluationReport,
    ExpectedCalculation,
    ExpectedFact,
    ExpectedGuidance,
    MetricScore,
)
from backend.eval.runner import run_evaluation
from backend.eval.taxonomy import (
    ClassifiedFailure,
    FailureCategory,
    FailureSeverity,
    Subsystem,
    classify_diagnostic_finding,
    synthesize_v3_recommendations,
)
from backend.models.v2_analysis import (
    Calculation,
    EvidenceRef,
    FinancialFact,
    GuidanceFact,
    HistoricalTranscript,
    InterpretationItem,
    SourceDocument,
    V2AnalysisRequest,
    V2AnalysisResponse,
    V2Coverage,
    V2ExtractionResponse,
    V2InterpretationResponse,
)


class V28EvaluationFailureAnalysisTests(unittest.TestCase):
    """Test suite for V2.8 real-world evaluation fixtures, failure taxonomy, and V3 synthesis."""

    def setUp(self) -> None:
        self.sample_current_transcript = (
            "Operator: Welcome to Enterprise Cloud Q3 2026 earnings conference call. "
            "Total revenue for the third quarter was $300 million, representing strong year-over-year momentum. "
            "Subscription gross margin was 75 percent for the quarter. "
            "Management expects revenue between $315 million and $325 million next quarter. "
            "Enterprise demand in North America remained solid across key accounts."
        )
        self.sample_hist_transcript = (
            "Operator: Welcome to Enterprise Cloud Q3 2025 earnings call. "
            "Total revenue was $250 million. "
            "Subscription gross margin was 72 percent. "
            "Commercial activities were steady."
        )

    def _build_mock_v2_response(self) -> V2AnalysisResponse:
        quote = "revenue for the third quarter was $300 million"
        start = self.sample_current_transcript.find(quote)
        end = start + len(quote)

        return V2AnalysisResponse(
            source_documents=[
                SourceDocument(
                    source_id="current",
                    document_type="current_earnings_call_transcript",
                    text=self.sample_current_transcript,
                )
            ],
            facts=V2ExtractionResponse(
                financial_facts=[
                    FinancialFact(
                        fact_id="f_rev_curr",
                        metric_key="revenue",
                        reported_value="$300 million",
                        unit="USD",
                        period="Q3 2026",
                        period_type="quarterly",
                        evidence=EvidenceRef(
                            source_id="current",
                            exact_quote=quote,
                            start_offset=start,
                            end_offset=end,
                        ),
                    )
                ],
                guidance=[],
                qualitative_observations=[],
            ),
            calculations=[],
            thesis=V2InterpretationResponse(
                bull_items=[
                    InterpretationItem(
                        claim="Revenue expanded with enterprise momentum.",
                        why_it_matters="Solid business growth.",
                        supporting_fact_ids=["f_rev_curr"],
                        calculation_ids=[],
                        evidence_refs=[
                            EvidenceRef(
                                source_id="current",
                                exact_quote=quote,
                                start_offset=start,
                                end_offset=end,
                            )
                        ],
                    )
                ]
            ),
            coverage=V2Coverage(
                source_count=1,
                financial_fact_count=1,
                guidance_count=0,
                qualitative_observation_count=0,
                valid_calculation_count=0,
                unavailable_calculation_count=0,
            ),
        )

    def test_fixture_loading_from_default_directory(self) -> None:
        """Verify fixtures in backend/eval/fixtures/ load and validate cleanly."""
        fixtures = load_fixtures_from_directory()
        self.assertGreaterEqual(len(fixtures), 4)

        for fix in fixtures:
            self.assertIsInstance(fix, TranscriptFixture)
            self.assertTrue(len(fix.fixture_id) > 0)
            self.assertTrue(len(fix.company_name) > 0)
            self.assertGreaterEqual(len(fix.current_transcript), 200)
            for h in fix.historical_transcripts:
                self.assertGreaterEqual(len(h.transcript), 200)

            # Conversion to BenchmarkCase
            case = fix.to_benchmark_case()
            self.assertIsInstance(case, BenchmarkCase)
            self.assertEqual(case.case_id, fix.fixture_id)

    def test_malformed_fixture_handling(self) -> None:
        """Verify non-existent and malformed fixture JSON files raise expected errors."""
        with self.assertRaises(FileNotFoundError):
            load_fixture_file("non_existent_fixture_path_123.json")

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            tmp.write("{ invalid json content ...")
            tmp_path = tmp.name

        try:
            with self.assertRaises(ValueError) as ctx:
                load_fixture_file(tmp_path)
            self.assertIn("Failed to parse JSON", str(ctx.exception))
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_failure_taxonomy_classification(self) -> None:
        """Verify diagnostic findings map to structured failure categories and severities."""
        # 1. Missing fact
        f1 = classify_diagnostic_finding(
            "case_1", "fact_extraction", "error", "revenue", "Expected financial fact 'revenue' was not extracted."
        )
        self.assertEqual(f1.category, FailureCategory.MISSING_FACT)
        self.assertEqual(f1.severity, FailureSeverity.HIGH)
        self.assertEqual(f1.subsystem, Subsystem.EXTRACTION)

        # 2. Evidence offset mismatch
        f2 = classify_diagnostic_finding(
            "case_1", "evidence_grounding", "error", "f_rev", "Evidence offset slice does not match exact_quote."
        )
        self.assertEqual(f2.category, FailureCategory.EVIDENCE_ERROR)
        self.assertEqual(f2.severity, FailureSeverity.CRITICAL)
        self.assertEqual(f2.subsystem, Subsystem.EVIDENCE)

        # 3. Calculation mismatch
        f3 = classify_diagnostic_finding(
            "case_1", "calculation_correctness", "error", "percentage_change", "Calculation result mismatch."
        )
        self.assertEqual(f3.category, FailureCategory.CALCULATION_ERROR)
        self.assertEqual(f3.severity, FailureSeverity.HIGH)

        # 4. Incompatible currency comparability
        f4 = classify_diagnostic_finding(
            "case_1", "comparability_gate", "error", "percentage_change", "Expected incompatible comparison."
        )
        self.assertEqual(f4.category, FailureCategory.COMPARABILITY_ERROR)

        # 5. Thesis unprovenanced numbers
        f5 = classify_diagnostic_finding(
            "case_1", "thesis_grounding", "error", "item_0", "Interpretation contains numbers without referencing a calculation ID."
        )
        self.assertEqual(f5.category, FailureCategory.THESIS_GROUNDING_ERROR)
        self.assertEqual(f5.severity, FailureSeverity.CRITICAL)

    def test_v3_recommendations_synthesis(self) -> None:
        """Verify synthesis groups failures by frequency and produces prioritized V3 items."""
        failures = [
            ClassifiedFailure(
                case_id="c1",
                category=FailureCategory.MISSING_FACT,
                severity=FailureSeverity.HIGH,
                subsystem=Subsystem.EXTRACTION,
                message="Missing ARR",
            ),
            ClassifiedFailure(
                case_id="c2",
                category=FailureCategory.MISSING_FACT,
                severity=FailureSeverity.HIGH,
                subsystem=Subsystem.EXTRACTION,
                message="Missing retention rate",
            ),
            ClassifiedFailure(
                case_id="c1",
                category=FailureCategory.EVIDENCE_ERROR,
                severity=FailureSeverity.CRITICAL,
                subsystem=Subsystem.EVIDENCE,
                message="Quote offset mismatch",
            ),
        ]

        recommendations = synthesize_v3_recommendations(failures)
        self.assertEqual(len(recommendations), 2)
        # Top failure category should be MISSING_FACT with count 2
        self.assertEqual(recommendations[0].primary_failure_category, FailureCategory.MISSING_FACT)
        self.assertEqual(recommendations[0].observed_occurrence_count, 2)
        self.assertEqual(recommendations[0].area, "Transcript Extraction")
        self.assertEqual(recommendations[1].primary_failure_category, FailureCategory.EVIDENCE_ERROR)

    def test_evaluation_runner_with_latency_and_report_generation(self) -> None:
        """Test evaluation runner captures latency, report summary, and passes mock pipeline."""
        fixture = TranscriptFixture(
            fixture_id="test_fixture_enterprise",
            company_name="Enterprise Cloud",
            reporting_period="Q3 2026",
            description="Test fixture for evaluation runner",
            current_transcript=self.sample_current_transcript,
            ground_truth=FixtureGroundTruth(
                expected_facts=[
                    ExpectedFact(
                        metric_key="revenue",
                        reported_value="$300 million",
                        source_id="current",
                    )
                ]
            ),
        )

        def mock_pipeline(req: V2AnalysisRequest) -> V2AnalysisResponse:
            return self._build_mock_v2_response()

        report = run_evaluation(
            benchmark_cases=[fixture],
            pipeline_runner=mock_pipeline,
        )

        self.assertIsInstance(report, EvaluationReport)
        self.assertEqual(report.total_cases, 1)
        self.assertEqual(report.passed_cases, 1)
        self.assertIsNotNone(report.case_results[0].latency_ms)
        self.assertGreater(report.case_results[0].latency_ms, 0)

        summary = report.summary_text()
        self.assertIn("CALLQ V2.8 FINANCIAL INTELLIGENCE EVALUATION", summary)
        self.assertIn("test_fixture_enterprise", summary)
        self.assertIn("PASS", summary)

    def test_runner_safely_captures_provider_exceptions(self) -> None:
        """Verify pipeline provider exceptions produce structured PROVIDER_ERROR without crashing."""
        fixture = TranscriptFixture(
            fixture_id="test_provider_fail",
            company_name="Failing Provider Test",
            reporting_period="Q3 2026",
            description="Testing provider exception capture",
            current_transcript=self.sample_current_transcript,
        )

        def failing_pipeline(req: V2AnalysisRequest) -> V2AnalysisResponse:
            raise RuntimeError("Gemini API error 503: Service Unavailable")

        report = run_evaluation(
            benchmark_cases=[fixture],
            pipeline_runner=failing_pipeline,
        )

        self.assertEqual(report.total_cases, 1)
        self.assertEqual(report.passed_cases, 0)
        self.assertEqual(report.failed_cases, 1)
        self.assertEqual(len(report.v3_recommendations), 1)
        self.assertEqual(report.v3_recommendations[0].primary_failure_category, FailureCategory.PROVIDER_ERROR)
        self.assertIn("PROVIDER_ERROR", report.summary_text())


if __name__ == "__main__":
    unittest.main()
