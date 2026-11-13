# Pruebas reales JSON-RPC 2.0 - RepoSync Semana 10

Endpoint: `http://localhost:8010/rpc`; ejecutado desde PowerShell con `curl.exe`.

## Caso 1 - Operacion 1 valida: rama con params objeto

Esperado: result

Comando:
```powershell
curl.exe -i -X POST http://localhost:8010/rpc -H 'Content-Type: application/json' --data-binary '@casos/01_crear_rama_objeto.json'
```
Respuesta observada:
```text
HTTP/1.1 200 OK
date: Fri, 13 Nov 2026 14:41:09 GMT
server: uvicorn
content-length: 85
content-type: application/json

{"jsonrpc":"2.0","result":{"repositorio":"proyecto","rama":"demo10","head":0},"id":1}
```

## Caso 2 - Operacion 2 valida: clonar con params lista

Esperado: result

Comando:
```powershell
curl.exe -i -X POST http://localhost:8010/rpc -H 'Content-Type: application/json' --data-binary '@casos/02_consultar_rama_lista.json'
```
Respuesta observada:
```text
HTTP/1.1 200 OK
date: Fri, 13 Nov 2026 14:41:10 GMT
server: uvicorn
content-length: 85
content-type: application/json

{"jsonrpc":"2.0","result":{"repositorio":"proyecto","rama":"demo10","head":0},"id":2}
```

## Caso 3 - Error de dominio: rama duplicada

Esperado: -32000

Comando:
```powershell
curl.exe -i -X POST http://localhost:8010/rpc -H 'Content-Type: application/json' --data-binary '@casos/03_error_dominio.json'
```
Respuesta observada:
```text
HTTP/1.1 200 OK
date: Fri, 13 Nov 2026 14:41:10 GMT
server: uvicorn
content-length: 99
content-type: application/json

{"jsonrpc":"2.0","error":{"code":-32000,"message":"Error del dominio","data":"RAMA_EXISTE"},"id":3}
```

## Caso 4 - Metodo inexistente

Esperado: -32601

Comando:
```powershell
curl.exe -i -X POST http://localhost:8010/rpc -H 'Content-Type: application/json' --data-binary '@casos/04_metodo_inexistente.json'
```
Respuesta observada:
```text
HTTP/1.1 200 OK
date: Fri, 13 Nov 2026 14:41:10 GMT
server: uvicorn
content-length: 77
content-type: application/json

{"jsonrpc":"2.0","error":{"code":-32601,"message":"Method not found"},"id":4}
```

## Caso 5 - Parametros incompletos

Esperado: -32602

Comando:
```powershell
curl.exe -i -X POST http://localhost:8010/rpc -H 'Content-Type: application/json' --data-binary '@casos/05_parametros_incorrectos.json'
```
Respuesta observada:
```text
HTTP/1.1 200 OK
date: Fri, 13 Nov 2026 14:41:10 GMT
server: uvicorn
content-length: 140
content-type: application/json

{"jsonrpc":"2.0","error":{"code":-32602,"message":"Invalid params","data":"rama() missing 1 required positional argument: 'origen'"},"id":5}
```

## Caso 6 - JSON invalido

Esperado: -32700

Comando:
```powershell
curl.exe -i -X POST http://localhost:8010/rpc -H 'Content-Type: application/json' --data-binary '@casos/06_json_invalido.json'
```
Respuesta observada:
```text
HTTP/1.1 200 OK
date: Fri, 13 Nov 2026 14:41:10 GMT
server: uvicorn
content-length: 75
content-type: application/json

{"jsonrpc":"2.0","error":{"code":-32700,"message":"Parse error"},"id":null}
```

## Caso 7 - Request sin jsonrpc

Esperado: -32600

Comando:
```powershell
curl.exe -i -X POST http://localhost:8010/rpc -H 'Content-Type: application/json' --data-binary '@casos/07_sin_jsonrpc.json'
```
Respuesta observada:
```text
HTTP/1.1 200 OK
date: Fri, 13 Nov 2026 14:41:10 GMT
server: uvicorn
content-length: 79
content-type: application/json

{"jsonrpc":"2.0","error":{"code":-32600,"message":"Invalid Request"},"id":null}
```

## Caso 8 - Notificacion sin id

Esperado: HTTP 204

Comando:
```powershell
curl.exe -i -X POST http://localhost:8010/rpc -H 'Content-Type: application/json' --data-binary '@casos/08_notificacion.json'
```
Respuesta observada:
```text
HTTP/1.1 204 No Content
date: Fri, 13 Nov 2026 14:41:10 GMT
server: uvicorn
```

## Caso 9 - Batch valido e inexistente

Esperado: result y -32601

Comando:
```powershell
curl.exe -i -X POST http://localhost:8010/rpc -H 'Content-Type: application/json' --data-binary '@casos/09_batch.json'
```
Respuesta observada:
```text
HTTP/1.1 200 OK
date: Fri, 13 Nov 2026 14:41:10 GMT
server: uvicorn
content-length: 164
content-type: application/json

[{"jsonrpc":"2.0","result":{"repositorio":"proyecto","rama":"main","head":0},"id":9},{"jsonrpc":"2.0","error":{"code":-32601,"message":"Method not found"},"id":10}]
```

