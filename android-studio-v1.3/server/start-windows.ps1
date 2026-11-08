$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (!(Test-Path '.venv/Scripts/python.exe')) {
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Instala Python 3.12 de 64 bits.' }
}
& .venv/Scripts/python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación de dependencias.' }
if (!(Test-Path 'server-token.txt')) {
    $secret = & .venv/Scripts/python.exe -c 'import secrets; print(secrets.token_urlsafe(32))'
    Set-Content -NoNewline -Path server-token.txt -Value $secret
}
$env:STUDIO_TOKEN = (Get-Content -Raw server-token.txt).Trim()
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollama) {
    Write-Host 'Preparando el modelo de texto local. La primera descarga puede tardar.'
    if (!$env:STUDIO_TEXT_MODEL) { $env:STUDIO_TEXT_MODEL = 'qwen3:4b' }
    & ollama pull $env:STUDIO_TEXT_MODEL
    if ($LASTEXITCODE -ne 0) { Write-Warning 'No se pudo preparar el modelo. Inicia Ollama y repite ollama pull qwen3:4b.' }
} else {
    Write-Warning 'Instala Ollama desde https://ollama.com/download e inicia su servicio. Después ejecuta ollama pull qwen3:4b.'
}
Write-Host 'Token para pegar en el APK (no lo compartas):'
Write-Host $env:STUDIO_TOKEN
Write-Host 'Direcciones locales: usa http://IP-DE-ESTA-PC:8790 en el APK'
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' } | Select-Object IPAddress
Write-Host 'La primera generación descarga los modelos. CPU puede ser muy lenta.'
& .venv/Scripts/python.exe -m uvicorn server:app --host 0.0.0.0 --port 8790 --workers 1
