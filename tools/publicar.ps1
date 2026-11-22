param(
    [switch]$SinPruebas,
    [switch]$SinCompilar
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

$version = (Select-String -Path "zaynix\core\config.py" -Pattern 'VERSION = "(.+)"').Matches[0].Groups[1].Value
Write-Host "Zaynix $version" -ForegroundColor Cyan

$python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
$flet = if (Test-Path ".venv\Scripts\flet.exe") { ".venv\Scripts\flet.exe" } else { "flet" }

if (-not $SinPruebas) {
    Write-Host "1/4 Pruebas" -ForegroundColor Cyan
    & $python -m pytest -m "not red"
    if ($LASTEXITCODE -ne 0) { throw "Las pruebas fallaron." }
}

if (-not $SinCompilar) {
    Write-Host "2/4 Compilando la app" -ForegroundColor Cyan
    & $flet build windows --yes --build-version $version
    if ($LASTEXITCODE -ne 0) { throw "flet build falló." }
}

& $python tools\recopilar_licencias.py
if ($LASTEXITCODE -ne 0) { throw "Faltan licencias de terceros." }

Write-Host "3/4 Creando el instalador" -ForegroundColor Cyan
$iscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "Inno Setup no está instalado (winget install JRSoftware.InnoSetup)." }
& $iscc "/DVersion=$version" "installer\zaynix.iss"
if ($LASTEXITCODE -ne 0) { throw "Inno Setup falló." }

Write-Host "4/4 Calculando la firma SHA-256" -ForegroundColor Cyan
$instalador = "dist\ZaynixSetup-$version.exe"
$hash = (Get-FileHash $instalador -Algorithm SHA256).Hash.ToLower()
"$hash  ZaynixSetup-$version.exe" | Set-Content "$instalador.sha256" -Encoding ascii

Write-Host ""
Write-Host "Listo: $instalador" -ForegroundColor Green
Write-Host "SHA-256: $hash"
