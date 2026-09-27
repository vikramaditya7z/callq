"""Unit tests for the V2.7 evaluation harness and benchmark framework."""

from __future__ import annotations

import unittest

from backend.eval.benchmarks.cases import (
    ALL_BENCHMARK_CASES,
    CASE_CROSS_BORDER_INCOMPATIBLE_CURRENCY,
    CASE_LIMITED_DISCLOSURE_NO_GUIDANCE,
    CASE_MANUFACTURING_MARGIN_CONTRACTION,
    CASE_SAAS_ENTERPRISE_GROWTH,
)
from backend.eval.evaluator import evaluate_v2_response, format_evaluation_summary
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
from backend.models.v2_analysis import (
    Calculation,
    EvidenceGap,
    EvidenceRef,
    FinancialFact,
    GuidanceFact,
    InterpretationItem,
    QualitativeObservation,
    SourceDocument,
    V2AnalysisRequest,
    V2AnalysisResponse,
    V2Coverage,
    V2ExtractionResponse,
    V2InterpretationResponse,
)


class V27EvaluationHarnessTests(unittest.TestCase):
    """Verify evaluation engine correctness, diagnostics, and reporting."""

    def setUp(self) -> None:
        self.doc_current = SourceDocument(
            source_id="current",
            document_type="current_earnings_call_transcript",
            text=(
                "Operator: Welcome to CloudScale Q3 2026 earnings conference call. "
                "CloudScale reported revenue of $300 million for Q3 2026. "
                "Gross margin was 75 percent for the quarter. "
                "Management expects revenue between $315 million and $325 million next quarter. "
                "Enterprise demand was resilient across all customer sectors."
            ),
        )
        self.doc_hist = SourceDocument(
            source_id="historical_1_q3-2025",
            document_type="historical_earnings_call_transcript",
            text=(
                "Operator: Welcome to CloudScale Q3 2025 earnings conference call. "
                "CloudScale reported revenue of $250 million for Q3 2025. "
                "Gross margin was 72 percent for the period. "
                "Enterprise demand was steady across all commercial teams."
            ),
        )

    def _build_mock_response(
        self,
        facts: list[FinancialFact] | None = None,
        guidance: list[GuidanceFact] | None = None,
        calculations: list[Calculation] | None = None,
        thesis: V2InterpretationResponse | None = None,
    ) -> V2AnalysisResponse:
        quote_curr = "revenue of $300 million"
        curr_start = self.doc_current.text.find(quote_curr)
        curr_end = curr_start + len(quote_curr)

        quote_hist = "revenue of $250 million"
        hist_start = self.doc_hist.text.find(quote_hist)
        hist_end = hist_start + len(quote_hist)

        quote_guid = "revenue between $315 million and $325 million"
        guid_start = self.doc_current.text.find(quote_guid)
        guid_end = guid_start + len(quote_guid)

        f_list = facts if facts is not None else [
            FinancialFact(
                fact_id="f_rev_curr",
                metric_key="revenue",
                reported_value="$300 million",
                unit="USD",
                period="Q3 2026",
                period_type="quarterly",
                evidence=EvidenceRef(
                    source_id="current",
                    exact_quote=quote_curr,
                    start_offset=curr_start,
                    end_offset=curr_end,
                ),
            ),
            FinancialFact(
                fact_id="f_rev_hist",
                metric_key="revenue",
                reported_value="$250 million",
                unit="USD",
                period="Q3 2025",
                period_type="quarterly",
                evidence=EvidenceRef(
                    source_id="historical_1_q3-2025",
                    exact_quote=quote_hist,
                    start_offset=hist_start,
                    end_offset=hist_end,
                ),
            ),
        ]
        g_list = guidance if guidance is not None else [
            GuidanceFact(
                fact_id="g_rev_q4",
                metric_key="revenue",
                guidance_value="$315 million to $325 million",
                unit="USD",
                period="Q4 2026",
                evidence=EvidenceRef(
                    source_id="current",
                    exact_quote=quote_guid,
                    start_offset=guid_start,
                    end_offset=guid_end,
                ),
            )
        ]
        c_list = calculations if calculations is not None else [
            Calculation(
                calculation_id="c_pct_growth",
                calculation_type="percentage_change",
                input_fact_ids=["f_rev_curr", "f_rev_hist"],
                formula="((current - previous) / previous) * 100",
                result=20.0,
                unit="percent",
                status="valid",
            )
        ]
        t_obj = thesis if thesis is not None else V2InterpretationResponse(
            bull_items=[
                InterpretationItem(
                    claim="Revenue expanded with enterprise momentum.",
                    why_it_matters="Solid business growth.",
                    supporting_fact_ids=["f_rev_curr"],
                    calculation_ids=[],
                    evidence_refs=[
                        EvidenceRef(
                            source_id="current",
                            exact_quote=quote_curr,
                            start_offset=curr_start,
                            end_offset=curr_end,
                        )
                    ],
                )
            ]
        )

        return V2AnalysisResponse(
            source_documents=[self.doc_current, self.doc_hist],
            facts=V2ExtractionResponse(
                financial_facts=f_list,
                guidance=g_list,
                qualitative_observations=[],
            ),
            calculations=c_list,
            thesis=t_obj,
            coverage=V2Coverage(
                source_count=2,
                financial_fact_count=len(f_list),
                guidance_count=len(g_list),
                qualitative_observation_count=0,
                valid_calculation_count=sum(1 for c in c_list if c.status == "valid"),
                unavailable_calculation_count=sum(1 for c in c_list if c.status == "unavailable"),
            ),
        )

    def test_benchmark_cases_integrity(self) -> None:
        """Verify all benchmark cases are properly configured."""
        self.assertGreaterEqual(len(ALL_BENCHMARK_CASES), 4)
        for case in ALL_BENCHMARK_CASES:
            self.assertTrue(case.case_id.startswith("case_"))
            self.assertGreater(len(case.name), 5)
            self.assertGreater(len(case.request.current_transcript), 50)

    def test_evaluate_facts_matching_and_diagnostics(self) -> None:
        """Test fact extraction scoring and missing fact diagnostics."""
        case = BenchmarkCase(
            case_id="case_test_facts",
            name="Test Facts",
            description="Testing fact evaluator",
            request=V2AnalysisRequest(current_transcript=self.doc_current.text),
            expected_facts=[
                ExpectedFact(metric_key="revenue", reported_value="$300 million", source_id="current"),
                ExpectedFact(metric_key="missing_metric", reported_value="10%", source_id="current"),
            ],
        )
        response = self._build_mock_response()
        result = evaluate_v2_response(case, response)

        self.assertFalse(result.passed)
        self.assertEqual(result.fact_extraction.passed, 1)
        self.assertEqual(result.fact_extraction.total, 2)
        error_finding = next(f for f in result.findings if f.category == "fact_extraction")
        self.assertIn("missing_metric", error_finding.message)

    def test_evaluate_guidance_empty_requirement(self) -> None:
        """Test require_empty_guidance enforcement."""
        case = BenchmarkCase(
            case_id="case_test_no_guidance",
            name="Test No Guidance",
            description="Testing empty guidance",
            request=V2AnalysisRequest(current_transcript=self.doc_current.text),
            require_empty_guidance=True,
        )

        # Case 1: Response has guidance -> should fail
        resp_with_guidance = self._build_mock_response()
        res_fail = evaluate_v2_response(case, resp_with_guidance)
        self.assertFalse(res_fail.passed)
        self.assertEqual(res_fail.guidance_extraction.score, 0.0)

        # Case 2: Response has empty guidance -> should pass
        resp_without_guidance = self._build_mock_response(guidance=[])
        res_pass = evaluate_v2_response(case, resp_without_guidance)
        self.assertEqual(res_pass.guidance_extraction.score, 1.0)

    def test_evaluate_evidence_grounding_valid_and_corrupt(self) -> None:
        """Test evidence grounding detects offset and quote mismatches."""
        case = BenchmarkCase(
            case_id="case_test_evidence",
            name="Test Evidence",
            description="Testing evidence",
            request=V2AnalysisRequest(current_transcript=self.doc_current.text),
        )

        # Corrupt offset
        corrupt_fact = FinancialFact(
            fact_id="f_corrupt",
            metric_key="revenue",
            reported_value="$300 million",
            evidence=EvidenceRef(
                source_id="current",
                exact_quote="revenue of $300 million",
                start_offset=0,  # Incorrect start offset
                end_offset=23,
            ),
        )
        response = self._build_mock_response(facts=[corrupt_fact])
        result = evaluate_v2_response(case, response)

        self.assertFalse(result.passed)
        evidence_finding = next(f for f in result.findings if f.category == "evidence_grounding")
        self.assertIn("offset slice does not match", evidence_finding.message)

    def test_evaluate_calculations_accuracy_and_tolerance(self) -> None:
        """Test calculation numerical validation with tolerances."""
        case = BenchmarkCase(
            case_id="case_test_calc",
            name="Test Calc",
            description="Testing calculation evaluation",
            request=V2AnalysisRequest(current_transcript=self.doc_current.text),
            expected_calculations=[
                ExpectedCalculation(
                    calculation_type="percentage_change",
                    status="valid",
                    expected_result=20.0,
                    tolerance=0.01,
                ),
                ExpectedCalculation(
                    calculation_type="margin_change",
                    status="valid",
                    expected_result=3.0,
                ),
            ],
        )
        # Mock response only contains percentage_change, not margin_change
        response = self._build_mock_response()
        result = evaluate_v2_response(case, response)

        self.assertFalse(result.passed)
        self.assertEqual(result.calculation_correctness.passed, 1)
        self.assertEqual(result.calculation_correctness.total, 2)
        calc_finding = next(f for f in result.findings if f.category == "calculation_correctness")
        self.assertIn("margin_change", calc_finding.message)

    def test_evaluate_comparability_gates(self) -> None:
        """Test comparability evaluator validates unavailable status and reason."""
        case = BenchmarkCase(
            case_id="case_test_comp",
            name="Test Comparability",
            description="Testing comparability gating",
            request=V2AnalysisRequest(current_transcript=self.doc_current.text),
            expected_calculations=[
                ExpectedCalculation(
                    calculation_type="percentage_change",
                    status="unavailable",
                    expected_reason_substring="incompatible currencies",
                )
            ],
        )
        unavail_calc = Calculation(
            calculation_id="c_unavail",
            calculation_type="percentage_change",
            input_fact_ids=["f1", "f2"],
            formula="((current - previous) / previous) * 100",
            result=None,
            status="unavailable",
            reason="Facts have incompatible currencies.",
        )
        response = self._build_mock_response(calculations=[unavail_calc])
        result = evaluate_v2_response(case, response)

        self.assertTrue(result.passed)
        self.assertEqual(result.comparability_correctness.score, 1.0)

    def test_evaluate_thesis_grounding_and_prohibited_claims(self) -> None:
        """Test thesis grounding flags unprovenanced numbers and prohibited advice."""
        case = BenchmarkCase(
            case_id="case_test_thesis",
            name="Test Thesis",
            description="Testing thesis grounding",
            request=V2AnalysisRequest(current_transcript=self.doc_current.text),
            prohibited_claims=["market leader"],
        )

        quote = "revenue of $300 million"
        start = self.doc_current.text.find(quote)
        end = start + len(quote)

        # 1. Prohibited advice: "buy"
        bad_thesis_1 = V2InterpretationResponse(
            bull_items=[
                InterpretationItem(
                    claim="Investors should buy the stock immediately.",
                    why_it_matters="Strong upside.",
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
        )
        res_1 = evaluate_v2_response(case, self._build_mock_response(thesis=bad_thesis_1))
        self.assertFalse(res_1.hallucination_free)
        hallucination_finding_1 = next(f for f in res_1.findings if f.category == "hallucination")
        self.assertIn("prohibited recommendation", hallucination_finding_1.message)

        # 2. Case prohibited claim: "market leader"
        bad_thesis_2 = V2InterpretationResponse(
            bull_items=[
                InterpretationItem(
                    claim="Company is now the market leader in cloud.",
                    why_it_matters="Scale advantages.",
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
        )
        res_2 = evaluate_v2_response(case, self._build_mock_response(thesis=bad_thesis_2))
        self.assertFalse(res_2.hallucination_free)
        hallucination_finding_2 = next(f for f in res_2.findings if f.category == "hallucination")
        self.assertIn("explicitly prohibited claim", hallucination_finding_2.message)

    def test_run_evaluation_runner_and_report_summary(self) -> None:
        """Test runner execution across multiple benchmark cases."""
        # Simple synthetic adapter that returns a valid mock response for any case
        def mock_pipeline(req: V2AnalysisRequest) -> V2AnalysisResponse:
            return self._build_mock_response()

        report = run_evaluation(
            benchmark_cases=[CASE_SAAS_ENTERPRISE_GROWTH],
            pipeline_runner=mock_pipeline,
        )

        self.assertIsInstance(report, EvaluationReport)
        self.assertEqual(report.total_cases, 1)
        self.assertIsInstance(report.summary_text(), str)
        self.assertIn("FINANCIAL INTELLIGENCE EVALUATION", report.summary_text())

    def test_report_serialization(self) -> None:
        """Test report JSON dumping and re-validation."""
        report = EvaluationReport(
            total_cases=2,
            passed_cases=2,
            failed_cases=0,
            mean_accuracy=1.0,
            case_results=[],
        )
        data = report.model_dump(mode="json")
        reloaded = EvaluationReport.model_validate(data)
        self.assertEqual(reloaded.total_cases, 2)
        self.assertEqual(reloaded.mean_accuracy, 1.0)


if __name__ == "__main__":
    unittest.main()
