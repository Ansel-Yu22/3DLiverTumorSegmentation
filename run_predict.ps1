param(
    [string]$CtPath = "D:/PycharmProjects/3DLiverTumorSegmentation/CT/ct/volume-40.nii",
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

Write-Host "1) Health check: $BaseUrl/health"
$health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
$health | ConvertTo-Json -Compress | Write-Host

Write-Host "2) Upload and predict: $CtPath"
$raw = & curl.exe -sS -X POST "$BaseUrl/predict" -F "file=@$CtPath"
if (-not $raw) {
    throw "Empty response from /predict"
}
Write-Host $raw

$resp = $raw | ConvertFrom-Json
if (-not $resp.result_path) {
    throw "Response does not contain result_path."
}

$resultPath = [string]$resp.result_path
if (-not [System.IO.Path]::IsPathRooted($resultPath)) {
    $resultPath = Join-Path (Get-Location) $resultPath
}
$resultPath = [System.IO.Path]::GetFullPath($resultPath)

if (-not (Test-Path -LiteralPath $resultPath)) {
    throw "Result file not found: $resultPath"
}

Write-Host "3) Result file:"
Get-Item -LiteralPath $resultPath | Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize
