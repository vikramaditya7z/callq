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
        "financial_metrics": {
            "type": "array",
            "description": "Explicitly stated financial metrics from the transcript.",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Metric name, such as revenue, margin, ARR, or cash flow.",
                    },
                    "value": {
                        "type": "string",
                        "description": "Exact reported value and units from the transcript.",
                    },
                    "change": {
                        "type": "string",
                        "nullable": True,
                        "description": "Reported comparison or change, if provided.",
                    },
                    "period": {
                        "type": "string",
                        "nullable": True,
                        "description": "Reported period for the metric, if provided.",
                    },
                },
                "required": ["name", "value", "change", "period"],
            },
        },
        "guidance": {
            "type": "array",
            "description": "Explicit forward-looking guidance from management.",
            "items": {
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "description": "Guided metric or business measure.",
                    },
                    "value": {
                        "type": "string",
                        "description": "Reported target, range, value, or qualitative guidance.",
                    },
                    "period": {
                        "type": "string",
                        "description": "Future period the guidance applies to.",
                    },
                    "context": {
                        "type": "string",
                        "nullable": True,
                        "description": "Useful supporting context from management, if provided.",
                    },
                },
                "required": ["metric", "value", "period", "context"],
            },
        },
        "management_signals": {
            "type": "object",
            "description": "Management tone and concrete signals from the call.",
            "properties": {
                "overall_tone": {
                    "type": "string",
                    "description": "Overall management tone supported by the transcript.",
                },
                "positive_signals": {
                    "type": "array",
                    "description": "Concrete positive management signals.",
                    "items": {
                        "type": "string",
                        "maxLength": MAX_INSIGHT_LENGTH,
                    },
                },
                "watch_signals": {
                    "type": "array",
                    "description": "Concrete cautionary or watch signals.",
                    "items": {
                        "type": "string",
                        "maxLength": MAX_INSIGHT_LENGTH,
                    },
                },
            },
            "required": ["overall_tone", "positive_signals", "watch_signals"],
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
        "financial_metrics",
        "guidance",
        "management_signals",
    ],
}
