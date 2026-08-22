import type { AnalysisResponse, FinancialMetric, GuidanceItem } from "../types/insights";

type V15InsightsProps = {
  analysis: AnalysisResponse | null;
  loading: boolean;
};

export function V15Insights({ analysis, loading }: V15InsightsProps) {
  if (loading || !analysis) {
    return null;
  }

  const hasFinancialMetrics = analysis.financial_metrics.length > 0;
  const hasGuidance = analysis.guidance.length > 0;
  const hasManagementSignals =
    analysis.management_signals.overall_tone.trim().length > 0 ||
    analysis.management_signals.positive_signals.length > 0 ||
    analysis.management_signals.watch_signals.length > 0;

  if (!hasFinancialMetrics && !hasGuidance && !hasManagementSignals) {
    return null;
  }

  return (
    <section className="v15-section" aria-label="Detailed analysis">
      {hasFinancialMetrics ? (
        <article className="v15-card">
          <div className="v15-heading">
            <p className="v15-kicker">Historical</p>
            <h2>Financial Metrics</h2>
          </div>
          <div className="metric-grid">
            {analysis.financial_metrics.map((metric) => (
              <FinancialMetricItem key={buildMetricKey(metric)} metric={metric} />
            ))}
          </div>
        </article>
      ) : null}

      {hasGuidance ? (
        <article className="v15-card">
          <div className="v15-heading">
            <p className="v15-kicker">Forward-looking</p>
            <h2>Management Guidance</h2>
          </div>
          <div className="guidance-list">
            {analysis.guidance.map((item) => (
              <GuidanceItemRow key={buildGuidanceKey(item)} item={item} />
            ))}
          </div>
        </article>
      ) : null}

      {hasManagementSignals ? (
        <article className="v15-card v15-card-wide">
          <div className="v15-heading">
            <p className="v15-kicker">Qualitative</p>
            <h2>Management Signals</h2>
          </div>
          {analysis.management_signals.overall_tone.trim().length > 0 ? (
            <p className="tone-pill">{analysis.management_signals.overall_tone}</p>
          ) : null}
          <div className="signals-grid">
            <SignalList
              title="Positive Signals"
              tone="positive"
              signals={analysis.management_signals.positive_signals}
            />
            <SignalList
              title="Watch Signals"
              tone="watch"
              signals={analysis.management_signals.watch_signals}
            />
          </div>
        </article>
      ) : null}
    </section>
  );
}

function FinancialMetricItem({ metric }: { metric: FinancialMetric }) {
  return (
    <div className="metric-item">
      <p className="metric-name">{metric.name}</p>
      <div className="metric-value-container">
        <span className="metric-value">{metric.value}</span>
        {metric.change ? <span className="metric-pill">{metric.change}</span> : null}
      </div>
      {metric.period ? (
        <div className="metric-period-container">
          <span className="metric-pill">
            {metric.period.charAt(0).toUpperCase() + metric.period.slice(1)}
          </span>
        </div>
      ) : null}
    </div>
  );
}

function GuidanceItemRow({ item }: { item: GuidanceItem }) {
  return (
    <div className="guidance-item">
      <div>
        <p className="guidance-metric">{item.metric}</p>
        <p className="guidance-context">{item.context || item.period}</p>
      </div>
      <div className="guidance-value-block">
        <p className="guidance-value">{item.value}</p>
        <p className="guidance-period">{item.period}</p>
      </div>
    </div>
  );
}

function SignalList({
  title,
  tone,
  signals,
}: {
  title: string;
  tone: "positive" | "watch";
  signals: string[];
}) {
  if (signals.length === 0) {
    return (
      <div className="signal-panel">
        <h3>{title}</h3>
        <p className="signal-empty">No clear signals identified.</p>
      </div>
    );
  }

  return (
    <div className={`signal-panel signal-panel-${tone}`}>
      <h3>{title}</h3>
      <ul>
        {signals.map((signal) => (
          <li key={signal}>{signal}</li>
        ))}
      </ul>
    </div>
  );
}

function buildMetricKey(metric: FinancialMetric): string {
  return [metric.name, metric.value, metric.period ?? "", metric.change ?? ""].join("-");
}

function buildGuidanceKey(item: GuidanceItem): string {
  return [item.metric, item.value, item.period].join("-");
}
