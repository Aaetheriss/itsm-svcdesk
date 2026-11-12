---
lab4_postmortem:
  ticket: "3ba75e92-1b55-483b-a69e-6097c02b182c"
  detecting_alert: ShopCheckoutSlow
  onset: 2026-10-12T05:01:00Z
  detection: 2026-10-12T05:06:19Z
  acknowledgement: 2026-10-12T05:06:56Z
  recovery: 2026-10-12T05:08:19Z
  mttd_seconds: 319
  mtta_seconds: 37
  mttr_seconds: 439
  identified_flags: [adFailure, intlShippingSlowdown, emailMemoryLeak]
---
<!-- ai-generated: 100% - ChatGPT reconstructed the incident from the assigned recording and drafted this blameless postmortem; the author must review the reasoning. -->

# Postmortem: checkout latency and degraded shop dependencies

## Date

The incident occurred on 12 October 2026, and this postmortem was prepared after the recorded evidence was reconstructed and checked in UTC.

## Authors

Aaetheriss is the submitting author. The reconstruction uses the immutable Prometheus snapshot, the P1 ticket, and the investigator ledgers, with AI assistance disclosed above.

## Status

Complete for the recorded incident; the service was restored, while the preventive and process action items remain open and assigned below.

## Summary

At 05:01:00Z three seeded failures began affecting the shop. Checkout became slow, the P1 `ShopCheckoutSlow` page fired at 05:06:19Z, and its first firing run ended at 05:08:19Z. The recording shows an ad failure, an international-shipping slowdown, and an email memory leak. The fault-active signal did not clear fully until approximately 05:10:05Z, so the detecting symptom recovered before every injected condition had been removed.

## Impact

Customers experienced a severe checkout delay. At 05:06:30Z the query
`histogram_quantile(0.99, sum by (le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="checkout",span_name="oteldemo.CheckoutService/PlaceOrder",span_kind="SPAN_KIND_SERVER"}[5m])))`
was approximately 8550 milliseconds, compared with less than 100 milliseconds on the healthy baseline. The shipping query
`histogram_quantile(0.99, sum by (le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="shipping",span_name="POST /ship-order",span_kind="SPAN_KIND_SERVER"}[5m])))`
was also approximately 8550 milliseconds. The same five-minute window contained 29 completed checkout server spans. Email memory pressure reached about 95.9 percent according to
`max_over_time(container_memory_percent_ratio{container_name="email"}[5m])`.
The user-facing detecting interval lasted 439 seconds from onset to the defined recovery.

## Root Causes

The `intlShippingSlowdown` control delayed non-US shipping operations and propagated that latency through checkout. The `emailMemoryLeak` control drove the email container close to its memory limit and increased operational risk during order confirmation. The `adFailure` control produced ad-service errors, visible in the `ShopServiceErrors` firing series for `service_name="ad"`. These were independent injected conditions; the on-call saw their combined symptoms rather than one single software defect.

## Trigger

The recorded injector activated the seeded fault at 2026-10-12T05:01:00Z after the required healthy baseline. No individual action by an operator caused the onset.

## Resolution

The recorded operator disabled the failing controls one at a time. The checkout latency symptom cleared first, so the detecting alert ended at 05:08:19Z. The snapshot's `seeded_fault_active` series shows that the last remaining injected condition was cleared at about 05:10:05Z. The operational workaround was therefore to switch off `intlShippingSlowdown`, `emailMemoryLeak`, and `adFailure`; permanent prevention requires safer flag controls and symptom tests.

## Detection

Prometheus detected the incident through `ShopCheckoutSlow`, a P1 symptom alert on checkout latency. It started firing at 05:06:19Z, 319 seconds after onset. The ticket was acknowledged 37 seconds later. Without this page, customers or the load-generator failure pattern would probably have been the first indication, delaying response further.

## Action Items

| Action Item | Type | Owner | Bug |
|---|---|---|---|
| Add an automated checkout canary that covers international shipping and blocks a flag rollout when p99 exceeds two seconds. | prevent | Checkout service owner | ITSM-401 |
| Add a memory-growth alert and restart-safety test for the email service before enabling leak-prone feature variants. | mitigate | Email service owner | ITSM-402 |
| Require a change record and an automatic expiry for high-impact feature flags used in production. | process | Service operations owner | ITSM-403 |

## Lessons Learned

### What went well

The page was based on a user-visible symptom, reached the pager, and was acknowledged quickly. The immutable snapshot and ticket made the timing independently reproducible.

### What went wrong

The five-minute latency window made detection arrive more than five minutes after onset, and several independent failures were active at once. The first recorded AI investigator also confused monotonically increasing counters with rising latency.

### Where we got lucky

The checkout latency alert recovered before the full fault ended, and the email process remained available despite reaching high memory pressure. A larger leak or longer exposure could have caused repeated restarts.

## Timeline

- 05:00:00Z — Last quiet minute before the onset; no P1 alert was firing on the healthy baseline.
- 05:01:00Z — Onset: the three seeded conditions became active.
- 05:06:19Z — Detection: `ShopCheckoutSlow` began its first P1 firing run.
- 05:06:36Z — P1 incident ticket `3ba75e92-1b55-483b-a69e-6097c02b182c` was created.
- 05:06:56Z — Acknowledgement: the on-call accepted the page and ticket.
- 05:07:00Z — Investigation focused on shipping latency, email memory pressure, and ad errors. The recorded AI transcript was scored separately; no untested AI claim was used to change the mitigation.
- 05:08:19Z — Recovery by the laboratory definition: the detecting alert's first firing run ended.
- 05:10:05Z — The last injected condition cleared according to `seeded_fault_active`.

## Supporting information

Evidence is in `incident/tsdb-snapshot.tar.gz`, `incident/ticket.json`, `ai-rca/transcript.md`, `ai-rca-eval.json`, and `ai-rca-eval-2.json`. The decisive PromQL checks are the checkout and shipping p99 queries, `container_memory_percent_ratio{container_name="email"} > 75`, and the recorded `ALERTS` series for `ShopCheckoutSlow` and ad-service errors.

## Problem record

- Incident record: P1 ticket 3ba75e92-1b55-483b-a69e-6097c02b182c records the restored customer-facing interruption.
- Root cause: Unsafe feature variants independently introduced ad errors, shipping latency, and email memory growth.
- Known error: The feature-control process can activate several high-impact failure modes without an automatic rollback gate.
- Workaround: Disable the affected feature flags and confirm checkout latency, email memory, and ad errors return to baseline.
