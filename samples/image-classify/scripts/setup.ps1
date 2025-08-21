# PowerShell setup script for the image-classify sample
# Sets up a single Python environment for the entire app (including scripts)

$envDir = ".venv"
$reqFile = "requirements.txt"

Write-Host "Creating virtual environment in $envDir..."
python -m venv $envDir

$activatePath = ".\\.venv\\Scripts\\Activate.ps1"
if (Test-Path $activatePath) {
	Write-Host "Activating virtual environment..."
	& $activatePath
	Write-Host "Virtual environment activated."
} else {
	Write-Host "Activation script not found: $activatePath"
}

# Upgrade pip, setuptools, wheel for best compatibility
Write-Host "Upgrading pip, setuptools, and wheel..."
python -m pip install --upgrade pip setuptools wheel

if (Test-Path $reqFile) {
	Write-Host "Installing required packages from $reqFile..."
	pip install -r $reqFile
} else {
	Write-Host "$reqFile not found. Please create it with your dependencies."
}



Write-Host "\nSetup complete. To activate the environment later, run:"
Write-Host $activatePath

Write-Host "\nTo run the canonical metadata extraction script, use:"
Write-Host "python -m scripts.gen_baseline --profile <profile>"
Write-Host "\nIf you encounter import errors, try:"
Write-Host "$env:PYTHONPATH='.'; python -m scripts.gen_baseline --profile <profile>"

Write-Host "\nFor more info, see README.md."
