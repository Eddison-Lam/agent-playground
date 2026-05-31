<#
.SYNOPSIS
    Start the application with unbuffered Python output from the project root.
#>

$ErrorActionPreference = "Stop"

# Force the working directory to be the project root parent folder
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $scriptDir)

Write-Host "============== Starting Application =============="
Write-Host "Current Directory: $pwd"

# Run Python with unbuffered output (-u)
python -u src/main.py

Write-Host "============== Application Stopped =============="
