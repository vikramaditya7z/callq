"""Gemini structured-output schema for V2.3 grounded interpretation."""

from __future__ import annotations

from typing import Any, Dict


EVIDENCE_REF_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "source_id": {"type": "string"},
        "exact_quote": {"type": "string"},
    },
    "required": ["source_id", "exact_quote"],
}

INTERPRETATION_ITEM_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "claim": {"type": "string"},
        "why_it_matters": {"type": "string"},
        "supporting_fact_ids": {"type": "array", "items": {"type": "string"}},
        "calculation_ids": {"type": "array", "items": {"type": "string"}},
        "evidence_refs": {"type": "array", "items": EVIDENCE_REF_SCHEMA},
    },
    "required": [
        "claim",
        "why_it_matters",
        "supporting_fact_ids",
        "calculation_ids",
        "evidence_refs",
    ],
}

EVIDENCE_GAP_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "gap_id": {"type": "string"},
        "description": {"type": "string"},
        "related_fact_ids": {"type": "array", "items": {"type": "string"}},
        "related_calculation_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "gap_id",
        "description",
        "related_fact_ids",
        "related_calculation_ids",
    ],
}

V2_INTERPRETATION_RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "bull_items": {"type": "array", "items": INTERPRETATION_ITEM_SCHEMA},
        "bear_items": {"type": "array", "items": INTERPRETATION_ITEM_SCHEMA},
        "watch_items": {"type": "array", "items": INTERPRETATION_ITEM_SCHEMA},
        "evidence_gaps": {"type": "array", "items": EVIDENCE_GAP_SCHEMA},
    },
    "required": ["bull_items", "bear_items", "watch_items", "evidence_gaps"],
}
