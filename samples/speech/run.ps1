#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run the Live Captions speech app

.DESCRIPTION
    This script sets up the environment and runs the live captions app.
    Creates a virtual environment if needed and installs dependencies.

.PARAMETER ModelSize
    Whisper model size (tiny, base, small). Default: tiny

.PARAMETER Language
    Language code (en, es, fr, etc.). Default: auto-detect

.PARAMETER Device
    Processing device (cpu, cuda). Default: cpu

.PARAMETER ComputeType
    Compute precision (int8, float16, etc.). Default: int8

.PARAMETER MicIndex
    Microphone device index. Default: system default

.PARAMETER NoVAD
    Disable voice activity detection

.PARAMETER ListDevices
    List available audio devices and exit

.EXAMPLE
    .\run.ps1
    .\run.ps1 -ModelSize base -Language en
    .\run.ps1 -ListDevices
#>

param(
    [ValidateSet("tiny", "base", "small", "medium", "large")]
    [string]$ModelSize = "tiny",
    
    [string]$Language,
    
    [ValidateSet("cpu", "cuda")]
    [string]$Device = "cpu",
    
    [ValidateSet("int8", "int8_float16", "float16", "float32")]
    [string]$ComputeType = "int8",
    
    [int]$MicIndex,
    
    [switch]$NoVAD,
    
    [switch]$ListDevices
)

# Colors for output
$Green = "`e[92m"
$Yellow = "`e[93m"
$Red = "`e[91m"
$Cyan = "`e[96m"
$Reset = "`e[0m"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = $Reset)
    Write-Host "${Color}${Message}${Reset}"
}

# Check if we're in the right directory
if (!(Test-Path "app.py")) {
    Write-ColorOutput "❌ Error: app.py not found. Make sure you're in the samples/speech directory." $Red
    exit 1
}

# Create virtual environment if it doesn't exist
if (!(Test-Path ".venv")) {
    Write-ColorOutput "📦 Creating virtual environment..." $Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "❌ Failed to create virtual environment" $Red
        exit 1
    }
}

# Activate virtual environment
Write-ColorOutput "🔧 Activating virtual environment..." $Cyan
if ($IsWindows -or $env:OS -eq "Windows_NT") {
    & .venv\Scripts\Activate.ps1
} else {
    . .venv/bin/activate
}

# Check if dependencies are installed
$needsInstall = $false
try {
    python -c "import faster_whisper, sounddevice, webrtcvad, numpy, rich" 2>$null
    if ($LASTEXITCODE -ne 0) { $needsInstall = $true }
} catch {
    $needsInstall = $true
}

if ($needsInstall) {
    Write-ColorOutput "📋 Installing dependencies..." $Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "❌ Failed to install dependencies" $Red
        exit 1
    }
}

# Build command line arguments
$appArgs = @()
if ($ModelSize) { $appArgs += "--model-size", $ModelSize }
if ($Language) { $appArgs += "--language", $Language }
if ($Device) { $appArgs += "--device", $Device }
if ($ComputeType) { $appArgs += "--compute-type", $ComputeType }
if ($MicIndex) { $appArgs += "--mic-index", $MicIndex }
if ($NoVAD) { $appArgs += "--no-vad" }
if ($ListDevices) { $appArgs += "--list-devices" }

# Run the app
if ($ListDevices) {
    Write-ColorOutput "🎤 Listing audio devices..." $Cyan
} else {
    Write-ColorOutput "🎙️ Starting Live Captions..." $Green
    Write-ColorOutput "   Model: $ModelSize | Device: $Device | VAD: $(!$NoVAD)" $Cyan
    Write-ColorOutput "   Press Ctrl+C to stop" $Yellow
}

python app.py @appArgs
