# Observaciones — RepoSync, Semana 9 (serialización explícita)

**Equipo:** Thomas Pinda
**Integrantes:** Thomas Pinda.
**Entorno observado:** PowerShell en Windows; cliente y servidor en contenedores `python:3.12-slim` conectados a `sd_net`.

Este documento recoge **únicamente las salidas reales compartidas durante la ejecución del laboratorio**. Cuando una prueba no tiene evidencia completa, se indica expresamente. Al cambiar el codec se recrearon los contenedores y se perdió el estado en RAM.

## Paso 2 — Ida y vuelta de los codecs

Comando: `docker compose exec cliente python codec.py`.

```text
json  solicitud 102 bytes  b'{"operacion": "PUSH", "argumentos": ["proyecto", "main", "0", "primer_cambio"], "id": 7, "version": 2}'
json  respuesta  75 bytes  b'{"id": 7, "estado": "OK", "datos": ["PUSH", "main", "HEAD=1"], "error": ""}'
bin   solicitud  46 bytes  b'\x02\x00\x00\x00\x07\x00\x04PUSH\x04\x00\x08proyecto\x00\x04main\x00\x010\x00\rprimer_cambio'
bin   respuesta  28 bytes  b'\x00\x00\x00\x07\x00\x03\x00\x04PUSH\x00\x04main\x00\x06HEAD=1\x00\x00'
ida y vuelta OK en los dos codecs
```

**Interpretación:** los dos codecs serializan y deserializan una `Solicitud` y una `Respuesta` sin cambiar los datos. El ejemplo muestra que el cuerpo binario ocupa menos bytes; no incluye los 4 bytes del enmarcado TCP.

## Paso 3 — Medición con mensajes de RepoSync

Comando: `docker compose exec cliente python bench_codec.py 10000`.

```text
N = 10000 solicitudes y 10000 respuestas del dominio RepoSync
```

| Mensaje | Codec | Bytes prom | Bytes totales | Codif (ms) | Decod (ms) |
|---|---|---:|---:|---:|---:|
| Solicitud | json | 90.9 | 908730 | 79.39 | 36.47 |
| Solicitud | bin | 35.0 | 349836 | 19.43 | 25.62 |
| Respuesta | json | 83.4 | 833648 | 70.60 | 38.24 |
| Respuesta | bin | 33.7 | 337254 | 21.23 | 24.02 |

**Conclusiones:** en esta medición, el binario ocupó **61,5 % menos bytes para solicitudes** y **59,5 % menos para respuestas**. También fue más rápido en codificar y decodificar estos mensajes, pero es más difícil de leer o depurar sin conocer el esquema exacto. Los tiempos son de procesamiento local de 10.000 mensajes, no de viaje por la red.

## Paso 4 — Integración del nuevo protocolo en RepoSync

Ambos contenedores levantaron correctamente en `sd_net`. Se verificó la conexión TCP al puerto 5000 y el cambio de codec con la variable `CODEC`.

| Prueba | `CODEC=json` (observado) | `CODEC=bin` (observado) |
|---|---|---|
| Contenedores | `sd_servidor` y `sd_cliente` `Up` | ambos contenedores recreados e iniciados |
| Registro del servidor | `codec=json hilo por cliente + Lock` | `codec=bin hilo por cliente + Lock` |
| `REPOS` | `OK proyecto` | `OK proyecto` |
| `CLONAR proyecto main` | `OK proyecto \| main \| HEAD=0` | No ejecutado en modo binario en las salidas compartidas |
| `RAMA proyecto demo main` | `OK RAMA \| demo \| HEAD=0` | `OK RAMA \| demo \| HEAD=0` |
| `PUSH proyecto demo 0 primer_cambio` | `OK PUSH \| demo \| HEAD=1` | `OK PUSH \| demo \| HEAD=1` |
| `HISTORIAL proyecto demo` | `OK 1:primer_cambio \| 0:inicio` | No ejecutado en modo binario en las salidas compartidas |
| `PUSH proyecto demo 0 segundo_cambio` | `ERROR CONFLICTO HEAD=1` | `ERROR CONFLICTO HEAD=1` |
| `HOLA estudiante` | `OK HOLA | estudiante` | No ejecutado en modo binario en las salidas compartidas |

**Evidencia posterior del comando `HOLA` en modo JSON:**

```text
conectado a servidor:5000 con codec=json (timeout 5.0 s)
  OK HOLA | estudiante
```

Esta prueba se realizó después de la verificación de fallas. La ejecución equivalente de `HOLA` en modo binario no se adjuntó y por ello no se afirma como observada en el equipo.

**Interpretación:** JSON y binario transmitieron el mismo esquema y dieron las mismas respuestas para las operaciones comparadas. El `PUSH` conflictivo demuestra que el control de versiones y el `Lock` permanecen en la lógica del servidor, independientemente del codec.

## Paso 5 — Fallas provocadas

Se usó `docker compose exec cliente python cliente_malo.py <modo>` y se comprobó que el servidor respondió a `REPOS` después de las pruebas.

| Modo | Cliente: salida observada | Registro del servidor disponible | ¿El servidor continuó? |
|---|---|---|---|
| `version` con JSON | `Respuesta(id=1, estado='ERROR', ..., error='versión 1 no soportada, use 2')` | `cli-1`: `versión no soportada 1`, luego desconexión | **Sí**, REPOS final correcto |
| `largo` con JSON | `! sin respuesta en 5.0 s` | `cli-2`: conexión y desconexión cinco segundos después, sin solicitud procesada | **Sí**, REPOS final correcto |
| `basura` con JSON | `mensaje mal formado (UnicodeDecodeError)` | `cli-3`: error UTF-8 al decodificar byte `0x9c` | **Sí**, REPOS final correcto |
| `cruzado` con JSON | `codificando con bin` → `mensaje mal formado (JSONDecodeError)` | `cli-4`: `Expecting value: line 1 column 1` | **Sí**, REPOS final correcto |
| `version` con bin | `versión 1 no soportada, use 2` | No se adjuntó log binario | **Sí**, REPOS después de la prueba |
| `largo` con bin | `! sin respuesta en 5.0 s` | No se adjuntó log binario | **Sí**, REPOS después de la prueba |
| `basura` con bin | `mensaje mal formado (ValueError)` | No se adjuntó log binario | **Sí**, REPOS después de la prueba |
| `cruzado` con bin | `codificando con json` → `mensaje mal formado (ValueError)` | No se adjuntó log binario | **Sí**, REPOS después de la prueba |

### Evidencia del servidor JSON (últimas líneas de `docker compose logs servidor --tail 30`)

```text
18:48:30 [MainThread] RepoSync v2 en 0.0.0.0:5000 codec=json hilo por cliente + Lock
18:49:10 [cli-1] conectado ... codec json
18:49:10 [cli-1] versión no soportada 1 ...
18:49:10 [cli-1] desconectado ...
18:49:13 [cli-2] conectado ... codec json
18:49:18 [cli-2] desconectado ...
18:49:47 [cli-3] mensaje mal formado ... -> UnicodeDecodeError 'utf-8' codec can't decode byte 0x9c in position 0: invalid start byte
18:49:50 [cli-4] mensaje mal formado ... -> JSONDecodeError Expecting value: line 1 column 1 (char 0)
18:50:22 [cli-5] solicitud 1 REPOS []
18:50:22 [cli-5] desconectado ...
```

**Por qué el servidor sobrevivió:** los mensajes incompatibles se rechazaron dentro del hilo que atendía a ese cliente. La siguiente solicitud `REPOS` devolvió `OK proyecto`. La prueba `largo` mostró un timeout de **cliente** de 5 segundos; no prueba que se haya agotado el timeout configurado en el servidor (30 segundos).

**¿Qué codec falló de forma más clara ante basura?** En esta ejecución, **JSON** produjo un `UnicodeDecodeError` explícito de UTF-8, mientras que **binario** devolvió un `ValueError` de estructura inválida. Ambos detectaron y manejaron los mensajes defectuosos. No se debe concluir que JSON detecta siempre mejor cualquier corrupción: depende de los bytes enviados.


