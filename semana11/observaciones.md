# Observaciones · Semana 11 · RepoSync / gRPC

**Laboratorio N.º 4: migración a gRPC y falla intermedia**  
**Fecha de las pruebas:** 13 de noviembre de 2026  
**Proyecto:** RepoSync, tema 04 — Control de versiones distribuido  
**Integrante:** Thomas Pinda 
**Equipo: ** Thomas Pinda

## 1. Arquitectura, dominio y contrato

El servicio usa `proto/servicio.proto` con `package reposync.v1` y cinco RPC: `Clonar`, `Rama`, `Push`, `Historial` y `PublicarAuto`. `dominio.py` contiene el estado de repositorios y ramas en RAM, las reglas y un `threading.Lock`. No importa detalles de JSON, HTTP ni gRPC. `servidor_grpc.py` aplica la lógica del dominio y devuelve estados gRPC. `cliente_grpc.py` construye solicitudes Protobuf y usa un deadline por intento. El mismo `id_solicitud` se conserva entre reintentos de una modificación.

- Consultas: `Clonar` y `Historial`, sin modificar RAM.
- Modificaciones: `Rama`, `Push` y `PublicarAuto`, todas con `id_solicitud`.
- `Push` exige la revisión `base` actual y rechaza conflictos.
- `PublicarAuto` es la operación nueva del laboratorio: registra un commit sobre el HEAD actual sin exigir `base`. Permite observar el problema de ejecutar repetidamente una solicitud no idempotente.
- El servidor gRPC y el cliente se ejecutaron en **contenedores Docker separados** (`sd11_servidor` y `sd11_cliente`) y se comunicaron por el puerto **50051**.

## 2. Compilación y generación de stubs

Comandos ejecutados desde `semana11/`:

```powershell
docker compose build
docker compose run --rm --no-deps servidor sh generar.sh
docker compose up -d
docker compose ps
```

**Resultados observados:** imagen `sd_grpc_reposync:semana11` construida correctamente; `generar.sh` produjo `servicio_pb2.py` (3610 bytes) y `servicio_pb2_grpc.py` (10190 bytes); contenedores `sd11_servidor` y `sd11_cliente` en estado `Up`; puerto `0.0.0.0:50051->50051/tcp` publicado.

| Elemento generado | Papel |
|---|---|
| `RepoSyncStub` | Stub del cliente: expone las llamadas remotas como métodos |
| `RepoSyncServicer` | Clase base que implementa el servidor (*skeleton*) |
| `add_RepoSyncServicer_to_server` | Registra el despachador de métodos RPC |
| `SerializeToString` / `FromString` | Serialización y deserialización (*marshalling*) Protobuf, concepto de la Semana 9 |

Los stubs se generaron **en el computador del integrante** y deben conservarse al guardar el trabajo en Git.

## 3. Pruebas funcionales del dominio

Todos los comandos siguientes se ejecutaron correctamente tras levantar los contenedores:

```powershell
docker compose exec cliente python cliente_grpc.py clonar proyecto main
docker compose exec cliente python cliente_grpc.py rama proyecto demo main
docker compose exec cliente python cliente_grpc.py push proyecto demo 0 primer_cambio
docker compose exec cliente python cliente_grpc.py historial proyecto demo
docker compose exec cliente python cliente_grpc.py push proyecto demo 0 segundo_cambio
```

| Operación | Salida real |
|---|---|
| `Clonar proyecto/main` | `OK proyecto/main HEAD=0` |
| `Rama proyecto/demo desde main` | `OK proyecto/demo HEAD=0` |
| `Push primer_cambio` con base 0 | `OK proyecto/demo HEAD=1` |
| `Historial proyecto/demo` | `OK 1:primer_cambio | 0:inicio` |
| Segundo `Push`, todavía con base 0 | `FAILED_PRECONDITION: CONFLICTO HEAD=1`; `solicitud rechazada sin reintento` |

El último resultado **no es una caída**: el servidor preservó la regla del dominio que evita escribir sobre un HEAD diferente del esperado.

## 4. Comparación de errores JSON-RPC y gRPC

| Caso | Semana 10: JSON-RPC | Semana 11: gRPC | Evidencia en esta sesión |
|---|---|---|---|
| Método inexistente | `-32601` | `UNIMPLEMENTED` | Equivalencia teórica; no se llamó a un método inexistente en gRPC |
| Parámetros inválidos | `-32602` | `INVALID_ARGUMENT` | Implementado; no se ejecutó un caso específico de parámetros inválidos |
| Conflicto del dominio | `-32000` | `FAILED_PRECONDITION` | **Observado:** `CONFLICTO HEAD=1` |
| Servidor interrumpido | Fallo de conexión | `UNAVAILABLE` | **Observado:** `Socket closed` en prueba 5 |
| Respuesta más lenta que el deadline | Timeout | `DEADLINE_EXCEEDED` | **Observado:** pruebas 2 y 3 y primer intento de prueba 4 |

## 5. Cinco experimentos de falla intermedia

Cada experimento recreó el contenedor del servidor antes de empezar, por lo que `main` comenzó con `HEAD=0`. Los comandos conservaron las variables de entorno en PowerShell y utilizaron `--force-recreate servidor` para aplicar las configuraciones; el cliente tenía un timeout predeterminado de **2 segundos**. En las pruebas 2, 3 y 4, el servidor demoró la respuesta **3 segundos después de aplicar la modificación**.

| N.º | Configuración / ejecución | Respuesta real del cliente | Consulta posterior | Interpretación |
|---|---|---|---|---|
| **1. Normal** | `FALLA=no`, `DEDUP=0`; una llamada a `publicar-auto` | `OK proyecto/main HEAD=1` | `HEAD=1` | Una ejecución confirmada |
| **2. Maybe** | `FALLA=siempre`, sin reintentos | `DEADLINE_EXCEEDED`; estado `DESCONOCIDO` | `HEAD=1` | La operación se ejecutó aunque el cliente creyó que pudo fallar |
| **3. At-least-once** | `FALLA=siempre`, `DEDUP=0`, `--reintentos 2` | Tres `DEADLINE_EXCEEDED`; estado `DESCONOCIDO` | `HEAD=3` | La misma solicitud se aplicó **tres veces** |
| **4. At-most-once** | `FALLA=siempre`, `DEDUP=1`, `--reintentos 2` | Intento 1: `DEADLINE_EXCEEDED`; intento 2: `OK HEAD=1` | `HEAD=1` | La segunda petición reutilizó el resultado cacheado, sin reaplicar |
| **5. Caída intermedia** | `FALLA=siempre`, `DEMORA=10`, `DEDUP=0`, `--timeout 15`; proceso matado tras ~3 s | `UNAVAILABLE: Socket closed`; estado `DESCONOCIDO` | Tras recrear el servidor: `HEAD=0` | El cambio se aplicó en RAM, pero se perdió al terminar el proceso |

### 5.1. Prueba 1 — Sin falla

```text
[cliente] intento 1, id_solicitud=1099e78a timeout=2s
[cliente]   OK proyecto/main HEAD=1
[cliente] intento 1, id_solicitud=- timeout=2s
[cliente]   OK proyecto/main HEAD=1
```

### 5.2. Prueba 2 — Maybe

```text
[cliente] intento 1, id_solicitud=c557644a timeout=2s
[cliente]   DEADLINE_EXCEEDED: Deadline Exceeded
[cliente] estado de ejecucion DESCONOCIDO si hubo fallo intermedio
[cliente] intento 1, id_solicitud=- timeout=2s
[cliente]   OK proyecto/main HEAD=1
```

**Lectura:** el cliente conoce el fallo de recepción, no el estado de ejecución del procedimiento remoto.

### 5.3. Prueba 3 — At-least-once, sin deduplicación

```text
[cliente] intento 1, id_solicitud=9d4febe5 timeout=2s
[cliente]   DEADLINE_EXCEEDED: Deadline Exceeded
[cliente] intento 2, id_solicitud=9d4febe5 timeout=2s
[cliente]   DEADLINE_EXCEEDED: Deadline Exceeded
[cliente] intento 3, id_solicitud=9d4febe5 timeout=2s
[cliente]   DEADLINE_EXCEEDED: Deadline Exceeded
[cliente] estado de ejecucion DESCONOCIDO si hubo fallo intermedio
[cliente] intento 1, id_solicitud=- timeout=2s
[cliente]   OK proyecto/main HEAD=3
```

Registro del servidor:

```text
[servidor] RepoSync gRPC puerto=50051 FALLA=siempre DEMORA=3.0 DEDUP=0
[servidor] PublicarAuto id=9d4febe5 -> {'repositorio': 'proyecto', 'rama': 'main', 'head': 1}
[servidor] FALLA=siempre, YA aplicado, demoro respuesta 3 s
[servidor] PublicarAuto id=9d4febe5 -> {'repositorio': 'proyecto', 'rama': 'main', 'head': 2}
[servidor] FALLA=siempre, YA aplicado, demoro respuesta 3 s
[servidor] PublicarAuto id=9d4febe5 -> {'repositorio': 'proyecto', 'rama': 'main', 'head': 3}
[servidor] FALLA=siempre, YA aplicado, demoro respuesta 3 s
[servidor] Clonar proyecto/main -> HEAD=3
```

### 5.4. Prueba 4 — At-most-once, con deduplicación

```text
[cliente] intento 1, id_solicitud=ff6c8e1b timeout=2s
[cliente]   DEADLINE_EXCEEDED: Deadline Exceeded
[cliente] intento 2, id_solicitud=ff6c8e1b timeout=2s
[cliente]   OK proyecto/main HEAD=1
[cliente] intento 1, id_solicitud=- timeout=2s
[cliente]   OK proyecto/main HEAD=1
```

Registro del servidor:

```text
[servidor] RepoSync gRPC puerto=50051 FALLA=siempre DEMORA=3.0 DEDUP=1
[servidor] PublicarAuto id=ff6c8e1b -> {'repositorio': 'proyecto', 'rama': 'main', 'head': 1}
[servidor] FALLA=siempre, YA aplicado, demoro respuesta 3 s
[servidor] PublicarAuto id=ff6c8e1b repetido, resultado cacheado SIN aplicar de nuevo
[servidor] Clonar proyecto/main -> HEAD=1
```

**Lectura:** el ID se genera una sola vez y el servidor guarda el resultado antes de responder. Reintentar la misma solicitud no produce otro commit **mientras el proceso y su caché sobrevivan**.

### 5.5. Prueba 5 — Matar al servidor durante una llamada

Secuencia ejecutada con un trabajo en segundo plano de PowerShell (`Start-Job`) para evitar abrir otra terminal:

```powershell
$env:FALLA="siempre"; $env:DEDUP="0"; $env:DEMORA="10"
docker compose up -d --force-recreate servidor
$job = Start-Job -ArgumentList (Get-Location).Path -ScriptBlock {
    param($ruta)
    Set-Location $ruta
    docker compose exec -T cliente python cliente_grpc.py publicar-auto proyecto main cambio_final --timeout 15
}
Start-Sleep -Seconds 3
docker compose kill servidor
Receive-Job $job -Wait
docker compose logs servidor --tail 12
docker compose up -d --force-recreate servidor
docker compose exec cliente python cliente_grpc.py clonar proyecto main
```

Salida real del cliente:

```text
[cliente] intento 1, id_solicitud=1e1ec108 timeout=15s
[cliente]   UNAVAILABLE: Socket closed
[cliente] estado de ejecucion DESCONOCIDO si hubo fallo intermedio
[cliente] intento 1, id_solicitud=- timeout=2s
[cliente]   OK proyecto/main HEAD=0
```

Registro real antes de la interrupción:

```text
[servidor] RepoSync gRPC puerto=50051 FALLA=siempre DEMORA=10.0 DEDUP=0
[servidor] PublicarAuto id=1e1ec108 -> {'repositorio': 'proyecto', 'rama': 'main', 'head': 1}
[servidor] FALLA=siempre, YA aplicado, demoro respuesta 10 s
```

**Lectura:** el registro prueba que el cambio llegó a aplicarse (`HEAD=1`). La conexión se cortó antes de que se enviara la respuesta. Al recrear el servidor, el repositorio se inicializó otra vez desde RAM (`HEAD=0`). La deduplicación en memoria tampoco garantizaría durabilidad frente a este reinicio.

## 6. Conclusiones

1. La migración a gRPC permitió conservar las reglas de negocio de RepoSync en `dominio.py`, separadas del transporte.
2. Protocol Buffers y los stubs reemplazaron la serialización y el despacho manual del protocolo TCP de la Semana 9; gRPC aporta además deadlines, estados de error y llamadas tipadas.
3. **Maybe:** con una respuesta perdida, el cliente no puede determinar por sí solo si la operación fue aplicada.
4. **At-least-once:** reintentar sin deduplicar ejecutó tres veces una modificación no idempotente: `HEAD=3`.
5. **At-most-once:** conservar `id_solicitud` y cachear el resultado evitó duplicados durante la vida del servidor: `HEAD=1`.
6. La simulación de caída mostró que **at-most-once no equivale a persistencia ni a exactamente una vez**. Cuando el servidor se reinicia, el estado y la caché en RAM desaparecen.
7. Para robustecer RepoSync sería necesario persistir commits y registros de deduplicación en almacenamiento duradero, además de definir recuperación frente a reinicios.
