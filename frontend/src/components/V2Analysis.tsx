import { useState } from "react";

import { analyzeV2 } from "../services/api";
import type { HistoricalTranscriptInput, V2AnalysisResponse } from "../types/v2Insights";
import { V2MetricAssessment } from "./V2MetricAssessment";
import { V2ThesisPanel } from "./V2ThesisPanel";

type HistoricalTranscriptDraft = HistoricalTranscriptInput & { id: number };

const MIN_TRANSCRIPT_LENGTH = 200;
const MAX_HISTORICAL_TRANSCRIPTS = 5;

export function V2Analysis() {
  const [currentTranscript, setCurrentTranscript] = useState("");
  const [historicalTranscripts, setHistoricalTranscripts] = useState<
    HistoricalTranscriptDraft[]
  >([]);
  const [nextHistoricalId, setNextHistoricalId] = useState(1);
  const [analysis, setAnalysis] = useState<V2AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasValidCurrentTranscript = currentTranscript.trim().length >= MIN_TRANSCRIPT_LENGTH;
  const hasValidHistoricalTranscripts = historicalTranscripts.every(
    (item) => item.label.trim().length > 0 && item.transcript.trim().length >= MIN_TRANSCRIPT_LENGTH,
  );
  const canAnalyze = hasValidCurrentTranscript && hasValidHistoricalTranscripts && !loading;

  async function handleAnalyze() {
    if (!canAnalyze) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await analyzeV2({
        current_transcript: currentTranscript,
        historical_transcripts: historicalTranscripts.map(({ label, transcript }) => ({
          label,
          transcript,
        })),
      });
      setAnalysis(result);
    } catch (caughtError) {
      setAnalysis(null);
      setError(getFriendlyV2Error(caughtError));
    } finally {
      setLoading(false);
    }
  }

  function addHistoricalTranscript() {
    if (historicalTranscripts.length >= MAX_HISTORICAL_TRANSCRIPTS || loading) {
      return;
    }

    setHistoricalTranscripts((items) => [
      ...items,
      { id: nextHistoricalId, label: "", transcript: "" },
    ]);
    setNextHistoricalId((value) => value + 1);
  }

  function updateHistoricalTranscript(
    id: number,
    field: "label" | "transcript",
    value: string,
  ) {
    setHistoricalTranscripts((items) =>
      items.map((item) => (item.id === id ? { ...item, [field]: value } : item)),
    );
  }

  function removeHistoricalTranscript(id: number) {
    setHistoricalTranscripts((items) => items.filter((item) => item.id !== id));
  }

  return (
    <section className="v2-workspace" aria-label="V2 financial reasoning analysis">
      <section className="v2-intro">
        <p className="eyebrow">V2 financial reasoning</p>
        <h2>Evidence-backed comparison workspace</h2>
        <p>
          Submit the current earnings call and, optionally, labeled prior calls. CallQ
          verifies extracted evidence before presenting deterministic calculations and
          grounded interpretation.
        </p>
      </section>

      <section className="v2-input-section" aria-busy={loading}>
        <div className="section-heading">
          <div>
            <h2>Current earnings call</h2>
            <p>This transcript is the current source used for comparisons.</p>
          </div>
          <button
            className="analyze-button"
            type="button"
            disabled={!canAnalyze}
            onClick={handleAnalyze}
          >
            {loading ? "Analyzing V2..." : "Run V2 analysis"}
          </button>
        </div>
        <textarea
          className="transcript-input"
          value={currentTranscript}
          onChange={(event) => setCurrentTranscript(event.target.value)}
          placeholder="Paste the current earnings call transcript..."
          aria-label="Current earnings call transcript"
          disabled={loading}
        />
        <p className="v2-input-helper">
          {currentTranscript.trim().length.toLocaleString()} characters · minimum {MIN_TRANSCRIPT_LENGTH}
        </p>
      </section>

      <section className="v2-history-section" aria-label="Historical transcripts">
        <div className="section-heading">
          <div>
            <h2>Historical transcripts</h2>
            <p>Optional labeled prior calls enable backend comparison when facts are compatible.</p>
          </div>
          <button
            className="v2-secondary-button"
            type="button"
            disabled={loading || historicalTranscripts.length >= MAX_HISTORICAL_TRANSCRIPTS}
            onClick={addHistoricalTranscript}
          >
            Add historical call
          </button>
        </div>
        {historicalTranscripts.length === 0 ? (
          <p className="v2-empty-copy">No historical calls added. V2 can still verify current-call facts.</p>
        ) : (
          <div className="v2-history-list">
            {historicalTranscripts.map((item) => (
              <article className="v2-history-card" key={item.id}>
                <div className="v2-history-actions">
                  <input
                    className="v2-label-input"
                    value={item.label}
                    onChange={(event) => updateHistoricalTranscript(item.id, "label", event.target.value)}
                    placeholder="Label, e.g. Q3 2024"
                    aria-label="Historical transcript label"
                    disabled={loading}
                  />
                  <button
                    className="v2-remove-button"
                    type="button"
                    onClick={() => removeHistoricalTranscript(item.id)}
                    disabled={loading}
                  >
                    Remove
                  </button>
                </div>
                <textarea
                  className="transcript-input v2-history-input"
                  value={item.transcript}
                  onChange={(event) =>
                    updateHistoricalTranscript(item.id, "transcript", event.target.value)
                  }
                  placeholder="Paste a prior earnings call transcript..."
                  aria-label={`Historical transcript ${item.label || item.id}`}
                  disabled={loading}
                />
                <p className="v2-input-helper">
                  {item.transcript.trim().length.toLocaleString()} characters · minimum {MIN_TRANSCRIPT_LENGTH}
                </p>
              </article>
            ))}
          </div>
        )}
      </section>

      {loading ? (
        <section className="loading-panel" aria-live="polite">
          <div className="loading-orbit" aria-hidden="true"><span /></div>
          <div>
            <h2>Building the verified reasoning chain</h2>
            <p>Extracting evidence, calculating compatible comparisons, and validating grounded interpretation.</p>
          </div>
        </section>
      ) : null}

      {error ? (
        <section className="error-panel" role="alert">
          <div>
            <h3>V2 analysis did not complete</h3>
            <p>{error}</p>
          </div>
          <button className="retry-button" type="button" disabled={!canAnalyze} onClick={handleAnalyze}>
            Retry
          </button>
        </section>
      ) : null}

      {analysis ? <V2Results analysis={analysis} /> : null}
    </section>
  );
}

function V2Results({ analysis }: { analysis: V2AnalysisResponse }) {
  const hasOutput =
    analysis.facts.financial_facts.length > 0 ||
    analysis.facts.guidance.length > 0 ||
    analysis.facts.qualitative_observations.length > 0 ||
    analysis.calculations.length > 0 ||
    analysis.thesis.bull_items.length > 0 ||
    analysis.thesis.bear_items.length > 0 ||
    analysis.thesis.watch_items.length > 0 ||
    analysis.thesis.evidence_gaps.length > 0;

  if (!hasOutput) {
    return <section className="v2-empty-state">V2 returned an empty analysis response.</section>;
  }

  return (
    <div className="v2-results">
      <section className="v2-coverage" aria-label="Analysis coverage">
        <span>{analysis.coverage.source_count} sources</span>
        <span>{analysis.coverage.financial_fact_count} financial facts</span>
        <span>{analysis.coverage.guidance_count} guidance items</span>
        <span>{analysis.coverage.valid_calculation_count} valid calculations</span>
        <span>{analysis.coverage.unavailable_calculation_count} unavailable comparisons</span>
      </section>
      <V2MetricAssessment
        financialFacts={analysis.facts.financial_facts}
        guidance={analysis.facts.guidance}
        calculations={analysis.calculations}
        sourceDocuments={analysis.source_documents}
      />
      <V2ThesisPanel
        bullItems={analysis.thesis.bull_items}
        bearItems={analysis.thesis.bear_items}
        watchItems={analysis.thesis.watch_items}
        evidenceGaps={analysis.thesis.evidence_gaps}
        sourceDocuments={analysis.source_documents}
      />
    </div>
  );
}

function getFriendlyV2Error(error: unknown): string {
  const message = error instanceof Error ? error.message : "";
  const normalizedMessage = message.toLowerCase();

  if (normalizedMessage.includes("failed to fetch")) {
    return "The backend could not be reached. Check that FastAPI is running, then try again.";
  }
  if (normalizedMessage.includes("provider") || normalizedMessage.includes("ai")) {
    return "The AI service could not complete the verified analysis. Your transcripts are preserved, so you can try again.";
  }
  if (normalizedMessage.includes("invalid v2 response")) {
    return "The backend returned an invalid V2 response. Please try again.";
  }

  return message || "Unable to complete V2 analysis. Please try again.";
}
