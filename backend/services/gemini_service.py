"""Gemini API integration for structured AI responses."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_API_KEY_ENV_VAR = "GEMINI_API_KEY"
GEMINI_MODEL_ENV_VAR = "GEMINI_MODEL"
REQUEST_TIMEOUT_SECONDS = 60


class GeminiServiceError(Exception):
    """Base exception for Gemini integration failures."""


class GeminiConfigurationError(GeminiServiceError):
    """Raised when Gemini configuration is missing or invalid."""


class GeminiAPIError(GeminiServiceError):
    """Raised when Gemini returns an API or network error."""


class GeminiResponseError(GeminiServiceError):
    """Raised when Gemini returns an unexpected response shape."""


def generate_structured_response(
    prompt: str,
    response_schema: dict[str, Any],
) -> dict[str, Any]:
    """Call Gemini and return a JSON object parsed from the model response."""
    api_key = _get_api_key()
    model_name = os.getenv(GEMINI_MODEL_ENV_VAR, DEFAULT_GEMINI_MODEL)
    request_url = f"{GEMINI_API_BASE_URL}/models/{model_name}:generateContent"

    request_body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseFormat": {
                "text": {
                    "mimeType": "APPLICATION_JSON",
                    "schema": response_schema,
                }
            },
        },
    }

    response_payload = _post_json(request_url, api_key, request_body)
    response_text = _extract_response_text(response_payload)

    try:
        parsed_response = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise GeminiResponseError("Gemini returned invalid JSON.") from error

    if not isinstance(parsed_response, dict):
        raise GeminiResponseError("Gemini response must be a JSON object.")

    return parsed_response


def _get_api_key() -> str:
    api_key = os.getenv(GEMINI_API_KEY_ENV_VAR)

    if not api_key:
        raise GeminiConfigurationError(
            f"Missing required environment variable: {GEMINI_API_KEY_ENV_VAR}."
        )

    return api_key


def _post_json(
    request_url: str,
    api_key: str,
    request_body: dict[str, Any],
) -> dict[str, Any]:
    request_data = json.dumps(request_body).encode("utf-8")
    request = urllib.request.Request(
        request_url,
        data=request_data,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT_SECONDS,
        ) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        raise GeminiAPIError(_build_http_error_message(error)) from error
    except urllib.error.URLError as error:
        raise GeminiAPIError("Could not reach Gemini API.") from error
    except TimeoutError as error:
        raise GeminiAPIError("Gemini API request timed out.") from error

    try:
        parsed_body = json.loads(response_body)
    except json.JSONDecodeError as error:
        raise GeminiResponseError("Gemini API returned invalid JSON.") from error

    if not isinstance(parsed_body, dict):
        raise GeminiResponseError("Gemini API response must be a JSON object.")

    return parsed_body


def _build_http_error_message(error: urllib.error.HTTPError) -> str:
    try:
        error_body = error.read().decode("utf-8")
        parsed_error = json.loads(error_body)
        message = parsed_error.get("error", {}).get("message")
    except (json.JSONDecodeError, UnicodeDecodeError):
        message = None

    if message:
        return f"Gemini API error {error.code}: {message}"

    return f"Gemini API error {error.code}."


def _extract_response_text(response_payload: dict[str, Any]) -> str:
    candidates = response_payload.get("candidates")

    if not isinstance(candidates, list) or not candidates:
        raise GeminiResponseError("Gemini response did not include candidates.")

    first_candidate = candidates[0]
    if not isinstance(first_candidate, dict):
        raise GeminiResponseError("Gemini candidate had an unexpected shape.")

    content = first_candidate.get("content")
    if not isinstance(content, dict):
        raise GeminiResponseError("Gemini candidate did not include content.")

    parts = content.get("parts")
    if not isinstance(parts, list) or not parts:
        raise GeminiResponseError("Gemini content did not include text parts.")

    first_part = parts[0]
    if not isinstance(first_part, dict):
        raise GeminiResponseError("Gemini text part had an unexpected shape.")

    response_text = first_part.get("text")
    if not isinstance(response_text, str) or not response_text.strip():
        raise GeminiResponseError("Gemini returned empty response text.")

    return response_text
