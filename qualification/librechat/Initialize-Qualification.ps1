param([Parameter(Mandatory = $true)][string]$RuntimeDirectory)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not [IO.Path]::IsPathRooted($RuntimeDirectory)) {
    throw 'Use an absolute path to a new disposable local directory.'
}
$runtimePath = [IO.Path]::GetFullPath($RuntimeDirectory).TrimEnd('\')
$repositoryPath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..')).TrimEnd('\')
if ($runtimePath.Equals($repositoryPath, [StringComparison]::OrdinalIgnoreCase) -or
    $runtimePath.StartsWith($repositoryPath + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Keep generated credentials and runtime data outside the repository.'
}
if ((Test-Path -LiteralPath $runtimePath) -and
    @(Get-ChildItem -LiteralPath $runtimePath -Force).Count -ne 0) {
    throw 'The disposable directory must be empty; existing files are preserved.'
}
New-Item -ItemType Directory -Path $runtimePath -Force | Out-Null
$owner = [Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls.exe $runtimePath /inheritance:r /grant:r "${owner}:(OI)(CI)(F)" '*S-1-5-18:(OI)(CI)(F)' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Could not restrict the runtime directory ACL.' }
foreach ($file in @('compose.yaml', 'compose.restore.yaml', 'scout-qualification.yaml', 'seed.cjs', 'probe.cjs', 'policy.cjs')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $file) -Destination (Join-Path $runtimePath $file)
}
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
function New-QualificationHex([int]$Length) {
    $bytes = New-Object byte[] $Length
    $rng.GetBytes($bytes)
    return [BitConverter]::ToString($bytes).Replace('-', '').ToLowerInvariant()
}
try {
    $lines = [Collections.Generic.List[string]]::new()
    $lines.Add('CREDS_KEY=' + (New-QualificationHex 32))
    $lines.Add('CREDS_IV=' + (New-QualificationHex 16))
    $lines.Add('JWT_SECRET=' + (New-QualificationHex 48))
    $lines.Add('JWT_REFRESH_SECRET=' + (New-QualificationHex 48))
    $lines.Add('QA_USER_PASSWORD=' + (New-QualificationHex 24))
    [IO.File]::WriteAllLines((Join-Path $runtimePath '.env.qa'), $lines)
} finally {
    $rng.Dispose()
}
Write-Output "Initialized disposable qualification directory: $runtimePath"
Write-Output 'Credentials remain in its protected .env.qa; no services were started.'
