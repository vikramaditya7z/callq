"""Fixture loader for external JSON transcript test datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.eval.models import (
    BenchmarkCase,
    ExpectedCalculation,
    ExpectedFact,
    ExpectedGuidance,
)
from backend.models.v2_analysis import HistoricalTranscript, V2AnalysisRequest


DEFAULT_FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FixtureGroundTruth(BaseModel):
    """Ground truth expectations associated with a transcript fixture."""

    model_config = ConfigDict(extra="forbid")

    expected_facts: List[ExpectedFact] = Field(default_factory=list)
    expected_guidance: List[ExpectedGuidance] = Field(default_factory=list)
    expected_calculations: List[ExpectedCalculation] = Field(default_factory=list)
    expected_evidence_gaps: List[str] = Field(default_factory=list)
    prohibited_claims: List[str] = Field(default_factory=list)
    require_empty_guidance: bool = False


class TranscriptFixture(BaseModel):
    """Structured earnings call transcript test fixture."""

    model_config = ConfigDict(extra="forbid")

    fixture_id: str
    company_name: str
    reporting_period: str
    description: str
    current_transcript: str
    historical_transcripts: List[HistoricalTranscript] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    ground_truth: Optional[FixtureGroundTruth] = None

    def to_benchmark_case(self) -> BenchmarkCase:
        """Convert the fixture into a runnable BenchmarkCase."""
        gt = self.ground_truth or FixtureGroundTruth()
        return BenchmarkCase(
            case_id=self.fixture_id,
            name=f"{self.company_name} ({self.reporting_period})",
            description=self.description,
            request=V2AnalysisRequest(
                current_transcript=self.current_transcript,
                historical_transcripts=self.historical_transcripts,
            ),
            expected_facts=gt.expected_facts,
            expected_guidance=gt.expected_guidance,
            expected_calculations=gt.expected_calculations,
            expected_evidence_gaps=gt.expected_evidence_gaps,
            prohibited_claims=gt.prohibited_claims,
            require_empty_guidance=gt.require_empty_guidance,
        )


def load_fixture_file(file_path: Path | str) -> TranscriptFixture:
    """Load and validate a single transcript fixture JSON file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Fixture file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        raise ValueError(f"Failed to parse JSON from {path}: {error}") from error

    return TranscriptFixture.model_validate(data)


def load_fixtures_from_directory(
    directory_path: Optional[Path | str] = None,
) -> List[TranscriptFixture]:
    """Load all JSON transcript fixtures from a directory."""
    target_dir = Path(directory_path) if directory_path is not None else DEFAULT_FIXTURES_DIR
    if not target_dir.exists():
        return []

    fixtures: List[TranscriptFixture] = []
    for file_path in sorted(target_dir.glob("*.json")):
        try:
            fixtures.append(load_fixture_file(file_path))
        except Exception as error:
            raise ValueError(f"Invalid fixture in {file_path}: {error}") from error

    return fixtures
