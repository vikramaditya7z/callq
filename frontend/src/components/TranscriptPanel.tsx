type TranscriptPanelProps = {
  transcript: string;
  loading: boolean;
  canAnalyze: boolean;
  error: string | null;
  onTranscriptChange: (transcript: string) => void;
  onAnalyze: () => void;
};

export function TranscriptPanel({
  transcript,
  loading,
  canAnalyze,
  error,
  onTranscriptChange,
  onAnalyze,
}: TranscriptPanelProps) {
  const characterCount = transcript.length;
  const isEmpty = transcript.trim().length === 0;

  return (
    <section
      className="transcript-section"
      aria-labelledby="transcript-title"
      aria-busy={loading}
    >
      <div className="section-heading">
        <div>
          <h2 id="transcript-title">Transcript</h2>
          <p>Paste the earnings call transcript below.</p>
        </div>
        <button
          className="analyze-button"
          type="button"
          disabled={!canAnalyze}
          onClick={onAnalyze}
        >
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      <textarea
        className="transcript-input"
        value={transcript}
        onChange={(event) => onTranscriptChange(event.target.value)}
        placeholder="Paste transcript text..."
        aria-label="Earnings call transcript"
        disabled={loading}
      />

      <div className="transcript-meta">
        <p className={isEmpty ? "helper-message helper-message-active" : "helper-message"}>
          {isEmpty
            ? "Paste a transcript to enable analysis."
            : "Ready when you are. The transcript stays here if analysis fails."}
        </p>
        <p className="character-count">{characterCount.toLocaleString()} characters</p>
      </div>

      {error ? (
        <div className="error-panel" role="alert">
          <div>
            <h3>Analysis did not complete</h3>
            <p>{error}</p>
          </div>
          <button
            className="retry-button"
            type="button"
            disabled={!canAnalyze}
            onClick={onAnalyze}
          >
            Retry
          </button>
        </div>
      ) : null}
    </section>
  );
}
