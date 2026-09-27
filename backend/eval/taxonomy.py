"""V2.8 Failure taxonomy and failure-driven V3 recommendation engine."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Sequence
from pydantic import BaseModel, ConfigDict, Field


class FailureCategory(str, Enum):
    """Structured failure categories identifying specific V2 weaknesses."""

    EXTRACTION_ERROR = "EXTRACTION_ERROR"
    MISSING_FACT = "MISSING_FACT"
    WRONG_FACT = "WRONG_FACT"
    EVIDENCE_ERROR = "EVIDENCE_ERROR"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    COMPARABILITY_ERROR = "COMPARABILITY_ERROR"
    THESIS_GROUNDING_ERROR = "THESIS_GROUNDING_ERROR"
    MISSING_GUIDANCE = "MISSING_GUIDANCE"
    FALSE_GUIDANCE = "FALSE_GUIDANCE"
    UNAVAILABLE_DATA_HANDLING = "UNAVAILABLE_DATA_HANDLING"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    OTHER = "OTHER"


class FailureSeverity(str, Enum):
    """Severity classification for evaluation failures."""

    CRITICAL = "critical"  # Pipeline crash, hallucinated fact/number, ungrounded advice
    HIGH = "high"          # Missing key metric, incorrect calculation result, bad comparability
    MEDIUM = "medium"      # Minor unit/period discrepancy, missing secondary evidence gap
    LOW = "low"            # Minor formatting or whitespace variation


class Subsystem(str, Enum):
    """V2 architecture subsystem responsible for the finding."""

    EXTRACTION = "extraction"
    EVIDENCE = "evidence"
    CALCULATION = "calculation"
    COMPARABILITY = "comparability"
    INTERPRETATION = "interpretation"
    PROVIDER = "provider"
    FIXTURE = "fixture"


class ClassifiedFailure(BaseModel):
    """Structured diagnostic failure with taxonomy classification and severity."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    category: FailureCategory
    severity: FailureSeverity
    subsystem: Subsystem
    target_id: Optional[str] = None
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)


class V3Recommendation(BaseModel):
    """Actionable improvement recommendation for V3 derived from observed failures."""

    model_config = ConfigDict(extra="forbid")

    area: str
    title: str
    description: str
    priority: Literal["critical", "high", "medium", "low"]
    primary_failure_category: FailureCategory
    affected_subsystem: Subsystem
    observed_occurrence_count: int = 1


def classify_diagnostic_finding(
    case_id: str,
    diagnostic_category: str,
    severity_str: str,
    target_id: Optional[str],
    message: str,
) -> ClassifiedFailure:
    """Classify a diagnostic finding into the standardized V2.8 failure taxonomy."""
    msg_lower = message.lower()

    if diagnostic_category == "fact_extraction":
        if "was not extracted" in msg_lower or "missing" in msg_lower:
            category = FailureCategory.MISSING_FACT
            severity = FailureSeverity.HIGH
        elif "mismatch" in msg_lower or "variation" in msg_lower:
            category = FailureCategory.WRONG_FACT
            severity = FailureSeverity.MEDIUM if severity_str == "warning" else FailureSeverity.HIGH
        else:
            category = FailureCategory.EXTRACTION_ERROR
            severity = FailureSeverity.HIGH
        subsystem = Subsystem.EXTRACTION

    elif diagnostic_category == "guidance_extraction":
        if "empty guidance" in msg_lower:
            category = FailureCategory.FALSE_GUIDANCE
            severity = FailureSeverity.HIGH
        elif "not found" in msg_lower or "missing" in msg_lower:
            category = FailureCategory.MISSING_GUIDANCE
            severity = FailureSeverity.HIGH
        else:
            category = FailureCategory.EXTRACTION_ERROR
            severity = FailureSeverity.HIGH
        subsystem = Subsystem.EXTRACTION

    elif diagnostic_category == "evidence_grounding":
        category = FailureCategory.EVIDENCE_ERROR
        severity = FailureSeverity.CRITICAL if "slice does not match" in msg_lower or "unknown source" in msg_lower else FailureSeverity.HIGH
        subsystem = Subsystem.EVIDENCE

    elif diagnostic_category == "calculation_correctness":
        category = FailureCategory.CALCULATION_ERROR
        severity = FailureSeverity.HIGH
        subsystem = Subsystem.CALCULATION

    elif diagnostic_category == "comparability_gate":
        if "unavailable" in msg_lower or "incompatible" in msg_lower:
            category = FailureCategory.COMPARABILITY_ERROR
            severity = FailureSeverity.HIGH if severity_str == "error" else FailureSeverity.MEDIUM
        else:
            category = FailureCategory.UNAVAILABLE_DATA_HANDLING
            severity = FailureSeverity.MEDIUM
        subsystem = Subsystem.COMPARABILITY

    elif diagnostic_category == "thesis_grounding":
        category = FailureCategory.THESIS_GROUNDING_ERROR
        if "without referencing a calculation" in msg_lower or "numbers" in msg_lower:
            severity = FailureSeverity.CRITICAL
        else:
            severity = FailureSeverity.HIGH
        subsystem = Subsystem.INTERPRETATION

    elif diagnostic_category == "hallucination":
        category = FailureCategory.THESIS_GROUNDING_ERROR
        severity = FailureSeverity.CRITICAL
        subsystem = Subsystem.INTERPRETATION

    else:
        category = FailureCategory.OTHER
        severity = FailureSeverity.MEDIUM
        subsystem = Subsystem.EXTRACTION

    return ClassifiedFailure(
        case_id=case_id,
        category=category,
        severity=severity,
        subsystem=subsystem,
        target_id=target_id,
        message=message,
    )


# Mapping of failure categories to specific, concrete V3 architectural recommendations
V3_RECOMMENDATION_TEMPLATES: Dict[FailureCategory, Dict[str, Any]] = {
    FailureCategory.MISSING_FACT: {
        "area": "Transcript Extraction",
        "title": "Multi-Segment & Financial Metric Extraction Granularity",
        "description": "Improve extraction recall for non-primary metrics (e.g. segment revenue, retention rates, capex, deferred revenue) by expanding extraction schemas and few-shot prompt guidance.",
        "priority": "high",
        "affected_subsystem": Subsystem.EXTRACTION,
    },
    FailureCategory.WRONG_FACT: {
        "area": "Metric Normalization",
        "title": "Robust Multi-Scale and Currency Unit Normalizer",
        "description": "Harden the financial value parser to automatically handle mixed scale terms (e.g. 'thousands', 'millions'), non-standard currency symbols, and fiscal calendar variations.",
        "priority": "medium",
        "affected_subsystem": Subsystem.CALCULATION,
    },
    FailureCategory.EVIDENCE_ERROR: {
        "area": "Evidence Grounding",
        "title": "Fuzzy Whitespace & Normalized Quote Resolution",
        "description": "Support whitespace-resilient and punctuation-normalized quote matching in the evidence resolution layer so minor transcript formatting differences do not reject valid quotes.",
        "priority": "critical",
        "affected_subsystem": Subsystem.EVIDENCE,
    },
    FailureCategory.CALCULATION_ERROR: {
        "area": "Financial Calculations",
        "title": "Expanded Financial Calculation Catalog & Precision Rules",
        "description": "Add support for CAGR, annualized run rates, basis points conversions, and GAAP vs Adjusted EBITDA bridge calculations with explicit rounding rules.",
        "priority": "high",
        "affected_subsystem": Subsystem.CALCULATION,
    },
    FailureCategory.COMPARABILITY_ERROR: {
        "area": "Historical Comparability",
        "title": "Automated Cross-Period & Accounting Standard Comparability Gates",
        "description": "Strengthen comparability detection for calendar shifts, M&A restatements, currency fluctuations (constant-currency vs reported), and non-GAAP definition changes.",
        "priority": "high",
        "affected_subsystem": Subsystem.COMPARABILITY,
    },
    FailureCategory.THESIS_GROUNDING_ERROR: {
        "area": "Interpretation Grounding",
        "title": "Multi-Hop Claim Verification & Numeric Attribution",
        "description": "Enforce strict AST/graph linking between qualitative thesis points, Python calculation IDs, and source quotes to ensure zero unprovenanced numbers in Bull/Bear/Watch claims.",
        "priority": "critical",
        "affected_subsystem": Subsystem.INTERPRETATION,
    },
    FailureCategory.MISSING_GUIDANCE: {
        "area": "Guidance Interpretation",
        "title": "Conditional & Multi-Metric Guidance Extraction",
        "description": "Expand guidance extraction to capture conditional ranges (e.g. 'assuming FX tailwinds'), full-year vs quarter guidance, and non-revenue targets (e.g. operating margin, EPS guidance).",
        "priority": "high",
        "affected_subsystem": Subsystem.EXTRACTION,
    },
    FailureCategory.FALSE_GUIDANCE: {
        "area": "Guidance Filtering",
        "title": "Qualitative Outlook vs Formal Guidance Boundary",
        "description": "Clarify prompt schemas to prevent general positive management commentary from being misclassified as quantitative forward guidance when no explicit numerical range is given.",
        "priority": "high",
        "affected_subsystem": Subsystem.EXTRACTION,
    },
    FailureCategory.PROVIDER_ERROR: {
        "area": "Provider Resilience",
        "title": "Adaptive Exponential Backoff & Secondary Provider Fallback",
        "description": "Implement structured retry policies with exponential backoff for transient provider 503 capacity spikes and fallback model routing.",
        "priority": "high",
        "affected_subsystem": Subsystem.PROVIDER,
    },
    FailureCategory.UNAVAILABLE_DATA_HANDLING: {
        "area": "Data Transparency",
        "title": "Automated Gap Explanation & Missing Input Ledger",
        "description": "Generate explicit user-facing explanations for missing inputs, incomplete disclosures, and why specific historical comparisons could not be completed.",
        "priority": "medium",
        "affected_subsystem": Subsystem.INTERPRETATION,
    },
}


def synthesize_v3_recommendations(
    failures: Sequence[ClassifiedFailure],
) -> List[V3Recommendation]:
    """Derive prioritized V3 recommendations based on observed failure categories."""
    category_counts: Dict[FailureCategory, int] = {}
    for f in failures:
        category_counts[f.category] = category_counts.get(f.category, 0) + 1

    recommendations: List[V3Recommendation] = []
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        template = V3_RECOMMENDATION_TEMPLATES.get(cat)
        if template:
            recommendations.append(
                V3Recommendation(
                    area=template["area"],
                    title=template["title"],
                    description=template["description"],
                    priority=template["priority"],
                    primary_failure_category=cat,
                    affected_subsystem=template["affected_subsystem"],
                    observed_occurrence_count=count,
                )
            )

    return recommendations
