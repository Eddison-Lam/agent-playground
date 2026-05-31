<#
.SYNOPSIS
    Fully automated environment setup: Install Python if missing -> Install uv -> Global package installation.
    Designed to run from the scripts/ subdirectory.
#>

$ErrorActionPreference = "Stop"

# Force the working directory to be the project root folder (parent of scripts/)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $scriptDir)

function Refresh-EnvPath {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

Write-Host "============== 1. Checking Python Environment =============="
Write-Host "Target Project Root: $pwd"

$pythonInstalled = $false
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found existing Python: $pythonVersion"
    $pythonInstalled = $true
} catch {
    Write-Host "Python not found. Starting automatic installation..."
}

if (-not $pythonInstalled) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Installing Python 3.11 via Windows Winget..."
        try {
            winget install --id Python.Python.3.11 --silent --accept-source-agreements --accept-package-agreements
            Write-Host "Python installed. Refreshing environment variables..."
            
            Start-Sleep -Seconds 3
            Refresh-EnvPath
            
            if (Get-Command python -ErrorAction SilentlyContinue) {
                $pythonVersion = python --version 2>&1
                Write-Host "Python successfully installed: $pythonVersion"
            } else {
                throw "Python installed but not found in PATH."
            }
        } catch {
            Write-Host "Error: Automatic Python installation failed. Please install Python manually from https://python.org."
            Exit 1
        }
    } else {
        Write-Host "Error: Windows Winget not found. Cannot install Python automatically."
        Exit 1
    }
}

Write-Host "`n============== 2. Checking uv Package Manager =============="

if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "uv package manager is already installed."
} else {
    Write-Host "Installing uv package manager..."
    try {
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh | iex"
        Start-Sleep -Seconds 2
        Refresh-EnvPath
        if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw "uv loading failed." }
        Write-Host "uv installed successfully."
    } catch {
        Write-Host "Warning: uv installation failed. Falling back to traditional pip..."
    }
}

Write-Host "`n============== 3. Installing Project Dependencies =============="

if (Get-Command uv -ErrorAction SilentlyContinue) {
    if ((Test-Path "uv.lock") -and (Test-Path "pyproject.toml")) {
        Write-Host "uv.lock detected. Synchronizing dependencies to global environment..."
        uv pip compile pyproject.toml -o requirements_tmp.txt
        uv pip install --system -r requirements_tmp.txt
        Remove-Item requirements_tmp.txt -ErrorAction SilentlyContinue
    }
    elif (Test-Path "requirements.txt") {
        Write-Host "requirements.txt detected. Installing via uv to global environment..."
        uv pip install --system -r requirements.txt
    }
    elif (Test-Path "pyproject.toml") {
        Write-Host "pyproject.toml detected. Installing via uv to global environment..."
        uv pip install --system -r pyproject.toml
    }
} else {
    Write-Host "Installing dependencies via traditional pip..."
    python -m pip install --upgrade pip
    if (Test-Path "requirements.txt") {
        python -m pip install -r requirements.txt
    } elseif (Test-Path "pyproject.toml") {
        python -m pip install .
    }
}

Write-Host "`n=================================================="
Write-Host "Success: Python environment and all dependencies are completely set up."
Write-Host "You can now run your application."
