# One-click quality check: lint + format + type + security + unit tests
$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

function Check-Step([string]$Name, [string]$Command) {
    Write-Host "==> $Name" -ForegroundColor Cyan
    Invoke-Expression $Command
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAILED: $Name (exit=$LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Check-Step "ruff check"           "python -m ruff check ."
Check-Step "ruff format --check"  "python -m ruff format --check ."
Check-Step "mypy"                 "python -m mypy core services config --ignore-missing-imports"
Check-Step "bandit"               "python -m bandit -r view services core config -q -f txt -s B110,B606"
Check-Step "pytest"               "python -m pytest tests -q"

Write-Host "All checks passed." -ForegroundColor Green
