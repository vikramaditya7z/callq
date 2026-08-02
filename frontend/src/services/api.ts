import type { AnalysisResponse } from "../types/insights";

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
