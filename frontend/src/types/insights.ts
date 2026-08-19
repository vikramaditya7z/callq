export type InsightTone =
  | "summary"
  | "positive"
  | "negative"
  | "risk"
  | "opportunity"
  | "outlook"
  | "theme";

export type FinancialMetric = {
  name: string;
  value: string;
  change: string | null;
  period: string | null;
};

export type GuidanceItem = {
  metric: string;
  value: string;
  period: string;
  context: string | null;
};

export type ManagementSignals = {
  overall_tone: string;
  positive_signals: string[];
  watch_signals: string[];
};

export type AnalysisResponse = {
  executive_summary: string[];
  positives: string[];
  negatives: string[];
  risks: string[];
  opportunities: string[];
  management_outlook: string;
  themes: string[];
  financial_metrics: FinancialMetric[];
  guidance: GuidanceItem[];
  management_signals: ManagementSignals;
};

type DisplayedInsightKey =
  | "executive_summary"
  | "positives"
  | "negatives"
  | "risks"
  | "opportunities"
  | "management_outlook"
  | "themes";

export type InsightSection = {
  title: string;
  responseKey: DisplayedInsightKey;
  tone: InsightTone;
};

export const insightSections: InsightSection[] = [
  { title: "Executive Summary", responseKey: "executive_summary", tone: "summary" },
  { title: "Positives", responseKey: "positives", tone: "positive" },
  { title: "Negatives", responseKey: "negatives", tone: "negative" },
  { title: "Risks", responseKey: "risks", tone: "risk" },
  { title: "Opportunities", responseKey: "opportunities", tone: "opportunity" },
  {
    title: "Management Outlook",
    responseKey: "management_outlook",
    tone: "outlook",
  },
  { title: "Themes", responseKey: "themes", tone: "theme" },
];
