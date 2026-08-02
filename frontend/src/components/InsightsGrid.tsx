import { InsightCard } from "./InsightCard";
import { insightSections, type AnalysisResponse } from "../types/insights";

type InsightsGridProps = {
  analysis: AnalysisResponse | null;
  loading: boolean;
};

export function InsightsGrid({ analysis, loading }: InsightsGridProps) {
  return (
    <section className="insights-section" aria-label="Analysis sections">
      {insightSections.map((section) => (
        <InsightCard
          key={section.title}
          section={section}
          value={analysis?.[section.responseKey]}
          loading={loading}
        />
      ))}
    </section>
  );
}
