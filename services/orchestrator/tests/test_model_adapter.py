import json

import httpx
import pytest

from agents import AgentRole, GeminiStructuredAdapter, TriageOutput


@pytest.mark.asyncio
async def test_gemini_adapter_requests_and_validates_structured_output():
    captured = {}

    async def handler(request):
        captured["request"] = request
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": json.dumps(
                                        {
                                            "classification": "application_exception",
                                            "severity": "medium",
                                            "affected_service": "inventory",
                                            "window_start": "2026-09-17T11:55:00Z",
                                            "window_end": "2026-09-17T12:01:00Z",
                                            "is_duplicate": False,
                                            "duplicate_of": None,
                                            "rationale": "Evidence points to inventory.",
                                        }
                                    )
                                }
                            ]
                        }
                    }
                ]
            },
        )

    adapter = GeminiStructuredAdapter(
        api_key="test-key",
        model_name="gemini-3.8-flash",
        transport=httpx.MockTransport(handler),
    )

    result = await adapter.generate_structured(
        role=AgentRole.TRIAGE,
        prompt_version="triage-v1",
        input_data={"incident": {"summary": "untrusted telemetry"}},
        response_model=TriageOutput,
    )

    assert result.affected_service == "inventory"
    request = captured["request"]
    assert request.url.path.endswith("/models/gemini-3.8-flash:generateContent")
    assert request.headers["x-goog-api-key"] == "test-key"
    payload = json.loads(request.content)
    assert "untrusted data" in payload["systemInstruction"]["parts"][0]["text"]
    response_format = payload["generationConfig"]["responseFormat"]["text"]
    assert response_format["mimeType"] == "application/json"
    assert response_format["schema"]["type"] == "object"


@pytest.mark.asyncio
async def test_gemini_adapter_rejects_response_without_output_text():
    async def handler(_request):
        return httpx.Response(200, json={"candidates": []})

    adapter = GeminiStructuredAdapter(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ValueError, match="did not contain structured output"):
        await adapter.generate_structured(
            role=AgentRole.TRIAGE,
            prompt_version="triage-v1",
            input_data={},
            response_model=TriageOutput,
        )
