
param(
    [switch]$gpu,
    [string]$infile = $null,
    [string]$outfile = $null,
    [string]$model = $null
)


# Change to the image-edit sample directory for all operations
$sampleDir = Join-Path $PSScriptRoot 'samples\image-edit'
Set-Location $sampleDir

# 0. Prerequisites check
Write-Host "[INFO] Checking prerequisites..." -ForegroundColor Cyan

# Check OS
if ($env:OS -notlike '*Windows*') {
    Write-Host "[ERROR] This sample is intended for Windows 10/11." -ForegroundColor Red
    exit 1
}

# Check Python exists, version 3.12 or newer
$pyv = & python --version 2>&1
if ($pyv -notmatch 'Python 3\.(1[2-9]|[2-9][0-9])') {
    Write-Host "[ERROR] Python 3.12+ required. Found: $pyv" -ForegroundColor Red
    exit 1
}

$venv = ".venv\Scripts\Activate.ps1"
$reqs = "requirements.txt"
$app = "app.py"

# 1. Create and activate virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "[INFO] Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
}

Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Cyan
. $venv

Write-Host "[INFO] Ensuring all Python requirements are installed..." -ForegroundColor Cyan
python -m pip install --upgrade pip
pip install -r $reqs

# 3. Run the app (GUI or CLI)
if ($infile -and $outfile) {
    Write-Host "[INFO] Running in CLI mode with input: $infile, output: $outfile" -ForegroundColor Cyan
    python $app --input $infile --output $outfile --model $model
} else {
    Write-Host "[INFO] Starting Background Remover GUI..." -ForegroundColor Cyan
    python $app
}
