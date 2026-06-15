# NarrativeIQ test runner
# Usage: powershell -ExecutionPolicy Bypass -File scripts/run_tests.ps1

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendVenv = Join-Path $ProjectRoot "backend\.venv"
$PythonExe = Join-Path $BackendVenv "Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "Backend venv not found. Run: cd backend && python -m venv .venv" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== NarrativeIQ Test Suite ===" -ForegroundColor Cyan

# Install test deps if needed
& $PythonExe -m pip install pytest httpx starlette --quiet

# Run pytest from project root
Set-Location $ProjectRoot
& $PythonExe -m pytest tests/ -v --tb=short

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n All tests passed." -ForegroundColor Green
} else {
    Write-Host "`n Some tests failed. Check output above." -ForegroundColor Red
    exit $LASTEXITCODE
}
