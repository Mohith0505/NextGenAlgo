param(
    [string],
    [string]
)

 = Split-Path -Parent 
 = Join-Path  'backend'

if () {
     = 
}
if () {
     = 
}

Push-Location 
try {
     = Join-Path '.venv' 'Scripts/celery.exe'
    if (-not (Test-Path )) {
        throw "Celery executable not found at . Ensure dependencies are installed."
    }
    &  '-A' 'app.celery_app' 'worker' '-l' 'info'
}
finally {
    Pop-Location
}
