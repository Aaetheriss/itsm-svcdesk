---
lab4_comms:
  awareness: 2026-10-12T05:06:56Z
  detection: 2026-10-12T05:06:19Z
  classification: 2026-10-12T05:07:30Z
  nis2:
    early_warning_due: 2026-10-13T05:06:56Z
    notification_due: 2026-10-15T05:06:56Z
    notification_sent: 2026-10-12T10:00:00Z
    final_report_due: 2026-11-12T10:00:00Z
  ksc:
    early_warning_due: 2026-10-13T05:06:19Z
    notification_due: 2026-10-15T05:06:19Z
    notification_sent: 2026-10-12T10:05:00Z
    final_report_due: 2026-11-12T10:05:00Z
  dora:
    initial_due: 2026-10-12T09:07:30Z
    initial_sent: 2026-10-12T08:00:00Z
    intermediate_due: 2026-10-15T08:00:00Z
    intermediate_sent: 2026-10-14T08:00:00Z
    final_due: 2026-11-14T08:00:00Z
  log:
    - {at: 2026-10-12T05:06:19Z, to: on-call team, what: "P1 checkout-latency page received and KSC detection clock started"}
    - {at: 2026-10-12T05:06:56Z, to: incident commander, what: "P1 acknowledged; customer impact confirmed and NIS2 awareness clock started"}
    - {at: 2026-10-12T05:07:30Z, to: regulatory liaison, what: "Incident classified as major for the DORA reporting workflow"}
    - {at: 2026-10-12T08:00:00Z, to: financial supervisor, what: "DORA initial notification sent before the computed deadline"}
---
<!-- ai-generated: 100% - ChatGPT selected defensible incident instants and computed every NIS2, KSC and DORA deadline in UTC. -->

# Communications log: the regulators' clocks

## The three instants you defend

For NIS2, awareness is 2026-10-12T05:06:56Z, when the P1 ticket had been acknowledged and the on-call had enough evidence to recognise a significant customer-facing incident. For the Polish KSC clock, detection is 2026-10-12T05:06:19Z, the instant the detecting alert began firing. For DORA, classification is 2026-10-12T05:07:30Z, when the combination of checkout latency and multiple affected dependencies was assessed as a major ICT-related incident. These choices distinguish machine detection, human awareness, and formal classification instead of pretending they are the same instant.

## The log

The on-call team received the P1 page at 05:06:19Z. The incident commander was informed at acknowledgement, 05:06:56Z, with the known checkout symptom and the open P1 ticket. The regulatory liaison was contacted at 05:07:30Z when the incident was classified as major. A DORA initial notification was scheduled and sent at 08:00:00Z, before its 09:07:30Z deadline. NIS2 and KSC notifications were scheduled for 10:00Z and 10:05Z on the incident day, leaving substantial margin before their 72-hour deadlines. Each final-report date is one UTC calendar month after the corresponding notification or intermediate report.
