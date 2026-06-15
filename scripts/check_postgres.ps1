param(
    [switch]$LoadWarehouse
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$EnvFile = Join-Path $Root ".env"

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

Import-DotEnv -Path $EnvFile

if (-not $env:NARRATIVEIQ_DATABASE_URL -and -not $env:DATABASE_URL) {
    Write-Host "PostgreSQL is not configured yet."
    Write-Host "Copy .env.example to .env and set NARRATIVEIQ_DATABASE_URL."
    exit 0
}

$psql_cmd = Get-Command psql -ErrorAction SilentlyContinue
$psql = if ($psql_cmd) { $psql_cmd.Source } else { $null }

if (-not $psql -and $IsWindows) {
    foreach ($ver in @("17", "16", "15", "14", "13", "12")) {
        $candidate = "C:\Program Files\PostgreSQL\$ver\bin\psql.exe"
        if (Test-Path -LiteralPath $candidate) {
            $psql = $candidate
            break
        }
    }
}

if (-not $psql) {
    Write-Host "PostgreSQL connection string exists, but psql was not found on PATH or in standard paths."
    Write-Host "Add the PostgreSQL bin folder to PATH, then re-run this script."
    exit 1
}

$DatabaseUrl = if ($env:NARRATIVEIQ_DATABASE_URL) { $env:NARRATIVEIQ_DATABASE_URL } else { $env:DATABASE_URL }

Write-Host "Checking PostgreSQL connection..."
& $psql -v ON_ERROR_STOP=1 --dbname $DatabaseUrl -c "SELECT current_database() AS database, current_user AS username;"

Write-Host "Checking NarrativeIQ warehouse loader..."
python (Join-Path $Root "etl\load_postgres.py") --dry-run

if ($LoadWarehouse) {
    Write-Host "Loading generated warehouse CSVs into PostgreSQL..."
    python (Join-Path $Root "etl\load_postgres.py")
}
else {
    Write-Host "Dry run complete. To load the warehouse, re-run with -LoadWarehouse."
}
