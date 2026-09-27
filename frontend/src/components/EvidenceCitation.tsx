import type { EvidenceRef, SourceDocument } from "../types/v2Insights";

type EvidenceCitationProps = {
  evidence: EvidenceRef;
  sourceDocuments: SourceDocument[];
};

export function EvidenceCitation({ evidence, sourceDocuments }: EvidenceCitationProps) {
  const source = sourceDocuments.find(
    (document) => document.source_id === evidence.source_id,
  );

  return (
    <details className="evidence-citation">
      <summary>
        Evidence · {source?.source_id ?? evidence.source_id}
        {source ? ` · ${formatDocumentType(source.document_type)}` : ""}
      </summary>
      <blockquote>{evidence.exact_quote}</blockquote>
      {source ? <p className="evidence-context">{buildContext(source, evidence)}</p> : null}
    </details>
  );
}

function formatDocumentType(documentType: string): string {
  return documentType.replace(/_/g, " ");
}

function buildContext(source: SourceDocument, evidence: EvidenceRef): string {
  if (evidence.start_offset === null || evidence.end_offset === null) {
    return "Verified source excerpt.";
  }

  const contextStart = Math.max(0, evidence.start_offset - 72);
  const contextEnd = Math.min(source.text.length, evidence.end_offset + 72);
  const prefix = contextStart > 0 ? "…" : "";
  const suffix = contextEnd < source.text.length ? "…" : "";

  return `${prefix}${source.text.slice(contextStart, contextEnd)}${suffix}`;
}
