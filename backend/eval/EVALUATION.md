# CallQ V2.8 Real-World Evaluation & Failure-Analysis Framework

## Overview

CallQ V2.8 provides a decoupled, reproducible evaluation and diagnostic framework designed to measure financial intelligence accuracy on realistic earnings-call transcripts and synthesize failure-driven priorities for V3 development.

---

## 1. Directory Structure

```
backend/eval/
├── __init__.py               # Public exports for evaluation runner and taxonomy
├── models.py                 # Pydantic data contracts (EvaluationReport, CaseEvaluationResult, etc.)
├── evaluator.py              # Multi-dimensional evaluation engine
├── runner.py                 # Execution runner with latency tracking & failure capture
├── taxonomy.py               # Failure taxonomy, severity classification & V3 synthesis
├── fixtures_loader.py        # External JSON transcript fixture loader
├── fixtures/                 # Realistic transcript test datasets (JSON)
│   ├── saas_enterprise_q3_2026.json
│   ├── industrial_manufacturing_q2_2026.json
│   ├── fintech_cross_border_fx_2026.json
│   └── retail_turnaround_no_guidance_2026.json
└── benchmarks/
    └── cases.py              # In-memory benchmark fixtures
```

---

## 2. Adding a Real-World Transcript Fixture

To add a new transcript benchmark case, create a JSON file in `backend/eval/fixtures/<name>.json`:

```json
{
  "fixture_id": "example_company_q3_2026",
  "company_name": "Example Corp",
  "reporting_period": "Q3 2026",
  "description": "Short scenario description",
  "current_transcript": "Operator: Welcome to Example Corp earnings call...",
  "historical_transcripts": [
    {
      "label": "Q3 2025",
      "transcript": "Operator: Welcome to prior year call..."
    }
  ],
  "metadata": {
    "sector": "Technology",
    "evaluation_focus": ["revenue_growth", "guidance"]
  },
  "ground_truth": {
    "expected_facts": [
      {
        "metric_key": "revenue",
        "reported_value": "$300 million",
        "source_id": "current",
        "unit": "USD",
        "period": "Q3 2026",
        "period_type": "quarterly"
      }
    ],
    "expected_guidance": [],
    "expected_calculations": [
      {
        "calculation_type": "percentage_change",
        "status": "valid",
        "expected_result": 20.0,
        "expected_unit": "percent"
      }
    ],
    "expected_evidence_gaps": [],
    "prohibited_claims": ["buy recommendation"],
    "require_empty_guidance": false
  }
}
```

*Note: All transcript strings must contain at least 200 characters to comply with V2 API contracts.*

---

## 3. Running Evaluations

### Automated / Offline Evaluation (Deterministic):
```python
from backend.eval.runner import run_evaluation

# Run across all fixtures in backend/eval/fixtures/
report = run_evaluation(pipeline_runner=mock_pipeline)
print(report.summary_text())
```

### Live Provider Evaluation (Requires `GEMINI_API_KEY`):
```python
from backend.eval.runner import run_evaluation
from backend.services.v2_analysis_service import run_v2_analysis

# Executes live against Gemini API
report = run_evaluation(pipeline_runner=run_v2_analysis)
print(report.summary_text())
```

---

## 4. Failure Taxonomy & Severities

| Category | Description | Subsystem | Default Severity |
|---|---|---|---|
| `EXTRACTION_ERROR` | Schema or structural parsing failure during V2.1 extraction | `extraction` | High |
| `MISSING_FACT` | Known financial metric in transcript was omitted from extraction | `extraction` | High |
| `WRONG_FACT` | Extracted fact contained incorrect value, unit, or period | `extraction` | High / Medium |
| `EVIDENCE_ERROR` | Quote not found in source text or offset slice mismatch | `evidence` | Critical |
| `CALCULATION_ERROR` | Formula error, numerical mismatch, or unexpected calculation failure | `calculation` | High |
| `COMPARABILITY_ERROR` | Incompatible cross-period metrics computed instead of marked unavailable | `comparability` | High |
| `THESIS_GROUNDING_ERROR` | Numeric claim without calculation ID, ungrounded thesis claim, or invalid reference | `interpretation` | Critical |
| `MISSING_GUIDANCE` | Stated forward guidance range was omitted | `extraction` | High |
| `FALSE_GUIDANCE` | Qualitative outlook falsely extracted as numeric guidance | `extraction` | High |
| `UNAVAILABLE_DATA_HANDLING`| Missing gap explanation for non-comparable inputs | `interpretation` | Medium |
| `PROVIDER_ERROR` | Upstream Gemini API timeout, 503 capacity spike, or auth error | `provider` | Critical |
| `OTHER` | Unclassified diagnostic finding | `extraction` | Medium |

### Severity Levels:
- **`critical`**: Grounding violation, hallucinated numbers in thesis, evidence offset corruption, or unhandled pipeline crash.
- **`high`**: Missing primary metric, incorrect calculation result, or invalid comparability gate.
- **`medium`**: Minor period/unit formatting variations, secondary guidance gap omission.
- **`low`**: Minor whitespace or cosmetic discrepancies.

---

## 5. Output Format

### Machine-Readable (`EvaluationReport`):
- `total_cases`: Total benchmark fixtures evaluated
- `passed_cases`: Count of fixtures passing all critical/high checks
- `failed_cases`: Count of fixtures with errors
- `mean_accuracy`: Aggregate score across all evaluation dimensions (0.0 to 1.0)
- `case_results`: Array of `CaseEvaluationResult` objects (per-fixture metrics, latency in ms, classified failures)
- `v3_recommendations`: Actionable, failure-frequency-weighted list of `V3Recommendation` objects

### Human-Readable (`report.summary_text()`):
```text
==================================================================
             CALLQ V2.8 FINANCIAL INTELLIGENCE EVALUATION         
==================================================================
Timestamp: 2026-09-27T09:45:00.000000+00:00
Total Benchmark Cases: 4
Passed: 4 | Failed: 0
Mean Accuracy Score: 100.0%
------------------------------------------------------------------
Case ID                        Status Accuracy  Latency   Failures
------------------------------------------------------------------
saas_enterprise_q3_2026        PASS   100.0%    124ms     0       
industrial_manufacturing_q2_2026 PASS   100.0%    98ms      0       
fintech_cross_border_fx_2026   PASS   100.0%    85ms      0       
retail_turnaround_no_guidance_2026 PASS   100.0%    62ms      0       
------------------------------------------------------------------
Zero failures detected across evaluated benchmark cases.
==================================================================
```

---

## 6. Limitations of V2.8 Evaluation

1. **Exact-Match Quote Grounding**: Evidence offsets require exact substring matching; differences in OCR formatting or non-breaking spaces require exact reproduction.
2. **Fixed Metric Catalog**: Calculations and comparisons are evaluated against known V2 calculation types (percentage change, absolute change, margin change in percentage points, guidance midpoint/width).
3. **Synthetic Ground Truths**: Repositories use legally safe, synthetic benchmark fixtures to avoid copyrighted transcripts.
