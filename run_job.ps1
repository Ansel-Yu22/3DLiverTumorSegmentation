param(
    [string]$CtPath = "D:/PycharmProjects/3DLiverTumorSegmentation/CT/ct/volume-40.nii",
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [int]$PollSeconds = 2,
    [int]$TimeoutSeconds = 900
)

$ErrorActionPreference = "Stop"

Write-Host "1) Health check: $BaseUrl/health"
$health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
$health | ConvertTo-Json -Compress | Write-Host

Write-Host "2) Submit job: $CtPath"
$submitRaw = & curl.exe -sS -X POST "$BaseUrl/jobs" -F "file=@$CtPath"
if (-not $submitRaw) {
    throw "Empty response from /jobs"
}
Write-Host $submitRaw

$submit = $submitRaw | ConvertFrom-Json
if (-not $submit.job_id) {
    throw "Response does not contain job_id."
}

$jobId = [string]$submit.job_id
Write-Host "Job ID: $jobId"

Write-Host "3) Poll job status..."
$start = Get-Date
$deadline = $start.AddSeconds($TimeoutSeconds)

while ($true) {
    $job = Invoke-RestMethod -Uri "$BaseUrl/jobs/$jobId" -Method Get
    $status = [string]$job.status
    Write-Host ("status={0} elapsed_ms={1}" -f $status, $job.elapsed_ms)

    if ($status -eq "succeeded") {
        $rawResultPath = [string]$job.result_path
        if (-not $rawResultPath) {
            throw "Job succeeded but result_path is empty."
        }

        $resultPath = $rawResultPath
        $isLinuxStyleAbsolute = $rawResultPath.StartsWith("/")

        if ($rawResultPath -like "/app/*") {
            $relativeFromApp = $rawResultPath.Substring(5).TrimStart("/")
            $mappedRelative = $relativeFromApp.Replace("/", [System.IO.Path]::DirectorySeparatorChar)
            $mappedLocal = Join-Path (Get-Location) $mappedRelative
            $mappedLocal = [System.IO.Path]::GetFullPath($mappedLocal)
            if (Test-Path -LiteralPath $mappedLocal) {
                $resultPath = $mappedLocal
            } else {
                Write-Host "4) Result path (container): $rawResultPath"
                Write-Host "Job succeeded, but this path is inside container and not mapped to current host directory."
                Write-Host "Tip: mount local Result folder to /app/Result when running docker."
                break
            }
        } elseif ($isLinuxStyleAbsolute) {
            Write-Host "4) Result path (linux absolute): $rawResultPath"
            Write-Host "Job succeeded."
            break
        } else {
            if (-not [System.IO.Path]::IsPathRooted($resultPath)) {
                $resultPath = Join-Path (Get-Location) $resultPath
            }
            $resultPath = [System.IO.Path]::GetFullPath($resultPath)
        }

        if (-not (Test-Path -LiteralPath $resultPath)) {
            throw "Result file not found on host: $resultPath (api returned: $rawResultPath)"
        }

        Write-Host "4) Result file:"
        Get-Item -LiteralPath $resultPath | Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize
        break
    }

    if ($status -eq "failed") {
        throw ("Job failed: " + [string]$job.error)
    }

    if ((Get-Date) -ge $deadline) {
        throw "Polling timeout."
    }

    Start-Sleep -Seconds $PollSeconds
}
