"""Gemini structured-output schema for V2.1 transcript extraction."""

from __future__ import annotations

from typing import Any, Dict


EVIDENCE_REF_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "source_id": {
            "type": "string",
            "description": "Identifier of the supplied source document.",
        },
        "exact_quote": {
            "type": "string",
            "description": "Exact verbatim quote copied from that source document.",
        },
    },
    "required": ["source_id", "exact_quote"],
}


V2_EXTRACTION_RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "financial_facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "fact_id": {"type": "string"},
                    "metric_key": {"type": "string"},
                    "reported_value": {"type": "string"},
                    "unit": {"type": "string", "nullable": True},
                    "period": {"type": "string", "nullable": True},
                    "period_type": {"type": "string", "nullable": True},
                    "evidence": EVIDENCE_REF_SCHEMA,
                },
                "required": [
                    "fact_id",
                    "metric_key",
                    "reported_value",
                    "unit",
                    "period",
                    "period_type",
                    "evidence",
                ],
            },
        },
        "guidance": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "fact_id": {"type": "string"},
                    "metric_key": {"type": "string"},
                    "guidance_value": {"type": "string"},
                    "unit": {"type": "string", "nullable": True},
                    "period": {"type": "string", "nullable": True},
                    "evidence": EVIDENCE_REF_SCHEMA,
                },
                "required": [
                    "fact_id",
                    "metric_key",
                    "guidance_value",
                    "unit",
                    "period",
                    "evidence",
                ],
            },
        },
        "qualitative_observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "observation_id": {"type": "string"},
                    "category": {"type": "string"},
                    "statement": {"type": "string"},
                    "evidence": EVIDENCE_REF_SCHEMA,
                },
                "required": [
                    "observation_id",
                    "category",
                    "statement",
                    "evidence",
                ],
            },
        },
    },
    "required": ["financial_facts", "guidance", "qualitative_observations"],
}
