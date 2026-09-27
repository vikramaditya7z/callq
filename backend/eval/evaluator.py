"""Core evaluation engine for CallQ V2 responses against benchmark expectations."""

from __future__ import annotations

import math
import re
from typing import Dict, List, Optional, Sequence, Tuple

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
from backend.models.v2_analysis import (
    Calculation,
    FinancialFact,
    GuidanceFact,
    InterpretationItem,
    QualitativeObservation,
    SourceDocument,
    V2AnalysisResponse,
)


NUMERIC_PATTERN = re.compile(r"\d")
PROHIBITED_RECOMMENDATIONS = re.compile(
    r"\b(buy|sell|hold|price target|investment recommendation|portfolio advice)\b",
    re.IGNORECASE,
)


from backend.eval.taxonomy import classify_diagnostic_finding


def evaluate_v2_response(
    case: BenchmarkCase,
    response: V2AnalysisResponse,
    latency_ms: Optional[float] = None,
) -> CaseEvaluationResult:
    """Evaluate a V2 analysis response against a benchmark ground truth case."""
    findings: List[DiagnosticFinding] = []
    documents_by_id = {doc.source_id: doc for doc in response.source_documents}

    # 1. Fact Extraction Evaluation
    fact_score = _evaluate_facts(case.expected_facts, response.facts.financial_facts, findings)

    # 2. Guidance Extraction Evaluation
    guidance_score = _evaluate_guidance(
        case.expected_guidance,
        case.require_empty_guidance,
        response.facts.guidance,
        findings,
    )

    # 3. Evidence Grounding Evaluation
    evidence_score = _evaluate_evidence_grounding(
        response.source_documents,
        response.facts.financial_facts,
        response.facts.guidance,
        response.facts.qualitative_observations,
        response.thesis.bull_items + response.thesis.bear_items + response.thesis.watch_items,
        documents_by_id,
        findings,
    )

    # 4. Calculation Correctness & Comparability Evaluation
    calc_score, comp_score = _evaluate_calculations(
        case.expected_calculations,
        response.calculations,
        findings,
    )

    # 5. Thesis Grounding & Reference Verification
    thesis_score, hallucination_free = _evaluate_thesis(
        case,
        response,
        documents_by_id,
        findings,
    )

    # Classify all findings into standardized V2.8 failure taxonomy
    classified_failures = [
        classify_diagnostic_finding(
            case_id=case.case_id,
            diagnostic_category=f.category,
            severity_str=f.severity,
            target_id=f.target_id,
            message=f.message,
        )
        for f in findings
        if f.severity in ("critical", "high", "error", "warning")
    ]

    # Overall pass: no error/critical findings
    has_blocking_failures = any(
        f.severity in ("critical", "high", "error") for f in findings
    )
    passed = not has_blocking_failures

    return CaseEvaluationResult(
        case_id=case.case_id,
        name=case.name,
        passed=passed,
        fact_extraction=fact_score,
        guidance_extraction=guidance_score,
        evidence_grounding=evidence_score,
        calculation_correctness=calc_score,
        comparability_correctness=comp_score,
        thesis_grounding=thesis_score,
        hallucination_free=hallucination_free,
        latency_ms=latency_ms,
        findings=findings,
        classified_failures=classified_failures,
    )


def _evaluate_facts(
    expected_facts: List[ExpectedFact],
    actual_facts: List[FinancialFact],
    findings: List[DiagnosticFinding],
) -> MetricScore:
    if not expected_facts:
        return MetricScore(passed=1, total=1)

    passed_count = 0
    actual_by_metric: Dict[str, List[FinancialFact]] = {}
    for fact in actual_facts:
        actual_by_metric.setdefault(fact.metric_key.lower(), []).append(fact)

    for exp in expected_facts:
        metric_key = exp.metric_key.lower()
        candidates = actual_by_metric.get(metric_key, [])
        matching_fact = None

        for cand in candidates:
            if cand.evidence.source_id != exp.source_id:
                continue
            if exp.expected_quote_substring and exp.expected_quote_substring not in cand.evidence.exact_quote:
                continue
            matching_fact = cand
            break

        if matching_fact is None:
            findings.append(
                DiagnosticFinding(
                    category="fact_extraction",
                    severity="error",
                    target_id=exp.metric_key,
                    message=f"Expected financial fact '{exp.metric_key}' from source '{exp.source_id}' was not extracted.",
                )
            )
        else:
            # Check unit and period if expected
            errors = []
            if exp.unit and matching_fact.unit and exp.unit.lower() != matching_fact.unit.lower():
                errors.append(f"unit mismatch: expected '{exp.unit}', got '{matching_fact.unit}'")
            if exp.period and matching_fact.period and exp.period.lower() not in matching_fact.period.lower():
                errors.append(f"period mismatch: expected '{exp.period}', got '{matching_fact.period}'")

            if errors:
                findings.append(
                    DiagnosticFinding(
                        category="fact_extraction",
                        severity="warning",
                        target_id=matching_fact.fact_id,
                        message=f"Fact '{exp.metric_key}' extracted with minor variations: {', '.join(errors)}.",
                    )
                )
            passed_count += 1

    return MetricScore(passed=passed_count, total=len(expected_facts))


def _evaluate_guidance(
    expected_guidance: List[ExpectedGuidance],
    require_empty: bool,
    actual_guidance: List[GuidanceFact],
    findings: List[DiagnosticFinding],
) -> MetricScore:
    if require_empty:
        if len(actual_guidance) == 0:
            return MetricScore(passed=1, total=1)
        findings.append(
            DiagnosticFinding(
                category="guidance_extraction",
                severity="error",
                message=f"Expected empty guidance array, but got {len(actual_guidance)} items.",
            )
        )
        return MetricScore(passed=0, total=1)

    if not expected_guidance:
        return MetricScore(passed=1, total=1)

    passed_count = 0
    for exp in expected_guidance:
        matched = False
        for actual in actual_guidance:
            if actual.metric_key.lower() == exp.metric_key.lower():
                if exp.expected_quote_substring and exp.expected_quote_substring not in actual.evidence.exact_quote:
                    continue
                matched = True
                break

        if matched:
            passed_count += 1
        else:
            findings.append(
                DiagnosticFinding(
                    category="guidance_extraction",
                    severity="error",
                    target_id=exp.metric_key,
                    message=f"Expected guidance for '{exp.metric_key}' was not found.",
                )
            )

    return MetricScore(passed=passed_count, total=len(expected_guidance))


def _evaluate_evidence_grounding(
    source_documents: Sequence[SourceDocument],
    facts: Sequence[FinancialFact],
    guidance: Sequence[GuidanceFact],
    observations: Sequence[QualitativeObservation],
    thesis_items: Sequence[InterpretationItem],
    documents_by_id: Dict[str, SourceDocument],
    findings: List[DiagnosticFinding],
) -> MetricScore:
    all_evidence = []
    for f in facts:
        all_evidence.append((f.fact_id, f.evidence))
    for g in guidance:
        all_evidence.append((g.fact_id, g.evidence))
    for o in observations:
        all_evidence.append((o.observation_id, o.evidence))
    for idx, t in enumerate(thesis_items):
        for e_idx, e in enumerate(t.evidence_refs):
            all_evidence.append((f"thesis_item_{idx}_ev_{e_idx}", e))

    if not all_evidence:
        return MetricScore(passed=1, total=1)

    passed_count = 0
    for target_id, ev in all_evidence:
        doc = documents_by_id.get(ev.source_id)
        if doc is None:
            findings.append(
                DiagnosticFinding(
                    category="evidence_grounding",
                    severity="error",
                    target_id=target_id,
                    message=f"Evidence references unknown source_id '{ev.source_id}'.",
                )
            )
            continue

        if ev.start_offset is None or ev.end_offset is None:
            findings.append(
                DiagnosticFinding(
                    category="evidence_grounding",
                    severity="error",
                    target_id=target_id,
                    message=f"Evidence for '{target_id}' is missing resolved character offsets.",
                )
            )
            continue

        extracted_slice = doc.text[ev.start_offset:ev.end_offset]
        if extracted_slice != ev.exact_quote:
            findings.append(
                DiagnosticFinding(
                    category="evidence_grounding",
                    severity="error",
                    target_id=target_id,
                    message=f"Evidence offset slice does not match exact_quote for '{target_id}'.",
                )
            )
            continue

        passed_count += 1

    return MetricScore(passed=passed_count, total=len(all_evidence))


def _evaluate_calculations(
    expected_calculations: List[ExpectedCalculation],
    actual_calculations: List[Calculation],
    findings: List[DiagnosticFinding],
) -> Tuple[MetricScore, MetricScore]:
    if not expected_calculations:
        return MetricScore(passed=1, total=1), MetricScore(passed=1, total=1)

    valid_expected = [c for c in expected_calculations if c.status == "valid"]
    unavail_expected = [c for c in expected_calculations if c.status == "unavailable"]

    # 1. Evaluate valid calculations
    valid_passed = 0
    for exp in valid_expected:
        matching = [
            c for c in actual_calculations
            if c.calculation_type == exp.calculation_type and c.status == "valid"
        ]
        if not matching:
            findings.append(
                DiagnosticFinding(
                    category="calculation_correctness",
                    severity="error",
                    target_id=exp.calculation_type,
                    message=f"Expected valid calculation of type '{exp.calculation_type}' was not produced.",
                )
            )
            continue

        # Check numerical result if specified
        found_accurate = False
        for m in matching:
            if exp.expected_result is not None:
                if m.result is None:
                    continue
                if math.isclose(m.result, exp.expected_result, rel_tol=exp.tolerance, abs_tol=exp.tolerance):
                    found_accurate = True
                    break
            else:
                found_accurate = True
                break

        if found_accurate:
            valid_passed += 1
        else:
            findings.append(
                DiagnosticFinding(
                    category="calculation_correctness",
                    severity="error",
                    target_id=exp.calculation_type,
                    message=f"Calculation '{exp.calculation_type}' result mismatch: expected approx {exp.expected_result}, got {[m.result for m in matching]}.",
                )
            )

    calc_score = MetricScore(
        passed=valid_passed,
        total=len(valid_expected) if valid_expected else 1,
    )

    # 2. Evaluate comparability / unavailable comparisons
    unavail_passed = 0
    for exp in unavail_expected:
        matching = [
            c for c in actual_calculations
            if c.calculation_type == exp.calculation_type and c.status == "unavailable"
        ]
        if not matching:
            findings.append(
                DiagnosticFinding(
                    category="comparability_gate",
                    severity="error",
                    target_id=exp.calculation_type,
                    message=f"Expected incompatible comparison '{exp.calculation_type}' to be status='unavailable', but it was not.",
                )
            )
            continue

        if exp.expected_reason_substring:
            reason_matched = any(
                exp.expected_reason_substring.lower() in (m.reason or "").lower()
                for m in matching
            )
            if not reason_matched:
                findings.append(
                    DiagnosticFinding(
                        category="comparability_gate",
                        severity="warning",
                        target_id=exp.calculation_type,
                        message=f"Unavailable calculation reason did not contain expected substring '{exp.expected_reason_substring}'.",
                    )
                )
        unavail_passed += 1

    comp_score = MetricScore(
        passed=unavail_passed,
        total=len(unavail_expected) if unavail_expected else 1,
    )

    return calc_score, comp_score


def _evaluate_thesis(
    case: BenchmarkCase,
    response: V2AnalysisResponse,
    documents_by_id: Dict[str, SourceDocument],
    findings: List[DiagnosticFinding],
) -> Tuple[MetricScore, bool]:
    items = (
        response.thesis.bull_items
        + response.thesis.bear_items
        + response.thesis.watch_items
    )
    all_fact_ids = {f.fact_id for f in response.facts.financial_facts}
    all_fact_ids.update(g.fact_id for g in response.facts.guidance)
    all_fact_ids.update(o.observation_id for o in response.facts.qualitative_observations)
    all_calc_ids = {c.calculation_id for c in response.calculations}

    if not items:
        return MetricScore(passed=1, total=1), True

    passed_count = 0
    hallucination_free = True

    for idx, item in enumerate(items):
        item_valid = True

        # Check supporting fact IDs
        for fact_id in item.supporting_fact_ids:
            if fact_id not in all_fact_ids:
                findings.append(
                    DiagnosticFinding(
                        category="thesis_grounding",
                        severity="error",
                        target_id=f"thesis_item_{idx}",
                        message=f"Interpretation item references unknown fact ID '{fact_id}'.",
                    )
                )
                item_valid = False
                hallucination_free = False

        # Check calculation IDs
        for calc_id in item.calculation_ids:
            if calc_id not in all_calc_ids:
                findings.append(
                    DiagnosticFinding(
                        category="thesis_grounding",
                        severity="error",
                        target_id=f"thesis_item_{idx}",
                        message=f"Interpretation item references unknown calculation ID '{calc_id}'.",
                    )
                )
                item_valid = False
                hallucination_free = False

        # Check numeric provenance
        text = f"{item.claim} {item.why_it_matters}"
        if NUMERIC_PATTERN.search(text) and not item.calculation_ids:
            findings.append(
                DiagnosticFinding(
                    category="thesis_grounding",
                    severity="error",
                    target_id=f"thesis_item_{idx}",
                    message=f"Interpretation contains numbers without referencing a calculation ID: '{item.claim}'.",
                )
            )
            item_valid = False
            hallucination_free = False

        # Check prohibited investment advice words
        if PROHIBITED_RECOMMENDATIONS.search(text):
            findings.append(
                DiagnosticFinding(
                    category="hallucination",
                    severity="error",
                    target_id=f"thesis_item_{idx}",
                    message=f"Interpretation contains prohibited recommendation/valuation advice: '{item.claim}'.",
                )
            )
            item_valid = False
            hallucination_free = False

        # Check case-specific prohibited claims
        for prohibited in case.prohibited_claims:
            if prohibited.lower() in text.lower():
                findings.append(
                    DiagnosticFinding(
                        category="hallucination",
                        severity="error",
                        target_id=f"thesis_item_{idx}",
                        message=f"Interpretation contains explicitly prohibited claim '{prohibited}'.",
                    )
                )
                item_valid = False
                hallucination_free = False

        if item_valid:
            passed_count += 1

    return MetricScore(passed=passed_count, total=len(items)), hallucination_free


def format_evaluation_summary(report: EvaluationReport) -> str:
    """Convenience helper to format an evaluation report."""
    return report.summary_text()
