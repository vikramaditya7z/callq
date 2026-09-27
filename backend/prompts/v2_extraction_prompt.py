"""Prompt construction for V2.1 evidence-backed extraction."""

from __future__ import annotations

from typing import Sequence

from backend.models.v2_analysis import SourceDocument


V2_EXTRACTION_PROMPT = """
You extract evidence-backed information from supplied earnings-call transcripts.

Use only the supplied source documents. Extract information only when it is
explicitly stated in a source. Preserve reported wording and values exactly.
Never invent historical values, normalize values, or infer unsupported facts.

Do not calculate growth rates, percentage changes, margin deltas, guidance
midpoints, CAGR, or any other derived financial values.

Return three distinct collections:
1. financial_facts: explicitly reported historical or current financial facts.
2. guidance: explicitly stated forward-looking management guidance. Preserve
   a range exactly as reported in guidance_value.
3. qualitative_observations: explicitly stated non-numeric management or
   business observations.

Every item must include evidence with the source_id of the supplied document
and an exact_quote copied verbatim from that document. Do not provide offsets;
Python resolves them. Do not create an item if no exact supporting quote exists.

Use concise stable identifiers for fact_id and observation_id. Use clear metric
keys, but do not turn a reported value into a calculation.

Return only JSON matching the supplied schema.
""".strip()


def build_v2_extraction_prompt(source_documents: Sequence[SourceDocument]) -> str:
    """Build a V2.1 extraction prompt containing labeled source documents."""
    rendered_sources = "\n\n".join(
        "Source ID: {source_id}\nDocument type: {document_type}\nTranscript:\n{text}".format(
            source_id=source_document.source_id,
            document_type=source_document.document_type,
            text=source_document.text,
        )
        for source_document in source_documents
    )
    return "{}\n\nSupplied source documents:\n{}".format(
        V2_EXTRACTION_PROMPT,
        rendered_sources,
    )
