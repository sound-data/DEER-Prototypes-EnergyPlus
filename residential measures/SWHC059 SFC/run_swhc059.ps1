# Run the four SWHC059 SFC studies with Modelkit, one after another, with logs and a
# completion count per study.
#
#   powershell -ExecutionPolicy Bypass -File run_swhc059.ps1                 # all four studies
#   powershell -ExecutionPolicy Bypass -File run_swhc059.ps1 DMo SFm_1975    # a subset
#   powershell -ExecutionPolicy Bypass -File run_swhc059.ps1 -CheckOnly      # just count what is done
#
# `modelkit rake` is built on file tasks, so relaunching after a crash or Ctrl+C only
# runs the cases that have no instance-out.sql yet. Logs land in <study>/runs/ (gitignored).
param(
    [Parameter(ValueFromRemainingArguments = $true)] [string[]] $Studies,
    [switch] $CheckOnly
)
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

$all = [ordered]@{
    "DMo"      = "SWHC059 SFC AC HP _DMo_Ex"
    "MFm"      = "SWHC059 SFC AC HP_MFm_Ex"
    "SFm_1975" = "SWHC059 SFC AC HP_SFm_1975"
    "SFm_1985" = "SWHC059 SFC AC HP_SFm_1985"
}
if (-not $Studies) { $Studies = @($all.Keys) }
$unknown = $Studies | Where-Object { -not $all.Contains($_) }
if ($unknown) { throw "unknown study key(s) $($unknown -join ', '); choose from $($all.Keys -join ', ')" }

# --- preflight: the EnergyPlus engine named in .modelkit-config must exist ---------------
$cfg = Get-Content (Join-Path $here ".modelkit-config")
$engineLine = $cfg | Where-Object { $_ -match "^\s*engine\s*=\s*'([^']+)'" } | Select-Object -First 1
if (-not $engineLine) { throw ".modelkit-config has no engine = '...' line" }
$engine = $Matches[1]
if (-not (Test-Path (Join-Path $engine "energyplus.exe"))) {
    throw "EnergyPlus engine '$engine' (from .modelkit-config) is not installed: no energyplus.exe there"
}
if (-not (Get-Command modelkit -ErrorAction SilentlyContinue)) { throw "modelkit is not on PATH" }
Write-Host "engine: $engine"

function Expected-Runs([string] $studyDir) {
    # climates not skipped x cases not skipped, summed over the cohorts' cases files
    $climates = @(Import-Csv (Join-Path $studyDir "climates.csv") | Where-Object { -not $_.skip -and $_.climate })
    $cases = 0
    foreach ($row in (Import-Csv (Join-Path $studyDir "cohorts.csv") | Where-Object { -not $_.skip -and $_.cohort })) {
        $f = Join-Path $studyDir ("cases\" + $row.cohort + ".csv")
        if (Test-Path $f) { $cases += @(Import-Csv $f | Where-Object { -not $_.skip -and $_.case_name }).Count }
    }
    return $climates.Count * $cases
}

function Report([string] $key, [string] $studyDir) {
    $runs = Join-Path $studyDir "runs"
    $expected = Expected-Runs $studyDir
    $sql = if (Test-Path $runs) { @(Get-ChildItem $runs -Recurse -Filter "instance-out.sql").Count } else { 0 }
    $ok = 0; $bad = @()
    if (Test-Path $runs) {
        foreach ($err in Get-ChildItem $runs -Recurse -Filter "instance-out.err") {
            if (Select-String -Path $err.FullName -Pattern "EnergyPlus Completed Successfully" -Quiet) { $ok++ }
            else { $bad += $err.Directory.FullName.Substring($runs.Length + 1) }
        }
    }
    $summary = Test-Path (Join-Path $studyDir "results-summary.csv")
    Write-Host ("{0,-9} {1,4}/{2,-4} instance-out.sql   {3,4} completed successfully   results-summary.csv: {4}" -f `
        $key, $sql, $expected, $ok, $(if ($summary) { "yes" } else { "no" }))
    foreach ($b in $bad) { Write-Host "          NOT successful: $b" }
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
foreach ($key in $Studies) {
    $studyDir = Join-Path $here $all[$key]
    if ($CheckOnly) { Report $key $studyDir; continue }

    Write-Host ""
    Write-Host "== $key  ($($all[$key]))  expected runs: $(Expected-Runs $studyDir)  started $(Get-Date -Format 'HH:mm:ss')"
    New-Item -ItemType Directory -Force (Join-Path $studyDir "runs") | Out-Null
    $log = Join-Path $studyDir "runs\modelkit_$stamp.log"
    Push-Location $studyDir
    try {
        $t0 = Get-Date
        # rake prints "(in <dir>)" on stderr; under ErrorActionPreference=Stop PowerShell would
        # turn that into a terminating NativeCommandError, so merge the streams inside cmd.
        & cmd /c "modelkit rake 2>&1" | Tee-Object -FilePath $log
        $rc = $LASTEXITCODE
        $mins = [math]::Round(((Get-Date) - $t0).TotalMinutes, 1)
        Write-Host "== $key finished rc=$rc after $mins min; log: $log"
    } finally { Pop-Location }
    Report $key $studyDir
}
