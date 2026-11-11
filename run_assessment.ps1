param(
    [string]$OutputDirectory = ('artifacts/live-' + (Get-Date -Format 'yyyyMMdd-HHmmss')),
    [switch]$SkipImport
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$AssessmentPython = Join-Path $PSScriptRoot 'venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $AssessmentPython)) { $AssessmentPython = 'python' }
function Invoke-AssessmentStep {
    param([string[]]$Arguments)
    & $AssessmentPython -m release_agent @Arguments
    if ($LASTEXITCODE -ne 0) { throw ('Assessment step failed: ' + ($Arguments -join ' ')) }
}
Invoke-AssessmentStep -Arguments @('validate-input')
Invoke-AssessmentStep -Arguments @('doctor')
if (-not $SkipImport) { Invoke-AssessmentStep -Arguments @('import') }
Invoke-AssessmentStep -Arguments @('verify-import')
Invoke-AssessmentStep -Arguments @('assess', '--output', $OutputDirectory)
Invoke-AssessmentStep -Arguments @('audit', $OutputDirectory)
Write-Output ('Completed live report: ' + (Join-Path $OutputDirectory 'report.md'))
