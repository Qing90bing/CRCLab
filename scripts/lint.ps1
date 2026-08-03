# One-click quality check: lint + format + type + security + unit tests
$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
Write-Host "==> ruff check" -ForegroundColor Cyan
python -m ruff check .
Write-Host "==> ruff format --check" -ForegroundColor Cyan
python -m ruff format --check .
Write-Host "==> mypy (core/services/config)" -ForegroundColor Cyan
python -m mypy core services config --ignore-missing-imports
Write-Host "==> bandit" -ForegroundColor Cyan
python -m bandit -r view services core config -q -f txt -s B110,B606
Write-Host "==> pytest" -ForegroundColor Cyan
python -m pytest tests -q
Write-Host "All checks passed." -ForegroundColor Green
