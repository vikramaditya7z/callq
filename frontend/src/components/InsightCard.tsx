import type { InsightSection } from "../types/insights";

type InsightCardProps = {
  section: InsightSection;
  value?: string | string[];
  loading: boolean;
};

export function InsightCard({ section, value, loading }: InsightCardProps) {
  const hasListValue = Array.isArray(value) && value.length > 0;
  const hasTextValue = typeof value === "string" && value.trim().length > 0;
  const hasContent = hasListValue || hasTextValue;

  return (
    <article className={`insight-card ${hasContent ? "insight-card-populated" : ""}`}>
      <div className={`accent accent-${section.tone}`} aria-hidden="true" />
      <h3>{section.title}</h3>
      {loading ? (
        <div className="card-loading" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      ) : null}
      {!loading && hasListValue ? (
        <ul className="insight-list">
          {value.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
      {!loading && hasTextValue ? <p className="insight-text">{value}</p> : null}
      {!loading && !hasContent ? (
        <div className="empty-state">
          <span>No analysis yet</span>
        </div>
      ) : null}
    </article>
  );
}
