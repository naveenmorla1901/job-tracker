# PowerShell script to run tests locally before pushing to GitHub

Write-Host "Running basic tests..." -ForegroundColor Cyan
pytest tests/test_basic.py -v

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Tests passed! You can safely push your changes." -ForegroundColor Green
} else {
    Write-Host "❌ Tests failed. Please fix the issues before pushing." -ForegroundColor Red
    exit 1
}
