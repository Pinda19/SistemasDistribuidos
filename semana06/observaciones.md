# Observaciones — Semana 6 - Laboratorio N.º 2


**Integrantes:** Thomas Pinda
**Dominio del servicio:** Inventario (dominio de referencia utilizado mientras se confirma la asignación)
**Entorno:** Fedora Linux, Docker Engine y Docker Compose, contenedores Python 3.12-slim

## Paso 1 — Servidor secuencial bajo carga

**Comandos ejecutados (directorio `semana06/demo/`):**

```bash
docker compose up -d --build
docker compose exec carga python cliente_carga.py --clientes 5 --comando "ESPERA 2"
```

**Tiempo de operación por cliente:** 2.00 s aproximadamente. El tiempo total de respuesta de cada uno fue aumentando porque debía esperar su turno:

| Cliente | Espera en fila | Operación | Total individual |
|---|---:|---:|---:|
| 4 | 0.01 s | 2.00 s | 2.01 s |
| 1 | 2.01 s | 2.00 s | 4.01 s |
| 0 | 4.01 s | 2.00 s | 6.01 s |
| 2 | 6.01 s | 2.00 s | 8.01 s |
| 3 | 8.01 s | 2.00 s | 10.01 s |

**TOTAL real:** **10.01 s**.

**¿Qué esperábamos? ¿Qué observamos?** Se esperaba alrededor de `5 × 2 = 10 s`, ya que el servidor secuencial atiende una conexión a la vez. El resultado fue **10.01 s**, prácticamente igual al cálculo. Mientras el servidor atendía a uno, los demás clientes esperaban en la cola de conexiones pendientes del sistema operativo; que `connect()` termine no implica que el servidor ya esté ejecutando el comando.

## Paso 2 — Hilo por cliente bajo carga

**Comandos ejecutados (directorio `semana06/demo/`):**

```bash
MODELO=hilos docker compose up -d --force-recreate servidor
docker compose exec carga python cliente_carga.py --clientes 5 --comando "ESPERA 2"
```

**TOTAL real:** **2.00 s**. Los cinco clientes reportaron aproximadamente **2.00 s** cada uno, con **0.00 s** de espera en fila (según el redondeo de la herramienta). Todos devolvieron `OK ESPERA 2`.

**Diferencia respecto al Paso 1 y explicación:**

| Modelo | Clientes | Comando | Tiempo total |
|---|---:|---|---:|
| Secuencial | 5 | `ESPERA 2` | **10.01 s** |
| Hilo por cliente | 5 | `ESPERA 2` | **2.00 s** |

La ejecución concurrente tardó **8.01 s menos** (aproximadamente **80 % menos tiempo**, o unas **5 veces más rápida** para esta carga de espera). Cada cliente fue atendido por un hilo independiente. Como `ESPERA` no requiere mantener un Lock, los cinco hilos pudieron esperar simultáneamente sin bloquearse unos a otros.

**Observación sobre el alcance:** esta comparación corresponde a la carpeta `demo`, tal como se ve en las rutas de terminal. No se adjuntó una medición separada del servidor secuencial adaptado al dominio propio dentro de `semana06/`.

**Limpieza de la demostración:** se ejecutó `docker compose down -v`; la salida confirmó la eliminación de los tres contenedores y de `sd_net` correspondientes a la demo.

## Paso 3 — Condición de carrera

**Operación utilizada:** `QUITAR manzana 1`, ejecutada cuatro veces por cada uno de 20 clientes (`20 × 4 = 80` retiros), sobre un inventario inicial de **100 manzanas** y **100 peras**.

**Valor esperado de manzanas:** `100 - 80 = 20`.

### Experimento A: SIN Lock

```bash
SIN_LOCK=1 docker compose up -d --force-recreate servidor
docker compose exec carga python cliente_carga.py --clientes 20 --comando "QUITAR manzana 1" --repeticiones 4
docker compose exec cliente python cliente.py
# Dentro del cliente: LISTAR
```

- **TOTAL de la carga:** **0.03 s**.
- **Respuesta real a `LISTAR`:** `OK manzana:91 pera:100`.
- **Valor observado sin Lock:** **91** manzanas, en lugar de 20.
- **Interpretación:** el inventario sólo reflejó 9 retiros netos, aunque la prueba realizó 80 operaciones de retiro. Se perdió el efecto de **71 actualizaciones** por condiciones de carrera: varios hilos leyeron un valor anterior y sobrescribieron resultados de otros hilos.

### Experimento B: CON Lock

```bash
SIN_LOCK=0 docker compose up -d --force-recreate servidor
docker compose exec carga python cliente_carga.py --clientes 20 --comando "QUITAR manzana 1" --repeticiones 4
docker compose exec cliente python cliente.py
# Dentro del cliente: LISTAR
```

- **TOTAL de la carga:** **0.09 s**.
- **Respuesta real a `LISTAR`:** `OK manzana:20 pera:100`.
- **Valor observado con Lock:** **20** manzanas, exactamente el valor esperado.
- **Interpretación:** el Lock protegió las actualizaciones compartidas. Aunque esta ejecución tardó 0.06 s más que la versión incorrecta, evitó la pérdida de actualizaciones.

**¿Dónde exactamente está la sección crítica?** En la plantilla del servidor, `op_quitar()` utiliza `with seccion_critica():` alrededor de la lectura de `estado["inventario"]`, las validaciones de ítem existente y stock suficiente, la pausa artificial de 0.001 s y la actualización de la cantidad. `op_agregar()` también protege la lectura y escritura del inventario; `op_listar()` protege la lectura consistente del inventario; el incremento de `estado["operaciones"]` se protege por separado. `seccion_critica()` devuelve un `threading.Lock` cuando `SIN_LOCK=0`, o un contexto sin protección cuando `SIN_LOCK=1`.

**Nota:** la pauta solicita verificar el resultado con Lock en **tres corridas independientes**. En las evidencias recibidas se documenta **una** corrida con Lock y **una** sin Lock. Las dos corridas adicionales siguen pendientes. Para cada una debe reiniciarse el servidor para restablecer el inventario inicial.

## Paso 4 — Despliegue con Docker Compose

**Comprobación:** `docker compose config` mostró una configuración válida con tres servicios: `servidor`, `cliente` y `carga`.

**Salida resumida de `docker compose ps`:**

| Contenedor | Servicio | Estado observado | Puerto publicado |
|---|---|---|---|
| `sd_servidor` | servidor | Up | `0.0.0.0:5000->5000/tcp` y `[::]:5000->5000/tcp` |
| `sd_cliente` | cliente | Up | — |
| `sd_carga` | carga | Up | — |

**Red Docker:** `sd_net`, driver `bridge` (confirmada por `docker network ls`).

**IP del equipo anfitrión durante la prueba:** **`192.168.1.92`**, interfaz `enp4s0` (`192.168.1.92/24`). Esta dirección fue asignada dinámicamente y puede cambiar. La dirección interna de Docker `172.18.0.1` no es la IP del host que otro equipo debe utilizar.

**Variables verificadas en `docker compose config`:** `PUERTO=5000`, `SIN_LOCK=0`, `TIMEOUT_CLIENTE=60` para el servidor; `SERVIDOR_HOST=servidor`, `SERVIDOR_PUERTO=5000` para cliente y carga.

**Topología:** los tres servicios comparten `sd_net`; el cliente interno se conecta por nombre DNS `servidor:5000`. El puerto 5000 está publicado en el anfitrión para permitir pruebas externas, siempre que la conectividad y el firewall lo permitan.

## Paso 5 — Prueba cruzada

**Equipo cuyo servidor probamos:** Pendiente.  
**¿Su `protocolo.md` alcanzó para conectarse sin preguntar?:** No evaluado; no se proporcionó repositorio ni servidor de otro equipo.  
**Mensajes enviados y respuestas del servidor ajeno:** No evaluados.  
**Qué falló y por qué:** No hay resultados de una prueba cruzada real que permitan atribuir fallas.  
**Equipo que probó nuestro servidor:** Pendiente.  
**Qué reportaron:** Pendiente.

**Verificación local disponible (no equivale a prueba cruzada):** el cliente de la plantilla se conectó a `servidor:5000` y obtuvo respuestas a `HOLA equipo`, `LISTAR`, un comando desconocido (`salid`) y `salir`:

```text
HOLA equipo  -> OK HOLA equipo
LISTAR       -> OK manzana:100 pera:100
salid        -> ERROR COMANDO_DESCONOCIDO
salir        -> OK CHAO
```

La ejecución con `listar` en minúsculas también respondió correctamente, lo que confirma que el servidor reconoce comandos sin distinguir mayúsculas.

**Pendiente académico:** coordinar la prueba cruzada con otro equipo o consultar al profesor si admite reemplazarla por una prueba desde otra máquina o contenedor independiente y registrar esa alternativa sin presentarla como una evaluación de pares.

## Falla provocada — Desconexión abrupta

**Comandos ejecutados:**

```bash
docker compose exec -d carga python cliente_carga.py --clientes 3 --comando "ESPERA 5"
docker compose kill carga
docker compose logs --tail 20 servidor
docker compose up -d carga
docker compose exec cliente python cliente.py
# Dentro del cliente: LISTAR, SALIR
```

**Qué registró el servidor:** tres conexiones desde `172.18.0.3`, con puertos **44392**, **44398** y **44406**, fueron registradas a las `01:53:25,543`. Sus cierres aparecieron a las `01:53:30,544`, con `operaciones=84` en las tres líneas. Las últimas 20 líneas facilitadas **no muestran una advertencia explícita** de `ConnectionResetError` o `BrokenPipeError`.

**¿El servidor siguió atendiendo a los demás?** **Sí.** Después de finalizar esa prueba y reiniciar `sd_carga`, se ejecutó un cliente nuevo y respondió:

```text
listar -> OK manzana:20 pera:100
salir  -> OK CHAO
```

La salida de `docker compose up -d carga` informó `sd_servidor Running`. Esto demuestra que el servidor continuó operativo después de la prueba. **No demuestra por sí solo que se detectara una excepción de desconexión abrupta**, pues los tres cierres quedaron registrados aproximadamente cinco segundos después de iniciar la operación. Esa diferencia debe conservarse en las observaciones, en lugar de afirmar un error que no aparece en el log adjunto.

## Conclusión

La demostración confirmó que el servidor secuencial acumula tiempos de espera (10.01 s para cinco clientes con `ESPERA 2`), mientras que el modelo de hilos atiende las operaciones de espera simultáneamente (2.00 s). Sin embargo, atender varios clientes al mismo tiempo introduce condiciones de carrera si comparten un recurso: con el Lock desactivado, 80 retiros dejaron 91 manzanas en vez de 20; con el Lock activo, el inventario quedó en el valor correcto. El despliegue con Docker Compose funcionó con tres servicios en `sd_net`, y el servidor continuó operativo después de finalizar el contenedor de carga. La prueba cruzada entre equipos y dos repeticiones adicionales del caso con Lock quedan pendientes.
