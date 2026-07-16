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

$gitSha = "unknown"
$gitTag = "v$($versionPayload.version)"

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
