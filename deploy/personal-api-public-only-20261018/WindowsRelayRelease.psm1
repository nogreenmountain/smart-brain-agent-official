Set-StrictMode -Version Latest

function ConvertTo-NormalizedField {
    param([AllowNull()]$Value)
    if ($null -eq $Value) { return '' }
    if ($Value -is [System.Array]) { return (($Value | ForEach-Object { [string]$_ }) -join ',') }
    return [string]$Value
}

function Test-RuleEnabled {
    param([AllowNull()]$Value)
    $text = (ConvertTo-NormalizedField $Value).Trim()
    return $text -in @('True', '1', 'Enabled')
}

function Test-ExactAny9000Rule {
    param([Parameter(Mandatory)]$Rule)
    $protocol = (ConvertTo-NormalizedField $Rule.Protocol).Trim()
    return (
        (Test-RuleEnabled $Rule.Enabled) -and
        (ConvertTo-NormalizedField $Rule.Direction) -eq 'Inbound' -and
        (ConvertTo-NormalizedField $Rule.Action) -eq 'Allow' -and
        $protocol -in @('TCP', '6') -and
        (ConvertTo-NormalizedField $Rule.LocalPort).Trim() -eq '9000' -and
        (ConvertTo-NormalizedField $Rule.RemoteAddress).Trim() -eq 'Any'
    )
}

function Test-NodePublicBroadRule {
    param([Parameter(Mandatory)]$Rule)
    $program = (ConvertTo-NormalizedField $Rule.Program).Trim()
    $profile = (ConvertTo-NormalizedField $Rule.Profile).Trim()
    return (
        (Test-RuleEnabled $Rule.Enabled) -and
        (ConvertTo-NormalizedField $Rule.Direction) -eq 'Inbound' -and
        (ConvertTo-NormalizedField $Rule.Action) -eq 'Allow' -and
        $profile -match '(^|,)Public($|,)' -and
        $program -ieq 'C:\Users\test\nodejs\node.exe' -and
        (ConvertTo-NormalizedField $Rule.Protocol).Trim() -in @('TCP', '6') -and
        (ConvertTo-NormalizedField $Rule.LocalPort).Trim() -eq 'Any' -and
        (ConvertTo-NormalizedField $Rule.RemoteAddress).Trim() -eq 'Any'
    )
}

function Get-RelayFirewallPlan {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][object[]]$Profiles,
        [Parameter(Mandatory)][object[]]$Rules,
        [Parameter(Mandatory)][string]$ReleaseId
    )

    foreach ($profile in $Profiles) {
        if ((ConvertTo-NormalizedField $profile.DefaultInboundAction).Trim() -ne 'Block') {
            throw "Firewall profile '$($profile.Name)' default inbound action must be Block"
        }
    }

    $any9000 = @($Rules | Where-Object { Test-ExactAny9000Rule $_ })
    if ($any9000.Count -ne 2) {
        throw "Expected exactly two enabled Any/9000 rules; found $($any9000.Count)"
    }
    $nodePublic = @($Rules | Where-Object { Test-NodePublicBroadRule $_ })
    if ($nodePublic.Count -ne 1) {
        throw "Expected exactly one enabled Node Public broad rule; found $($nodePublic.Count)"
    }
    $uniqueBroadIds = @($any9000 + $nodePublic | ForEach-Object {
        $identity = [string]$_.InstanceId
        if (-not $identity) { $identity = [string]$_.Name }
        $identity
    } | Sort-Object -Unique)
    if ($uniqueBroadIds.Count -ne 3) {
        throw "Expected three distinct broad firewall rules; found $($uniqueBroadIds.Count)"
    }

    $safeId = $ReleaseId -replace '[^A-Za-z0-9_.-]', '-'
    [pscustomobject]@{
        Operation = 'CreateExactAllow'
        Name = "SmartBrain-Personal-API-9000-$safeId"
        DisplayName = "SmartBrain Personal API 9000 from 192.168.10.165 ($ReleaseId)"
        Direction = 'Inbound'
        Action = 'Allow'
        Enabled = 'True'
        Profile = 'Any'
        Protocol = 'TCP'
        LocalAddress = '192.168.10.146'
        LocalPort = 9000
        RemoteAddress = '192.168.10.165'
        Group = 'SmartBrain Personal API Public Only'
    }

    $seen = @{}
    foreach ($rule in @($any9000 + $nodePublic)) {
        $identity = [string]$rule.InstanceId
        if (-not $identity) { $identity = [string]$rule.Name }
        if ($seen.ContainsKey($identity)) { continue }
        $seen[$identity] = $true
        [pscustomobject]@{
            Operation = 'DisableBroadRule'
            InstanceId = $identity
            Name = [string]$rule.Name
            DisplayName = [string]$rule.DisplayName
        }
    }
}

function Confirm-RelayRuntimeIdentity {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Expected,
        [Parameter(Mandatory)]$Actual
    )
    $same = (
        [int]$Expected.Pid -eq [int]$Actual.Pid -and
        [string]$Expected.StartTimeUtc -ceq [string]$Actual.StartTimeUtc -and
        [string]$Expected.ProcessName -ceq [string]$Actual.ProcessName
    )
    if (-not $same) { throw 'Relay runtime identity changed; refusing an imprecise process stop' }
    return $true
}

function Test-RelayDrainSamples {
    [CmdletBinding()]
    param([Parameter(Mandatory)][int[]]$EstablishedCounts)
    if ($EstablishedCounts.Count -lt 2) { return $false }
    return ($EstablishedCounts[-1] -eq 0 -and $EstablishedCounts[-2] -eq 0)
}

function Test-IdleRelayProof {
    param($First, $Second, [int]$RemotePort)
    try {
        $elapsed = ([DateTimeOffset]::Parse($Second.at)-[DateTimeOffset]::Parse($First.at)).TotalSeconds
        $age = ([DateTimeOffset]::UtcNow-[DateTimeOffset]::Parse($Second.at)).TotalSeconds
        if ($elapsed -lt 10 -or $elapsed -gt 60 -or $age -lt -2 -or $age -gt 20) { return $false }
        foreach ($sample in @($First,$Second)) {
            if ($sample.cid -cne '7e700797f7cc3981d41466cda2ae6af6c84d063308ab49cc4567b0fdbe231b20' -or $sample.source_port -ne $RemotePort) { return $false }
            foreach ($field in @('active','waiting','database_in_use','send_queue','receive_queue')) {
                if ($sample.$field -ne 0) { return $false }
            }
            if ($sample.counts.lastsnd -lt 1800000 -or $sample.counts.lastrcv -lt 1800000) { return $false }
        }
        return ($First.counts.bytes_sent -eq $Second.counts.bytes_sent -and $First.counts.bytes_received -eq $Second.counts.bytes_received)
    } catch { return $false }
}

Export-ModuleMember -Function Get-RelayFirewallPlan, Confirm-RelayRuntimeIdentity, Test-RelayDrainSamples, Test-IdleRelayProof
