# Contrato de servicio · RepoSync · Semana 11

**Protocolo:** gRPC / Protocol Buffers (`proto3`)  
**Paquete:** `reposync.v1`  
**Servicio:** `RepoSync`  
**Contrato fuente:** [`proto/servicio.proto`](proto/servicio.proto)  
**Fecha de validación:** 13 de noviembre de 2026

## 1. Separación entre dominio y comunicación

El estado y las reglas de negocio se mantienen en `dominio.py`, sin importar JSON, HTTP ni gRPC. Tanto `rpc.py` (JSON-RPC) como `servidor_grpc.py` pueden importar sus funciones. **No comparten automáticamente la misma RAM cuando se ejecutan en procesos distintos.** `threading.Lock` evita modificaciones simultáneas inconsistentes dentro de un proceso.

## 2. Operaciones y reglas

| RPC | Función en `dominio.py` | Entrada | Respuesta | Modifica RAM | Idempotencia |
|---|---|---|---|---|---|
| `Clonar` | `clonar(repo, rama)` | Repositorio y rama | `EstadoRamaRespuesta` | No | Sí, como consulta |
| `Rama` | `rama(repo, nueva, origen)` | ID, repositorio, nueva rama y origen | `EstadoRamaRespuesta` | Sí | No como repetición literal: devuelve `RAMA_EXISTE` |
| `Push` | `push(repo, rama, base, mensaje)` | ID, repo, rama, revisión base y mensaje | `EstadoRamaRespuesta` | Sí | Protegido contra duplicado por comparación de HEAD; no necesariamente misma respuesta |
| `Historial` | `historial(repo, rama)` | Repositorio y rama | `HistorialRespuesta` | No | Sí, como consulta |
| **`PublicarAuto`** | **`publicar_auto(repo, rama, mensaje)`** | **ID, repo, rama y mensaje** | `EstadoRamaRespuesta` | **Sí** | **No; cada ejecución crea un commit** |

**Nueva operación para la actividad autónoma:** `PublicarAuto`. El objetivo es estudiar las semánticas de fallos sin eliminar la comprobación de revisión que implementa `Push`.

## 3. Mensajes Protobuf y numeración

| Mensaje | Campos (número = nombre: tipo) |
|---|---|
| `ClonarSolicitud` | `1 = repo: string`, `2 = rama: string` |
| `RamaSolicitud` | `1 = id_solicitud: string`, `2 = repo: string`, `3 = nueva: string`, `4 = origen: string` |
| `PushSolicitud` | `1 = id_solicitud: string`, `2 = repo: string`, `3 = rama: string`, `4 = base: int64`, `5 = mensaje: string` |
| `HistorialSolicitud` | `1 = repo: string`, `2 = rama: string` |
| `PublicarAutoSolicitud` | `1 = id_solicitud: string`, `2 = repo: string`, `3 = rama: string`, `4 = mensaje: string` |
| `EstadoRamaRespuesta` | `1 = repositorio: string`, `2 = rama: string`, `3 = head: int64` |
| `Revision` | `1 = numero: int64`, `2 = mensaje: string` |
| `HistorialRespuesta` | `1 = revisiones: repeated Revision` |

Los campos `id_solicitud` son obligatorios **por validación del servidor**, no por `proto3` (donde un `string` omitido llega como texto vacío). La numeración de campos publicada no se reutiliza en versiones posteriores.

## 4. Condiciones y errores

| Situación | Estado gRPC | Significado |
|---|---|---|
| Faltan `id_solicitud` o datos obligatorios; valores inválidos | `INVALID_ARGUMENT` | Petición mal formada a nivel de parámetros |
| La rama o repo no existen; rama duplicada; conflicto de revisión HEAD | `FAILED_PRECONDITION` | Regla de negocio impide aplicar la operación |
| Método RPC inexistente | `UNIMPLEMENTED` | Método no registrado en el contrato expuesto |
| Respuesta no recibida antes del deadline | `DEADLINE_EXCEEDED` | No prueba que no se haya aplicado |
| Servidor caído o conexión interrumpida | `UNAVAILABLE` | Estado final de la modificación puede ser desconocido |

En el laboratorio se observaron directamente `FAILED_PRECONDITION`, `DEADLINE_EXCEEDED` y `UNAVAILABLE`; las otras equivalencias se documentan a partir de la interfaz y el código.

## 5. Reintentos, idempotencia y deduplicación

- El cliente genera un `id_solicitud` una única vez por **solicitud lógica**, y lo reutiliza en todos sus intentos.
- `--reintentos 2` significa hasta **tres intentos** en total.
- Son reintentables los estados `DEADLINE_EXCEEDED` y `UNAVAILABLE`.
- Sin `DEDUP` cada reintento de `PublicarAuto` crea una nueva revisión. Resultado observado: **`HEAD=3`**.
- Con `DEDUP=1`, el servidor guarda un resultado por ID en `_vistas` y lo reutiliza. Resultado observado: **`HEAD=1`**, con respuesta `OK` en el segundo intento.
- La caché está en RAM y se pierde al reiniciar el servidor. Esta implementación **no garantiza ejecución exactamente una vez**, ni persistencia de commits.

## 6. Evidencias verificadas

### Operaciones originales

```text
CLONAR proyecto/main -> OK HEAD=0
RAMA proyecto/demo main -> OK HEAD=0
PUSH proyecto/demo base=0 primer_cambio -> OK HEAD=1
HISTORIAL proyecto/demo -> 1:primer_cambio | 0:inicio
PUSH proyecto/demo base=0 segundo_cambio -> FAILED_PRECONDITION: CONFLICTO HEAD=1
```

### Nueva operación, reintento sin deduplicación

```text
[servidor] PublicarAuto id=9d4febe5 -> {'repositorio': 'proyecto', 'rama': 'main', 'head': 1}
[servidor] PublicarAuto id=9d4febe5 -> {'repositorio': 'proyecto', 'rama': 'main', 'head': 2}
[servidor] PublicarAuto id=9d4febe5 -> {'repositorio': 'proyecto', 'rama': 'main', 'head': 3}
```

### Nueva operación, reintento con deduplicación

```text
[servidor] PublicarAuto id=ff6c8e1b -> {'repositorio': 'proyecto', 'rama': 'main', 'head': 1}
[servidor] PublicarAuto id=ff6c8e1b repetido, resultado cacheado SIN aplicar de nuevo
```

### Reinicio y pérdida de estado

```text
[servidor] PublicarAuto id=1e1ec108 -> {'repositorio': 'proyecto', 'rama': 'main', 'head': 1}
[cliente] UNAVAILABLE: Socket closed
[cliente] OK proyecto/main HEAD=0  # después del reinicio del proceso
```

El procedimiento reproducible y las salidas completas están en [`observaciones.md`](observaciones.md).

## 7. Compatibilidad y alcance

`reposync.v1` es la versión inicial del contrato gRPC de RepoSync. Un cliente que conozca solo `Clonar`, `Rama`, `Push` e `Historial` puede seguir usándolos sin utilizar `PublicarAuto`. Los métodos nuevos y campos numerados se agregan sin cambiar identificadores anteriores. Los archivos `servicio_pb2.py` y `servicio_pb2_grpc.py` se regeneran con `generar.sh`; no se editan a mano.

