param(
    [int]$Records = 50000,
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [int]$StartupTimeoutSeconds = 60,
    [switch]$RefreshData,
    [switch]$SkipData,
    [switch]$SkipReport,
    [switch]$BuildFrontend,
    [switch]$SkipFrontendBuild,
    [switch]$SeedDemoBriefs
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$EnvFile = Join-Path $Root ".env"
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$LogDir = Join-Path $Root "logs"
$BackendOut = Join-Path $LogDir "backend-demo.out.log"
$BackendErr = Join-Path $LogDir "backend-demo.err.log"
$FrontendOut = Join-Path $LogDir "frontend-demo.out.log"
$FrontendErr = Join-Path $LogDir "frontend-demo.err.log"

function Import-DotEnv {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    Get-Content -LiteralPath $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }

        $key, $value = $line.Split("=", 2)
        $key = $key.Trim()
        $value = $value.Trim().Trim('"').Trim("'")
        if ($key) {
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

function Stop-Port {
    param([int]$Port)

    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    $processIds = @($connections | Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($processId in $processIds) {
        if ($processId) {
            Write-Host "Stopping existing process on port $Port (PID $processId)..."
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
    }
}

function Wait-Http {
    param(
        [string]$Url,
        [string]$Name,
        [int]$TimeoutSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 4
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Host "$Name is ready: $Url"
                return $true
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

function Show-LogTail {
    param(
        [string]$Label,
        [string]$Path
    )

    if (Test-Path -LiteralPath $Path) {
        Write-Host ""
        Write-Host "$Label log tail:"
        Get-Content -LiteralPath $Path -Tail 25
    }
}

function Invoke-RequiredCommand {
    param(
        [string]$Label,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory
    )

    Write-Host $Label
    Push-Location $WorkingDirectory
    try {
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "$Label failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}

function Start-DemoProcess {
    param(
        [string]$Label,
        [string]$WorkingDirectory,
        [string]$Command,
        [string]$StdOut,
        [string]$StdErr
    )

    if (Test-Path -LiteralPath $StdOut) {
        Remove-Item -LiteralPath $StdOut -Force
    }
    if (Test-Path -LiteralPath $StdErr) {
        Remove-Item -LiteralPath $StdErr -Force
    }

    $quotedWorkingDirectory = $WorkingDirectory.Replace('"', '""')
    $quotedOut = $StdOut.Replace('"', '""')
    $quotedErr = $StdErr.Replace('"', '""')
    $cmdLine = "cd /d `"$quotedWorkingDirectory`" && $Command > `"$quotedOut`" 2> `"$quotedErr`""
    $process = Start-Process -FilePath "cmd.exe" -ArgumentList @("/d", "/c", $cmdLine) -WindowStyle Hidden -PassThru
    Write-Host "$Label requested (launcher PID $($process.Id))."
}

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
Import-DotEnv -Path $EnvFile

if (-not $env:NEXT_PUBLIC_API_BASE_URL) {
    $env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:$BackendPort"
}

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    throw "Python was not found on PATH."
}

$BackendPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $BackendPython)) {
    Write-Host "Creating backend virtual environment..."
    & $Python.Source -m venv (Join-Path $BackendDir ".venv")
    $BackendPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
    Invoke-RequiredCommand `
        -Label "Installing backend requirements..." `
        -FilePath $BackendPython `
        -Arguments @("-m", "pip", "install", "-r", (Join-Path $BackendDir "requirements.txt")) `
        -WorkingDirectory $BackendDir
}

$MartPath = Join-Path $Root "datasets\marts\narrativeiq_mart.json"
if (-not $SkipData -and ($RefreshData -or -not (Test-Path -LiteralPath $MartPath))) {
    Invoke-RequiredCommand `
        -Label "Generating NarrativeIQ dataset..." `
        -FilePath $Python.Source `
        -Arguments @((Join-Path $Root "etl\pipeline.py"), "--records", "$Records") `
        -WorkingDirectory $Root
}
elseif (-not $SkipData) {
    Write-Host "Using existing NarrativeIQ mart. Pass -RefreshData to regenerate it."
}

if (-not $SkipReport) {
    Invoke-RequiredCommand `
        -Label "Generating exhibition HTML report..." `
        -FilePath $Python.Source `
        -Arguments @((Join-Path $Root "reports\generate_report.py")) `
        -WorkingDirectory $Root
}

$Npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $Npm) {
    throw "npm.cmd was not found on PATH."
}

$NextBin = Join-Path $FrontendDir "node_modules\next\dist\bin\next"
if (-not (Test-Path -LiteralPath $NextBin)) {
    Invoke-RequiredCommand `
        -Label "Installing frontend dependencies..." `
        -FilePath $Npm.Source `
        -Arguments @("install") `
        -WorkingDirectory $FrontendDir
}

$BuildId = Join-Path $FrontendDir ".next\BUILD_ID"
if (-not $SkipFrontendBuild -and ($BuildFrontend -or -not (Test-Path -LiteralPath $BuildId))) {
    Invoke-RequiredCommand `
        -Label "Building frontend production bundle..." `
        -FilePath $Npm.Source `
        -Arguments @("run", "build") `
        -WorkingDirectory $FrontendDir
}
elseif (-not $SkipFrontendBuild) {
    Write-Host "Using existing frontend production build. Pass -BuildFrontend to rebuild it."
}

Stop-Port -Port $BackendPort
Stop-Port -Port $FrontendPort
Start-Sleep -Seconds 1

$BackendCommand = "`"$BackendPython`" -m uvicorn app.main:app --host 127.0.0.1 --port $BackendPort"
$Node = Get-Command node.exe -ErrorAction SilentlyContinue
if (-not $Node) {
    throw "node.exe was not found on PATH."
}
$FrontendCommand = "`"$($Node.Source)`" node_modules/next/dist/bin/next start -H 0.0.0.0 -p $FrontendPort"

Write-Host "Starting FastAPI on http://127.0.0.1:$BackendPort"
Start-DemoProcess -Label "FastAPI" -WorkingDirectory $BackendDir -Command $BackendCommand -StdOut $BackendOut -StdErr $BackendErr

Write-Host "Starting Next.js on http://localhost:$FrontendPort"
Start-DemoProcess -Label "Next.js" -WorkingDirectory $FrontendDir -Command $FrontendCommand -StdOut $FrontendOut -StdErr $FrontendErr

$backendReady = Wait-Http -Url "http://127.0.0.1:$BackendPort/" -Name "FastAPI" -TimeoutSeconds $StartupTimeoutSeconds
$frontendReady = Wait-Http -Url "http://localhost:$FrontendPort/" -Name "Next.js" -TimeoutSeconds $StartupTimeoutSeconds

if (-not $backendReady -or -not $frontendReady) {
    Show-LogTail -Label "Backend stdout" -Path $BackendOut
    Show-LogTail -Label "Backend stderr" -Path $BackendErr
    Show-LogTail -Label "Frontend stdout" -Path $FrontendOut
    Show-LogTail -Label "Frontend stderr" -Path $FrontendErr
    throw "NarrativeIQ demo did not become ready within $StartupTimeoutSeconds seconds."
}

if ($SeedDemoBriefs) {
    Write-Host "Seeding demo live-topic briefs..."
    & $BackendPython (Join-Path $Root "scripts\seed_demo_briefs.py") --api "http://127.0.0.1:$BackendPort"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Demo brief seeding did not complete. The dashboard still runs; check the output above."
    }
}

Write-Host ""
Write-Host "NarrativeIQ exhibition demo is ready."
Write-Host "Dashboard: http://localhost:$FrontendPort"
Write-Host "API:       http://127.0.0.1:$BackendPort"
Write-Host "Docs:      http://127.0.0.1:$BackendPort/docs"
Write-Host "Report:    reports\generated\narrativeiq_exhibition_report.html"
Write-Host "Logs:      logs\backend-demo.*.log and logs\frontend-demo.*.log"

if ($env:NARRATIVEIQ_DATABASE_URL -or $env:DATABASE_URL) {
    Write-Host "PostgreSQL: configured for this demo process."
}
else {
    Write-Host "PostgreSQL: pending. Copy .env.example to .env and set NARRATIVEIQ_DATABASE_URL."
}
