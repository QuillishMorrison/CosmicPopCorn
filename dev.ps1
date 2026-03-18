param(
    [string]$PythonCmd = "python",
    [string]$NpmCmd = "npm"
)

$ErrorActionPreference = "Stop"

function Resolve-CommandPath {
    param(
        [string]$Primary,
        [string[]]$Fallbacks = @()
    )

    $resolved = Get-Command $Primary -ErrorAction SilentlyContinue
    if ($resolved) {
        return $resolved.Source
    }

    foreach ($candidate in $Fallbacks) {
        if ([string]::IsNullOrWhiteSpace($candidate)) {
            continue
        }
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    return $null
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendJob = $null
$apiPort = 8001

$pythonPath = Resolve-CommandPath -Primary $PythonCmd
if (-not $pythonPath) {
    throw "Python command '$PythonCmd' not found in PATH."
}

$script:NODE_HOME = $null
$npmPath = Resolve-CommandPath -Primary $NpmCmd -Fallbacks @(
    "D:\programms\Node\npm.cmd",
    "C:\Program Files\nodejs\npm.cmd"
)

if (-not $npmPath) {
    throw "npm command '$NpmCmd' not found in PATH or known Node folders."
}

$nodeHome = Split-Path -Parent $npmPath
$env:Path = "$nodeHome;$env:Path"

try {
    $busyPort = Get-NetTCPConnection -LocalPort $apiPort -State Listen -ErrorAction SilentlyContinue
    if ($busyPort) {
        throw "Port $apiPort is already in use. Stop the old backend process first, then run .\\dev.cmd again."
    }

    Write-Host "Starting backend..." -ForegroundColor Cyan
    $backendJob = Start-Job -Name "sector-relay-backend" -ScriptBlock {
        param($projectRoot, $pythonExecutable, $port)
        Set-Location $projectRoot
        $env:API_PORT = [string]$port
        & $pythonExecutable -m app.main
    } -ArgumentList $root, $pythonPath, $apiPort

    Start-Sleep -Seconds 3
    if ($backendJob.State -ne "Running") {
        Receive-Job $backendJob -Keep
        throw "Backend failed to start. See job output above."
    }

    Write-Host "Starting frontend..." -ForegroundColor Cyan
    Set-Location (Join-Path $root "frontend")
    & $npmPath run dev
}
finally {
    if ($backendJob) {
        Write-Host "Stopping backend..." -ForegroundColor Yellow
        Stop-Job $backendJob -ErrorAction SilentlyContinue | Out-Null
        Remove-Job $backendJob -ErrorAction SilentlyContinue | Out-Null
    }
}
