# Load .env into this PowerShell session, then (optionally) start an editor or agent from it.
# Usage:  . .\scripts\dev-shell.ps1            (just load the variables)
#         . .\scripts\dev-shell.ps1 claude     (load, then start Claude Code in this repo)
#         . .\scripts\dev-shell.ps1 code       (load, then open VS Code here)
#         . .\scripts\dev-shell.ps1 cursor     (load, then open Cursor here)
# Why: the MCP configs (.mcp.json, .cursor/mcp.json) read NEATLOGS_API_KEY from the environment
# so no secret is ever written into a committed file. The editor or agent must be started from a
# shell that has the variables.
param([string]$Launch = "")
$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env"
if (-not (Test-Path $envFile)) { Write-Error ".env not found at $envFile"; return }
Get-Content $envFile | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
  $k, $v = $_ -split '=', 2
  if ($v.Trim() -ne '') { Set-Item -Path "Env:$($k.Trim())" -Value $v.Trim() }
}
$env:Path = [Environment]::GetEnvironmentVariable('Path','User') + ';' + [Environment]::GetEnvironmentVariable('Path','Machine')
$gc = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin"
if (Test-Path $gc) { $env:Path += ";$gc" }
Write-Host "Loaded .env into this session (values are not printed)."
Set-Location $root
if ($Launch) { & $Launch . }
