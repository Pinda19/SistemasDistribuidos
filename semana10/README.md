# Semana 10 — RepoSync / JSON-RPC 2.0

Adaptación del esqueleto oficial del profesor `rpc.py` al dominio de RepoSync.
Dos métodos: `rama` (RAMA) y `clonar` (CLONAR). Estado en RAM del proceso RPC.
**No es una conexión al TCP de Semana 9:** la guía pide un prototipo con estado en el proceso FastAPI. No modifica `semana09/` ni `semana07/`.

## Iniciar desde PowerShell

```powershell
cd C:\Users\Thomas\Desktop\SistemasDistribuidos\semana10
docker compose up -d --build
docker compose ps
```

La API está en http://localhost:8010/rpc y el OpenAPI general de FastAPI en http://localhost:8010/docs. El endpoint `/rpc` acepta cuerpos JSON-RPC, NO las operaciones de inventario del ejemplo oficial.

## Probar los 9 casos en PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File .\pruebas.ps1
```

El script usa `curl.exe` con archivos `casos/*.json` para evitar problemas de comillas en PowerShell. Escribe **respuestas reales** en `pruebas.md`. Para repetir desde cero:

```powershell
docker compose restart rpc
powershell -ExecutionPolicy Bypass -File .\pruebas.ps1
```

## Operaciones

| Método | Parámetros | Resultado |
|---|---|---|
| `rama` | `repo`, `nueva`, `origen` | Crea una rama a partir del HEAD del origen |
| `clonar` | `repo`, `rama` | Devuelve el HEAD (no descarga archivos) |

`proyecto` y `main` existen desde el arranque, `HEAD=0`. El estado se pierde al reiniciar el proceso. Dos métodos replican las operaciones `RAMA` y `CLONAR` de Semana 9; no se agregó otra dependencia más allá de FastAPI/Uvicorn ya usados en Semana 7.

## Entregables guía autónoma

* `rpc.py` con dominio RepoSync y contrato JSON-RPC 2.0
* `pruebas.md` con nueve pruebas **ejecutadas** de `curl.exe`
* `cuadro_comparativo.md` con diez criterios para RMI, CORBA, DCOM y JSON-RPC (revisar y personalizar)
* `bitacora_<apellido>.md` individual, basado en `bitacora_plantilla.md`; registrar solo horas/trabajo real

## Puerto y limpieza

El servicio se publica en `localhost:8010` y tiene red Docker propia `sd10_net`; no interfiere con `semana09`, que puede permanecer activo.

```powershell
docker compose down
```
