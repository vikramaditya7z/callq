import type { AnalysisResponse } from "../types/insights";
import type { V2AnalysisResponse, V2AnalyzeRequest } from "../types/v2Insights";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

type AnalyzeRequest = {
  transcript: string;
};

export async function analyzeTranscript(
  transcript: string,
): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ transcript } satisfies AnalyzeRequest),
  });

  if (!response.ok) {
    throw new Error(await buildErrorMessage(response));
  }

  return response.json() as Promise<AnalysisResponse>;
}

export async function analyzeV2(request: V2AnalyzeRequest): Promise<V2AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/analyze/v2`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(await buildErrorMessage(response));
  }

  const payload: unknown = await response.json();
  if (!isV2AnalysisResponse(payload)) {
    throw new Error("Invalid V2 response from the backend.");
  }

  return payload;
}

async function buildErrorMessage(response: Response): Promise<string> {
  try {
    const errorBody = (await response.json()) as { detail?: unknown };

    if (typeof errorBody.detail === "string") {
      return errorBody.detail;
    }
  } catch {
    return "Unable to analyze transcript. Please try again.";
  }

  return "Unable to analyze transcript. Please try again.";
}

function isV2AnalysisResponse(value: unknown): value is V2AnalysisResponse {
  if (!isRecord(value) || !isRecord(value.facts) || !isRecord(value.thesis) || !isRecord(value.coverage)) {
    return false;
  }

  return (
    Array.isArray(value.source_documents) &&
    Array.isArray(value.facts.financial_facts) &&
    Array.isArray(value.facts.guidance) &&
    Array.isArray(value.facts.qualitative_observations) &&
    Array.isArray(value.calculations) &&
    Array.isArray(value.thesis.bull_items) &&
    Array.isArray(value.thesis.bear_items) &&
    Array.isArray(value.thesis.watch_items) &&
    Array.isArray(value.thesis.evidence_gaps)
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
