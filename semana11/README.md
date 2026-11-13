# RepoSync · Semana 11 · Migracion a gRPC

Paquete adaptado de `semana11/laboratorio` del profesor. Se mantiene separado de `semana09/` y `semana10/`.

## En PowerShell (desde la raiz del repositorio)

```powershell
cd semana11
docker compose build
docker compose run --rm --no-deps servidor sh generar.sh
docker compose up -d
docker compose ps
```

> Primero **generar los stubs** con `generar.sh`. Si no se generan,
> `servidor_grpc.py` no puede importar `servicio_pb2`.

## Pruebas funcionales

```powershell
docker compose exec cliente python cliente_grpc.py clonar proyecto main
docker compose exec cliente python cliente_grpc.py rama proyecto demo main
docker compose exec cliente python cliente_grpc.py push proyecto demo 0 primer_cambio
docker compose exec cliente python cliente_grpc.py historial proyecto demo
docker compose exec cliente python cliente_grpc.py push proyecto demo 0 obsoleto
```

`PUSH` conserva la comprobacion de HEAD (`CONFLICTO HEAD=...`).
`PUBLICAR_AUTO` es una operacion **nueva** del laboratorio que crea una
revision en el HEAD actual sin pasar `base`. Es no idempotente, por lo que
sirve para demostrar el peligro de reintentar tras un timeout.

## Falla intermedia (probar por separado en este orden)

**1. Sin falla:**
```powershell
$env:FALLA="no"; $env:DEDUP="0"; docker compose up -d --force-recreate servidor
docker compose exec cliente python cliente_grpc.py publicar-auto proyecto main cambio
docker compose exec cliente python cliente_grpc.py clonar proyecto main
```
**2. Falla intermedia, sin reintento (maybe):**
```powershell
$env:FALLA="siempre"; $env:DEDUP="0"; docker compose up -d --force-recreate servidor
docker compose exec cliente python cliente_grpc.py publicar-auto proyecto main cambio
docker compose exec cliente python cliente_grpc.py clonar proyecto main
```
**3. Dos reintentos, sin deduplicacion (at-least-once):**
```powershell
$env:FALLA="siempre"; $env:DEDUP="0"; docker compose up -d --force-recreate servidor
docker compose exec cliente python cliente_grpc.py publicar-auto proyecto main cambio --reintentos 2
docker compose exec cliente python cliente_grpc.py clonar proyecto main
```
**4. Dos reintentos, con deduplicacion (at-most-once):**
```powershell
$env:FALLA="siempre"; $env:DEDUP="1"; docker compose up -d --force-recreate servidor
docker compose exec cliente python cliente_grpc.py publicar-auto proyecto main cambio --reintentos 2
docker compose exec cliente python cliente_grpc.py clonar proyecto main
```

Resultados **observados** en las pruebas del 13 de noviembre de 2026 (ver `observaciones.md`):
- Sin falla: `HEAD=1` y cliente OK.
- Sin reintentos: cliente `DEADLINE_EXCEEDED`, servidor ya cambio `HEAD=1`.
- Reintentos sin DEDUP: tres aplicaciones, `HEAD=3`.
- Reintentos con DEDUP: una aplicacion, `HEAD=1`, segundo intento obtiene OK cacheado.

**5. Caida intermedia:**
Terminal A, primero preparar `FALLA` y `DEMORA`, y lanzar una operacion con tiempo suficiente:
```powershell
$env:FALLA="siempre"; $env:DEMORA="10"; $env:DEDUP="0"
docker compose up -d --force-recreate servidor
docker compose exec cliente python cliente_grpc.py publicar-auto proyecto main cambio --timeout 15
```
Mientras el cliente espera, en otra terminal PowerShell dentro de `semana11`:
```powershell
docker compose kill servidor
docker compose logs servidor --tail 15
docker compose up -d servidor
docker compose exec cliente python cliente_grpc.py clonar proyecto main
```
El estado se pierde porque vive en RAM. No asumir si el servidor alcanzo a aplicar hasta revisar logs.

Limpieza de variables de la terminal (cuando termines):
```powershell
Remove-Item Env:FALLA, Env:DEMORA, Env:DEDUP -ErrorAction SilentlyContinue
```

La tabla de `observaciones.md` ya incluye los cinco experimentos y las salidas reales de la ejecución en Windows. `contrato.md` documenta la nueva operación y la actividad autónoma.
Para documentar la operacion nueva usar `contrato.md`.

**Notas importantes:** gRPC no es JSON-RPC ni usa los mismos formatos. `rpc.py`
reutiliza funciones de `dominio.py` pero, si se inicia en otro proceso,
no comparte la misma RAM. La deduplicacion tambien vive en RAM y desaparece
si el servidor se reinicia.


## Entrega / versión de los archivos

El laboratorio de Semana 11 se documentó con las cinco pruebas **reales** del 13-11-2026.
Este paquete incorpora el código `.py`, `proto/servicio.proto`, `observaciones.md` y `contrato.md`.
Los archivos generados `servicio_pb2.py` y `servicio_pb2_grpc.py` están **en el directorio de trabajo local**, porque el usuario ya ejecutó `generar.sh` dentro de Docker. Conservarlos y subirlos junto con el resto de `semana11/`; no deben editarse a mano.
No hacer `git push` hasta finalizar las semanas pendientes.
