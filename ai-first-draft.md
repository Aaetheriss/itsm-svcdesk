---
lab3_first_draft:
  source: ai
  tool: "ChatGPT (GPT-5.6 Sol Pro), chat.openai.com, 10 October 2026"
  ladder: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
  verdict: refuted
  evidence: {p99_seconds: 0.1089, bucket: [0.1, 0.25], relative_width: 1.377}
lab3_flawed_ladder:
  verdict: refuted
  evidence: {p99_seconds: 0.1089, bucket: [0.04, 0.5], relative_width: 4.224}
---
<!-- ai-generated: 100% - ChatGPT supplied the first draft; the measurement arithmetic was generated locally from the published load result. -->

# The assistant's first draft, and two verdicts

## Prompt

Before I measure the service, propose a generic Prometheus histogram bucket ladder in seconds for the latency of GET /kb/search and propose one multiwindow burn-rate alert rule for a 99% availability SLO. State your assumptions; do not use any measured values from my service.

## Answer

A reasonable measurement-free first draft is to start with a conventional web-service ladder:

`[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]`

It covers fast local responses and a long tail, but it is only a generic starting point. After measuring the real p99, I would place more boundaries around the slow mode because the wide 0.1-to-0.25-second and 0.25-to-0.5-second buckets may make p99 interpolation imprecise.

For a 99% availability SLO, use a fast multiwindow burn-rate alert with burn rate 14.4, a 1-hour long window, a 5-minute short window and `for: 5m`. The expression should require both the 1-hour and 5-minute ratios of 5xx responses on `/kb/search` to exceed `14.4 * (1 - 0.99)`. Label it P1 because a sustained burn at that rate consumes the 28-day error budget in roughly 47 hours. Add a slower alert separately after the SLO policy is chosen.

## Verdict on the draft ladder

The measured p99 was 0.1089 s. The draft ladder places it in (0.1, 0.25], whose width is 0.15 s. The relative width is (0.25 - 0.1) / 0.1089 = 1.377. A histogram quantile may therefore be interpolated anywhere across that coarse interval. The verdict is **refuted** under M-11. The measured p50 was 0.0268 s. The measured p95 was 0.0458 s. The direct kb-index p99 was 0.0956 s.

## The draft alert rule

The useful part of the draft was the multiwindow 14.4x availability alert: both a long and short error ratio must exceed the same visible constant threshold. I retained that design as the P1 rule and added a 6x, 6h/30m P2 rule so a slower sustained burn reaches chat without waking a person for a brief spike. Both rules filter the /kb/search route and keep their thresholds in the alert expressions so mutation testing can change them.

## Verdict on the instructor's flawed ladder

The same p99, 0.1089 s, falls in (0.04, 0.5] in the instructor ladder. Its width is 0.46 s and its relative width is (0.5 - 0.04) / 0.1089 = 4.224. That interval is much wider than 20% of the measured p99, so the ladder is **refuted**. It spends many boundaries below 40 ms while leaving the slow-mode region almost entirely inside one bucket.