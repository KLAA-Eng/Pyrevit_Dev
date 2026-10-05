param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot)
)

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$versionPath = Join-Path $RepoRoot "version.json"
$buildInfoPath = Join-Path $RepoRoot "lib\build_info.py"

if (-not (Test-Path $versionPath)) {
    throw "version.json not found at $versionPath"
}

$versionPayload = Get-Content $versionPath -Raw | ConvertFrom-Json
$today = Get-Date -Format "yyyy-MM-dd"
$releaseDate = $versionPayload.release_date
$channel = $versionPayload.channel
if ($versionPayload.version -notmatch '^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$') {
    throw "version must be numeric MAJOR.MINOR.PATCH"
}
if ($channel -cnotin @('dev', 'beta', 'stable')) { throw "channel must be dev, beta, or stable" }
if ($releaseDate -notmatch '^\d{4}-\d{2}-\d{2}$') { throw "release_date must be YYYY-MM-DD" }
[void][DateTime]::ParseExact($releaseDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
$versionLabel = "v$($versionPayload.version)"

if ($channel -ne "stable") {
    $versionLabel = "$versionLabel-$channel"
}

$gitSha = "unknown"

try {
    $gitShaOutput = git -C "$RepoRoot" rev-parse HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and $gitShaOutput) {
        $gitSha = ($gitShaOutput | Select-Object -First 1).Trim()
    }
} catch {
}

$buildInfo = @"
# This file is generated from version.json.
# Do not edit by hand; update version.json and regenerate instead.
# METADATA_SOURCE_SHA is HEAD at generation, not the resulting release commit.

VERSION = "$($versionPayload.version)"
CHANNEL = "$($versionPayload.channel)"
RELEASE_DATE = "$releaseDate"
VERSION_LABEL = "$versionLabel"
METADATA_SOURCE_SHA = "$gitSha"
BUILD_DATE = "$today"
"@

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($buildInfoPath, $buildInfo.Replace("`r`n", "`n") + "`n", $utf8NoBom)

Write-Host "Wrote $buildInfoPath"
