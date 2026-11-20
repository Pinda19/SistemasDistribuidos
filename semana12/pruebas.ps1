# Ejecutar desde semana12: powershell -ExecutionPolicy Bypass -File .\pruebas.ps1
# Reinicia SOLO los contenedores de esta semana; las revisiones son de laboratorio.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force evidencias | Out-Null
$script:registro = Join-Path $PSScriptRoot 'evidencias\docker.txt'
Set-Content -Encoding UTF8 $script:registro "RepoSync Semana 12 - $(Get-Date -Format o)"

function Dc {
    param([string[]]$Parametros, [int]$Esperado = 0)
    "`n> docker compose $($Parametros -join ' ')" | Tee-Object -FilePath $script:registro -Append | Write-Host
    $preferencia = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & docker compose @Parametros 2>&1 | Tee-Object -FilePath $script:registro -Append | Write-Host
    $codigo = $LASTEXITCODE
    $ErrorActionPreference = $preferencia
    if ($codigo -ne $Esperado) { throw "Docker devolvio $codigo; esperado $Esperado" }
}
function Esperar-Servicio {
    $ErrorActionPreference = 'Continue'
    for ($i = 0; $i -lt 30; $i++) {
        & docker compose exec -T cliente python cliente_pyro.py clonar proyecto main *> $null
        if ($LASTEXITCODE -eq 0) { return }
        Start-Sleep -Seconds 1
    }
    throw 'El servicio no estuvo listo en 30 segundos; revisar docker compose logs'
}
function Esperar-Log {
    param([string]$Archivo, [string]$Texto)
    for ($i = 0; $i -lt 20; $i++) {
        if ((Test-Path $Archivo) -and (Select-String -Path $Archivo -SimpleMatch $Texto -Quiet)) { return }
        Start-Sleep -Seconds 1
    }
    throw "No aparecio '$Texto' en $Archivo"
}
$variables = @('MODO', 'POR_VALOR', 'REREGISTRO')
$anteriores = @{}
foreach ($nombre in $variables) { $anteriores[$nombre] = [Environment]::GetEnvironmentVariable($nombre, 'Process') }
try {
    $env:MODO = 'single'; $env:POR_VALOR = '0'; $env:REREGISTRO = '0'
    Dc -Parametros @('up', '-d', '--build', '--force-recreate')
    Esperar-Servicio
    Dc -Parametros @('ps')
    Dc -Parametros @('exec', '-T', 'cliente', 'python', 'cliente_pyro.py', 'uri')
    Dc -Parametros @('exec', '-T', 'cliente', 'python', 'verificar.py', 'base')
    Dc -Parametros @('exec', '-T', 'cliente', 'python', 'verificar.py', 'single')
    $env:POR_VALOR = '1'
    Dc -Parametros @('up', '-d', '--force-recreate', 'servidor'); Esperar-Servicio
    Dc -Parametros @('exec', '-T', 'cliente', 'python', 'verificar.py', 'valor')
    $env:POR_VALOR = '0'; $env:MODO = 'session'
    Dc -Parametros @('up', '-d', '--force-recreate', 'servidor'); Esperar-Servicio
    Dc -Parametros @('exec', '-T', 'cliente', 'python', 'verificar.py', 'session')
    $env:MODO = 'single'
    Dc -Parametros @('up', '-d', '--force-recreate', 'servidor'); Esperar-Servicio
    Dc -Parametros @('exec', '-T', 'cliente', 'python', 'cliente_pyro.py', 'push', 'proyecto', 'main', '0', 'antes_caida')
    Remove-Item evidencias\DETENER, evidencias\vigilar.txt, evidencias\cambio.txt -ErrorAction SilentlyContinue
    Dc -Parametros @('exec', '-T', '-d', 'cliente', 'sh', '-c', 'python -u cliente_pyro.py vigilar --detener /evidencias/DETENER > /evidencias/vigilar.txt 2>&1')
    Dc -Parametros @('exec', '-T', '-d', 'cliente', 'sh', '-c', 'python -u cliente_pyro.py cambio proyecto main Thomas temporal.txt --esperar 6 > /evidencias/cambio.txt 2>&1')
    Esperar-Log -Archivo 'evidencias\vigilar.txt' -Texto 'ok '
    Esperar-Log -Archivo 'evidencias\cambio.txt' -Texto 'estado remoto'
    Dc -Parametros @('kill', 'servidor')
    Esperar-Log -Archivo 'evidencias\vigilar.txt' -Texto 'FALLA'
    Dc -Parametros @('exec', '-T', 'cliente', 'python', 'cliente_pyro.py', 'clonar', 'proyecto', 'main') -Esperado 5
    Dc -Parametros @('start', 'servidor'); Esperar-Servicio
    Start-Sleep -Seconds 2
    Dc -Parametros @('exec', '-T', 'cliente', 'python', 'cliente_pyro.py', 'clonar', 'proyecto', 'main')
    Esperar-Log -Archivo 'evidencias\cambio.txt' -Texto 'ERROR'
    Dc -Parametros @('kill', 'nombres')
    Start-Sleep -Seconds 2
    Dc -Parametros @('exec', '-T', 'cliente', 'python', 'cliente_pyro.py', 'clonar', 'proyecto', 'main') -Esperado 2
    Dc -Parametros @('start', 'nombres')
    Start-Sleep -Seconds 2
    Dc -Parametros @('exec', '-T', 'cliente', 'python', 'cliente_pyro.py', 'clonar', 'proyecto', 'main') -Esperado 2
    Dc -Parametros @('restart', 'servidor'); Esperar-Servicio
    Dc -Parametros @('exec', '-T', 'cliente', 'python', 'cliente_pyro.py', 'uri')
    New-Item -ItemType File -Force evidencias\DETENER | Out-Null
    Start-Sleep -Seconds 2
    Get-Content evidencias\vigilar.txt, evidencias\cambio.txt | Tee-Object -FilePath $script:registro -Append | Write-Host
    # Recuperacion automatica del registro, sin reiniciar el servidor tras volver nombres.
    $env:REREGISTRO = '5'
    Dc -Parametros @('up', '-d', '--force-recreate', 'servidor'); Esperar-Servicio
    Dc -Parametros @('kill', 'nombres')
    Dc -Parametros @('start', 'nombres'); Esperar-Servicio
    Dc -Parametros @('exec', '-T', 'cliente', 'python', 'cliente_pyro.py', 'uri')
    # Restablecer la configuracion base del taller.
    $env:REREGISTRO = '0'
    Dc -Parametros @('up', '-d', '--force-recreate', 'servidor'); Esperar-Servicio
    Dc -Parametros @('logs', '--no-color', 'servidor', 'nombres')
    'PRUEBAS TERMINADAS. Evidencia: semana12/evidencias/docker.txt' | Tee-Object -FilePath $script:registro -Append | Write-Host
} finally {
    New-Item -ItemType File -Force evidencias\DETENER | Out-Null
    foreach ($nombre in $variables) { [Environment]::SetEnvironmentVariable($nombre, $anteriores[$nombre], 'Process') }
}
