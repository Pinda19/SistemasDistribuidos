# Observaciones — fallas provocadas - Semana 4 - Equipo Thomas Pinda

**Entorno:** Fedora Linux, Docker Compose, contenedores `cliente` y `servidor` conectados a `sd_net`; servidor TCP secuencial en el puerto `5000`.

**Verificación inicial:** `ping -c 3 servidor` → 3 paquetes enviados, 3 recibidos, `0%` de pérdida y RTT promedio de `0.048 ms`. La inspección de `sd_net` mostró a ambos contenedores. El guion base respondió correctamente: `HOLA`, `ECO`, `CONTAR`, comando desconocido y `SALIR`, con tiempos cercanos a `0.1 ms`. Se implementó y comprobó `ACUMULAR` (3 + 5 = 8).

## Falla 1 — servidor muerto con el cliente conectado

Comando usado: `docker compose kill servidor`.

Antes del corte, el cliente había recibido `OK hola PruebaFalla` y `OK acumulado 10` (ambos con `0.2 ms`). Se mató el contenedor del servidor mientras esa sesión estaba abierta; luego el cliente intentó ejecutar `CONTAR`.

| Pregunta | Respuesta |
|---|---|
| ¿Qué mensaje mostró el cliente? | `CONEXIÓN PERDIDA: ConnectionError: el servidor cerró la conexión sin responder`. |
| ¿Cuánto tardó en aparecer desde que enviaron el comando? (ms o s) | **No medido**. No hay una medición independiente del intervalo entre enviar `CONTAR` y mostrar el error; no debe inferirse de los horarios de los logs. |
| ¿El cliente supo que el servidor estaba muerto o solo que la conexión se cerró? | Solo detectó que la conexión terminó sin respuesta. Ese mensaje no permite distinguir por sí mismo un proceso muerto de otra causa de cierre. |
| Al levantar el servidor de nuevo, ¿se recuperó la sesión anterior (nombre, contador)? | No. Tras `docker compose up -d servidor`, un cliente nuevo envió `CONTAR` y obtuvo `OK 1` (`0.2 ms`), lo que muestra que comenzó una sesión nueva. El estado anterior (`PruebaFalla`, acumulado 10 y contador) no se recuperó. |

**Evidencia en el log:** para la sesión anterior al corte aparecen `HOLA PruebaFalla` y `ACUMULAR 10`; luego `servidor exited with code 137`. Después del reinicio se registra un nuevo mensaje `servidor escuchando en 0.0.0.0:5000` y una conexión nueva que responde `CONTAR` → `OK 1`.

## Falla 2 — cliente sin red con el servidor vivo

Comandos usados: `docker network disconnect sd_net cliente` y, al finalizar, `docker network connect sd_net cliente`.

Se inició una conexión que respondió `HOLA PruebaRed` → `OK hola PruebaRed` (`0.2 ms`). Tras la desconexión de red se intentó `ECO Sigues ahi`.

| Pregunta | Respuesta |
|---|---|
| ¿Qué mensaje mostró el cliente? | `TIMEOUT: el servidor no respondió en 5 s. ¿Caído, sin red o lento? No se puede saber.` |
| ¿Cuánto tardó en aparecer? | El programa notificó su **timeout configurado de 5 s**. No se hizo una medición independiente con cronómetro. |
| ¿Qué mostró el log del servidor en ese momento? | Se observa `HOLA PruebaRed` → `OK hola PruebaRed` y después `ECO Sigues ahi` → `ECO Sigues ahi`, seguido del cierre de la conexión (2 mensajes). Es decir, el servidor registró el procesamiento aunque el cliente no obtuvo una respuesta dentro del timeout. |
| Desde el punto de vista del cliente, ¿en qué se diferencia esta falla de la falla 1? | En la primera se informó **`CONEXIÓN PERDIDA`**; en la segunda, **`TIMEOUT`** tras 5 s. Ninguno de esos mensajes identifica por sí solo toda la causa: el cliente no puede asegurar si el servidor cayó, la red falló o la respuesta se retrasó. |

**Después de reconectar:** se ejecutó `ping -c 2 servidor` y respondió con `0%` de pérdida y RTT promedio de `0.039 ms`, confirmando la conectividad de red restaurada.

**Precisión:** los logs no incluyen una marca de tiempo del comando `docker network disconnect`; por tanto, no se puede determinar con exactitud cuándo ocurrió el corte ni durante cuánto tiempo estuvo desconectada la interfaz.

## Segundo cliente mientras el primero está conectado (paso 3)

| Pregunta | Respuesta |
|---|---|
| ¿El segundo cliente logró conectarse (`connect`)? | Sí. Mostró `conectado desde 172.18.0.3:35952`. Esto demuestra que completar la conexión TCP no equivale a estar siendo atendido por la aplicación. |
| ¿Recibió respuesta a su primer comando? ¿Qué mostró? | No dentro del plazo. Al enviar `HOLA Cliente2`, mostró `TIMEOUT: el servidor no respondió en 5 s. ¿Caído, sin red o lento? No se puede saber.` |
| ¿Qué mostró el log del servidor cuando el primer cliente hizo `SALIR`? | A las `02:19:23` registró `SALIR` → `ADIOS` y cierre del Cliente1 (`35940`, 2 mensajes); **en ese mismo segundo** empezó a registrar la conexión del Cliente2 (`35952`) y `HOLA Cliente2` → `OK hola Cliente2`. El Cliente2 ya había informado timeout; por eso la respuesta no se observó en su terminal. |

Esto confirma que el servidor era **secuencial**: mientras el primer cliente mantenía abierta la sesión, no atendió los comandos del segundo.

## Conclusión del equipo (3 a 5 líneas)

El laboratorio evidencia la falacia de suponer que **la red es confiable** y que una conexión TCP exitosa garantiza una respuesta inmediata.
El segundo cliente pudo conectarse, pero agotó su timeout porque el servidor secuencial seguía atendiendo al primero.
Al matar el servidor se informó una conexión perdida; al desconectar la red del cliente se informó un timeout de 5 s.
Desde el cliente, un retraso no permite distinguir con certeza entre servidor ocupado, red cortada o servidor caído sin información adicional.
Por ello, son necesarios los timeouts, el manejo explícito de desconexiones y un servidor capaz de atender conexiones concurrentes.
