import { useState } from "react";

import { InsightsGrid } from "./components/InsightsGrid";
import { LoadingPanel } from "./components/LoadingPanel";
import { PageHeader } from "./components/PageHeader";
import { TranscriptPanel } from "./components/TranscriptPanel";
import { analyzeTranscript } from "./services/api";
import type { AnalysisResponse } from "./types/insights";

export default function App() {
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
