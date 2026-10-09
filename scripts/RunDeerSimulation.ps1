# RunDeerSimulation.ps1

param(
    [string]$RunId,
    [string]$Repository,
    [string]$CommitSha,
    [string]$MeasurePath,
    [string]$S3Bucket,
    [int]$RunAttempt
)

$Workspace = "E:\githubactions\$RunId"
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true

$LogDir = "$Workspace\attempt-$RunAttempt"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$LogFile = "$LogDir\RunDeerSimulation.log"

# Capture everything written to the console
Start-Transcript -Path $LogFile -Force

$RunStatus = "Success"
$FailureMessage = ""
$StartDate = Get-Date
$AwsCli = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"

try {
    Write-Host "RunId: $RunId"
    Write-Host "CommitSha: $CommitSha"
    Write-Host "MeasurePath: $MeasurePath"

    Write-Host "Cloning repository into $Workspace\repo"

    New-Item -ItemType Directory -Force -Path $Workspace

    $RepoDir = "$Workspace\repo"

    if (-not (Test-Path "$RepoDir\.git")) {
        Write-Host "Repository not found. Cloning..."
        git clone "https://github.com/$Repository.git" $RepoDir
    }
    else {
        Write-Host "Repository already exists. Reusing existing checkout."
    }

    Set-Location $RepoDir
    git remote get-url origin

    # In case the user re-runs the same job with a different commit, we need to fetch all commits to ensure the specified commit is available.
    git fetch --all
    git checkout $CommitSha

    Set-Location "$Workspace\repo\$MeasurePath"

    modelkit rake compose *>> "$LogDir\compose.log"

    & $AwsCli s3 cp `
        "$LogDir\compose.log" `
        "s3://$S3Bucket/githubactions/$RunId/attempt-$RunAttempt/compose.log"

    # modelkit rake run

    & $AwsCli s3 sync `
        "$Workspace\repo\$MeasurePath\runs" `
        "s3://$S3Bucket/githubactions/$RunId/runs"

    # Run the "QC incomplete simulations notebook" and publish its outputs.
    $QcDir = Join-Path $Workspace "qc"
    $QcNotebook = Join-Path $QcDir "QC incomplete simulations.py"
    $SimulationStats = Join-Path $QcDir "simulation_stats.csv"

    New-Item -ItemType Directory -Force -Path $QcDir | Out-Null

    Write-Host "Downloading QC notebook from S3..."

    & $AwsCli s3 cp `
        "s3://$S3Bucket/githubactions/$RunId/QC incomplete simulations.py" `
        $QcNotebook

    Write-Host "Executing QC notebook..."

    $CondaExe = "C:\ProgramData\Anaconda3\Scripts\conda.exe"

    if (-not (Test-Path $CondaExe)) {
        throw "Conda executable not found at $CondaExe"
    }

    & $CondaExe run --no-capture-output -n py314 `
        python --version

    # Use conda run instead of conda activate because this script executes
    # non-interactively through SSM.
    
    & $CondaExe run --no-capture-output -n py314 `
        python $QcNotebook `
        "$Workspace\repo\$MeasurePath" `
        "$SimulationStats"

    if (-not (Test-Path $SimulationStats)) {
       throw "QC script did not produce $SimulationStats"
    }

    Write-Host "Uploading QC outputs to S3..."

    & $AwsCli s3 cp `
        $SimulationStats `
        "s3://$S3Bucket/githubactions/$RunId/qc/simulation_stats.csv"

    # If everything was successful and there is no chance we need to re-run the job,
    # we can clean up the workspace to save space on the instance. Uncomment the following line to enable this behavior.

    # Remove-Item $Workspace -Recurse -Force
}
catch {
    Write-Host "ERROR:"
    Write-Host $_

    $RunStatus = "Failed"
    $FailureMessage = $_.Exception.Message

    throw
}
finally {

    $EndDate = Get-Date
    Stop-Transcript

    $status = @{
        RunId = $RunId
        Repository = $Repository
        CommitSha = $CommitSha
        MeasurePath = $MeasurePath
        Status = $RunStatus
        FailureMessage = $FailureMessage
        StartDate = $StartDate
        EndDate = $EndDate
        RunTimeSeconds = ($EndDate - $StartDate).TotalSeconds
    } | ConvertTo-Json

    $status | Set-Content "$Workspace\status.json"

    & $AwsCli s3 cp `
        "$Workspace\status.json" `
        "s3://$S3Bucket/githubactions/$RunId/status.json"

    & $AwsCli s3 cp `
        $LogFile `
        "s3://$S3Bucket/githubactions/$RunId/attempt-$RunAttempt/RunDeerSimulation.log"

}

