export type EvidenceRef = {
  source_id: string;
  exact_quote: string;
  start_offset: number | null;
  end_offset: number | null;
};

export type SourceDocument = {
  source_id: string;
  document_type: string;
  text: string;
};

export type FinancialFact = {
  fact_id: string;
  metric_key: string;
  reported_value: string;
  unit: string | null;
  period: string | null;
  period_type: string | null;
  evidence: EvidenceRef;
};

export type GuidanceFact = {
  fact_id: string;
  metric_key: string;
  guidance_value: string;
  unit: string | null;
  period: string | null;
  evidence: EvidenceRef;
};

export type QualitativeObservation = {
  observation_id: string;
  category: string;
  statement: string;
  evidence: EvidenceRef;
};

export type Calculation = {
  calculation_id: string;
  calculation_type: string;
  input_fact_ids: string[];
  formula: string;
  result: number | null;
  unit: string | null;
  status: "valid" | "unavailable";
  reason: string | null;
};

export type InterpretationItem = {
  claim: string;
  why_it_matters: string;
  supporting_fact_ids: string[];
  calculation_ids: string[];
  evidence_refs: EvidenceRef[];
};

export type EvidenceGap = {
  gap_id: string;
  description: string;
  related_fact_ids: string[];
  related_calculation_ids: string[];
};

export type V2AnalysisResponse = {
  source_documents: SourceDocument[];
  facts: {
    financial_facts: FinancialFact[];
    guidance: GuidanceFact[];
    qualitative_observations: QualitativeObservation[];
  };
  calculations: Calculation[];
  thesis: {
    bull_items: InterpretationItem[];
    bear_items: InterpretationItem[];
    watch_items: InterpretationItem[];
    evidence_gaps: EvidenceGap[];
  };
  coverage: {
    source_count: number;
    financial_fact_count: number;
    guidance_count: number;
    qualitative_observation_count: number;
    valid_calculation_count: number;
    unavailable_calculation_count: number;
  };
};

export type HistoricalTranscriptInput = {
  label: string;
  transcript: string;
};

export type V2AnalyzeRequest = {
  current_transcript: string;
  historical_transcripts: HistoricalTranscriptInput[];
};
