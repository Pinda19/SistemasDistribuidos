# Guía de laboratorio N°2 — Servidor concurrente en Docker

Viernes 02-10 · 14.15 a 16.00 · Laboratorio de Informática

## La idea en tres líneas

El jueves vimos que el servidor de la semana 4 atiende a un cliente a la vez y que cinco clientes tardan cinco veces más. Hoy cada equipo convierte **su** servidor en uno que atiende a varios a la vez, con hilos y con Lock, lo deja corriendo en tres contenedores y lo entrega a otro equipo para que lo use leyendo solo el `protocolo.md`.

## Qué trae esta carpeta y para qué sirve

| Archivo | Qué es |
|---|---|
| `servidor.py` | Un servidor **de ejemplo**, ya concurrente, con hilos, Lock, manejo de errores y timeout. El dominio es un inventario de manzanas y peras. **Es un molde**, no el servidor del equipo |
| `cliente.py` | Cliente interactivo, el mismo estilo de la semana 4 |
| `cliente_carga.py` | Abre N conexiones a la vez y mide por cliente el tiempo en fila, el tiempo de la operación y el total |
| `docker-compose.yml`, `Dockerfile` | Tres contenedores (`servidor`, `cliente`, `carga`) en la red `sd_net`, puerto 5000 publicado |
| `protocolo.md` | Plantilla del protocolo versión 2, con el inventario de ejemplo ya llenado |
| `observaciones.md` | Donde se anotan los resultados de cada paso |
| `pauta_prueba_cruzada.md` | Rotación entre equipos y checklist del paso 5 |

**Cómo se usa el molde.** `servidor.py` tiene tres partes. Arriba, el diccionario `estado` con el inventario. Al medio, una función por operación (`op_listar`, `op_agregar`, `op_quitar`, `op_espera`), cada una con `with seccion_critica()` alrededor de las líneas que leen y escriben el estado. Abajo, el bucle de `accept()` que crea un hilo por cliente, los `except` para cuando el cliente se desconecta y el `finally` que registra el cierre. **La parte de abajo no se toca.** Lo que cambia cada equipo es el estado y las funciones del medio, para que el servidor sea de su dominio (saldos, salas, sensores, sesiones, pedidos, mensajes). Las ideas por tema están en el documento *Ideas de servicio por tema de investigación*.

Si el equipo va atrasado o no tiene claro su dominio, hace todos los pasos con el inventario tal cual y cambia el dominio en el trabajo autónomo.

## Convenciones (no cambian entre semanas)

Red `sd_net` · servicios `servidor`, `cliente`, `carga` · contenedores `sd_servidor`, `sd_cliente`, `sd_carga` · puerto 5000 · variables `PUERTO`, `SIN_LOCK`, `TIMEOUT_CLIENTE`, `SERVIDOR_HOST`, `SERVIDOR_PUERTO`.

Alias útil

```bash
alias c='docker compose exec cliente'          # bash / zsh
function c { docker compose exec cliente @args } # PowerShell
```

## Preparación (10 min)

```bash
# desde la raíz del repositorio del equipo
cp -r <ruta_del_zip>/semana06/laboratorio semana06
cd semana06
cp ../semana04/servidor.py servidor_secuencial.py     # el servidor de la semana 4, el que atiende de a uno
docker compose up -d --build
docker compose ps                                       # tres servicios Up
c python cliente.py
HOLA equipo
LISTAR
SALIR
```

Debe responder `OK HOLA equipo`, `OK manzana:100 pera:100`, `OK CHAO`.

## Paso 1 — ver el problema en el servidor propio (15 min)

Correr el servidor secuencial del equipo dentro del contenedor `cliente` (que está libre) y lanzarle carga apuntando a él.

```bash
docker compose exec -d cliente python servidor_secuencial.py
docker compose exec -e SERVIDOR_HOST=cliente carga python cliente_carga.py --clientes 5 --comando "ESPERA 2"
```

Si el protocolo del equipo no tiene `HOLA` ni `SALIR`, agregar `--saludo "" --cierre ""`. Si no tiene una operación lenta, usar `ESPERA` como en el molde.

Resultado esperado

```
  cliente   en fila   operacion      total   ultima respuesta
        2    0.01 s    2.00 s    2.01 s   OK ESPERA 2
        1    2.01 s    2.00 s    4.01 s   OK ESPERA 2
        0    4.01 s    2.00 s    6.01 s   OK ESPERA 2
        4    6.01 s    2.00 s    8.02 s   OK ESPERA 2
        3    8.01 s    2.00 s   10.02 s   OK ESPERA 2
TOTAL: 10.02 s
```

Anotar en `observaciones.md` el TOTAL y la respuesta a «¿dónde esperó el último cliente durante ocho segundos?».

Apagar el servidor secuencial para seguir

```bash
docker compose restart cliente
```

## Paso 2 — un hilo por cliente, con el dominio del equipo (20 min)

Abrir `servidor.py` y adaptar solo la parte de arriba y la del medio.

1. Reemplazar el diccionario `estado` por el del dominio. Ejemplo para Pagos

   ```python
   estado = {"cuentas": {"ana": 100000, "beto": 20000}, "operaciones": 0}
   ```

2. Reemplazar `op_listar`, `op_agregar` y `op_quitar` por las operaciones del dominio, con el **mismo patrón**, una función por operación, `with seccion_critica()` solo alrededor de las líneas que leen y escriben `estado`, y `return "ERROR CODIGO detalle"` para cada caso inválido. Mínimo tres operaciones, al menos una que modifique estado.

3. Registrar los nombres nuevos en el diccionario `OPERACIONES`.

4. Mantener `HOLA`, `SALIR` y `ESPERA` tal cual.

5. **No tocar** `atender()` ni `main()`. Ahí están los hilos, los `except` y el `finally`.

Reconstruir y repetir la carga

```bash
docker compose up -d --build --force-recreate servidor
docker compose exec carga python cliente_carga.py --clientes 5 --comando "ESPERA 2"
```

Resultado esperado, `TOTAL ≈ 2 s` y la columna en fila en 0 para todos. Anotar el nuevo TOTAL. Mirar el log, cada línea debe decir qué hilo (`cli-<puerto>`) la escribió

```bash
docker compose logs --tail 10 servidor
```

## Paso 3 — provocar la carrera y corregirla (15 min)

Primero **sin** candado. Elegir la operación del dominio que modifica estado (`RETIRAR`, `ENTRAR`, `LEER`, `VER`, `TOMAR`, `ENVIAR` o `QUITAR` si siguen con el inventario).

```bash
SIN_LOCK=1 docker compose up -d --force-recreate servidor
docker compose exec carga python cliente_carga.py --clientes 20 --comando "QUITAR manzana 1" --repeticiones 4
c python cliente.py
LISTAR
SALIR
```

Esperado `manzana 100 - 80 = 20`. Observado algo como `manzana:93`, y distinto en cada corrida. Anotar esperado y observado.

Después **con** candado. Comprobar que el `with seccion_critica()` cubre exactamente las líneas que leen y escriben el estado, y nada más.

```bash
SIN_LOCK=0 docker compose up -d --force-recreate servidor
docker compose exec carga python cliente_carga.py --clientes 20 --comando "QUITAR manzana 1" --repeticiones 4
c python cliente.py
LISTAR
SALIR
```

Debe dar `manzana:20` exacto, tres corridas seguidas.

Última comprobación, la del error más común. Repetir la carga del paso 2

```bash
docker compose exec carga python cliente_carga.py --clientes 5 --comando "ESPERA 2"
```

Si volvió a dar 10 s, el Lock está envolviendo `ESPERA` o alguna espera. Achicarlo.

En PowerShell las variables se ponen con `$env:SIN_LOCK="1"` antes del `docker compose up`.

## Paso 4 — docker compose versionado y la IP (10 min)

```bash
docker compose config           # sin errores
docker compose ps               # tres servicios Up
docker network ls | grep sd_net # la red se llama sd_net, no semana06_sd_net
git add docker-compose.yml
```

Averiguar la IP del notebook en la red del laboratorio

```bash
ipconfig | findstr IPv4           # Windows
ip -4 addr show | grep inet       # Linux
ipconfig getifaddr en0            # macOS
```

Probar desde el propio notebook con la IP real, no con `servidor`

```bash
docker compose exec -e SERVIDOR_HOST=192.168.1.37 cliente python cliente.py
```

Escribir en el pizarrón el nombre del equipo, la IP, el puerto y el comando inicial del protocolo (o «ninguno»). Empezar a llenar `protocolo.md` con las operaciones del dominio; otro equipo lo va a usar en diez minutos.

## Paso 5 — prueba cruzada y falla provocada (15 min)

Ver `pauta_prueba_cruzada.md`. Cada equipo recibe **solo** el `protocolo.md` del equipo que le toca y se conecta a su IP. No se puede preguntar nada al otro equipo; todo lo que no esté escrito se anota como hallazgo.

```bash
docker compose exec -e SERVIDOR_HOST=<IP_OTRO> cliente python cliente.py
```

Recorrer el checklist de ocho puntos de la pauta. A la señal del docente, falla provocada contra el servidor ajeno

```bash
docker compose exec -d -e SERVIDOR_HOST=<IP_OTRO> carga python cliente_carga.py --clientes 3 --comando "ESPERA 5"
sleep 1
docker compose kill carga
docker compose exec -e SERVIDOR_HOST=<IP_OTRO> cliente python cliente.py    # ¿sigue vivo?
docker compose up -d carga                                                   # restaurar
```

El equipo dueño mira `docker compose logs -f servidor` y debe ver «se desconecto abruptamente» y luego el cliente nuevo atendido.

Si la red del laboratorio no deja llegar al otro notebook, ruta de respaldo

```bash
git clone <repo_del_otro_equipo> otro && cd otro/semana06
docker compose up -d --build servidor
docker compose exec cliente python cliente.py
```

## Cierre (10 min, antes de las 16.00)

`observaciones.md` completo, con números y con los dos reportes de la prueba cruzada (el que hicimos y el que nos hicieron).

```bash
docker compose down -v
git add semana06/
git commit -m "semana06 servidor concurrente y compose"
git push
```

Debe quedar en `semana06/` `servidor.py`, `servidor_secuencial.py`, `cliente.py`, `cliente_carga.py`, `docker-compose.yml`, `Dockerfile`, `protocolo.md` (borrador) y `observaciones.md`.

## Trabajo autónomo (plazo jueves 08-10, 18.00)

1. Convertir cada hallazgo del equipo que nos probó en un cambio de código o de documento. Si el servidor se cayó con la falla provocada, corregirlo primero. Quitar la pausa artificial de la sección crítica.
2. `protocolo.md` versión 2 completo, las seis secciones y la tabla de operaciones del dominio.
3. Si quedaron con el inventario de ejemplo, hacer el cambio al dominio propio.

## Si algo no funciona

- **Docker no anda.** `PUERTO=5000 python servidor.py` en una terminal y `SERVIDOR_HOST=127.0.0.1 python cliente.py` en otra. La prueba cruzada por IP funciona igual.
- **`address already in use`.** `docker compose down`; si persiste, algo del host usa el 5000 (en macOS suele ser AirPlay). Cambiar la línea `ports` a `"5050:5000"` y anotar 5050 en el pizarrón.
- **La red se llama `semana06_sd_net`.** Falta `name: sd_net` bajo `networks`.
- **Con Lock sigue dando mal.** El Lock se creó dentro de `atender()`, uno por hilo. Debe ser uno solo, global.
- **Después del paso 2 sigue en 10 s.** El Lock envuelve una espera, o faltó `.start()` en el hilo.
