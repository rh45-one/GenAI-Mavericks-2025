# Usage:
#   1) Copy backend\dev_env.template.txt to dev_env.local.txt in the repo root and fill in LLM_API_KEY, DEEPSEEK_API_KEY, etc.
#   2) From repo root: powershell -ExecutionPolicy Bypass -File backend\scripts\start_stack.ps1
#
# The script:
#   - Loads env vars from dev_env.local.txt (if present)
#   - Starts the backend (uvicorn) in a new PowerShell window
#   - Starts the frontend (npm run dev) in a new PowerShell window

param(
    [string]$EnvFile = "dev_env.local.txt",
    [string]$BackendHost = $null,
    [string]$BackendPort = $null
)

$repoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
if (-not $repoRoot) {
    # Fallback: use two-level parent of script path
    $repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSCommandPath))
}
Set-Location $repoRoot

$resolvedEnvFile = $EnvFile
if (-not (Split-Path -IsAbsolute $EnvFile)) {
    $resolvedEnvFile = Join-Path $repoRoot $EnvFile
}

function Load-EnvFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        Write-Host "Env file not found: $Path" -ForegroundColor Yellow
        return @{}
    }
    $vars = @{}
    Get-Content $Path | ForEach-Object {
        if ($_ -match '^\s*#') { return }
        if ($_ -match '^\s*$') { return }
        if ($_ -match '^\s*([^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            $vars[$name] = $value
        }
    }
    return $vars
}

$envVars = Load-EnvFile -Path $resolvedEnvFile

function Start-Window {
    param(
        [string]$Title,
        [string]$Command,
        [hashtable]$Vars
    )
    # Use LiteralPath to avoid parsing issues with spaces or special characters
    $lines = @("Set-Location -LiteralPath '$repoRoot'")
    foreach ($k in $Vars.Keys) {
        # Build the assignment string without allowing outer-string interpolation
        # to avoid PowerShell treating $env:... as a variable in the generator.
        $val = $Vars[$k] -replace "'", "''"
        $assign = ('$env:' + $k + " = '" + $val + "'")
        $lines += $assign
    }
    $lines += $Command
    $joined = $lines -join "; "
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $joined -WindowStyle Normal
}

# Backend window
$backendVars = $envVars.Clone()
if ($BackendHost) { $backendVars["BACKEND_HOST"] = $BackendHost }
if ($BackendPort) { $backendVars["BACKEND_PORT"] = $BackendPort }
$backendHostVal = $backendVars["BACKEND_HOST"] | ForEach-Object { if ($_){$_} else {"0.0.0.0"} }
$backendPortVal = $backendVars["BACKEND_PORT"] | ForEach-Object { if ($_){$_} else {"8000"} }
$backendCmd = "python -m uvicorn backend.app:app --host $backendHostVal --port $backendPortVal --reload"
Start-Window -Title "Backend" -Command $backendCmd -Vars $backendVars

# Frontend window
$frontendVars = @{}
if ($envVars.ContainsKey("VITE_API_BASE_URL")) { $frontendVars["VITE_API_BASE_URL"] = $envVars["VITE_API_BASE_URL"] }
$frontendDir = Join-Path $repoRoot 'frontend'
$frontendCmd = "Set-Location -LiteralPath '$frontendDir'; npm install; npm run dev -- --host 127.0.0.1 --port 5173"
Start-Window -Title "Frontend" -Command $frontendCmd -Vars $frontendVars

Write-Host "Launched backend and frontend. Env source: $resolvedEnvFile" -ForegroundColor Green
