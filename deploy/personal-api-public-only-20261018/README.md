# Personal API public-only relay

This package hardens the Windows relay used behind the SmartBrain personal API.

- AI requests require the production gateway peer `192.168.10.165` and `X-SmartBrain-Gateway-Proxy: personal-api`.
- The management panel and management APIs are loopback-only.
- The internal marker is removed before forwarding to CPA on `127.0.0.1:3000`.
- The existing personal-key authorize call, CPA credential exchange, concurrency behavior and response streaming remain unchanged.

Validation:

```powershell
C:\Users\test\nodejs\node.exe --test proxy-server.test.js proxy-public-only.test.js
powershell.exe -NoProfile -ExecutionPolicy Bypass -File start-public-only.test.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File windows-relay-release.test.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File windows-relay-prepare-fixture.test.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File windows-relay-apply-rollback-fixture.test.ps1
```

The files contain no credentials. Production installation must preserve the existing `config.yaml`, `secrets`, logs and OAuth state. Do not use `restart-proxy.ps1`; coordinate `CLIProxyAPI2Services`, wait for in-flight traffic, and restart the exact relay once.

Reviewed candidate hashes are `proxy-server.js` = `8EE401EB7169347F4308A29C3C942121E0F9CE10479EB240E9C0A286607A208C` and `start-services.ps1` = `AE95AC240D24BA695F24FEE0105F1E1EC6B5177ECB52D0D74C39E73737E6A2E6`. `Prepare` refuses any other candidate bytes.

## Reviewed Windows release workflow

`Invoke-WindowsRelayRelease.ps1` is a three-action, fail-closed release tool. It requires an explicit install directory and a new state directory; it never discovers or reads `config.yaml`, credential files, process command lines, request bodies or response bodies.

1. `Prepare` is read-only for the relay, firewall, scheduled task and processes. It saves the installed `proxy-server.js` and `start-services.ps1`, their SHA-256 hashes, the exact three broad firewall rule identities, the firewall profiles, the watchdog XML/state, and the exact 9000/3000 PID plus start time. Review `release-state.json` before continuing.
2. `Apply` requires `-ConfirmReleaseId personal-api-public-only-20261018-r1`. It rechecks every prepared identity, creates the exact `192.168.10.165 -> 192.168.10.146:9000/TCP` allow first, disables exactly two enabled `Any/9000` rules and one distinct enabled Node/Public/Any rule, stops and disables `CLIProxyAPI2Services`, waits for two consecutive zero-connection samples (or the specifically pinned old gateway idle connection proof described below), replaces the two scripts, stops the exact reviewed 9000 PID once, invokes `start-services.ps1` once, and restores the original watchdog state.
3. Any caught Apply failure runs the same restoration routine used by `Rollback`. Explicit `Rollback` requires the release confirmation, stops only the recorded new PID/start-time after drain when needed; an unchanged original process is retained, restores the two backed-up files and hashes, restores the three rules' enabled state, removes only this release's owned exact allow rule, invokes the original start script once when needed, and restores the watchdog state.

Example shape for a future authorized execution (replace both paths with reviewed absolute Windows paths):

```powershell
$common = @{
  InstallDir = 'C:\reviewed\CLIProxyAPI2'
  CandidateDir = 'C:\reviewed\personal-api-public-only-20261018'
  StateDir = 'C:\reviewed\release-state\personal-api-public-only-20261018-r1'
  ReleaseId = 'personal-api-public-only-20261018-r1'
}
& .\Invoke-WindowsRelayRelease.ps1 -Action Prepare @common
# Review release-state.json, firewall-before.json, watchdog-before.xml and backup hashes.
& .\Invoke-WindowsRelayRelease.ps1 -Action Apply @common -ConfirmReleaseId $common.ReleaseId
# Only if rollback is required:
& .\Invoke-WindowsRelayRelease.ps1 -Action Rollback @common -ConfirmReleaseId $common.ReleaseId
```

The script creates no explicit Block rule. It requires all effective firewall profiles to have default inbound `Block`; any profile, rule-count, rule-owner, file-hash, watchdog-definition, PID, start-time, listener or backend binding drift aborts before the exact relay stop.

## Retained idle HTTP connection

`inspect_idle_relay.py` uses the existing SSH connection to inspect only the pinned old gateway health counters and TCP counters. An idle exception requires the exact production source port, active/waiting/DB counters all zero, TCP queues zero, no Windows backend connection, last send/receive over 1800 seconds, and unchanged byte counters over at least 10 seconds. All conditions are checked again immediately before stopping the exact relay PID. New traffic fails closed. Existing relay logs are copied and hash-verified before startup can truncate them.

## Linux release tooling

The Python tooling is a new `personal-api-public-only-20261018-r1` identity. Never replay prior relay-auth r1–r4. It retains exact old CID/image/network/unit/inventory recovery, backup/static-capacity gates, one-shot stages, and adds two zero-activity health samples before service stop. Direct unmarked requests and remote management return 403; trusted marked anonymous requests return 401.

`collect_backup_receipt.py` verifies only the newly started exact online backup. `collect_natural_success.py` accepts only completed successful requests begun after cutover, with the original credential fingerprint unchanged. No terminal Key input is used. Anonymous probes and fixture tests never produce a successful authenticated receipt. Promotion remains pending until that receipt arrives and restores the old gateway on deadline/failure. Full frozen restore is outside this release's evidence.

Run Python tests with `python -m unittest discover -s deploy/personal-api-public-only-20261018 -p "test*.py"`. Run `windows-idle-proof.test.ps1` alongside the PowerShell tests above.
