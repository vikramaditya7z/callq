"""Gemini-compatible structured output schemas."""

from __future__ import annotations

from typing import Any

from backend.models.analysis import (
    MAX_INSIGHT_ITEMS,
    MAX_INSIGHT_LENGTH,
    MAX_OUTLOOK_LENGTH,
)


GEMINI_ANALYSIS_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "executive_summary": {
            "type": "array",
            "description": "Concise summary points covering the most important takeaways.",
            "minItems": 1,
            "maxItems": MAX_INSIGHT_ITEMS,
            "items": {
                "type": "string",
                "maxLength": MAX_INSIGHT_LENGTH,
            },
        },
        "positives": {
            "type": "array",
            "description": "Positive signals or strengths mentioned in the transcript.",
            "minItems": 1,
            "maxItems": MAX_INSIGHT_ITEMS,
            "items": {
                "type": "string",
                "maxLength": MAX_INSIGHT_LENGTH,
            },
        },
        "negatives": {
            "type": "array",
            "description": "Negative signals or weaknesses mentioned in the transcript.",
            "minItems": 1,
            "maxItems": MAX_INSIGHT_ITEMS,
            "items": {
                "type": "string",
                "maxLength": MAX_INSIGHT_LENGTH,
            },
        },
        "risks": {
            "type": "array",
            "description": "Business, financial, operational, or market risks mentioned.",
            "minItems": 1,
            "maxItems": MAX_INSIGHT_ITEMS,
            "items": {
                "type": "string",
                "maxLength": MAX_INSIGHT_LENGTH,
            },
        },
        "opportunities": {
            "type": "array",
            "description": "Growth opportunities or favorable future possibilities mentioned.",
            "minItems": 1,
            "maxItems": MAX_INSIGHT_ITEMS,
            "items": {
                "type": "string",
                "maxLength": MAX_INSIGHT_LENGTH,
            },
        },
        "management_outlook": {
            "type": "string",
            "description": "Management's stated outlook, guidance, or forward-looking tone.",
            "minLength": 1,
            "maxLength": MAX_OUTLOOK_LENGTH,
        },
        "themes": {
            "type": "array",
            "description": "Major recurring themes from the earnings call.",
            "minItems": 1,
            "maxItems": MAX_INSIGHT_ITEMS,
            "items": {
                "type": "string",
                "maxLength": MAX_INSIGHT_LENGTH,
            },
        },
    },
    "required": [
        "executive_summary",
        "positives",
        "negatives",
        "risks",
        "opportunities",
        "management_outlook",
        "themes",
    ],
}
