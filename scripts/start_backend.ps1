param(
    [string]$DatabaseUrl
)

$root = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $root 'backend'
$defaultDb = "sqlite+pysqlite:///${root.Replace('\', '/')}/db/dev.db"

if (-not $DatabaseUrl) {
    $DatabaseUrl = $defaultDb
}

Push-Location $backendDir
try {
    $env:DATABASE_URL = $DatabaseUrl
    Write-Host "DATABASE_URL=$($env:DATABASE_URL)"
    $pythonExe = Join-Path '.venv' 'Scripts/python.exe'
    if (Test-Path $pythonExe) {
        Write-Host 'Applying database migrations (alembic upgrade head)...'
        & $pythonExe '-m' 'alembic' 'upgrade' 'head'
    } else {
        Write-Warning 'Virtual environment not found for running migrations.'
    }
    $uvicorn = Join-Path '.venv' 'Scripts/uvicorn.exe'
    if (-not (Test-Path $uvicorn)) {
        throw "Uvicorn not found at $uvicorn. Ensure the virtual environment is created."
    }
    & $uvicorn 'app.main:app' --reload --host 0.0.0.0 --port 8000
}
finally {
    Pop-Location
}
