param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot)
)

$versionPath = Join-Path $RepoRoot "version.json"
$buildInfoPath = Join-Path $RepoRoot "lib\build_info.py"

if (-not (Test-Path $versionPath)) {
    throw "version.json not found at $versionPath"
}

$versionPayload = Get-Content $versionPath -Raw | ConvertFrom-Json
$today = Get-Date -Format "yyyy-MM-dd"
$releaseDate = if ($versionPayload.release_date) { $versionPayload.release_date } else { $today }
$channel = if ($versionPayload.channel) { $versionPayload.channel.ToLowerInvariant() } else { "stable" }
$gitTag = "v$($versionPayload.version)"

# Legacy version strings already include their channel (for example 0.0.6beta).
# New releases use a numeric version plus a separate beta or stable channel.
if ($channel -ne "stable" -and $versionPayload.version -notmatch "(alpha|beta|rc)$") {
    $gitTag = "$gitTag-$channel"
}

$gitSha = "unknown"

try {
    $gitShaOutput = git -c safe.directory="$RepoRoot" rev-parse --short HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and $gitShaOutput) {
        $gitSha = ($gitShaOutput | Select-Object -First 1).Trim()
    }
} catch {
}

try {
    $gitTagOutput = git -c safe.directory="$RepoRoot" describe --tags --exact-match HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and $gitTagOutput) {
        $gitTag = ($gitTagOutput | Select-Object -First 1).Trim()
    }
} catch {
}

$buildInfo = @"
# This file is generated from version.json.
# Do not edit by hand; update version.json and regenerate instead.

VERSION = "$($versionPayload.version)"
CHANNEL = "$($versionPayload.channel)"
RELEASE_DATE = "$releaseDate"
GIT_TAG = "$gitTag"
GIT_SHA = "$gitSha"
BUILD_DATE = "$today"
"@

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($buildInfoPath, $buildInfo, $utf8NoBom)

Write-Host "Wrote $buildInfoPath"
