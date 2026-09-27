"""Data models for V2.8 benchmark fixtures and failure-analysis reports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.eval.taxonomy import ClassifiedFailure, V3Recommendation
from backend.models.v2_analysis import V2AnalysisRequest


class EvalModel(BaseModel):
    """Base model with strict validation for evaluation contracts."""

    model_config = ConfigDict(extra="forbid")


class ExpectedFact(EvalModel):
    """Expected financial fact criteria for extraction evaluation."""

    metric_key: str
    reported_value: str
    source_id: str = "current"
    unit: Optional[str] = None
    period: Optional[str] = None
    period_type: Optional[str] = None
    expected_quote_substring: Optional[str] = None


class ExpectedGuidance(EvalModel):
    """Expected guidance criteria for extraction evaluation."""

    metric_key: str
    guidance_value: str
    source_id: str = "current"
    unit: Optional[str] = None
    period: Optional[str] = None
    expected_quote_substring: Optional[str] = None


class ExpectedCalculation(EvalModel):
    """Expected deterministic calculation outcome."""

    calculation_type: str
    metric_key: Optional[str] = None
    status: Literal["valid", "unavailable"] = "valid"
    expected_result: Optional[float] = None
    expected_unit: Optional[str] = None
    expected_reason_substring: Optional[str] = None
    tolerance: float = 0.02


class BenchmarkCase(EvalModel):
    """A standalone test fixture containing input transcripts and ground truth expectations."""

    case_id: str
    name: str
    description: str
    request: V2AnalysisRequest
    expected_facts: List[ExpectedFact] = Field(default_factory=list)
    expected_guidance: List[ExpectedGuidance] = Field(default_factory=list)
    expected_calculations: List[ExpectedCalculation] = Field(default_factory=list)
    expected_evidence_gaps: List[str] = Field(default_factory=list)
    prohibited_claims: List[str] = Field(default_factory=list)
    require_empty_guidance: bool = False


class DiagnosticFinding(EvalModel):
    """Specific explainable diagnostic finding for an evaluation check."""

    category: Literal[
        "fact_extraction",
        "guidance_extraction",
        "evidence_grounding",
        "calculation_correctness",
        "comparability_gate",
        "thesis_grounding",
        "hallucination",
        "provider",
    ]
    severity: Literal["critical", "high", "medium", "low", "error", "warning", "info"]
    target_id: Optional[str] = None
    message: str


class MetricScore(EvalModel):
    """Normalized scoring summary for one evaluation category."""

    passed: int = 0
    total: int = 0

    @property
    def score(self) -> float:
        """Calculate the ratio between 0.0 and 1.0 (defaults to 1.0 if total is 0)."""
        if self.total == 0:
            return 1.0
        return round(self.passed / self.total, 4)


class CaseEvaluationResult(EvalModel):
    """Detailed evaluation results for a single benchmark case."""

    case_id: str
    name: str
    passed: bool
    fact_extraction: MetricScore
    guidance_extraction: MetricScore
    evidence_grounding: MetricScore
    calculation_correctness: MetricScore
    comparability_correctness: MetricScore
    thesis_grounding: MetricScore
    hallucination_free: bool
    latency_ms: Optional[float] = None
    findings: List[DiagnosticFinding] = Field(default_factory=list)
    classified_failures: List[ClassifiedFailure] = Field(default_factory=list)

    @property
    def overall_accuracy(self) -> float:
        """Weighted aggregate accuracy across applicable evaluation dimensions."""
        scores = [
            self.fact_extraction.score,
            self.guidance_extraction.score,
            self.evidence_grounding.score,
            self.calculation_correctness.score,
            self.comparability_correctness.score,
            self.thesis_grounding.score,
        ]
        if not self.hallucination_free:
            scores.append(0.0)
        return round(sum(scores) / len(scores), 4)


class EvaluationReport(EvalModel):
    """Machine-readable aggregate evaluation report across all benchmark cases."""

    total_cases: int
    passed_cases: int
    failed_cases: int
    mean_accuracy: float
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    case_results: List[CaseEvaluationResult] = Field(default_factory=list)
    v3_recommendations: List[V3Recommendation] = Field(default_factory=list)

    def summary_text(self) -> str:
        """Generate a concise human-readable evaluation summary."""
        lines = [
            "==================================================================",
            "             CALLQ V2.8 FINANCIAL INTELLIGENCE EVALUATION         ",
            "==================================================================",
            f"Timestamp: {self.timestamp}",
            f"Total Benchmark Cases: {self.total_cases}",
            f"Passed: {self.passed_cases} | Failed: {self.failed_cases}",
            f"Mean Accuracy Score: {self.mean_accuracy * 100:.1f}%",
            "------------------------------------------------------------------",
            f"{'Case ID':<30} {'Status':<6} {'Accuracy':<9} {'Latency':<9} {'Failures':<8}",
            "------------------------------------------------------------------",
        ]
        for res in self.case_results:
            status_str = "PASS" if res.passed else "FAIL"
            err_count = len(res.classified_failures)
            lat_str = f"{res.latency_ms:.0f}ms" if res.latency_ms is not None else "N/A"
            lines.append(
                f"{res.case_id:<30} {status_str:<6} {res.overall_accuracy * 100:>5.1f}%   {lat_str:<9} {err_count:<8}"
            )
        lines.append("------------------------------------------------------------------")

        # Collect all classified failures
        all_failures = [
            f for res in self.case_results for f in res.classified_failures
        ]
        if all_failures:
            lines.append("\nCLASSIFIED FAILURES:")
            for failure in all_failures:
                lines.append(
                    f"  [{failure.case_id}] [{failure.category.value}] ({failure.severity.value.upper()}) {failure.message}"
                )
        else:
            lines.append("\nZero failures detected across evaluated benchmark cases.")

        if self.v3_recommendations:
            lines.append("\nRECOMMENDED V3 PRIORITIES (FAILURE-DRIVEN):")
            for idx, rec in enumerate(self.v3_recommendations, start=1):
                lines.append(
                    f"  {idx}. [{rec.priority.upper()}] {rec.area}: {rec.title}"
                )
                lines.append(f"     -> {rec.description} (occurrences: {rec.observed_occurrence_count})")

        lines.append("==================================================================")
        return "\n".join(lines)
