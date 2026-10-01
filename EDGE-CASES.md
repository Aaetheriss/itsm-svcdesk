---
# ai-generated: 80% - ChatGPT drafted the analysis from METRIC-SPEC.md and the service results.
lab2_edge_cases:
  E1: {rule: R-08, count: 3}
  E2: {rule: R-06, count: 2}
  E3: {rule: R-09, count: 4}
  E4: {rule: R-10, count: 4}
  E5: {rule: R-12, count: 1}
  E6: {rule: R-13, count: 11}
---

# Edge cases in the practice event log

## E1 - clock skew produces a negative lead time

- **What the log contains:** Three commit and deployment pairs have commit timestamps later than the successful production deployments that carried them, which is possible when source-control and deployment clocks disagree.
- **What a default definition would have done:** A naive implementation would discard the negative values or leave them negative, silently changing the sample and producing a misleading median that depends on clock quality.
- **Why the rule is defensible:** R-08 keeps each delivery observation but clamps the impossible duration to zero, so the dashboard remains complete while the anomaly count makes the data-quality problem visible to the service owner.

## E2 - a revert of a revert

- **What the log contains:** Two commits are reverts, including a chain in which a revert targets another revert, so the commits still refer transitively to the original unit of work.
- **What a default definition would have done:** Treating every commit as a new change would inflate throughput and the number of delivered changes even though the team was only undoing and then restoring the same change.
- **Why the rule is defensible:** R-06 follows the revert chain to the original change identifier, preserving the business meaning of a change and preventing corrective commit activity from masquerading as new value.

## E3 - a hotfix that never touched `main`

- **What the log contains:** Four distinct commits carried by in-window production deployments have a branch other than `main`, including hotfix work that reached users directly.
- **What a default definition would have done:** Filtering to `branch == "main"` would omit real production work and make both lead-time evidence and operational risk look better than the deployment record supports.
- **Why the rule is defensible:** R-09 treats deployment to production as the evidence of delivery, regardless of branch naming, so emergency paths remain visible and teams cannot improve the dashboard by changing branch labels.

## E4 - a deployment with zero linked commits

- **What the log contains:** Four production deployments in the window have an empty `commits` list, so they contain no lead-time pair but still represent deployment activity and possible operational exposure.
- **What a default definition would have done:** Dropping these records would understate deployment frequency and remove them from failure and rework denominators, while inventing a lead time would fabricate data that is not present.
- **Why the rule is defensible:** R-10 counts the deployment everywhere a deployment belongs and contributes no lead-time pair, separating a missing linkage problem from the fact that a production action occurred.

## E5 - a deployment that failed and never recovered

- **What the log contains:** One failed production deployment has no usable recovery instant because no covering incident resolves it within the available event history.
- **What a default definition would have done:** Closing it at the observation-window boundary would invent a recovery, while dropping it from every metric would hide a failure that still affects change fail rate.
- **Why the rule is defensible:** R-12 excludes the case only from the recovery-time median, reports it as an open failure, and retains it in the change-fail numerator, which distinguishes unknown duration from nonexistent failure.

## E6 - overlapping incidents

- **What the log contains:** The incident intervals form eleven unordered overlapping pairs, and some incidents cover failed deployments during time ranges that intersect other incidents.
- **What a default definition would have done:** Merging overlaps would erase incident identity, while summing incident wall-clock durations would double-count time and would not measure recovery for each failed deployment.
- **Why the rule is defensible:** R-13 measures recovery per failed deployment and reports overlap separately, preserving causal records while warning the dashboard reader that concurrent incidents complicate operational interpretation.

## Gaming demonstration

The transformed log improves `deployment_frequency_per_day` under R-11 from 2.0 to 2.52381 deployments per day, a relative increase of about 26.19%. It does this by moving the 34 successful base deployments outside the published window and adding 45 successful production deployments with no linked commits. The existing commits and incidents remain unchanged, and no base deployment is moved earlier.

This dashboard improvement is harmful rather than valuable. When the checker measures only the original work, `ground_truth.changes_delivered` falls from 65 to 0 because the real successful deliveries were delayed beyond the window. A team rewarded for deployment frequency could therefore schedule empty or operationally meaningless releases while postponing customer work. The delivery team and the manager reporting the frequency target would receive the apparent reward, while customers would receive none of the original changes during the measured period.
