# Run LLM Bench Sample
# This script launches the CLI benchmarking tool for local LLMs

Write-Host "Starting LLM Bench Sample..." -ForegroundColor Cyan

# Navigate to the bench directory
Push-Location "${PSScriptRoot}\bench"

# Ensure Python venv is created/activated
if (!(Test-Path .venv)) {
    Write-Host "Creating Python virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "Activating Python virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

# Install Python dependencies
Write-Host "Installing Python requirements..." -ForegroundColor Yellow
pip install -r requirements.txt

# Run the benchmark CLI
Write-Host "Launching LLM Benchmark CLI..." -ForegroundColor Green
python app.py

# Return to original location
Pop-Location
