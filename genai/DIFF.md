---
lab3_genai_diff:
  instrumentation: "opentelemetry-sdk 1.45.0 manual GenAI client span around an OpenAI-compatible local call"
  spec_ref: "semantic-conventions@v1.41.1"
  attributes:
    - {name: gen_ai.operation.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.provider.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.max_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.temperature, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.id, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.finish_reasons, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.input_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.output_tokens, emitted: true, in_spec: true, stability: development}
---
<!-- ai-generated: 100% - ChatGPT generated the capture schema and compared its attributes with semantic-conventions v1.41.1. -->

# GenAI span diff

The capture records one deterministic OpenAI-compatible chat call. Every `gen_ai.*` key present in `spans.json` is declared above, and all ten attributes are listed as development in the selected v1.41.1 registry. The capture deliberately omits prompt and completion content, so the artifact demonstrates the schema without placing personal or sensitive text in the public repository. The useful compatibility result is that dashboards can rely on operation, provider, model, response and token-usage fields, while still treating them as development conventions rather than stable API.
