param (
    [string[]]$Only,
    [switch]$NoClear
)

# Ensure UTF-8 output and encoding
$env:PYTHONUTF8 = "1"
$OutputEncoding = [System.Text.Encoding]::UTF8

$PYTHON = "$PSScriptRoot\agent_core\.venv\Scripts\python.exe"
if (-not (Test-Path $PYTHON)) {
    Write-Error "Virtual environment python.exe not found at $PYTHON. Please make sure to install dependencies first."
    exit 1
}

$queriesFile = "$PSScriptRoot\Test Queries.json"
if (-not (Test-Path $queriesFile)) {
    Write-Error "Queries file not found at $queriesFile"
    exit 1
}

# Load queries
$queries = Get-Content -Raw -Path $queriesFile | ConvertFrom-Json

# Filter if -Only is specified
if ($Only) {
    $onlyIds = @()
    foreach ($o in $Only) {
        $onlyIds += $o.Split(",")
    }
    $onlyIds = $onlyIds | ForEach-Object { $_.Trim().ToUpper() }
    $queries = $queries | Where-Object { $onlyIds -contains $_.id.ToUpper() }
}

if ($queries.Count -eq 0) {
    Write-Warning "No queries matched. Check -Only filter."
    exit 1
}

function Clear-Memory {
    Write-Host "  [clearing memory...]"
    & $PYTHON -c "import sys; sys.path.insert(0, 'agent_core'); from memory import clear; clear()"
    
    # Wipe artifacts
    $artifactsPath = "$PSScriptRoot\agent_core\state\artifacts"
    if (Test-Path $artifactsPath) {
        Remove-Item -Path "$artifactsPath\*.bin" -ErrorAction SilentlyContinue
        Remove-Item -Path "$artifactsPath\*.json" -ErrorAction SilentlyContinue
    }
    Write-Host "  [memory cleared]"
}

# Run loop
$results = @()
$pass = 0
$fail = 0

foreach ($q in $queries) {
    $key = "$($q.id)-run-$($q.run)"
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host "  Query $key   (expected ~$($q.expected_iterations) iterations)"
    Write-Host "  $($q.query)"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Clear memory unless -NoClear is set or this run depends on prior run state
    $skipClear = $NoClear -or (($q.id -eq "C" -and $q.run -eq 2) -or ($q.id -eq "F" -and $q.run -eq 2))
    if (-not $skipClear) {
        Clear-Memory
    }

    # Run the agent
    & $PYTHON "$PSScriptRoot\agent_core\agent7.py" $q.query
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        $results += [PSCustomObject]@{ Key = $key; Result = "PASS" }
        $pass++
    } else {
        $results += [PSCustomObject]@{ Key = $key; Result = "FAIL (exit $exitCode)" }
        $fail++
    }
}

# Summary
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "  RESULTS"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$results | Sort-Object Key | ForEach-Object {
    Write-Host ("  {0,-15} {1}" -f $_.Key, $_.Result)
}
Write-Host ""
Write-Host "  Total: $pass passed, $fail failed"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ($fail -gt 0) {
    exit 1
}
