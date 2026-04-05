Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$artifactDir = Join-Path $repoRoot "docs/evidence/Reliability/artifacts"
New-Item -ItemType Directory -Path $artifactDir -Force | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$artifactFile = Join-Path $artifactDir "chaos-restart-$timestamp.md"
$latestFile = Join-Path $artifactDir "chaos-restart-latest.md"

$lines = [System.Collections.Generic.List[string]]::new()
function Add-Line([string]$text) {
    $lines.Add($text) | Out-Null
    Write-Host $text
}

function Wait-ForHealth([string]$healthUrl, [int]$timeoutSeconds) {
    $deadline = (Get-Date).AddSeconds($timeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $res = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 3
            if ($res.status -eq "ok") {
                return $true
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    return $false
}

Add-Line "# Chaos Restart Proof"
Add-Line ""
Add-Line "- Timestamp: $(Get-Date -Format o)"
Add-Line "- Runner: $env:COMPUTERNAME"
Add-Line ""

$exitCode = 0

try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker CLI is not installed or not available on PATH."
    }

    $composeVersion = docker compose version
    Add-Line "## Tooling"
    Add-Line ""
    Add-Line "- docker compose: $composeVersion"
    Add-Line ""

    $proxyPort = if ($env:APP_PROXY_PORT) { $env:APP_PROXY_PORT } else { "5001" }
    $baseUrl = "http://localhost:$proxyPort"
    $healthUrl = "$baseUrl/health"

    Add-Line "## Startup"
    Add-Line ""
    Add-Line "Running: docker compose down -v --remove-orphans"
    docker compose down -v --remove-orphans | Out-Null

    Add-Line "Running: docker compose up -d app nginx postgres redis tempo"

    $env:DATABASE_INITIALIZE = "false"
    docker compose up -d app nginx postgres redis tempo | Out-Null

    if (-not (Wait-ForHealth -healthUrl $healthUrl -timeoutSeconds 120)) {
        throw "Health endpoint did not become ready at $healthUrl"
    }

    $initialHealth = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 5
    Add-Line "- Initial health: $($initialHealth.status)"

    Add-Line ""
    Add-Line "## Data Setup"

    $seedUserName = "chaos_user_$timestamp"
    $seedEmail = "chaos+$timestamp@example.com"
    $userPayload = @{ username = $seedUserName; email = $seedEmail } | ConvertTo-Json
    $user = Invoke-RestMethod -Uri "$baseUrl/users/" -Method Post -ContentType "application/json" -Body $userPayload

    $urlPayload = @{ user_id = $user.id; original_url = "https://example.com/chaos"; title = "chaos-proof" } | ConvertTo-Json
    $url = Invoke-RestMethod -Uri "$baseUrl/urls" -Method Post -ContentType "application/json" -Body $urlPayload

    Add-Line ""
    Add-Line "- Created user id: $($user.id)"
    Add-Line "- Created url id: $($url.id)"

    Add-Line ""
    Add-Line "## Chaos Action"

    $appIdsBefore = (docker compose ps -q app) -split "`n" | Where-Object { $_.Trim() -ne "" }
    if ($appIdsBefore.Count -lt 1) {
        throw "Could not find app container id"
    }
    $appIdBefore = $appIdsBefore[0].Trim()
    $startedBefore = docker inspect -f "{{.State.StartedAt}}" $appIdBefore

    Add-Line ""
    Add-Line "- App container before kill: $appIdBefore"
    Add-Line "- StartedAt before kill: $startedBefore"
    Add-Line "- Running: docker kill $appIdBefore"

    docker kill $appIdBefore | Out-Null

    $deadline = (Get-Date).AddSeconds(120)
    $recovered = $false
    $appIdAfter = $null
    $startedAfter = $null

    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 2
        $currentIds = (docker compose ps -q app) -split "`n" | Where-Object { $_.Trim() -ne "" }
        if ($currentIds.Count -lt 1) {
            continue
        }

        $appIdAfter = $currentIds[0].Trim()
        $startedAfter = docker inspect -f "{{.State.StartedAt}}" $appIdAfter

        $isHealthy = Wait-ForHealth -healthUrl $healthUrl -timeoutSeconds 5
        if ($isHealthy -and ($appIdAfter -ne $appIdBefore -or $startedAfter -ne $startedBefore)) {
            $recovered = $true
            break
        }
    }

    if (-not $recovered) {
        throw "App did not recover in time after kill"
    }

    Add-Line ""
    Add-Line "- App container after recovery: $appIdAfter"
    Add-Line "- StartedAt after recovery: $startedAfter"
    Add-Line "- Recovery detected: yes"

    Add-Line ""
    Add-Line "## Post-Recovery Validation"

    $reloadedUrl = Invoke-RestMethod -Uri "$baseUrl/urls/$($url.id)" -Method Get -TimeoutSec 5
    if ($reloadedUrl.id -ne $url.id) {
        throw "Expected url id $($url.id) after recovery, got $($reloadedUrl.id)"
    }

    Add-Line ""
    Add-Line "- URL fetch after restart: success"
    Add-Line "- Persisted url id: $($reloadedUrl.id)"
    Add-Line "- Verdict: PASS"
}
catch {
    $exitCode = 1
    Add-Line ""
    Add-Line "## Failure"
    Add-Line ""
    Add-Line "- Verdict: FAIL"
    Add-Line "- Reason: $($_.Exception.Message)"
    Write-Error $_
}
finally {
    $lines | Set-Content -Path $artifactFile -Encoding UTF8
    $lines | Set-Content -Path $latestFile -Encoding UTF8
    Write-Host ""
    Write-Host "Artifact written: $artifactFile"
    Write-Host "Latest pointer: $latestFile"
}

exit $exitCode
