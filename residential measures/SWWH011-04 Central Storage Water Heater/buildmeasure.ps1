# Build script (after simulation)
# Runs locally, assume all files are where you expect them to be.
# Assume that DEER-UES-Tool scripts are available in the environment.

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

############################################################
# USER-EDITABLE VARIABLES
############################################################

$result3Script = "..\..\scripts\result3.py"
$postProcessingScript = "..\..\scripts\post_processing.py"
# Save a copy of MFm.py in the measure folder and fill in the blanks - measure folder, version, etc. Rename the file.
$mfmExScript = ".\MFm_SWWH011_Ex.py"
$mfmNewScript = ".\MFm_SWWH011_New.py"

$query = "query.txt"

$CollectSteps = @(
    @{
        Script  = $result3Script
        Args    = @(
            "--query",
            $query
        )
        Outputs = @(
            "simdata.sqlite"
        )
    },
    @{
        Script  = $mfmExScript
        Args    = @()
        Outputs = @(
            "CEDARS_LoadShape_MFm_Ex.zip"
        )
    }
    @{
        Script  = $mfmNewScript
        Args    = @()
        Outputs = @(
            "CEDARS_LoadShape_MFm_New.zip"
        )
    }
)

$CalculateSteps = @(
    @{
        Script  = $postProcessingScript
        Args    = @()
        Outputs = @(
            "simdata.sqlite"
        )
    }
)

############################################################
# FUNCTIONS
############################################################

function RunStep {
    param($Step)

    Write-Host ""
    Write-Host "Running $($Step.Script)"

    & python $Step.Script @($Step.Args)

    if ($LASTEXITCODE -ne 0) {
        throw "Failed: $($Step.Script)"
    }

    return $Step.Outputs
}

Write-Host ""
Write-Host "===== COLLECT ====="
# Steps that need to read directly from model output files.
$collectOutputs = @()

foreach ($step in $CollectSteps) {
    $collectOutputs += RunStep $step
}

# Write the list of collected output files to collect.json
$collectOutputs |
    ConvertTo-Json |
    Set-Content collect.json

Write-Host "Created collect.json"

Write-Host ""
Write-Host "===== CALCULATE ====="
# Steps that can reference other output files (not directly from model output).
$calculateOutputs = @()

foreach ($step in $CalculateSteps) {
    $calculateOutputs += RunStep $step
}

# Write the list of collected output files to calculate.json
$calculateOutputs |
    ConvertTo-Json |
    Set-Content calculate.json

Write-Host "Created calculate.json"

Write-Host ""
Write-Host "Complete"