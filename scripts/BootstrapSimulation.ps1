# C:\Scripts\BootstrapSimulation.ps1

# BootstrapSimulation.ps1

param(
    [string]$RunId,
    [string]$Repository,
    [string]$CommitSha,
    [string]$MeasurePath,
    [string]$S3Bucket
)

$ErrorActionPreference = 'Stop'

$Workspace = "E:\githubactions\$RunId"

New-Item -ItemType Directory -Force -Path $Workspace

# Download the RunDeerSimulation.ps1 script from S3 to the simulation instance
$AwsCli = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"

& $AwsCli s3 cp `
  "s3://$S3Bucket/githubactions/$RunId/RunDeerSimulation.ps1" `
  "$Workspace\RunDeerSimulation.ps1"

# Execute the RunDeerSimulation.ps1 script with the provided parameters

pwsh "$Workspace\RunDeerSimulation.ps1" `
  -RunId $RunId `
  -Repository $Repository `
  -CommitSha $CommitSha `
  -MeasurePath "$MeasurePath" `
  -S3Bucket $S3Bucket
