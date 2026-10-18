$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'WindowsRelayRelease.psm1') -Force
$now=[DateTimeOffset]::UtcNow
$a=[pscustomobject]@{cid='7e700797f7cc3981d41466cda2ae6af6c84d063308ab49cc4567b0fdbe231b20';source_port=58020;at=$now.AddSeconds(-12).ToString('o');active=0;waiting=0;database_in_use=0;send_queue=0;receive_queue=0;counts=[pscustomobject]@{bytes_sent=100;bytes_received=50;lastsnd=2000000;lastrcv=2000000}}
$b=$a|ConvertTo-Json|ConvertFrom-Json
$b.at=$now.ToString('o')
if (-not (Test-IdleRelayProof -First $a -Second $b -RemotePort 58020)) {throw 'Stable idle proof rejected'}
foreach ($field in @('active','waiting','database_in_use','send_queue','receive_queue')) {
 $bad=$b|ConvertTo-Json|ConvertFrom-Json;$bad.$field=1
 if (Test-IdleRelayProof -First $a -Second $bad -RemotePort 58020) {throw "Active proof accepted: $field"}
}
$bad=$b|ConvertTo-Json|ConvertFrom-Json;$bad.counts.bytes_sent=101
if (Test-IdleRelayProof -First $a -Second $bad -RemotePort 58020) {throw 'Traffic accepted as idle'}
if (Test-IdleRelayProof -First $a -Second $b -RemotePort 58021) {throw 'Wrong socket accepted'}
$b.at=$now.AddSeconds(-11).ToString('o')
if (Test-IdleRelayProof -First $a -Second $b -RemotePort 58020) {throw 'Short sample interval accepted'}
'PASS: idle proof rejects traffic, active work, queue usage, wrong peer and short sampling'
