type LoadingPanelProps = {
  visible: boolean;
};

export function LoadingPanel({ visible }: LoadingPanelProps) {
  if (!visible) {
    return null;
  }

  return (
    <section className="loading-panel" aria-live="polite" aria-label="Analysis loading">
      <div className="loading-orbit" aria-hidden="true">
        <span />
      </div>
      <div>
        <h2>Analyzing transcript</h2>
        <p>
          The AI is reviewing management commentary, risks, opportunities, and
          recurring themes.
        </p>
      </div>
    </section>
  );
}
