# RepoSync — Protocolo v3 (Semana 9)

## 1. Identificación

- Dominio: **control de versiones simplificado**, RepoSync.
- Transporte: **TCP, puerto 5000**, dentro de `sd_net`.
- Versión del **documento**: 3; versión del **mensaje**: `2`.
- Dos codecs alternativos con el mismo esquema: `CODEC=json` y `CODEC=bin`.

## 2. Contrato de los mensajes

**Enmarcado:** cuatro bytes `!I` (unsigned big-endian) con el tamaño del cuerpo, seguidos por exactamente ese número de bytes.

**Solicitud:** `version: int`, `id: int`, `operacion: str`, `argumentos: list[str]`.

**Respuesta:** `id: int`, `estado: 'OK'|'ERROR'`, `datos: list[str]`, `error: str`.

Se conserva `id` para correlacionar respuesta y petición. El servidor solo acepta `version=2`.

### JSON

Ejemplo de solicitud:

```json
{"operacion": "PUSH", "argumentos": ["proyecto", "main", "0", "primer_cambio"], "id": 7, "version": 2}
```

### Binario (`struct`, orden de red big-endian)

- Solicitud: `version(1B)` + `id(4B)` + `operacion(2B largo + UTF8)` + `n_args(1B)` + cada argumento como texto de largo prefijado.
- Respuesta: `id(4B)` + `estado(1B: 0=OK, 1=ERROR)` + `n_datos(1B)` + datos como textos de largo prefijado + `error(2B largo + UTF8)`.
- El encabezado de **4 bytes de largo** se agrega en ambos formatos antes del cuerpo.

## 3. Operaciones del dominio

| Operación | Argumentos | Resultado correcto | Errores del dominio |
|---|---|---|---|
| `HOLA` | `[nombre]` opcional | `HOLA nombre` | — |
| `REPOS` | ninguno | lista de repositorios (inicial `proyecto`) | `FORMATO REPOS` |
| `CLONAR` | `repo rama` | `repo rama HEAD=n` | `REPO_NO_EXISTE`, `RAMA_NO_EXISTE` |
| `RAMA` | `repo nueva origen` | `RAMA nueva HEAD=n` | `RAMA_EXISTE`, `RAMA_NO_EXISTE`, `REPO_NO_EXISTE` |
| `PUSH` | `repo rama base mensaje` | `PUSH rama HEAD=n` | `CONFLICTO HEAD=n`, formato, repo/rama inexistente |
| `HISTORIAL` | `repo rama` | lista de revisiones `id:mensaje` (hasta 10) | repo/rama inexistente |
| `ESPERA` | `segundos` (0 a 10) | `ESPERA segundos` | formato incorrecto |
| `SALIR` | ninguno | `CHAO` | — |

Ejemplo de correlación: `Solicitud(id=7, operacion='REPOS')` → `Respuesta(id=7, estado='OK', datos=['proyecto'])`.

## 4. Errores de protocolo

| Anomalía | Comportamiento |
|---|---|
| `version` distinta de `2` | `ERROR versión X no soportada, use 2`, misma conexión |
| JSON inválido, binario truncado o ilegible | `ERROR mensaje mal formado`, cierra solo esa conexión |
| Largo mayor a 1 MB | `ERROR mensaje mal formado`, cierra solo esa conexión |
| Largo anunciado sin cuerpo completo | servidor espera hasta `TIMEOUT_SERVIDOR=30`, cierra la conexión; cliente espera hasta 5 s |
| Operación desconocida | `ERROR COMANDO_DESCONOCIDO` |

## 5. Concurrencia

Un hilo (`threading.Thread`) por conexión TCP. `threading.Lock` protege `estado['repos']`, `estado['operaciones']` y la comparación-modificación de HEAD durante `PUSH`. La operación `ESPERA` no mantiene el Lock bloqueado.

## 6. Ejemplo de sesión

```text
HOLA estudiante                -> OK HOLA | estudiante
REPOS                          -> OK proyecto
RAMA proyecto demo main        -> OK RAMA | demo | HEAD=0
CLONAR proyecto demo           -> OK proyecto | demo | HEAD=0
PUSH proyecto demo 0 primer    -> OK PUSH | demo | HEAD=1
PUSH proyecto demo 0 obsoleto  -> ERROR CONFLICTO HEAD=1
HISTORIAL proyecto demo        -> OK 1:primer | 0:inicio
SALIR                          -> OK CHAO
```

En la sesión real cada comando se serializa como `Solicitud` y el resultado como `Respuesta`: el cliente los imprime en texto para facilitar la demostración. La operación `HOLA estudiante` fue verificada en **JSON** con la respuesta `OK HOLA | estudiante`. No se ha recibido aún una ejecución de `HOLA` en binario desde el equipo.

## 7. Medición de codecs — datos reales del equipo

Comando utilizado desde el contenedor `cliente`:

```powershell
docker compose exec cliente python bench_codec.py 10000
```

Se midieron **10.000 solicitudes y 10.000 respuestas** generadas con las operaciones del dominio RepoSync. Los tiempos pertenecen a esa ejecución concreta; el benchmark mide serialización y deserialización local, **no latencia de red**. El tamaño registrado corresponde al **cuerpo serializado**; en una conexión TCP se añaden además **4 bytes de longitud por mensaje**.

| Mensaje | Codec | Bytes promedio | Bytes totales | Codificar (ms) | Decodificar (ms) |
|---|---|---:|---:|---:|---:|
| Solicitud | json | 90.9 | 908730 | 79.39 | 36.47 |
| Solicitud | bin | 35.0 | 349836 | 19.43 | 25.62 |
| Respuesta | json | 83.4 | 833648 | 70.60 | 38.24 |
| Respuesta | bin | 33.7 | 337254 | 21.23 | 24.02 |

- **Solicitudes:** el binario utilizó **61,5 % menos bytes** que JSON.
- **Respuestas:** el binario utilizó **59,5 % menos bytes** que JSON.
- En esta muestra, la codificación y decodificación con binario fueron más rápidas, a costa de legibilidad y de requerir el mismo contrato en ambos extremos.
- Las cifras son experimentales, no garantías universales para otros equipos, cargas o tamaños de mensaje.

En la prueba simple `python codec.py`, una solicitud PUSH concreta ocupó **102 bytes JSON** versus **46 bytes binarios**, y su respuesta **75 bytes JSON** versus **28 bytes binarios**. Estos tamaños corresponden a **un ejemplo**, no al promedio del benchmark.

## 8. Historial de versiones

| Documento | Hito | Cambio |
|---|---|---|
| v1 | Semana 4 | Protocolo de texto por línea |
| v2 | Semana 6 y 7 | Hilos, Lock, operaciones RepoSync y API REST |
| v3 | Semana 9 | Solicitud/Respuesta, enmarcado, version, id, JSON y binario |

## Limitaciones

`proyecto` se crea al iniciar; el estado está en RAM y se pierde al reiniciar. `CLONAR` solo consulta HEAD, no descarga archivos; `PUSH` simula revisiones, no utiliza Git real. Las APIs antiguas `api.py` no se ejecutan junto al servidor Semana 9 hasta actualizarlas al nuevo codec.
