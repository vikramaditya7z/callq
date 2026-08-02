export type InsightTone =
  | "summary"
  | "positive"
  | "negative"
  | "risk"
  | "opportunity"
  | "outlook"
  | "theme";

export type InsightSection = {
  title: string;
  responseKey: keyof AnalysisResponse;
  tone: InsightTone;
};

export type AnalysisResponse = {
  executive_summary: string[];
  positives: string[];
  negatives: string[];
  risks: string[];
  opportunities: string[];
  management_outlook: string;
  themes: string[];
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
