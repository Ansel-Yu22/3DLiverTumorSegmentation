param(
    [ValidateSet("predict", "job", "job_simple")]
    [string]$Mode = "job",
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

function Resolve-ResultPath([string]$rawResultPath) {
    if (-not $rawResultPath) {
        return $null
    }

    # Relative path from API.
    if ((-not [System.IO.Path]::IsPathRooted($rawResultPath)) -and (-not $rawResultPath.StartsWith("/"))) {
        return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $rawResultPath))
    }

    # Container path mapping /app/... -> local current directory.
    if ($rawResultPath -like "/app/*") {
        $relativeFromApp = $rawResultPath.Substring(5).TrimStart("/")
        $mappedRelative = $relativeFromApp.Replace("/", [System.IO.Path]::DirectorySeparatorChar)
        $mappedLocal = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $mappedRelative))
        if (Test-Path -LiteralPath $mappedLocal) {
            return $mappedLocal
        }
    }

    return $rawResultPath
}

Write-Host "1) Health check: $BaseUrl/health"
$health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
$health | ConvertTo-Json -Compress | Write-Host

if ($Mode -eq "predict") {
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

    $rawResultPath = [string]$resp.result_path
    $resultPath = Resolve-ResultPath $rawResultPath

    if ($resultPath -and (Test-Path -LiteralPath $resultPath)) {
        Write-Host "3) Result file:"
        Get-Item -LiteralPath $resultPath | Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize
    }
    else {
        Write-Host "3) Result path: $rawResultPath"
        Write-Host "Predict succeeded, but host cannot access the returned path."
    }

    exit 0
}

Write-Host "2) Submit job: $CtPath"
$submitRaw = & curl.exe -sS --no-progress-meter -X POST "$BaseUrl/jobs" -F "file=@$CtPath"
if (-not $submitRaw) {
    throw "Empty response from /jobs"
}
if ($Mode -eq "job") {
    Write-Host $submitRaw
}

$submit = $submitRaw | ConvertFrom-Json
if (-not $submit.job_id) {
    throw "Response does not contain job_id."
}

$jobId = [string]$submit.job_id
if ($Mode -eq "job") {
    Write-Host "Job ID: $jobId"
    Write-Host "3) Poll job status..."
}

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$job = $null

while ($true) {
    $job = Invoke-RestMethod -Uri "$BaseUrl/jobs/$jobId" -Method Get
    $status = [string]$job.status

    if ($Mode -eq "job") {
        Write-Host ("status={0} elapsed_ms={1}" -f $status, $job.elapsed_ms)
    }

    if ($status -in @("succeeded", "failed")) {
        break
    }

    if ((Get-Date) -ge $deadline) {
        if ($Mode -eq "job_simple") {
            $wallMs = Get-WallMs $scriptStart (Get-Date)
            Write-Host "status=failed step=timeout job_id=$jobId wall_ms=$wallMs"
            exit 1
        }
        throw "Polling timeout."
    }

    Start-Sleep -Seconds $PollSeconds
}

$rawResultPath = [string]$job.result_path
$resolvedResultPath = Resolve-ResultPath $rawResultPath

if ([string]$job.status -eq "succeeded") {
    if ($Mode -eq "job_simple") {
        $wallMs = Get-WallMs $scriptStart (Get-Date)
        $inferMs = if ($null -ne $job.elapsed_ms) { [int]$job.elapsed_ms } else { -1 }
        Write-Host "status=succeeded job_id=$jobId infer_ms=$inferMs wall_ms=$wallMs"
        Write-Host "result_path=$resolvedResultPath"
        exit 0
    }

    if ($resolvedResultPath -and (Test-Path -LiteralPath $resolvedResultPath)) {
        Write-Host "4) Result file:"
        Get-Item -LiteralPath $resolvedResultPath | Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize
    }
    else {
        Write-Host "4) Result path: $rawResultPath"
        Write-Host "Job succeeded, but host cannot access the returned path."
    }
    exit 0
}

if ($Mode -eq "job_simple") {
    $wallMs = Get-WallMs $scriptStart (Get-Date)
    $inferMs = if ($null -ne $job.elapsed_ms) { [int]$job.elapsed_ms } else { -1 }
    $reason = [string]$job.error
    if (-not $reason) {
        $reason = "unknown error"
    }
    Write-Host "status=failed job_id=$jobId infer_ms=$inferMs wall_ms=$wallMs"
    Write-Host "error=$reason"
    exit 1
}

throw ("Job failed: " + [string]$job.error)
