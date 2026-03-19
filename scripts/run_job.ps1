param(
    [string]$CtPath = "D:/PycharmProjects/3DLiverTumorSegmentation/CT/ct/volume-40.nii",
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [int]$PollSeconds = 2,
    [int]$TimeoutSeconds = 900
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$scriptRoot\run_api.ps1" -Mode job -CtPath $CtPath -BaseUrl $BaseUrl -PollSeconds $PollSeconds -TimeoutSeconds $TimeoutSeconds
exit $LASTEXITCODE
