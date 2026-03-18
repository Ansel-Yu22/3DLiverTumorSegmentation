param(
    [string]$CtPath = "D:/PycharmProjects/3DLiverTumorSegmentation/CT/ct/volume-40.nii",
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [int]$PollSeconds = 2,
    [int]$TimeoutSeconds = 900
)

$ErrorActionPreference = "Stop"
$scriptStart = Get-Date

function Get-WallMs([datetime]$start, [datetime]$end) {
    return [int](New-TimeSpan -Start $start -End $end).TotalMilliseconds
}

try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
    if ($health.status -ne "ok") {
        throw "Health check failed: $($health | ConvertTo-Json -Compress)"
    }
}
catch {
    Write-Host "status=failed step=health error=$($_.Exception.Message)"
    exit 1
}

try {
    $submitRaw = & curl.exe -sS --no-progress-meter -X POST "$BaseUrl/jobs" -F "file=@$CtPath"
    if (-not $submitRaw) {
        throw "Empty response from /jobs"
    }
    $submit = $submitRaw | ConvertFrom-Json
    if (-not $submit.job_id) {
        throw "Response does not contain job_id"
    }
}
catch {
    Write-Host "status=failed step=submit error=$($_.Exception.Message)"
    exit 1
}

$jobId = [string]$submit.job_id
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$job = $null

while ($true) {
    try {
        $job = Invoke-RestMethod -Uri "$BaseUrl/jobs/$jobId" -Method Get
    }
    catch {
        Write-Host "status=failed step=poll job_id=$jobId error=$($_.Exception.Message)"
        exit 1
    }

    $status = [string]$job.status
    if ($status -in @("succeeded", "failed")) {
        break
    }

    if ((Get-Date) -ge $deadline) {
        $wallMs = Get-WallMs $scriptStart (Get-Date)
        Write-Host "status=failed step=timeout job_id=$jobId wall_ms=$wallMs"
        exit 1
    }

    Start-Sleep -Seconds $PollSeconds
}

$wallMs = Get-WallMs $scriptStart (Get-Date)
$inferMs = if ($null -ne $job.elapsed_ms) { [int]$job.elapsed_ms } else { -1 }

if ([string]$job.status -eq "succeeded") {
    $resultPath = [string]$job.result_path
    if (-not [System.IO.Path]::IsPathRooted($resultPath)) {
        $resultPath = Join-Path (Get-Location) $resultPath
    }
    $resultPath = [System.IO.Path]::GetFullPath($resultPath)
    Write-Host "status=succeeded job_id=$jobId infer_ms=$inferMs wall_ms=$wallMs"
    Write-Host "result_path=$resultPath"
    exit 0
}
else {
    $reason = [string]$job.error
    if (-not $reason) {
        $reason = "unknown error"
    }
    Write-Host "status=failed job_id=$jobId infer_ms=$inferMs wall_ms=$wallMs"
    Write-Host "error=$reason"
    exit 1
}
