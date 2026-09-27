"""Execution runner for evaluating CallQ V2 against benchmark suites and real-world fixtures."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, List, Optional, Union

from backend.eval.benchmarks.cases import ALL_BENCHMARK_CASES
from backend.eval.evaluator import evaluate_v2_response
from backend.eval.fixtures_loader import (
    TranscriptFixture,
    load_fixtures_from_directory,
)
from backend.eval.models import (
    BenchmarkCase,
    CaseEvaluationResult,
    DiagnosticFinding,
    EvaluationReport,
    MetricScore,
)
from backend.eval.taxonomy import (
    ClassifiedFailure,
    FailureCategory,
    FailureSeverity,
    Subsystem,
    synthesize_v3_recommendations,
)
from backend.models.v2_analysis import V2AnalysisRequest, V2AnalysisResponse
from backend.services.v2_analysis_service import run_v2_analysis


PipelineCallable = Callable[[V2AnalysisRequest], V2AnalysisResponse]


def run_evaluation(
    benchmark_cases: Optional[
        List[Union[BenchmarkCase, TranscriptFixture]]
    ] = None,
    fixtures_dir: Optional[Union[Path, str]] = None,
    pipeline_runner: Optional[PipelineCallable] = None,
) -> EvaluationReport:
    """Run evaluation across benchmark cases or fixtures and produce an aggregate report."""
    runner = pipeline_runner if pipeline_runner is not None else run_v2_analysis

    # Resolve target cases
    cases: List[BenchmarkCase] = []
    if benchmark_cases is not None:
        for item in benchmark_cases:
            if isinstance(item, TranscriptFixture):
                cases.append(item.to_benchmark_case())
            else:
                cases.append(item)
    elif fixtures_dir is not None:
        fixtures = load_fixtures_from_directory(fixtures_dir)
        cases = [f.to_benchmark_case() for f in fixtures]
    else:
        # Load from default fixtures directory if present, otherwise built-in cases
        fixtures = load_fixtures_from_directory()
        if fixtures:
            cases = [f.to_benchmark_case() for f in fixtures]
        else:
            cases = ALL_BENCHMARK_CASES

    case_results: List[CaseEvaluationResult] = []

    for case in cases:
        start_time = time.perf_counter()
        try:
            response = runner(case.request)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result = evaluate_v2_response(case, response, latency_ms=round(elapsed_ms, 2))
        except Exception as error:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            err_msg = str(error)
            is_provider = "provider" in err_msg.lower() or "gemini" in err_msg.lower() or "503" in err_msg

            failure = ClassifiedFailure(
                case_id=case.case_id,
                category=FailureCategory.PROVIDER_ERROR if is_provider else FailureCategory.EXTRACTION_ERROR,
                severity=FailureSeverity.CRITICAL,
                subsystem=Subsystem.PROVIDER if is_provider else Subsystem.EXTRACTION,
                message=f"Pipeline execution raised {type(error).__name__}: {err_msg}",
            )
            result = CaseEvaluationResult(
                case_id=case.case_id,
                name=case.name,
                passed=False,
                fact_extraction=MetricScore(passed=0, total=len(case.expected_facts) or 1),
                guidance_extraction=MetricScore(passed=0, total=len(case.expected_guidance) or 1),
                evidence_grounding=MetricScore(passed=0, total=1),
                calculation_correctness=MetricScore(passed=0, total=len(case.expected_calculations) or 1),
                comparability_correctness=MetricScore(passed=0, total=1),
                thesis_grounding=MetricScore(passed=0, total=1),
                hallucination_free=False,
                latency_ms=round(elapsed_ms, 2),
                findings=[
                    DiagnosticFinding(
                        category="provider" if is_provider else "fact_extraction",
                        severity="critical",
                        message=failure.message,
                    )
                ],
                classified_failures=[failure],
            )
        case_results.append(result)

    passed_cases = sum(1 for res in case_results if res.passed)
    failed_cases = len(case_results) - passed_cases
    mean_accuracy = (
        sum(res.overall_accuracy for res in case_results) / len(case_results)
        if case_results
        else 1.0
    )

    all_failures = [f for res in case_results for f in res.classified_failures]
    recommendations = synthesize_v3_recommendations(all_failures)

    return EvaluationReport(
        total_cases=len(case_results),
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        mean_accuracy=round(mean_accuracy, 4),
        case_results=case_results,
        v3_recommendations=recommendations,
    )
