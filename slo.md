---
lab3_slo:
  service: svcdesk
  route: /kb/search
  window: 28d
  slis:
    availability:
      objective: 0.99
      good: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code!~"5.."}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.01, minutes: 403.2}
    latency:
      objective: 0.98
      threshold_seconds: 0.1433
      good: 'sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="0.1433"}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.02, minutes: 806.4}
  alerts:
    - {alert: KbSearchAvailabilityBurnFast, sli: availability, burn_rate: 14.4, long_window: 1h, short_window: 5m}
    - {alert: KbSearchAvailabilityBurnSlow, sli: availability, burn_rate: 6, long_window: 6h, short_window: 30m}
---
<!-- ai-generated: 100% - ChatGPT drafted the SLO; its threshold and bucket arithmetic were selected from the local Aaetheriss measurement. -->

# SLO for GET /kb/search

## Availability

A request is good when /kb/search returns a non-5xx response and valid when it reaches that route at all. The 99% objective leaves a 1% error budget: 403.2 minutes in a 28-day window. This is deliberately above the dependency's small normal error probability, so occasional kb-index failures consume budget without making an honest release permanently fail the future canary gate. A persistent upstream or integration failure still burns the budget quickly.

## Latency

The latency SLI counts requests at or below 0.1433 s, a real boundary in the service histogram, divided by all /kb/search requests. The local open-loop p99 was 0.1089 s and the selected threshold is the first ladder boundary at least 25% above it. The 98% objective leaves a 2% budget, 806.4 minutes over 28 days, and tolerates the seeded slow mode while still making a broader latency regression visible. The measured p50 was 0.0268 s. The measured p95 was 0.0458 s. The direct kb-index p99 was 0.0956 s.

## Alerts

| alert | SLI | burn rate | long / short window | budget exhausted at this rate | severity |
|---|---|---:|---|---|---|
| KbSearchAvailabilityBurnFast | availability | 14.4 | 1h / 5m | about 46.7 hours | P1 page |
| KbSearchAvailabilityBurnSlow | availability | 6 | 6h / 30m | 112 hours | P2 chat |

The fast rule pages because waiting until morning during a 14.4x burn could spend a material share of the monthly budget and leave users without knowledge-base search. The page has a human cost, so it requires confirmation in both windows and a five-minute or. The 6x rule goes to chat: it identifies a slower sustained problem early enough for daytime intervention, but it does not justify waking a person for a short-lived dependency fluctuation.

## Buckets

The final ladder is [0.02, 0.0228, 0.026, 0.0297, 0.0338, 0.0386, 0.044, 0.0501, 0.0572, 0.0652, 0.0743, 0.0847, 0.0966, 0.1102, 0.1256, 0.1433, 0.1634, 0.1863, 0.2124, 0.2422, 0.2762, 0.3149, 0.3591, 0.4094, 0.4669, 0.5324, 0.607, 0.6922, 0.7893, 0.9]. The measured p99 falls in (0.0966, 0.1102], width 0.0136 s, or 0.125 of p99. Adjacent boundaries use a ratio of about 1.14, so the ladder resolves a broad band rather than one laptop-specific point. Boundaries below the slow mode preserve visibility of normal traffic; the upper boundaries retain coverage for regressions up to 0.9 s while staying within the limit of 30 finite boundaries.