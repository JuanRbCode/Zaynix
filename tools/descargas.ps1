param([string]$Repo = "JuanRbCode/Zaynix")

$ErrorActionPreference = "Stop"
$historial = Join-Path $env:LOCALAPPDATA "ZaynixPanel\descargas.csv"

$respuesta = gh api "repos/$Repo/releases?per_page=100"
if ($LASTEXITCODE -ne 0) { throw "No se pudo consultar GitHub." }
$lanzamientos = @(($respuesta -join "`n") | ConvertFrom-Json | ForEach-Object { $_ })

$filas = @(foreach ($l in $lanzamientos) {
    foreach ($a in $l.assets) {
        if ($a.name -like "ZaynixSetup*.exe") {
            [pscustomobject]@{
                Version   = $l.tag_name
                Publicada = ([string]$l.published_at).Substring(0, 10)
                Descargas = [int]$a.download_count
            }
        }
    }
})
$total = [int]($filas | Measure-Object Descargas -Sum).Sum

$hoy = Get-Date -Format "yyyy-MM-dd"
$registro = @()
if (Test-Path $historial) { $registro = @(Import-Csv $historial) }
$previo = $registro | Where-Object { $_.Fecha -lt $hoy } | Select-Object -Last 1
$registro = @($registro | Where-Object { $_.Fecha -ne $hoy }) + [pscustomobject]@{ Fecha = $hoy; Total = $total }
New-Item -ItemType Directory -Force (Split-Path $historial) | Out-Null
$registro | Export-Csv $historial -NoTypeInformation -Encoding utf8

$filas | Format-Table -AutoSize
Write-Host "Total: $total descargas" -ForegroundColor Cyan
if ($previo) { Write-Host ("Desde {0}: {1:+0;-0;0}" -f $previo.Fecha, ($total - [int]$previo.Total)) }
