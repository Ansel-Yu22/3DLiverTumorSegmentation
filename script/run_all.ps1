param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$PythonExe = "python",
    [string]$DbUrl = $env:DB_URL,
    [int]$ApiReadyTimeoutSec = 90,
    [switch]$SkipHealthCheck
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ((Split-Path -Leaf $ScriptDir) -eq "script") {
    $ProjectRoot = Split-Path -Parent $ScriptDir
}
else {
    $ProjectRoot = $ScriptDir
}
Set-Location $ProjectRoot

function Escape-SingleQuote([string]$text) {
    return $text -replace "'", "''"
}

function Start-TerminalProcess {
    param(
        [string]$Title,
        [string]$Command
    )

    $safeTitle = Escape-SingleQuote $Title
    $safeRoot = Escape-SingleQuote $ProjectRoot
    $wrapped = @"
`$Host.UI.RawUI.WindowTitle = '$safeTitle'
Set-Location '$safeRoot'
$Command
"@

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", $wrapped
    ) | Out-Null
}

Write-Host "ProjectRoot: $ProjectRoot"
Write-Host "PythonExe: $PythonExe"
Write-Host "BaseUrl: $BaseUrl"
if ([string]::IsNullOrWhiteSpace($DbUrl)) {
    Write-Error "DbUrl is required. This project now uses MySQL only. Please pass -DbUrl or set `$env:DB_URL first."
    exit 1
}
Write-Host "DbUrl: $DbUrl"

Write-Host ""
Write-Host "[1/3] Starting API terminal..."
$safeDbUrl = Escape-SingleQuote $DbUrl
$apiCommand = @"
`$env:DB_URL = '$safeDbUrl'
& '$PythonExe' api.py
"@
Start-TerminalProcess -Title "LiverSeg API" -Command $apiCommand

if (-not $SkipHealthCheck) {
    Write-Host "[2/3] Waiting API health..."
    $deadline = (Get-Date).AddSeconds($ApiReadyTimeoutSec)
    $ready = $false

    while ((Get-Date) -lt $deadline) {
        try {
            $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 3
            if ($health.status -eq "ok") {
                $ready = $true
                break
            }
        }
        catch {
            # API may still be starting.
        }
        Start-Sleep -Seconds 1
    }

    if ($ready) {
        Write-Host "API is ready."
    }
    else {
        Write-Warning "API did not become ready within $ApiReadyTimeoutSec seconds. UI will still be started."
    }
}
else {
    Write-Host "[2/3] Skip health check."
}

Write-Host "[3/3] Starting UI terminal..."
$safeBaseUrl = Escape-SingleQuote $BaseUrl
$uiCommand = @"
`$env:SEG_API_BASE_URL = '$safeBaseUrl'
& '$PythonExe' ui.py
"@
Start-TerminalProcess -Title "LiverSeg UI" -Command $uiCommand

Write-Host ""
Write-Host "Done. Two terminals were started:"
Write-Host "- LiverSeg API  (backend)"
Write-Host "- LiverSeg UI   (desktop app)"
Write-Host ""
Write-Host "Stop services:"
Write-Host "- In each terminal press Ctrl + C"
