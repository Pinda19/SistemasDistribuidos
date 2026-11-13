# Ejecutar desde semana10: powershell -ExecutionPolicy Bypass -File .\pruebas.ps1
# Guarda en pruebas.md las respuestas REALES obtenidas con curl.exe.
$ErrorActionPreference = 'Stop'
$endpoint = 'http://localhost:8010/rpc'
$casos = @(
    @('1','Operacion 1 valida: rama con params objeto','01_crear_rama_objeto.json','result'),
    @('2','Operacion 2 valida: clonar con params lista','02_consultar_rama_lista.json','result'),
    @('3','Error de dominio: rama duplicada','03_error_dominio.json','-32000'),
    @('4','Metodo inexistente','04_metodo_inexistente.json','-32601'),
    @('5','Parametros incompletos','05_parametros_incorrectos.json','-32602'),
    @('6','JSON invalido','06_json_invalido.json','-32700'),
    @('7','Request sin jsonrpc','07_sin_jsonrpc.json','-32600'),
    @('8','Notificacion sin id','08_notificacion.json','HTTP 204'),
    @('9','Batch valido e inexistente','09_batch.json','result y -32601')
)
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('# Pruebas reales JSON-RPC 2.0 - RepoSync Semana 10')
$lines.Add('')
$lines.Add('Endpoint: `http://localhost:8010/rpc`; ejecutado desde PowerShell con `curl.exe`.')
$lines.Add('')
foreach ($c in $casos) {
    $num, $titulo, $archivo, $esperado = $c
    $ruta = Join-Path (Join-Path $PSScriptRoot 'casos') $archivo
    $res = & curl.exe -sS -i -X POST $endpoint -H 'Content-Type: application/json' --data-binary "@$ruta" 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Fallo curl en caso $num : $res" }
    $salida = ($res -join "`n").Trim()
    $lines.Add("## Caso $num - $titulo")
    $lines.Add('')
    $lines.Add("Esperado: $esperado")
    $lines.Add('')
    $lines.Add('Comando:')
    $lines.Add('```powershell')
    $lines.Add("curl.exe -i -X POST $endpoint -H 'Content-Type: application/json' --data-binary '@casos/$archivo'")
    $lines.Add('```')
    $lines.Add('Respuesta observada:')
    $lines.Add('```text')
    $lines.Add($salida)
    $lines.Add('```')
    $lines.Add('')
    Write-Host "CASO $num - $titulo" -ForegroundColor Cyan
    Write-Host $salida
    Write-Host ''
}
$lines | Set-Content -Path (Join-Path $PSScriptRoot 'pruebas.md') -Encoding UTF8
Write-Host 'Se guardaron las nueve pruebas en semana10/pruebas.md' -ForegroundColor Green
