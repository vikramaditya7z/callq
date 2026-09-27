"""Deterministic unit tests for the V2.2 financial calculation engine."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest

from backend.models.v2_analysis import (
    Calculation,
    EvidenceRef,
    FinancialFact,
    GuidanceFact,
)
from backend.services.financial_calculations import (
    calculate_absolute_change,
    calculate_guidance_midpoint,
    calculate_guidance_range_width,
    calculate_margin_change,
    calculate_percentage_change,
    classify_trend,
    normalize_financial_fact,
)


def financial_fact(
    fact_id: str,
    metric_key: str,
    reported_value: str,
    unit: str,
    period: str = "Q3 2025",
    period_type: str = "quarterly",
) -> FinancialFact:
    """Build a minimal verified-style fact for deterministic calculation tests."""
    return FinancialFact(
        fact_id=fact_id,
        metric_key=metric_key,
        reported_value=reported_value,
        unit=unit,
        period=period,
        period_type=period_type,
        evidence=EvidenceRef(source_id="source", exact_quote=reported_value),
    )


class V22FinancialCalculationTests(unittest.TestCase):
    """Financial arithmetic and conservative comparability tests."""

    def setUp(self) -> None:
        self.current_revenue = financial_fact(
            "revenue_2025", "revenue", "$1.20 billion", "USD", "Q3 2025"
        )
        self.previous_revenue = financial_fact(
            "revenue_2024", "revenue", "$900 million", "USD", "Q3 2024"
        )

    def test_absolute_change(self) -> None:
        calculation = calculate_absolute_change(
            "calc_revenue_absolute", self.current_revenue, self.previous_revenue
        )

        self.assertEqual(calculation.status, "valid")
        self.assertEqual(calculation.result, 300000000.0)
        self.assertEqual(calculation.unit, "USD")

    def test_percentage_growth(self) -> None:
        calculation = calculate_percentage_change(
            "calc_revenue_growth", self.current_revenue, self.previous_revenue
        )

        self.assertEqual(calculation.status, "valid")
        self.assertEqual(calculation.result, 33.33)
        self.assertEqual(calculation.unit, "percent")

    def test_zero_denominator_is_unavailable(self) -> None:
        previous = financial_fact(
            "revenue_2024", "revenue", "$0", "USD", "Q3 2024"
        )

        calculation = calculate_percentage_change(
            "calc_revenue_growth", self.current_revenue, previous
        )

        self.assertEqual(calculation.status, "unavailable")
        self.assertIn("previous value is zero", calculation.reason)

    def test_margin_change_is_percentage_points(self) -> None:
        current = financial_fact("gross_margin_2025", "gross_margin", "72%", "percent")
        previous = financial_fact("gross_margin_2024", "gross_margin", "69%", "percent")

        calculation = calculate_margin_change("calc_margin", current, previous)

        self.assertEqual(calculation.status, "valid")
        self.assertEqual(calculation.result, 3.0)
        self.assertEqual(calculation.unit, "percentage_points")

    def test_guidance_midpoint(self) -> None:
        guidance = GuidanceFact(
            fact_id="revenue_guidance",
            metric_key="revenue",
            guidance_value="$1.20 billion to $1.40 billion",
            unit="USD",
            period="Q4 2025",
            evidence=EvidenceRef(source_id="source", exact_quote="guidance quote"),
        )

        calculation = calculate_guidance_midpoint("calc_guidance_midpoint", guidance)

        self.assertEqual(calculation.status, "valid")
        self.assertEqual(calculation.result, 1300000000.0)
        self.assertEqual(calculation.unit, "USD")

    def test_guidance_range_width(self) -> None:
        guidance = GuidanceFact(
            fact_id="revenue_guidance",
            metric_key="revenue",
            guidance_value="$1.20 billion to $1.40 billion",
            unit="USD",
            period="Q4 2025",
            evidence=EvidenceRef(source_id="source", exact_quote="guidance quote"),
        )

        calculation = calculate_guidance_range_width("calc_guidance_width", guidance)

        self.assertEqual(calculation.status, "valid")
        self.assertEqual(calculation.result, 200000000.0)

    def test_improving_trend(self) -> None:
        trend = classify_trend(
            Calculation(
                calculation_id="growth", calculation_type="percentage_change",
                input_fact_ids=["current", "previous"], formula="formula", result=2.0,
                unit="percent", status="valid",
            )
        )

        self.assertEqual(trend.classification, "improving")

    def test_deteriorating_trend(self) -> None:
        trend = classify_trend(
            Calculation(
                calculation_id="margin", calculation_type="margin_change",
                input_fact_ids=["current", "previous"], formula="formula", result=-1.5,
                unit="percentage_points", status="valid",
            )
        )

        self.assertEqual(trend.classification, "deteriorating")

    def test_flat_trend(self) -> None:
        trend = classify_trend(
            Calculation(
                calculation_id="growth", calculation_type="percentage_change",
                input_fact_ids=["current", "previous"], formula="formula", result=0.5,
                unit="percent", status="valid",
            )
        )

        self.assertEqual(trend.classification, "flat")
        self.assertEqual(trend.threshold, 1.0)

    def test_revenue_comparison_normalizes_billion_and_million(self) -> None:
        normalized = normalize_financial_fact(self.current_revenue)

        self.assertEqual(str(normalized.numeric_value), "1200000000.00")
        self.assertEqual(normalized.currency, "USD")

    def test_invalid_metric_comparison_is_unavailable(self) -> None:
        subscription_revenue = financial_fact(
            "subscription_revenue_2024",
            "subscription_revenue",
            "$900 million",
            "USD",
            "Q3 2024",
        )

        calculation = calculate_absolute_change(
            "calc_invalid_metric", self.current_revenue, subscription_revenue
        )

        self.assertEqual(calculation.status, "unavailable")
        self.assertIn("metric_key", calculation.reason)

    def test_invalid_period_comparison_is_unavailable(self) -> None:
        annual_revenue = financial_fact(
            "revenue_annual", "revenue", "$900 million", "USD", "FY 2024", "annual"
        )

        calculation = calculate_absolute_change(
            "calc_invalid_period", self.current_revenue, annual_revenue
        )

        self.assertEqual(calculation.status, "unavailable")
        self.assertIn("period_type", calculation.reason)

    def test_invalid_currency_comparison_is_unavailable(self) -> None:
        euro_revenue = financial_fact(
            "revenue_eur", "revenue", "€900 million", "EUR", "Q3 2024"
        )

        calculation = calculate_absolute_change(
            "calc_invalid_currency", self.current_revenue, euro_revenue
        )

        self.assertEqual(calculation.status, "unavailable")
        self.assertIn("currencies", calculation.reason)

    def test_gaap_and_adjusted_metrics_are_incompatible(self) -> None:
        gaap_eps = financial_fact("gaap_eps", "gaap_eps", "$1.42", "USD")
        adjusted_eps = financial_fact("adjusted_eps", "adjusted_eps", "$1.50", "USD")

        calculation = calculate_percentage_change("calc_eps", gaap_eps, adjusted_eps)

        self.assertEqual(calculation.status, "unavailable")
        self.assertIn("metric_key", calculation.reason)

    def test_calculation_provenance(self) -> None:
        calculation = calculate_percentage_change(
            "calc_revenue_growth", self.current_revenue, self.previous_revenue
        )

        self.assertEqual(calculation.calculation_id, "calc_revenue_growth")
        self.assertEqual(calculation.input_fact_ids, ["revenue_2025", "revenue_2024"])
        self.assertEqual(calculation.formula, "((current - previous) / previous) * 100")

    def test_serialization_and_deserialization(self) -> None:
        calculation = calculate_percentage_change(
            "calc_revenue_growth", self.current_revenue, self.previous_revenue
        )

        round_tripped = Calculation.model_validate_json(calculation.model_dump_json())

        self.assertEqual(round_tripped, calculation)


class Python39CompatibilityTests(unittest.TestCase):
    """Ensure V2.2 source uses syntax accepted by Python 3.9."""

    def test_v22_source_parses_with_python_39_grammar(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        v22_files = [
            repository_root / "backend/models/v2_analysis.py",
            repository_root / "backend/services/financial_calculations.py",
        ]

        for source_file in v22_files:
            with self.subTest(source_file=source_file):
                ast.parse(
                    source_file.read_text(encoding="utf-8"),
                    filename=str(source_file),
                    feature_version=(3, 9),
                )


if __name__ == "__main__":
    unittest.main()
