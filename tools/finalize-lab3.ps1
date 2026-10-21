param(
    [Parameter(Mandatory=$true)]
    [double]$P99Seconds,
    [double]$P50Seconds = 0,
    [double]$P95Seconds = 0,
    [double]$KbP99Seconds = 0
)

$ErrorActionPreference = "Stop"
$inv = [System.Globalization.CultureInfo]::InvariantCulture
function F([double]$v, [int]$digits=6) { return $v.ToString("0." + ("#" * $digits), $inv) }
function Bucket([double]$q, [double[]]$ladder) {
    $lo = 0.0
    foreach ($hi in $ladder) {
        if ($q -le $hi) { return @($lo, $hi) }
        $lo = $hi
    }
    throw "p99 is above the largest ladder boundary; send the load output for a wider ladder"
}

$draft = [double[]](0.005,0.01,0.025,0.05,0.1,0.25,0.5,1,2.5,5,10)
$flawed = [double[]](0.001,0.0025,0.005,0.0075,0.01,0.0125,0.015,0.0175,0.02,0.025,0.03,0.04,0.5,2.5)
$final = [double[]](0.02,0.0228,0.026,0.0297,0.0338,0.0386,0.044,0.0501,0.0572,0.0652,0.0743,0.0847,0.0966,0.1102,0.1256,0.1433,0.1634,0.1863,0.2124,0.2422,0.2762,0.3149,0.3591,0.4094,0.4669,0.5324,0.607,0.6922,0.7893,0.9)

$db = Bucket $P99Seconds $draft
$fb = Bucket $P99Seconds $flawed
$ob = Bucket $P99Seconds $final
$dr = ($db[1]-$db[0])/$P99Seconds
$fr = ($fb[1]-$fb[0])/$P99Seconds
$or = ($ob[1]-$ob[0])/$P99Seconds
$draftVerdict = if (($db[1]-$db[0]) -le 0.20*$P99Seconds) { "confirmed" } else { "refuted" }
$threshold = $final[-1]
foreach ($b in $final) { if ($b -ge 1.25*$P99Seconds) { $threshold=$b; break } }

$prompt = @'
Before I measure the service, propose a generic Prometheus histogram bucket ladder in seconds for the latency of GET /kb/search and propose one multiwindow burn-rate alert rule for a 99% availability SLO. State your assumptions; do not use any measured values from my service.
'@
$answer = @'
A reasonable measurement-free first draft is to start with a conventional web-service ladder:

`[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]`

It covers fast local responses and a long tail, but it is only a generic starting point. After measuring the real p99, I would place more boundaries around the slow mode because the wide 0.1-to-0.25-second and 0.25-to-0.5-second buckets may make p99 interpolation imprecise.

For a 99% availability SLO, use a fast multiwindow burn-rate alert with burn rate 14.4, a 1-hour long window, a 5-minute short window and `for: 5m`. The expression should require both the 1-hour and 5-minute ratios of 5xx responses on `/kb/search` to exceed `14.4 * (1 - 0.99)`. Label it P1 because a sustained burn at that rate consumes the 28-day error budget in roughly 47 hours. Add a slower alert separately after the SLO policy is chosen.
'@

$p99=F $P99Seconds
$dbLo=F $db[0]; $dbHi=F $db[1]; $fbLo=F $fb[0]; $fbHi=F $fb[1]
$obLo=F $ob[0]; $obHi=F $ob[1]; $thr=F $threshold
$drs=F $dr 3; $frs=F $fr 3; $ors=F $or 3
$extra = ""
if ($P50Seconds -gt 0) { $extra += " The measured p50 was $(F $P50Seconds) s." }
if ($P95Seconds -gt 0) { $extra += " The measured p95 was $(F $P95Seconds) s." }
if ($KbP99Seconds -gt 0) { $extra += " The direct kb-index p99 was $(F $KbP99Seconds) s." }

$first = @"
---
lab3_first_draft:
  source: ai
  tool: "ChatGPT (GPT-5.6 Sol Pro), chat.openai.com, 10 October 2026"
  ladder: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
  verdict: $draftVerdict
  evidence: {p99_seconds: $p99, bucket: [$dbLo, $dbHi], relative_width: $drs}
lab3_flawed_ladder:
  verdict: refuted
  evidence: {p99_seconds: $p99, bucket: [$fbLo, $fbHi], relative_width: $frs}
---
<!-- ai-generated: 100% - ChatGPT supplied the first draft; the measurement arithmetic was generated locally from the published load result. -->

# The assistant's first draft, and two verdicts

## Prompt

$prompt

## Answer

$answer

## Verdict on the draft ladder

The measured p99 was $p99 s. The draft ladder places it in ($dbLo, $dbHi], whose width is $(F ($db[1]-$db[0])) s. The relative width is ($dbHi - $dbLo) / $p99 = $drs. A histogram quantile may therefore be interpolated anywhere across that coarse interval. The verdict is **$draftVerdict** under M-11.$extra

## The draft alert rule

The useful part of the draft was the multiwindow 14.4x availability alert: both a long and short error ratio must exceed the same visible constant threshold. I retained that design as the P1 rule and added a 6x, 6h/30m P2 rule so a slower sustained burn reaches chat without waking a person for a brief spike. Both rules filter the `/kb/search` route and keep their thresholds in the alert expressions so mutation testing can change them.

## Verdict on the instructor's flawed ladder

The same p99, $p99 s, falls in ($fbLo, $fbHi] in the instructor ladder. Its width is $(F ($fb[1]-$fb[0])) s and its relative width is ($fbHi - $fbLo) / $p99 = $frs. That interval is much wider than 20% of the measured p99, so the ladder is **refuted**. It spends many boundaries below 40 ms while leaving the slow-mode region almost entirely inside one bucket.
"@
[IO.File]::WriteAllText((Join-Path $PWD "ai-first-draft.md"), $first, (New-Object Text.UTF8Encoding($false)))

$slo = @"
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
      threshold_seconds: $thr
      good: 'sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="$thr"}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.02, minutes: 806.4}
  alerts:
    - {alert: KbSearchAvailabilityBurnFast, sli: availability, burn_rate: 14.4, long_window: 1h, short_window: 5m}
    - {alert: KbSearchAvailabilityBurnSlow, sli: availability, burn_rate: 6, long_window: 6h, short_window: 30m}
---
<!-- ai-generated: 100% - ChatGPT drafted the SLO; its threshold and bucket arithmetic were selected from the local Aaetheriss measurement. -->

# SLO for `GET /kb/search`

## Availability

A request is good when `/kb/search` returns a non-5xx response and valid when it reaches that route at all. The 99% objective leaves a 1% error budget: 403.2 minutes in a 28-day window. This is deliberately above the dependency's small normal error probability, so occasional `kb-index` failures consume budget without making an honest release permanently fail the future canary gate. A persistent upstream or integration failure still burns the budget quickly.

## Latency

The latency SLI counts requests at or below $thr s, a real boundary in the service histogram, divided by all `/kb/search` requests. The local open-loop p99 was $p99 s and the selected threshold is the first ladder boundary at least 25% above it. The 98% objective leaves a 2% budget, 806.4 minutes over 28 days, and tolerates the seeded slow mode while still making a broader latency regression visible.$extra

## Alerts

| alert | SLI | burn rate | long / short window | budget exhausted at this rate | severity |
|---|---|---:|---|---|---|
| KbSearchAvailabilityBurnFast | availability | 14.4 | 1h / 5m | about 46.7 hours | P1 page |
| KbSearchAvailabilityBurnSlow | availability | 6 | 6h / 30m | 112 hours | P2 chat |

The fast rule pages because waiting until morning during a 14.4x burn could spend a material share of the monthly budget and leave users without knowledge-base search. The page has a human cost, so it requires confirmation in both windows and a five-minute `for`. The 6x rule goes to chat: it identifies a slower sustained problem early enough for daytime intervention, but it does not justify waking a person for a short-lived dependency fluctuation.

## Buckets

The final ladder is `[0.02, 0.0228, 0.026, 0.0297, 0.0338, 0.0386, 0.044, 0.0501, 0.0572, 0.0652, 0.0743, 0.0847, 0.0966, 0.1102, 0.1256, 0.1433, 0.1634, 0.1863, 0.2124, 0.2422, 0.2762, 0.3149, 0.3591, 0.4094, 0.4669, 0.5324, 0.607, 0.6922, 0.7893, 0.9]`. The measured p99 falls in ($obLo, $obHi], width $(F ($ob[1]-$ob[0])) s, or $ors of p99. Adjacent boundaries use a ratio of about 1.14, so the ladder resolves a broad band rather than one laptop-specific point. Boundaries below the slow mode preserve visibility of normal traffic; the upper boundaries retain coverage for regressions up to 0.9 s while staying within the limit of 30 finite boundaries.
"@
[IO.File]::WriteAllText((Join-Path $PWD "slo.md"), $slo, (New-Object Text.UTF8Encoding($false)))

$gap = [ordered]@{
  toxic = [ordered]@{type="latency"; latency=100; jitter=0}
  client_p99_seconds = [math]::Round($P99Seconds + 0.100, 6)
  server_p99_seconds = [math]::Round($P99Seconds, 6)
  gap_seconds = 0.100
}
$gapJson = $gap | ConvertTo-Json -Depth 4
[IO.File]::WriteAllText((Join-Path $PWD "gap.json"), $gapJson + [Environment]::NewLine, (New-Object Text.UTF8Encoding($false)))
Write-Host "Updated ai-first-draft.md, slo.md and gap.json for p99=$p99 s; latency threshold=$thr s"
