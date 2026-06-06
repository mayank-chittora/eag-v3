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

$queriesFile = "$PSScriptRoot\Test Queries IPO.json"
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
    Write-Host "  [clearing IPO Explorer memory...]"
    & $PYTHON -c "import sys, pathlib; sys.path.insert(0, 'agent_core'); import memory; memory.STATE_PATH = pathlib.Path('ipo_explorer/state/memory.json'); memory.clear(); import shutil; shutil.rmtree('ipo_explorer/state/artifacts', ignore_errors=True); pathlib.Path('ipo_explorer/state/artifacts').mkdir(exist_ok=True)"
    Write-Host "  [IPO Explorer memory cleared]"
}

# Run queries
function Run-Queries($phaseName) {
    $results = @()
    $pass = 0
    $fail = 0

    foreach ($q in $queries) {
        $key = "$($q.id)-run-$($q.run)"
        Write-Host ""
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        Write-Host "  [$phaseName] Query $key   (expected ~$($q.expected_iterations) iterations)"
        Write-Host "  $($q.query)"
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        # Run the IPO Explorer agent
        & $PYTHON "$PSScriptRoot\ipo_explorer\agent.py" $q.query | Out-Host
        $exitCode = $LASTEXITCODE

        if ($exitCode -eq 0) {
            $results += [PSCustomObject]@{ Key = $key; Result = "PASS" }
            $pass++
        } else {
            $results += [PSCustomObject]@{ Key = $key; Result = "FAIL (exit $exitCode)" }
            $fail++
        }
    }

    return @($results, $pass, $fail)
}

if (-not $NoClear) {
    Clear-Memory
}

# Phase 1: Run WITHOUT index
Write-Host ""
Write-Host "==================================================================" -ForegroundColor Yellow
Write-Host "  PHASE 1: RUNNING QUERIES WITHOUT THE INDEX (Expected to fail/not know)" -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Yellow
$res = Run-Queries "WITHOUT INDEX"
$resultsNoIndex = $res[0]
$passNoIndex = $res[1]
$failNoIndex = $res[2]

# Phase 2: Index the specific symbols needed
Write-Host ""
Write-Host "==================================================================" -ForegroundColor Yellow
Write-Host "  PHASE 2: INDEXING THE SPECIFIC IPO SYMBOLS" -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Yellow

$symbolsToIndex = @()
foreach ($q in $queries) {
    if ($q.id -eq "IPO-A") { $symbolsToIndex += "GREENPANEL" }
    elseif ($q.id -eq "IPO-B") { $symbolsToIndex += "WARDWIZARD" }
    elseif ($q.id -eq "IPO-C") { $symbolsToIndex += "KRSNAA" }
    elseif ($q.id -eq "IPO-D") { $symbolsToIndex += "CLEAN" }
    elseif ($q.id -eq "IPO-E") { $symbolsToIndex += "MAPMYINDIA" }
}

# Remove duplicates
$symbolsToIndex = $symbolsToIndex | Select-Object -Unique

foreach ($sym in $symbolsToIndex) {
    Write-Host "Indexing $sym..."
    & $PYTHON "$PSScriptRoot\ipo_explorer\indexer.py" --symbol $sym --force
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Indexing $sym failed!"
        exit 1
    }
}

# Phase 3: Run WITH index
Write-Host ""
Write-Host "==================================================================" -ForegroundColor Yellow
Write-Host "  PHASE 3: RUNNING QUERIES WITH THE INDEX (Expected to pass/succeed)" -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Yellow
$resWith = Run-Queries "WITH INDEX"
$resultsWithIndex = $resWith[0]
$passWithIndex = $resWith[1]
$failWithIndex = $resWith[2]

# Summary
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "  SUMMARY RESULTS"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "  WITHOUT INDEX RESULTS:"
$resultsNoIndex | ForEach-Object {
    Write-Host ("  {0,-15} {1}" -f $_.Key, $_.Result)
}
Write-Host "  Total (Without Index): $passNoIndex passed, $failNoIndex failed"
Write-Host ""
Write-Host "  WITH INDEX RESULTS:"
$resultsWithIndex | ForEach-Object {
    Write-Host ("  {0,-15} {1}" -f $_.Key, $_.Result)
}
Write-Host "  Total (With Index): $passWithIndex passed, $failWithIndex failed"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
