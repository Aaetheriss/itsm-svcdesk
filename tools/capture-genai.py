# ai-generated: 100% - ChatGPT wrote a deterministic local OpenTelemetry GenAI span capture helper.
from __future__ import annotations

import json
from pathlib import Path

ATTRIBUTES = {
    "gen_ai.operation.name": "chat",
    "gen_ai.provider.name": "openai",
    "gen_ai.request.model": "local-mock-model",
    "gen_ai.request.max_tokens": 16,
    "gen_ai.request.temperature": 0.0,
    "gen_ai.response.id": "chatcmpl-local-001",
    "gen_ai.response.model": "local-mock-model",
    "gen_ai.response.finish_reasons": ["stop"],
    "gen_ai.usage.input_tokens": 8,
    "gen_ai.usage.output_tokens": 4,
}

span = {
    "name": "chat local-mock-model",
    "kind": "SpanKind.CLIENT",
    "attributes": ATTRIBUTES,
    "events": [],
    "links": [],
    "resource": {"attributes": {"service.name": "lab3-genai-capture"}},
}
Path("genai").mkdir(exist_ok=True)
Path("genai/spans.json").write_text(json.dumps([span], indent=2) + "\n", encoding="utf-8")
print("Wrote genai/spans.json with", len(ATTRIBUTES), "gen_ai attributes")
