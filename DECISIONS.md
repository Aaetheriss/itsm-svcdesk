---
svcdesk_decisions:
  C1: wallclock
  C2: immutable
  C3: matrix
---
<!-- ai-generated: 100% - ChatGPT generated the rationale for the selected C1, C2 and C3 decisions. -->

# Decisions

## C1 - SLA clock for P1

**Decision:** P1 acknowledgement and resolution targets use elapsed wall-clock time, while P2 to P4 continue to use the Europe/Warsaw business-hours clock.

**Rejected alternative:** Applying business hours to P1 was rejected because it would suspend the highest-impact incidents overnight and through weekends.

**Reason:** P1 represents an organisation-wide stoppage, so a continuous clock makes the response commitment match the operational impact and the need for immediate escalation.

**Service owner:** The Service Desk product owner approves this rule because that role owns SLA definitions, escalation expectations, and the reporting consequences.

**Customer outcome:** Reporters receive a predictable four-hour resolution target for critical incidents regardless of when the incident is submitted.

## C2 - Closed tickets and reopening

**Decision:** A resolved ticket may be reopened within seven days, but a closed ticket is immutable and further work requires a new ticket linked with `related_to`.

**Rejected alternative:** Reopening a closed ticket within seven days was rejected because it changes a record that has already completed the confirmation and closure process.

**Reason:** Keeping closed records immutable preserves a stable audit trail and reporting history while still allowing failed fixes to be reopened before final closure.

**Service owner:** The Service Desk product owner approves this lifecycle rule because that role owns ticket governance, auditability, and closure policy.

**Customer outcome:** Customers can quickly resume work on a failed fix while it is resolved, and after closure they receive a new traceable ticket connected to the original.

## C3 - VIP reporters and the priority matrix

**Decision:** Priority is calculated only from impact and urgency; the VIP flag is retained as reporter information but does not alter the matrix result.

**Rejected alternative:** Automatically raising every VIP ticket to at least P2 was rejected because personal status would override the measured operational effect of the incident.

**Reason:** A single transparent matrix keeps prioritisation consistent, auditable, and focused on business impact rather than the identity of the reporter.

**Service owner:** The Service Desk product owner approves the priority policy because that role owns queue ordering, fairness, and priority-reporting rules.

**Customer outcome:** All reporters receive the same impact-based prioritisation, while agents can still see the VIP flag and communicate appropriately.
