param(
    [string]$CtPath = "D:/PycharmProjects/3DLiverTumorSegmentation/CT/ct/volume-40.nii",
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$scriptRoot\run_api.ps1" -Mode predict -CtPath $CtPath -BaseUrl $BaseUrl
exit $LASTEXITCODE
