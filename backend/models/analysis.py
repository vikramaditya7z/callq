"""Version 1 analysis request and response contracts."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


MIN_TRANSCRIPT_LENGTH = 200
MAX_TRANSCRIPT_LENGTH = 100_000
MAX_INSIGHT_ITEMS = 20
MAX_INSIGHT_LENGTH = 1_000
MAX_OUTLOOK_LENGTH = 2_000


class EarningsAnalysisRequest(BaseModel):
    """Request body for analyzing one earnings call transcript."""

    model_config = ConfigDict(extra="forbid")

    transcript: str = Field(
        ...,
        min_length=MIN_TRANSCRIPT_LENGTH,
        max_length=MAX_TRANSCRIPT_LENGTH,
        description="Raw earnings call transcript text submitted by the user.",
    )

    @field_validator("transcript")
    @classmethod
    def validate_transcript(cls, value: str) -> str:
        """Trim whitespace and require transcript-like content."""
        cleaned_value = value.strip()

        if len(cleaned_value) < MIN_TRANSCRIPT_LENGTH:
            raise ValueError(
                "Transcript must contain enough text for meaningful analysis."
            )

        if not any(character.isalpha() for character in cleaned_value):
            raise ValueError("Transcript must contain readable text.")

        return cleaned_value


class FinancialMetric(BaseModel):
    """Financial metric extracted from an earnings call transcript."""

    model_config = ConfigDict(extra="forbid")

    name: str
    value: str
    change: Optional[str]
    period: Optional[str]


class GuidanceItem(BaseModel):
    """Forward-looking guidance item extracted from management commentary."""

    model_config = ConfigDict(extra="forbid")

    metric: str
    value: str
    period: str
    context: Optional[str]


class ManagementSignals(BaseModel):
    """Structured view of management tone and notable signals."""

    model_config = ConfigDict(extra="forbid")

    overall_tone: str
    positive_signals: list[str]
    watch_signals: list[str]


class EarningsAnalysisResponse(BaseModel):
    """Structured earnings call analysis output."""

    model_config = ConfigDict(extra="forbid")

    executive_summary: list[str] = Field(
        ...,
        min_length=1,
        max_length=MAX_INSIGHT_ITEMS,
        description="Concise summary points covering the most important takeaways.",
    )
    positives: list[str] = Field(
        ...,
        min_length=1,
        max_length=MAX_INSIGHT_ITEMS,
        description="Positive signals or strengths mentioned in the transcript.",
    )
    negatives: list[str] = Field(
        ...,
        min_length=1,
        max_length=MAX_INSIGHT_ITEMS,
        description="Negative signals or weaknesses mentioned in the transcript.",
    )
    risks: list[str] = Field(
        ...,
        min_length=1,
        max_length=MAX_INSIGHT_ITEMS,
        description="Business, financial, operational, or market risks mentioned.",
    )
    opportunities: list[str] = Field(
        ...,
        min_length=1,
        max_length=MAX_INSIGHT_ITEMS,
        description="Growth opportunities or favorable future possibilities mentioned.",
    )
    management_outlook: str = Field(
        ...,
        min_length=1,
        max_length=MAX_OUTLOOK_LENGTH,
        description="Management's stated outlook, guidance, or forward-looking tone.",
    )
    themes: list[str] = Field(
        ...,
        min_length=1,
        max_length=MAX_INSIGHT_ITEMS,
        description="Major recurring themes from the earnings call.",
    )
    financial_metrics: list[FinancialMetric] = Field(
        ...,
        description="Financial metrics extracted from the transcript.",
    )
    guidance: list[GuidanceItem] = Field(
        ...,
        description="Forward-looking guidance items discussed by management.",
    )
    management_signals: ManagementSignals = Field(
        ...,
        description="Management tone and notable positive or watch signals.",
    )

    @field_validator(
        "executive_summary",
        "positives",
        "negatives",
        "risks",
        "opportunities",
        "themes",
    )
    @classmethod
    def validate_insight_list(cls, value: list[str]) -> list[str]:
        """Trim insight items and reject blank or overly long items."""
        cleaned_items: list[str] = []

        for item in value:
            cleaned_item = item.strip()

            if not cleaned_item:
                raise ValueError("Insight lists cannot contain blank items.")

            if len(cleaned_item) > MAX_INSIGHT_LENGTH:
                raise ValueError(
                    f"Insight items must be {MAX_INSIGHT_LENGTH} characters or fewer."
                )

            cleaned_items.append(cleaned_item)

        return cleaned_items

    @field_validator("management_outlook")
    @classmethod
    def validate_management_outlook(cls, value: str) -> str:
        """Trim management outlook and reject blank content."""
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("Management outlook cannot be blank.")

        return cleaned_value


class ErrorResponse(BaseModel):
    """Standard error response contract for future API routes."""

    model_config = ConfigDict(extra="forbid")

    error_code: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Stable machine-readable error identifier.",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Safe human-readable error message.",
    )
    details: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional safe context about the error.",
    )
