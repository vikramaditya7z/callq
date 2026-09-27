import { EvidenceCitation } from "./EvidenceCitation";
import type {
  Calculation,
  FinancialFact,
  GuidanceFact,
  SourceDocument,
} from "../types/v2Insights";

type V2MetricAssessmentProps = {
  financialFacts: FinancialFact[];
  guidance: GuidanceFact[];
  calculations: Calculation[];
  sourceDocuments: SourceDocument[];
};

type DisplayFact = FinancialFact | GuidanceFact;

export function V2MetricAssessment({
  financialFacts,
  guidance,
  calculations,
  sourceDocuments,
}: V2MetricAssessmentProps) {
  const facts: DisplayFact[] = [...financialFacts, ...guidance];
  const unavailableCalculations = calculations.filter(
    (calculation) => calculation.status === "unavailable",
  );

  return (
    <section className="v2-section" aria-label="Verified facts and calculations">
      <div className="v2-section-heading">
        <div>
          <p className="v2-kicker">Verified facts → deterministic calculations</p>
          <h2>Financial facts and provenance</h2>
        </div>
        <span className="v2-count">{facts.length} extracted items</span>
      </div>

      {facts.length === 0 ? (
        <EmptyState message="No supported financial facts or guidance were extracted." />
      ) : (
        <div className="v2-fact-grid">
          {facts.map((fact) => {
            const relatedCalculations = calculations.filter((calculation) =>
              calculation.input_fact_ids.includes(fact.fact_id),
            );

            return (
              <article className="v2-fact-card" key={fact.fact_id}>
                <div className="v2-fact-heading">
                  <div>
                    <p className="v2-fact-label">{formatLabel(fact.metric_key)}</p>
                    <p className="v2-fact-value">{getFactValue(fact)}</p>
                  </div>
                  <span className="v2-source-badge">{fact.evidence.source_id}</span>
                </div>
                <p className="v2-fact-meta">
                  {fact.period ?? "Period not supplied"}
                  {" · "}
                  {"reported_value" in fact ? "Financial fact" : "Management guidance"}
                </p>
                <EvidenceCitation evidence={fact.evidence} sourceDocuments={sourceDocuments} />
                <RelatedCalculations calculations={relatedCalculations} />
              </article>
            );
          })}
        </div>
      )}

      <div className="v2-calculation-section">
        <div className="v2-section-heading v2-section-heading-compact">
          <div>
            <p className="v2-kicker">Python-generated only</p>
            <h3>Calculation ledger</h3>
          </div>
          <span className="v2-count">{calculations.length} calculations</span>
        </div>
        {calculations.length === 0 ? (
          <EmptyState message="No compatible calculation inputs were available." />
        ) : (
          <div className="v2-calculation-list">
            {calculations.map((calculation) => (
              <CalculationRow key={calculation.calculation_id} calculation={calculation} />
            ))}
          </div>
        )}
      </div>

      {unavailableCalculations.length > 0 ? (
        <div className="v2-gap-panel" aria-label="Unavailable comparisons">
          <h3>Unavailable comparisons</h3>
          <ul>
            {unavailableCalculations.map((calculation) => (
              <li key={calculation.calculation_id}>
                <strong>{formatLabel(calculation.calculation_type)}:</strong>{" "}
                {calculation.reason ?? "The backend did not provide a reason."}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

function RelatedCalculations({ calculations }: { calculations: Calculation[] }) {
  if (calculations.length === 0) {
    return <p className="v2-related-empty">No deterministic comparison was returned.</p>;
  }

  return (
    <ul className="v2-related-calculations">
      {calculations.map((calculation) => (
        <li key={calculation.calculation_id}>
          {formatLabel(calculation.calculation_type)}: {formatCalculationResult(calculation)}
        </li>
      ))}
    </ul>
  );
}

function CalculationRow({ calculation }: { calculation: Calculation }) {
  const isUnavailable = calculation.status === "unavailable";

  return (
    <article className={`v2-calculation-row ${isUnavailable ? "is-unavailable" : ""}`}>
      <div>
        <p className="v2-calculation-name">{formatLabel(calculation.calculation_type)}</p>
        <p className="v2-calculation-formula">{calculation.formula}</p>
        <p className="v2-calculation-inputs">
          Input facts: {calculation.input_fact_ids.join(", ")}
        </p>
      </div>
      <div className="v2-calculation-result">
        <span className={`v2-status v2-status-${calculation.status}`}>{calculation.status}</span>
        <strong>{formatCalculationResult(calculation)}</strong>
        {isUnavailable && calculation.reason ? (
          <p className="v2-unavailable-reason">{calculation.reason}</p>
        ) : null}
      </div>
    </article>
  );
}

function EmptyState({ message }: { message: string }) {
  return <div className="v2-empty-state">{message}</div>;
}

function getFactValue(fact: DisplayFact): string {
  return "reported_value" in fact ? fact.reported_value : fact.guidance_value;
}

function formatCalculationResult(calculation: Calculation): string {
  if (calculation.status === "unavailable" || calculation.result === null) {
    return "Unavailable";
  }

  return `${calculation.result.toLocaleString()}${calculation.unit ? ` ${calculation.unit}` : ""}`;
}

function formatLabel(value: string): string {
  return value.replace(/_/g, " ");
}
