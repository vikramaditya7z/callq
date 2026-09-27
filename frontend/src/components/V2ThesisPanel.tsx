import { EvidenceCitation } from "./EvidenceCitation";
import type {
  EvidenceGap,
  InterpretationItem,
  SourceDocument,
} from "../types/v2Insights";

type V2ThesisPanelProps = {
  bullItems: InterpretationItem[];
  bearItems: InterpretationItem[];
  watchItems: InterpretationItem[];
  evidenceGaps: EvidenceGap[];
  sourceDocuments: SourceDocument[];
};

export function V2ThesisPanel({
  bullItems,
  bearItems,
  watchItems,
  evidenceGaps,
  sourceDocuments,
}: V2ThesisPanelProps) {
  return (
    <section className="v2-section" aria-label="Grounded financial interpretation">
      <div className="v2-section-heading">
        <div>
          <p className="v2-kicker">Verified facts + calculations → grounded interpretation</p>
          <h2>Evidence-backed thesis</h2>
        </div>
      </div>

      <div className="v2-thesis-grid">
        <ThesisColumn
          tone="bull"
          title="Bull"
          items={bullItems}
          sourceDocuments={sourceDocuments}
        />
        <ThesisColumn
          tone="bear"
          title="Bear"
          items={bearItems}
          sourceDocuments={sourceDocuments}
        />
        <ThesisColumn
          tone="watch"
          title="Watch"
          items={watchItems}
          sourceDocuments={sourceDocuments}
        />
      </div>

      <div className="v2-gap-panel" aria-label="Evidence gaps and limitations">
        <h3>Evidence gaps and limitations</h3>
        {evidenceGaps.length === 0 ? (
          <p>No additional limitations were returned by the backend.</p>
        ) : (
          <ul>
            {evidenceGaps.map((gap) => (
              <li key={gap.gap_id}>
                {gap.description}
                {gap.related_fact_ids.length > 0 ? (
                  <span> Facts: {gap.related_fact_ids.join(", ")}.</span>
                ) : null}
                {gap.related_calculation_ids.length > 0 ? (
                  <span> Calculations: {gap.related_calculation_ids.join(", ")}.</span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

function ThesisColumn({
  tone,
  title,
  items,
  sourceDocuments,
}: {
  tone: "bull" | "bear" | "watch";
  title: string;
  items: InterpretationItem[];
  sourceDocuments: SourceDocument[];
}) {
  return (
    <article className={`v2-thesis-column v2-thesis-${tone}`}>
      <h3>{title}</h3>
      {items.length === 0 ? (
        <p className="v2-thesis-empty">No supported {title.toLowerCase()} items returned.</p>
      ) : (
        <div className="v2-thesis-items">
          {items.map((item, index) => (
            <article className="v2-thesis-item" key={`${title}-${index}-${item.claim}`}>
              <h4>{item.claim}</h4>
              <p>{item.why_it_matters}</p>
              <ReferenceList label="Facts" values={item.supporting_fact_ids} />
              <ReferenceList label="Calculations" values={item.calculation_ids} />
              <div className="v2-thesis-evidence">
                {item.evidence_refs.map((evidence, evidenceIndex) => (
                  <EvidenceCitation
                    key={`${evidence.source_id}-${evidence.start_offset}-${evidenceIndex}`}
                    evidence={evidence}
                    sourceDocuments={sourceDocuments}
                  />
                ))}
              </div>
            </article>
          ))}
        </div>
      )}
    </article>
  );
}

function ReferenceList({ label, values }: { label: string; values: string[] }) {
  if (values.length === 0) {
    return null;
  }

  return (
    <p className="v2-reference-list">
      <strong>{label}:</strong> {values.join(", ")}
    </p>
  );
}
