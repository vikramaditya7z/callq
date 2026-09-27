"""V2.8 Real-world financial intelligence evaluation and failure-analysis layer."""

from backend.eval.evaluator import evaluate_v2_response, format_evaluation_summary
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
    V3Recommendation,
    classify_diagnostic_finding,
    synthesize_v3_recommendations,
)

__all__ = [
    "BenchmarkCase",
    "CaseEvaluationResult",
    "ClassifiedFailure",
    "DiagnosticFinding",
    "EvaluationReport",
    "ExpectedCalculation",
    "ExpectedFact",
    "ExpectedGuidance",
    "FailureCategory",
    "FailureSeverity",
    "FixtureGroundTruth",
    "MetricScore",
    "Subsystem",
    "TranscriptFixture",
    "V3Recommendation",
    "classify_diagnostic_finding",
    "evaluate_v2_response",
    "format_evaluation_summary",
    "load_fixture_file",
    "load_fixtures_from_directory",
    "run_evaluation",
    "synthesize_v3_recommendations",
]
