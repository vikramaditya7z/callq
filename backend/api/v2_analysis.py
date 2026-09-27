"""Additive API route for the V2 financial reasoning pipeline."""

from fastapi import APIRouter, HTTPException, status

from backend.models.v2_analysis import V2AnalysisRequest, V2AnalysisResponse
from backend.services.gemini_service import GeminiConfigurationError, GeminiServiceError
from backend.services.v2_analysis_service import (
    V2AnalysisServiceError,
    V2CalculationPipelineError,
    run_v2_analysis,
)


router = APIRouter(tags=["v2-analysis"])


@router.post("/analyze/v2", response_model=V2AnalysisResponse)
def analyze_v2(request: V2AnalysisRequest) -> V2AnalysisResponse:
    """Run the isolated V2 pipeline without altering the V1.5 route."""
    try:
        return run_v2_analysis(request)
    except GeminiConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="V2 AI provider is not configured.",
        ) from error
    except GeminiServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="V2 AI provider failed to return a valid response.",
        ) from error
    except V2CalculationPipelineError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="V2 deterministic calculation pipeline failed.",
        ) from error
    except V2AnalysisServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="V2 analysis could not be validated.",
        ) from error
