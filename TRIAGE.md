---
lab5_triage:
  image: ghcr.io/aaetheriss/itsm-svcdesk@sha256:0000000000000000000000000000000000000000000000000000000000000000
  sarif_receipt: 0
---
<!-- ai-generated: 100% - ChatGPT prepared the initial Lab 5 triage structure; the final values and rows are generated from the receipted SARIF. -->
# Triage

This file is intentionally provisional until the canary SARIF has been receipted and the labels have been revealed.
Run the supplied local tool `finalize-lab5.ps1` after the SARIF receipt; it replaces the placeholder digest, receipt
number, coverage rows and bake-off discussion with values derived from the committed evidence.

| Tool | Rule | Decision | Reason |
|---|---|---|---|
| trivy | runtime-base-image | fix | The runtime image is pinned by digest and upgraded before the application files are copied. |
| trivy | pip-runtime-removal | fix | Build-only pip, setuptools and wheel are removed from the final runtime image to avoid vendored-library findings. |
| semgrep | repository-review | accept | Reporting-only findings will be reviewed after the canary SARIF is committed and receipted. |

## Bake-off

This section is replaced after the SARIF receipt. The final text will quote the measured TP, FP, FN, precision,
recall and F1 values for each detector, state which tools are appropriate as hard gates, and explain why the seeded
canary results are an upper bound rather than a direct estimate of performance on production defects.
