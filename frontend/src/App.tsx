import { useState } from "react";

import { InsightsGrid } from "./components/InsightsGrid";
import { LoadingPanel } from "./components/LoadingPanel";
import { PageHeader } from "./components/PageHeader";
import { TranscriptPanel } from "./components/TranscriptPanel";
import { V15Insights } from "./components/V15Insights";
import { V2Analysis } from "./components/V2Analysis";
import { analyzeTranscript } from "./services/api";
import type { AnalysisResponse } from "./types/insights";

export default function App() {
  const [mode, setMode] = useState<"v15" | "v2">("v15");
  const [transcript, setTranscript] = useState("");
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canAnalyze = transcript.trim().length > 0 && !loading;

  async function handleAnalyze() {
    if (!canAnalyze) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await analyzeTranscript(transcript);
      setAnalysis(result);
    } catch (caughtError) {
      const message =
        caughtError instanceof Error
          ? getFriendlyErrorMessage(caughtError.message)
          : "Unable to analyze transcript. Please try again.";

      setError(message);
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <PageHeader />
      <nav className="analysis-mode-switcher" aria-label="Analysis mode">
        <button
          className={mode === "v15" ? "mode-button mode-button-active" : "mode-button"}
          type="button"
          onClick={() => setMode("v15")}
        >
          V1.5 insights
        </button>
        <button
          className={mode === "v2" ? "mode-button mode-button-active" : "mode-button"}
          type="button"
          onClick={() => setMode("v2")}
        >
          V2 reasoning
        </button>
      </nav>
      {mode === "v15" ? (
        <>
          <TranscriptPanel
            transcript={transcript}
            loading={loading}
            canAnalyze={canAnalyze}
            error={error}
            onTranscriptChange={setTranscript}
            onAnalyze={handleAnalyze}
          />
          <LoadingPanel visible={loading} />
          <InsightsGrid analysis={analysis} loading={loading} />
          <V15Insights analysis={analysis} loading={loading} />
        </>
      ) : (
        <V2Analysis />
      )}
    </main>
  );
}

function getFriendlyErrorMessage(message: string): string {
  const normalizedMessage = message.toLowerCase();

  if (normalizedMessage.includes("failed to fetch")) {
    return "The backend could not be reached. Check that FastAPI is running, then try again.";
  }

  if (
    normalizedMessage.includes("provider") ||
    normalizedMessage.includes("gemini") ||
    normalizedMessage.includes("ai")
  ) {
    return "The AI service could not complete the analysis. Your transcript is preserved, so you can try again.";
  }

  return message || "Unable to analyze transcript. Please try again.";
}
