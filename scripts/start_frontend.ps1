param(
    [string]$ApiBaseUrl = "http://localhost:8000"
)

$root = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $root 'frontend'

Push-Location $frontendDir
try {
    $env:VITE_API_BASE_URL = $ApiBaseUrl
    Write-Host "VITE_API_BASE_URL=$($env:VITE_API_BASE_URL)"
    npm run dev
}
finally {
    Pop-Location
}
