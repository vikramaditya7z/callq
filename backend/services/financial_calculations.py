"""Deterministic V2.2 financial normalization, comparisons, and calculations."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from typing import Optional, Tuple

from backend.models.v2_analysis import (
    Calculation,
    FinancialFact,
    GuidanceFact,
    NormalizedFinancialValue,
    NormalizedGuidanceRange,
    TrendClassification,
)


DISPLAY_PRECISION = Decimal("0.01")
TREND_FLAT_THRESHOLD = Decimal("1")

_VALUE_PATTERN = re.compile(
    r"^\s*(?P<currency>US\$|\$|€|£)?\s*"
    r"(?P<number>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*"
    r"(?P<scale>thousand|million|billion)?\s*"
    r"(?P<percent>%|percent)?\s*$",
    re.IGNORECASE,
)
_RANGE_SEPARATOR = re.compile(r"\s+(?:to|and)\s+|\s*(?:–|-)\s*", re.IGNORECASE)
_SCALE_MULTIPLIERS = {
    None: Decimal("1"),
    "thousand": Decimal("1000"),
    "million": Decimal("1000000"),
    "billion": Decimal("1000000000"),
}
_CURRENCY_SYMBOLS = {"US$": "USD", "$": "USD", "€": "EUR", "£": "GBP"}
_CURRENCY_UNITS = {"USD", "EUR", "GBP"}


class FinancialCalculationError(Exception):
    """Raised when a value cannot be safely normalized."""


def normalize_financial_fact(fact: FinancialFact) -> NormalizedFinancialValue:
    """Normalize an explicitly reported financial fact without deriving values."""
    numeric_value, normalized_unit, currency = _parse_reported_value(
        fact.reported_value,
        fact.unit,
    )
    return NormalizedFinancialValue(
        fact_id=fact.fact_id,
        metric_key=fact.metric_key,
        numeric_value=numeric_value,
        normalized_unit=normalized_unit,
        currency=currency,
        original_reported_value=fact.reported_value,
        period=fact.period,
        period_type=fact.period_type,
    )


def normalize_guidance_range(guidance: GuidanceFact) -> NormalizedGuidanceRange:
    """Normalize an explicit two-value guidance range without calculating it."""
    endpoints = _RANGE_SEPARATOR.split(guidance.guidance_value.strip())
    if len(endpoints) != 2 or not all(endpoints):
        raise FinancialCalculationError(
            "Guidance must contain exactly two explicit range endpoints."
        )

    low, low_unit, low_currency = _parse_reported_value(endpoints[0], guidance.unit)
    high, high_unit, high_currency = _parse_reported_value(endpoints[1], guidance.unit)

    if low_unit != high_unit or low_currency != high_currency:
        raise FinancialCalculationError("Guidance range endpoints use incompatible units.")
    if low > high:
        raise FinancialCalculationError("Guidance range low endpoint exceeds high endpoint.")

    return NormalizedGuidanceRange(
        fact_id=guidance.fact_id,
        metric_key=guidance.metric_key,
        low=low,
        high=high,
        normalized_unit=low_unit,
        currency=low_currency,
        original_guidance_value=guidance.guidance_value,
        period=guidance.period,
    )


def calculate_absolute_change(
    calculation_id: str,
    current_fact: FinancialFact,
    previous_fact: FinancialFact,
) -> Calculation:
    """Calculate current minus previous when financial facts are comparable."""
    return _calculate_comparison(
        calculation_id,
        "absolute_change",
        current_fact,
        previous_fact,
        "current - previous",
        lambda current, previous: current - previous,
        _result_unit,
    )


def calculate_percentage_change(
    calculation_id: str,
    current_fact: FinancialFact,
    previous_fact: FinancialFact,
) -> Calculation:
    """Calculate percentage change and reject a zero previous value."""
    current, previous, unavailable = _normalized_comparison_inputs(
        calculation_id,
        "percentage_change",
        current_fact,
        previous_fact,
        "((current - previous) / previous) * 100",
    )
    if unavailable is not None:
        return unavailable
    if previous.numeric_value == 0:
        return _unavailable_calculation(
            calculation_id,
            "percentage_change",
            [current_fact.fact_id, previous_fact.fact_id],
            "((current - previous) / previous) * 100",
            "Percentage change is unavailable when previous value is zero.",
        )

    result = ((current.numeric_value - previous.numeric_value) / previous.numeric_value) * 100
    return _valid_calculation(
        calculation_id,
        "percentage_change",
        [current_fact.fact_id, previous_fact.fact_id],
        "((current - previous) / previous) * 100",
        result,
        "percent",
    )


def calculate_margin_change(
    calculation_id: str,
    current_fact: FinancialFact,
    previous_fact: FinancialFact,
) -> Calculation:
    """Calculate a margin change in percentage points, never percentage growth."""
    current, previous, unavailable = _normalized_comparison_inputs(
        calculation_id,
        "margin_change",
        current_fact,
        previous_fact,
        "current_margin - previous_margin",
    )
    if unavailable is not None:
        return unavailable
    if not _is_margin_metric(current.metric_key):
        return _unavailable_calculation(
            calculation_id,
            "margin_change",
            [current_fact.fact_id, previous_fact.fact_id],
            "current_margin - previous_margin",
            "Margin change requires a metric_key ending in '_margin'.",
        )
    if current.normalized_unit != "percent":
        return _unavailable_calculation(
            calculation_id,
            "margin_change",
            [current_fact.fact_id, previous_fact.fact_id],
            "current_margin - previous_margin",
            "Margin change requires percentage inputs.",
        )

    return _valid_calculation(
        calculation_id,
        "margin_change",
        [current_fact.fact_id, previous_fact.fact_id],
        "current_margin - previous_margin",
        current.numeric_value - previous.numeric_value,
        "percentage_points",
    )


def calculate_guidance_midpoint(
    calculation_id: str,
    guidance: GuidanceFact,
) -> Calculation:
    """Calculate the midpoint of a normalized explicit guidance range."""
    try:
        normalized_range = normalize_guidance_range(guidance)
    except FinancialCalculationError as error:
        return _unavailable_calculation(
            calculation_id,
            "guidance_midpoint",
            [guidance.fact_id],
            "(low + high) / 2",
            str(error),
        )

    return _valid_calculation(
        calculation_id,
        "guidance_midpoint",
        [guidance.fact_id],
        "(low + high) / 2",
        (normalized_range.low + normalized_range.high) / 2,
        _guidance_result_unit(normalized_range),
    )


def calculate_guidance_range_width(
    calculation_id: str,
    guidance: GuidanceFact,
) -> Calculation:
    """Calculate high minus low for a normalized explicit guidance range."""
    try:
        normalized_range = normalize_guidance_range(guidance)
    except FinancialCalculationError as error:
        return _unavailable_calculation(
            calculation_id,
            "guidance_range_width",
            [guidance.fact_id],
            "high - low",
            str(error),
        )

    return _valid_calculation(
        calculation_id,
        "guidance_range_width",
        [guidance.fact_id],
        "high - low",
        normalized_range.high - normalized_range.low,
        _guidance_result_unit(normalized_range),
    )


def classify_trend(calculation: Calculation) -> TrendClassification:
    """Classify supported changes with a documented one-unit flat threshold.

    Percentage changes use a one-percent threshold and margin changes use a
    one-percentage-point threshold. This only describes direction; it does not
    assign financial significance.
    """
    if calculation.status != "valid" or calculation.result is None:
        return _unavailable_trend(
            calculation.calculation_id,
            "Trend is unavailable because the input calculation is unavailable.",
        )
    if calculation.calculation_type not in {"percentage_change", "margin_change"}:
        return _unavailable_trend(
            calculation.calculation_id,
            "Trend classification supports percentage_change and margin_change only.",
        )

    result = Decimal(str(calculation.result))
    threshold = TREND_FLAT_THRESHOLD
    if result >= threshold:
        classification = "improving"
    elif result <= -threshold:
        classification = "deteriorating"
    else:
        classification = "flat"

    return TrendClassification(
        calculation_id=calculation.calculation_id,
        classification=classification,
        threshold=float(threshold),
        status="valid",
        reason=None,
    )


def _calculate_comparison(
    calculation_id: str,
    calculation_type: str,
    current_fact: FinancialFact,
    previous_fact: FinancialFact,
    formula: str,
    operation,
    unit_builder,
) -> Calculation:
    current, previous, unavailable = _normalized_comparison_inputs(
        calculation_id,
        calculation_type,
        current_fact,
        previous_fact,
        formula,
    )
    if unavailable is not None:
        return unavailable
    return _valid_calculation(
        calculation_id,
        calculation_type,
        [current_fact.fact_id, previous_fact.fact_id],
        formula,
        operation(current.numeric_value, previous.numeric_value),
        unit_builder(current),
    )


def _normalized_comparison_inputs(
    calculation_id: str,
    calculation_type: str,
    current_fact: FinancialFact,
    previous_fact: FinancialFact,
    formula: str,
) -> Tuple[
    Optional[NormalizedFinancialValue],
    Optional[NormalizedFinancialValue],
    Optional[Calculation],
]:
    input_fact_ids = [current_fact.fact_id, previous_fact.fact_id]
    try:
        current = normalize_financial_fact(current_fact)
        previous = normalize_financial_fact(previous_fact)
    except FinancialCalculationError as error:
        return None, None, _unavailable_calculation(
            calculation_id,
            calculation_type,
            input_fact_ids,
            formula,
            str(error),
        )

    incompatibility_reason = _comparability_reason(current, previous)
    if incompatibility_reason is not None:
        return None, None, _unavailable_calculation(
            calculation_id,
            calculation_type,
            input_fact_ids,
            formula,
            incompatibility_reason,
        )
    return current, previous, None


def _comparability_reason(
    current: NormalizedFinancialValue,
    previous: NormalizedFinancialValue,
) -> Optional[str]:
    if current.metric_key != previous.metric_key:
        return "Facts have incompatible metric_key values."
    if not current.period_type or not previous.period_type:
        return "Facts require period_type values for comparison."
    if current.period_type != previous.period_type:
        return "Facts have incompatible period_type values."
    if current.normalized_unit != previous.normalized_unit:
        return "Facts have incompatible normalized units."
    if current.currency != previous.currency:
        return "Facts have incompatible currencies."
    return None


def _parse_reported_value(
    reported_value: str,
    declared_unit: Optional[str],
) -> Tuple[Decimal, str, Optional[str]]:
    match = _VALUE_PATTERN.match(reported_value)
    if match is None:
        raise FinancialCalculationError(
            "Reported value is not in a supported explicit numeric format."
        )

    try:
        numeric_value = Decimal(match.group("number"))
    except InvalidOperation as error:
        raise FinancialCalculationError("Reported value contains an invalid number.") from error

    scale = match.group("scale")
    numeric_value *= _SCALE_MULTIPLIERS[scale.lower() if scale else None]
    symbol_currency = _CURRENCY_SYMBOLS.get(match.group("currency"))
    is_percent = bool(match.group("percent"))
    declared_currency = _declared_currency(declared_unit)

    if symbol_currency and declared_currency and symbol_currency != declared_currency:
        raise FinancialCalculationError("Reported currency conflicts with declared unit.")
    if is_percent and declared_currency:
        raise FinancialCalculationError("Percentage value conflicts with declared currency.")

    if is_percent or _is_percent_unit(declared_unit):
        if symbol_currency:
            raise FinancialCalculationError("Percentage value cannot include a currency symbol.")
        return numeric_value, "percent", None
    if symbol_currency or declared_currency:
        return numeric_value, "currency", symbol_currency or declared_currency
    return numeric_value, "number", None


def _declared_currency(declared_unit: Optional[str]) -> Optional[str]:
    if not declared_unit:
        return None
    normalized_unit = declared_unit.strip().upper()
    return normalized_unit if normalized_unit in _CURRENCY_UNITS else None


def _is_percent_unit(declared_unit: Optional[str]) -> bool:
    if not declared_unit:
        return False
    return declared_unit.strip().lower() in {"%", "percent", "percentage"}


def _is_margin_metric(metric_key: str) -> bool:
    return metric_key.lower().endswith("_margin")


def _result_unit(value: NormalizedFinancialValue) -> str:
    if value.normalized_unit == "currency":
        return value.currency or "currency"
    return value.normalized_unit


def _guidance_result_unit(guidance: NormalizedGuidanceRange) -> str:
    if guidance.normalized_unit == "currency":
        return guidance.currency or "currency"
    return guidance.normalized_unit


def _valid_calculation(
    calculation_id: str,
    calculation_type: str,
    input_fact_ids: list[str],
    formula: str,
    result: Decimal,
    unit: str,
) -> Calculation:
    rounded_result = result.quantize(DISPLAY_PRECISION, rounding=ROUND_HALF_UP)
    return Calculation(
        calculation_id=calculation_id,
        calculation_type=calculation_type,
        input_fact_ids=input_fact_ids,
        formula=formula,
        result=float(rounded_result),
        unit=unit,
        status="valid",
        reason=None,
    )


def _unavailable_calculation(
    calculation_id: str,
    calculation_type: str,
    input_fact_ids: list[str],
    formula: str,
    reason: str,
) -> Calculation:
    return Calculation(
        calculation_id=calculation_id,
        calculation_type=calculation_type,
        input_fact_ids=input_fact_ids,
        formula=formula,
        result=None,
        unit=None,
        status="unavailable",
        reason=reason,
    )


def _unavailable_trend(calculation_id: str, reason: str) -> TrendClassification:
    return TrendClassification(
        calculation_id=calculation_id,
        classification=None,
        threshold=None,
        status="unavailable",
        reason=reason,
    )
