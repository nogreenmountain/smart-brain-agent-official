$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$workspace=Split-Path $root -Parent
$source=Join-Path $workspace 'deploy/personal-api-public-only-20261018/Invoke-WindowsRelayRelease.ps1'
$t=$null;$e=$null;$ast=[System.Management.Automation.Language.Parser]::ParseFile($source,[ref]$t,[ref]$e)
$fn=$ast.Find({param($x) $x -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $x.Name -eq 'Start-RelayOnce'},$false).Extent.Text
$dir=Join-Path (Join-Path $workspace '.artifacts/personal-api-public-only-20261018') ('wait-fixture-'+[guid]::NewGuid().ToString('N'));New-Item -ItemType Directory -Path $dir | Out-Null
$child=Join-Path $dir 'child.ps1';'Start-Sleep -Seconds 90' | Set-Content -LiteralPath $child
$starter=Join-Path $dir 'starter.ps1';$pidfile=Join-Path $dir 'child-pid.txt'
("`$p=Start-Process powershell.exe -ArgumentList @('-NoProfile','-File','`"{0}`"') -WindowStyle Hidden -PassThru; `$p.Id | Set-Content -LiteralPath '{1}'" -f $child,$pidfile) | Set-Content -LiteralPath $starter
$driver=Join-Path $dir 'driver.ps1'
("`$ErrorActionPreference='Stop';`$InstallDir='{0}';`$BackupDir='{0}'`n{1}`nStart-RelayOnce -StartScript '{2}'" -f $dir,$fn,$starter) | Set-Content -LiteralPath $driver
$p=Start-Process powershell.exe -ArgumentList @('-NoProfile','-File',('"'+$driver+'"')) -WindowStyle Hidden -PassThru
$exited=$p.WaitForExit(8000)
$childId=[int](Get-Content -LiteralPath $pidfile)
if (-not $exited) { Stop-Process -Id $p.Id -ErrorAction Stop; Start-Sleep -Milliseconds 300 }
$childSurvived=[bool](Get-Process -Id $childId -ErrorAction SilentlyContinue)
if ($childSurvived) { Stop-Process -Id $childId }
[pscustomobject]@{StarterReturned=$exited;BackgroundChildSurvived=$childSurvived;DriverPid=$p.Id;ChildPid=$childId;Fixture=$dir} | ConvertTo-Json
if (-not $exited -or -not $childSurvived) { throw 'Starter must return while background service remains running' }
