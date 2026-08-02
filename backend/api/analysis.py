"""Analysis route for earnings call transcript requests."""

from fastapi import APIRouter, HTTPException, status

from backend.models.analysis import EarningsAnalysisRequest, EarningsAnalysisResponse
from backend.services.analysis_service import (
    AnalysisServiceError,
    GeminiServiceError,
    analyze_transcript,
)
from backend.services.gemini_service import GeminiConfigurationError


router = APIRouter(tags=["analysis"])


@router.post("/analyze", response_model=EarningsAnalysisResponse)
def analyze_earnings_call(
    request: EarningsAnalysisRequest,
) -> EarningsAnalysisResponse:
    """Analyze one earnings call transcript using the service layer."""
    try:
        return analyze_transcript(request.transcript)
    except GeminiConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI provider is not configured.",
        ) from error
    except (GeminiServiceError, AnalysisServiceError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI provider failed to return a valid analysis.",
        ) from error
