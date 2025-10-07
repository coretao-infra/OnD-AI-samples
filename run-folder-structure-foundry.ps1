# Run Folder Structure Foundry Local Sample
# This script launches the Next.js app for folder structure analysis using Foundry Local

Write-Host "Starting Folder Structure Foundry Local Sample..." -ForegroundColor Cyan

# Navigate to the sample directory
Push-Location "${PSScriptRoot}\samples\folder-structure"

# Ensure dependencies are installed
Write-Host "Installing dependencies (npm install)..." -ForegroundColor Yellow
npm install

# Start the development server
Write-Host "Launching Next.js dev server (npm run dev)..." -ForegroundColor Green
npm run dev

# Return to original location when done
Pop-Location
