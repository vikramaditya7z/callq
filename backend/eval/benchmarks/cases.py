"""Standard financial intelligence benchmark cases for CallQ V2 evaluation."""

from __future__ import annotations

from typing import List

from backend.eval.models import (
    BenchmarkCase,
    ExpectedCalculation,
    ExpectedFact,
    ExpectedGuidance,
)
from backend.models.v2_analysis import HistoricalTranscript, V2AnalysisRequest


CASE_SAAS_ENTERPRISE_GROWTH = BenchmarkCase(
    case_id="case_saas_enterprise_growth",
    name="Enterprise SaaS Multi-Quarter Growth and Expansion",
    description="SaaS earnings call with ARR, revenue expansion, gross margin improvement, and explicit forward guidance.",
    request=V2AnalysisRequest(
        current_transcript=(
            "Operator: Welcome to CloudScale Q3 2026 earnings conference call. "
            "Total revenue for the third quarter was $300 million, representing strong year-over-year momentum. "
            "Subscription gross margin was 75 percent for the quarter. "
            "Net revenue retention rate remained healthy at 115 percent. "
            "Looking forward to the fourth quarter of 2026, management expects revenue between $315 million and $325 million. "
            "Enterprise customer expansions in the financial sector continued to drive adoption."
        ),
        historical_transcripts=[
            HistoricalTranscript(
                label="Q3 2025",
                transcript=(
                    "Operator: Welcome to CloudScale Q3 2025 earnings conference call. "
                    "Total revenue for the third quarter was $250 million. "
                    "Subscription gross margin was 72 percent for the period. "
                    "Net revenue retention was 110 percent. "
                    "Management remains confident in our multi-product strategy."
                ),
            )
        ],
    ),
    expected_facts=[
        ExpectedFact(
            metric_key="revenue",
            reported_value="$300 million",
            source_id="current",
            unit="USD",
            period="Q3 2026",
            period_type="quarterly",
            expected_quote_substring="Total revenue for the third quarter was $300 million",
        ),
        ExpectedFact(
            metric_key="subscription_gross_margin",
            reported_value="75 percent",
            source_id="current",
            unit="percent",
            period="Q3 2026",
            period_type="quarterly",
            expected_quote_substring="Subscription gross margin was 75 percent",
        ),
        ExpectedFact(
            metric_key="revenue",
            reported_value="$250 million",
            source_id="historical_1_q3-2025",
            unit="USD",
            period="Q3 2025",
            period_type="quarterly",
            expected_quote_substring="Total revenue for the third quarter was $250 million",
        ),
    ],
    expected_guidance=[
        ExpectedGuidance(
            metric_key="revenue",
            guidance_value="$315 million to $325 million",
            source_id="current",
            unit="USD",
            period="Q4 2026",
            expected_quote_substring="revenue between $315 million and $325 million",
        )
    ],
    expected_calculations=[
        ExpectedCalculation(
            calculation_type="percentage_change",
            status="valid",
            expected_result=20.0,
            expected_unit="percent",
        ),
        ExpectedCalculation(
            calculation_type="absolute_change",
            status="valid",
            expected_result=50000000.0,
            expected_unit="USD",
        ),
        ExpectedCalculation(
            calculation_type="margin_change",
            status="valid",
            expected_result=3.0,
            expected_unit="percentage_points",
        ),
        ExpectedCalculation(
            calculation_type="guidance_midpoint",
            status="valid",
            expected_result=320000000.0,
            expected_unit="USD",
        ),
        ExpectedCalculation(
            calculation_type="guidance_range_width",
            status="valid",
            expected_result=10000000.0,
            expected_unit="USD",
        ),
    ],
)


CASE_MANUFACTURING_MARGIN_CONTRACTION = BenchmarkCase(
    case_id="case_manufacturing_margin_contraction",
    name="Industrial Manufacturing Margin Pressure",
    description="Manufacturing earnings call showing top-line revenue growth alongside operating margin contraction due to input costs.",
    request=V2AnalysisRequest(
        current_transcript=(
            "Operator: Welcome to Apex Manufacturing Q2 2026 earnings conference call. "
            "Total revenue for the second quarter reached $500 million. "
            "Operating margin for the quarter was 12 percent. "
            "Free cash flow generated was $40 million. "
            "Management noted raw material inflation and freight bottlenecks impacted margins during the period."
        ),
        historical_transcripts=[
            HistoricalTranscript(
                label="Q2 2025",
                transcript=(
                    "Operator: Welcome to Apex Manufacturing Q2 2025 earnings conference call. "
                    "Total revenue for the second quarter was $450 million. "
                    "Operating margin for the quarter was 16 percent. "
                    "Free cash flow for the prior year quarter was $55 million."
                ),
            )
        ],
    ),
    expected_facts=[
        ExpectedFact(
            metric_key="revenue",
            reported_value="$500 million",
            source_id="current",
            unit="USD",
            period="Q2 2026",
            period_type="quarterly",
        ),
        ExpectedFact(
            metric_key="operating_margin",
            reported_value="12 percent",
            source_id="current",
            unit="percent",
            period="Q2 2026",
            period_type="quarterly",
        ),
        ExpectedFact(
            metric_key="revenue",
            reported_value="$450 million",
            source_id="historical_1_q2-2025",
            unit="USD",
            period="Q2 2025",
            period_type="quarterly",
        ),
        ExpectedFact(
            metric_key="operating_margin",
            reported_value="16 percent",
            source_id="historical_1_q2-2025",
            unit="percent",
            period="Q2 2025",
            period_type="quarterly",
        ),
    ],
    expected_calculations=[
        ExpectedCalculation(
            calculation_type="percentage_change",
            status="valid",
            expected_result=11.11,
            expected_unit="percent",
            tolerance=0.05,
        ),
        ExpectedCalculation(
            calculation_type="margin_change",
            status="valid",
            expected_result=-4.0,
            expected_unit="percentage_points",
        ),
    ],
)


CASE_CROSS_BORDER_INCOMPATIBLE_CURRENCY = BenchmarkCase(
    case_id="case_incompatible_currency_accounting",
    name="Incompatible Currency Comparison",
    description="Cross-border comparison between USD and EUR transcripts requiring honest comparability rejection.",
    request=V2AnalysisRequest(
        current_transcript=(
            "Operator: Welcome to Global Holdings Q1 2026 financial results conference call. "
            "Reported revenue for our US operations was $120 million for the third quarter. "
            "Domestic customer demand showed continuous expansion and steady volume growth. "
            "Management remains focused on disciplined cost management across all business lines."
        ),
        historical_transcripts=[
            HistoricalTranscript(
                label="Q1 2025 European Division",
                transcript=(
                    "Operator: Welcome to Global Holdings Q1 2025 European Division conference call. "
                    "Reported revenue for our European operations was €100 million for the quarter. "
                    "Regional business activities and commercial sales were stable during the prior period. "
                    "Operating expenses remained aligned with strategic targets."
                ),
            )
        ],
    ),
    expected_facts=[
        ExpectedFact(
            metric_key="revenue",
            reported_value="$120 million",
            source_id="current",
            unit="USD",
            period="Q1 2026",
            period_type="quarterly",
        ),
        ExpectedFact(
            metric_key="revenue",
            reported_value="€100 million",
            source_id="historical_1_q1-2025-european-division",
            unit="EUR",
            period="Q1 2025",
            period_type="quarterly",
        ),
    ],
    expected_calculations=[
        ExpectedCalculation(
            calculation_type="percentage_change",
            status="unavailable",
            expected_reason_substring="incompatible",
        ),
        ExpectedCalculation(
            calculation_type="absolute_change",
            status="unavailable",
            expected_reason_substring="incompatible",
        ),
    ],
)


CASE_LIMITED_DISCLOSURE_NO_GUIDANCE = BenchmarkCase(
    case_id="case_limited_disclosure_no_guidance",
    name="Limited Disclosure with Explicit No-Guidance Statement",
    description="Transcript containing historical metrics and explicit statement that forward guidance is withheld.",
    request=V2AnalysisRequest(
        current_transcript=(
            "Operator: Welcome to CoreLogistics Q3 2026 corporate update conference call. "
            "During the third quarter, total revenue was $85 million for the business. "
            "Capital expenditures for the period were $12 million across logistics centers. "
            "Management is not providing forward-looking financial guidance or targets for future quarters at this time. "
            "Our focus remains on operational cost management, network reliability, and customer service execution."
        ),
    ),
    expected_facts=[
        ExpectedFact(
            metric_key="revenue",
            reported_value="$85 million",
            source_id="current",
            unit="USD",
            period="Q3 2026",
        ),
        ExpectedFact(
            metric_key="capital_expenditures",
            reported_value="$12 million",
            source_id="current",
            unit="USD",
            period="Q3 2026",
        ),
    ],
    require_empty_guidance=True,
)


ALL_BENCHMARK_CASES: List[BenchmarkCase] = [
    CASE_SAAS_ENTERPRISE_GROWTH,
    CASE_MANUFACTURING_MARGIN_CONTRACTION,
    CASE_CROSS_BORDER_INCOMPATIBLE_CURRENCY,
    CASE_LIMITED_DISCLOSURE_NO_GUIDANCE,
]
