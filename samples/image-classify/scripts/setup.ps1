# PowerShell setup script for the image-classify sample
# Sets up a single Python environment for the entire app (including scripts)


$envDir = ".venv"
$reqFile = "requirements.txt"
$activatePath = ".\\.venv\\Scripts\\Activate.ps1"

# Check if already in a venv
if ($env:VIRTUAL_ENV) {
	Write-Host "WARNING: You are already in a virtual environment: $env:VIRTUAL_ENV"
	Write-Host "It's best to run this script from outside any venv."
}

if (-Not (Test-Path $envDir)) {
	Write-Host "Creating virtual environment in $envDir..."
	python -m venv $envDir
	if ($LASTEXITCODE -ne 0) {
		Write-Host "ERROR: Failed to create virtual environment."
		exit 1
	}
} else {
	Write-Host "Virtual environment $envDir already exists. Skipping creation."
}

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
