"""V2.1 financial extraction and evidence contracts."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class V2ContractModel(BaseModel):
    """Base model that keeps V2 contracts strict."""

    model_config = ConfigDict(extra="forbid")


class SourceDocument(V2ContractModel):
    """A transcript supplied as an evidence source for V2 extraction."""

    source_id: str = Field(..., min_length=1, max_length=100)
    document_type: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1)

    @field_validator("source_id", "document_type", "text")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        """Reject values that become blank after trimming."""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("Value cannot be blank.")
        return cleaned_value


class EvidenceRef(V2ContractModel):
    """Exact transcript evidence supporting one extracted item.

    The extraction model supplies ``source_id`` and ``exact_quote``. Python
    resolves offsets from the quote and does not trust supplied offsets.
    """

    source_id: str = Field(..., min_length=1, max_length=100)
    exact_quote: str = Field(..., min_length=1, max_length=5_000)
    start_offset: Optional[int] = Field(default=None, ge=0)
    end_offset: Optional[int] = Field(default=None, ge=0)

    @field_validator("source_id", "exact_quote")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        """Reject blank evidence identifiers and quotes."""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("Value cannot be blank.")
        return cleaned_value


class FinancialFact(V2ContractModel):
    """One explicitly reported financial fact; it is not a calculation."""

    fact_id: str = Field(..., min_length=1, max_length=100)
    metric_key: str = Field(..., min_length=1, max_length=100)
    reported_value: str = Field(..., min_length=1, max_length=500)
    unit: Optional[str] = Field(default=None, max_length=100)
    period: Optional[str] = Field(default=None, max_length=200)
    period_type: Optional[str] = Field(default=None, max_length=100)
    evidence: EvidenceRef


class GuidanceFact(V2ContractModel):
    """One explicitly reported management guidance fact; ranges stay as reported."""

    fact_id: str = Field(..., min_length=1, max_length=100)
    metric_key: str = Field(..., min_length=1, max_length=100)
    guidance_value: str = Field(..., min_length=1, max_length=500)
    unit: Optional[str] = Field(default=None, max_length=100)
    period: Optional[str] = Field(default=None, max_length=200)
    evidence: EvidenceRef


class QualitativeObservation(V2ContractModel):
    """A non-numeric observation explicitly supported by the transcript."""

    observation_id: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=100)
    statement: str = Field(..., min_length=1, max_length=1_000)
    evidence: EvidenceRef


class V2ExtractionResponse(V2ContractModel):
    """Validated V2.1 extraction output before later reasoning stages."""

    financial_facts: List[FinancialFact] = Field(default_factory=list)
    guidance: List[GuidanceFact] = Field(default_factory=list)
    qualitative_observations: List[QualitativeObservation] = Field(default_factory=list)


class NormalizedFinancialValue(V2ContractModel):
    """A parsed financial fact ready for deterministic calculation."""

    fact_id: str = Field(..., min_length=1, max_length=100)
    metric_key: str = Field(..., min_length=1, max_length=100)
    numeric_value: Decimal
    normalized_unit: str = Field(..., min_length=1, max_length=50)
    currency: Optional[str] = Field(default=None, max_length=10)
    original_reported_value: str = Field(..., min_length=1, max_length=500)
    period: Optional[str] = Field(default=None, max_length=200)
    period_type: Optional[str] = Field(default=None, max_length=100)


class NormalizedGuidanceRange(V2ContractModel):
    """A guidance range with explicit numeric endpoints for V2.2 only."""

    fact_id: str = Field(..., min_length=1, max_length=100)
    metric_key: str = Field(..., min_length=1, max_length=100)
    low: Decimal
    high: Decimal
    normalized_unit: str = Field(..., min_length=1, max_length=50)
    currency: Optional[str] = Field(default=None, max_length=10)
    original_guidance_value: str = Field(..., min_length=1, max_length=500)
    period: Optional[str] = Field(default=None, max_length=200)


class Calculation(V2ContractModel):
    """An auditable deterministic calculation or explicit unavailable result."""

    calculation_id: str = Field(..., min_length=1, max_length=100)
    calculation_type: str = Field(..., min_length=1, max_length=100)
    input_fact_ids: List[str] = Field(..., min_length=1, max_length=10)
    formula: str = Field(..., min_length=1, max_length=500)
    result: Optional[float] = None
    unit: Optional[str] = Field(default=None, max_length=50)
    status: Literal["valid", "unavailable"]
    reason: Optional[str] = Field(default=None, max_length=500)


class TrendClassification(V2ContractModel):
    """Directional classification from a supported deterministic calculation."""

    calculation_id: str = Field(..., min_length=1, max_length=100)
    classification: Optional[Literal["improving", "deteriorating", "flat"]] = None
    threshold: Optional[float] = None
    status: Literal["valid", "unavailable"]
    reason: Optional[str] = Field(default=None, max_length=500)


class InterpretationItem(V2ContractModel):
    """One grounded Bull, Bear, or Watch interpretation item."""

    claim: str = Field(..., min_length=1, max_length=1_000)
    why_it_matters: str = Field(..., min_length=1, max_length=1_500)
    supporting_fact_ids: List[str] = Field(default_factory=list, max_length=20)
    calculation_ids: List[str] = Field(default_factory=list, max_length=20)
    evidence_refs: List[EvidenceRef] = Field(..., min_length=1, max_length=20)


class EvidenceGap(V2ContractModel):
    """A limitation caused by missing or incomparable verified inputs."""

    gap_id: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1_000)
    related_fact_ids: List[str] = Field(default_factory=list, max_length=20)
    related_calculation_ids: List[str] = Field(default_factory=list, max_length=20)


class V2InterpretationResponse(V2ContractModel):
    """Validated V2.3 grounded interpretation output."""

    bull_items: List[InterpretationItem] = Field(default_factory=list)
    bear_items: List[InterpretationItem] = Field(default_factory=list)
    watch_items: List[InterpretationItem] = Field(default_factory=list)
    evidence_gaps: List[EvidenceGap] = Field(default_factory=list)


V2_MIN_TRANSCRIPT_LENGTH = 200
V2_MAX_TRANSCRIPT_LENGTH = 100_000
V2_MAX_HISTORICAL_TRANSCRIPTS = 5


class HistoricalTranscript(V2ContractModel):
    """A labeled prior transcript supplied for V2 comparison."""

    label: str = Field(..., min_length=1, max_length=100)
    transcript: str = Field(
        ...,
        min_length=V2_MIN_TRANSCRIPT_LENGTH,
        max_length=V2_MAX_TRANSCRIPT_LENGTH,
    )

    @field_validator("label", "transcript")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        """Reject values that become blank after trimming."""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("Value cannot be blank.")
        return cleaned_value


class V2AnalysisRequest(V2ContractModel):
    """Input for the additive V2 analysis pipeline."""

    current_transcript: str = Field(
        ...,
        min_length=V2_MIN_TRANSCRIPT_LENGTH,
        max_length=V2_MAX_TRANSCRIPT_LENGTH,
    )
    historical_transcripts: List[HistoricalTranscript] = Field(
        default_factory=list,
        max_length=V2_MAX_HISTORICAL_TRANSCRIPTS,
    )

    @field_validator("current_transcript")
    @classmethod
    def validate_current_transcript(cls, value: str) -> str:
        """Trim input and require readable current-transcript content."""
        cleaned_value = value.strip()
        if len(cleaned_value) < V2_MIN_TRANSCRIPT_LENGTH:
            raise ValueError("Transcript must contain enough text for analysis.")
        if not any(character.isalpha() for character in cleaned_value):
            raise ValueError("Transcript must contain readable text.")
        return cleaned_value


class V2Coverage(V2ContractModel):
    """Deterministic summary of the pipeline inputs and calculation outcomes."""

    source_count: int = Field(..., ge=1)
    financial_fact_count: int = Field(..., ge=0)
    guidance_count: int = Field(..., ge=0)
    qualitative_observation_count: int = Field(..., ge=0)
    valid_calculation_count: int = Field(..., ge=0)
    unavailable_calculation_count: int = Field(..., ge=0)


class V2AnalysisResponse(V2ContractModel):
    """Complete V2.4 response composed from the existing V2 stages."""

    source_documents: List[SourceDocument] = Field(..., min_length=1)
    facts: V2ExtractionResponse
    calculations: List[Calculation] = Field(default_factory=list)
    thesis: V2InterpretationResponse
    coverage: V2Coverage
