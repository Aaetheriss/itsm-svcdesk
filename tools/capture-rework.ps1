# Generates the two files required by L2-STRETCH-2 from the public submissions repository.
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$CaptureDirectory = Join-Path $RepoRoot "captures"
$CaptureFile = Join-Path $CaptureDirectory "rework-class-issues.json"
$SummaryFile = Join-Path $RepoRoot "rework-class.json"
New-Item -ItemType Directory -Force -Path $CaptureDirectory | Out-Null

$Headers = @{
    Accept = "application/vnd.github+json"
    "User-Agent" = "Aaetheriss-itsmlab-lab2"
    "X-GitHub-Api-Version" = "2022-11-28"
}

$AllIssues = @()
$Page = 1
while ($true) {
    $Uri = "https://api.github.com/repos/swasik/itsm-2026-submissions/issues?state=all&labels=receipted%2Ckind%3Asubmission&per_page=100&page=$Page"
    $Batch = @(Invoke-RestMethod -Method Get -Uri $Uri -Headers $Headers)
    if ($Batch.Count -eq 0) { break }
    $AllIssues += $Batch
    if ($Batch.Count -lt 100) { break }
    $Page += 1
}

# Store a deterministic compact JSON capture. ConvertTo-Json preserves the complete API objects.
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$Payload = ConvertTo-Json -InputObject @($AllIssues) -Depth 100 -Compress
[System.IO.File]::WriteAllText($CaptureFile, $Payload + "`n", $Utf8NoBom)

$ReworkDeployments = 0
foreach ($Issue in $AllIssues) {
    $SearchText = [string]$Issue.title + "`n" + [string]$Issue.body
    $Match = [regex]::Match($SearchText, 'lab\d+/v(\d+)', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    if ($Match.Success -and [int]$Match.Groups[1].Value -ge 2) {
        $ReworkDeployments += 1
    }
}

$Deployments = $AllIssues.Count
if ($Deployments -eq 0) {
    $Rate = $null
} else {
    $Rate = [Math]::Round(
        [double]$ReworkDeployments / [double]$Deployments,
        6,
        [MidpointRounding]::AwayFromZero
    )
}

$Digest = (Get-FileHash -Algorithm SHA256 -Path $CaptureFile).Hash.ToLowerInvariant()
$RelativeCapturePath = "captures/rework-class-issues.json"
$Source = 'gh api --paginate "repos/swasik/itsm-2026-submissions/issues?state=all&labels=receipted,kind:submission&per_page=100"'
$Summary = [ordered]@{
    source = $Source
    captured_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    capture_path = $RelativeCapturePath
    sha256 = $Digest
    deployments = $Deployments
    rework_deployments = $ReworkDeployments
    deployment_rework_rate = $Rate
}
$SummaryJson = ConvertTo-Json -InputObject $Summary -Depth 10
[System.IO.File]::WriteAllText($SummaryFile, $SummaryJson + "`n", $Utf8NoBom)

Write-Host "Created $RelativeCapturePath"
Write-Host "Created rework-class.json"
Write-Host "deployments=$Deployments rework_deployments=$ReworkDeployments deployment_rework_rate=$Rate"
