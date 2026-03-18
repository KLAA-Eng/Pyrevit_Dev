param(
    [Parameter(Mandatory=$true)]
    [string]$JsonPath
)

# Read the file
$content = Get-Content $JsonPath -Raw

# Check if already injected
if ($content -match 'KL&A Tools') {
    Write-Host "      Already present - skipping"
    exit 0
}

# Define the new entry as a clean heredoc - no escaping needed
$newEntry = @"
        ,{
            "builtin": "False",
            "default_enabled": "True",
            "type": "extension",
            "rocket_mode_compatible": "true",
            "name": "KL&A Tools",
            "description": "All of KL&A's in house production tools.",
            "author": "KL&A Pyrevit Dev Group",
            "author_profile": "https://github.com/KLAA-Eng",
            "url": "https://github.com/KLAA-Eng/Pyrevit_Dev.git",
            "website": "https://github.com/KLAA-Eng",
            "image": "",
            "dependencies": []
        }
"@

# Find the closing ] } and insert before it
$content = $content -replace '(?s)(\s*\]\s*\}\s*)$', "`n$newEntry`n    ]`n}"

# Write back as UTF-8 without BOM
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($JsonPath, $content, $utf8NoBom)

Write-Host "      KL&A Tools entry added successfully"
exit 0