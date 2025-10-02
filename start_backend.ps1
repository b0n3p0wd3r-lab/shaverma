# Set UTF-8 encoding for PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Change to backend directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$backendPath = Join-Path $scriptPath "backend"

Write-Host "Starting backend server..."
Write-Host "Backend path: $backendPath"

Set-Location $backendPath

# Start Python web API
try {
    python web_api.py
} catch {
    Write-Host "Error starting backend: $_"
    Read-Host "Press Enter to continue..."
}
