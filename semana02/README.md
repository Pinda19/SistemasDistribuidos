# Laboratorio N°1 — Midiendo las falacias de la computación distribuida

**Sistemas Distribuidos (FDICI25 / INFO35)** · Ingeniería Civil en Informática · Universidad de Los Lagos
**Semana 2** · Viernes 28-08-2026, 14:15–16:00 · Laboratorio de Informática
**Docente:** Carlos Jesús Rojas Latorre

---

## 1. Qué es este material

Un cliente y un servidor TCP mínimos, cada uno en su propio contenedor Docker, conectados por la red `sd_net`. El cliente hace 100 llamadas remotas seguidas y mide cuánto tarda cada una. El servidor solo responde `PONG n` a cada `PING n`.

Esta semana **no escriben código**: el sistema lo provee el curso y ustedes lo miden. El objetivo es observar con números cómo la latencia y la pérdida de paquetes degradan un sistema que funciona perfecto en la red local, y descubrir qué falacia asumió este código sin decirlo. En la semana 4 escribirán su propio cliente y servidor partiendo de lo que aprendan aquí.

## 2. Contenido de la carpeta

| Archivo | Qué es | ¿Se modifica? |
|---|---|---|
| `docker-compose.yml` | Define los dos nodos (`servidor`, `cliente`) y la red `sd_net`. Da el permiso `NET_ADMIN` que necesita `tc`. | No |
| `Dockerfile` | Imagen `python:3.12-slim` con `ping`, `iperf3` e `iproute2` (`tc`). | No |
| `servidor.py` | Servidor TCP en el puerto 5000. Caja negra esta semana. | No |
| `cliente.py` | Hace N llamadas y reporta total, promedio, mínimo y máximo. Léanlo: son 40 líneas. | No |
| `mediciones.md` | Plantilla de registro. **Este es el archivo que ustedes completan.** | Sí |
| `README.md` | Este documento. | No |

## 3. Requisitos previos (traer listo el viernes)

- **Docker** instalado y funcionando: Docker Desktop en Windows o macOS (iniciarlo antes de las 14:15; demora 1 a 2 minutos en arrancar) o Docker Engine con el plugin Compose en Linux (`docker compose version` debe responder).
- Una terminal: PowerShell en Windows, o bash/zsh en Linux y macOS. Los comandos son los mismos salvo dos diferencias que se indican en las secciones 4 y 6.
- **Git** y el repositorio del equipo clonado en el notebook.
- Los tres contenedores de la semana 1 funcionando: es la verificación de entrada.
- Roles definidos: un integrante opera la terminal, el otro registra en `mediciones.md`. Rotan en el Paso 3.

## 4. Instalación

1. Descargar `semana02.zip` desde la plataforma del curso.
2. Descomprimirlo **dentro del repositorio del equipo**, de modo que quede la carpeta `semana02/` al mismo nivel que el material de la semana 1.
3. Abrir una terminal y entrar a la carpeta:

```bash
cd ruta/del/repositorio-equipo/semana02      # en Windows: ruta\del\repositorio-equipo\semana02
```

4. Construir y levantar los dos contenedores (la primera vez demora 1 a 3 minutos):

```bash
docker compose up -d --build
docker compose ps          # cliente Up, servidor Up
```

5. Definir el atajo que se usa en todo el laboratorio. `c` significa "ejecutar dentro del contenedor cliente". Dura mientras la ventana de la terminal esté abierta; si la cierran, vuelvan a definirlo. Esta es la primera diferencia entre sistemas:

```bash
# Windows (PowerShell)
function c { docker compose exec cliente @args }
```

```bash
# Linux / macOS (bash o zsh)
c() { docker compose exec cliente "$@"; }
```

6. Verificar que el cliente ve al servidor por nombre:

```bash
c ping -c 2 servidor
```

Si el ping falla: `docker compose down`, borrar una red vieja de la semana 1 con `docker network rm sd_net`, y volver a levantar.

## 5. Qué deben hacer: los cinco pasos

Cada paso termina con números anotados en `mediciones.md`. Un número sin unidad, o sin la condición en que se midió, no sirve.

### Paso 1 — Línea base (14:30–14:37)

```bash
c ping -c 10 servidor
docker compose exec -d servidor iperf3 -s      # servidor iperf3 en segundo plano
c iperf3 -c servidor -t 5
```

Anotar: RTT promedio del ping (ms) y throughput de iperf3 (Gbit/s). Estos son los valores de "la red perfecta" que las falacias suponen.

### Paso 2 — 100 llamadas con la red sana (14:37–14:45)

```bash
c python cliente.py
c env N_LLAMADAS=1000 python cliente.py
docker compose logs servidor
```

Anotar en la fila `0 ms (base)`: total, promedio y máximo. Observen que el total es N × promedio, porque cada llamada espera a la anterior.

### Paso 3 — Inyectar latencia (14:45–15:05)

La primera regla se crea con `add`; las siguientes se cambian con `change`.

```bash
c tc qdisc add dev eth0 root netem delay 50ms
c ping -c 3 servidor                 # debe mostrar ~50 ms
c python cliente.py

c tc qdisc change dev eth0 root netem delay 200ms
c python cliente.py

c tc qdisc change dev eth0 root netem delay 500ms
c python cliente.py
```

Antes de ejecutar cada nivel, calculen cuánto debería tardar el total y anótenlo. Después comparen con lo medido. Pregunta guía para el informe: ¿la degradación es lineal? ¿Qué pasa con el máximo? ¿Cambió algo del lado del servidor?

**Pausa 15:05–15:15.**

### Paso 4 — Pérdida de paquetes y falla provocada (15:15–15:35)

Solo pérdida, sin retardo (`netem` reemplaza la regla anterior):

```bash
c tc qdisc change dev eth0 root netem loss 1%
c iperf3 -c servidor -t 5
c python cliente.py
# repetir con  loss 5%  y  loss 20%
```

Anotar por cada nivel: throughput de iperf3, total del cliente y una observación. Fíjense en que el cliente sigue "funcionando" pero el máximo se dispara: TCP está retransmitiendo en silencio.

**Falla provocada.** Esta es la parte más importante del laboratorio:

```bash
c tc qdisc change dev eth0 root netem loss 100%
c python cliente.py
```

No pasa nada. Esperen 60 segundos mirando la pantalla. El programa no muestra error, no termina, no se entera de que la red desapareció. Aborten con `Ctrl+C`. Ahora el mismo cliente con una sola variable distinta:

```bash
c env TIMEOUT_S=3 python cliente.py
```

Anotar en la fila `100%`: cuánto esperaron antes de abortar, si el servidor registró algo (`docker compose logs servidor`), y qué debería hacer una aplicación después de un timeout: reintentar, avisar o abortar.

### Paso 5 — Registro, commit y push (15:35–15:50)

1. Completar todas las filas de `mediciones.md`, incluida la sección final "Falacia que asumimos sin advertirlo".
2. Subir al repositorio del equipo:

```bash
git add semana02/mediciones.md
git commit -m "Semana 2: mediciones de latencia y perdida (Lab 1)"
git push
```

3. Confirmar en GitHub que `mediciones.md` quedó visible. Plazo: **15:50**.

### Limpieza (15:50–15:55)

```bash
c tc qdisc del dev eth0 root
docker compose down -v
docker network ls          # sd_net no debe aparecer
```

Es obligatorio: la sala se usa a las 16:00 para otro curso y una red `sd_net` huérfana provoca errores en la semana 4.

## 6. Plan B: si `tc` no funciona

Si al crear la regla aparece `RTNETLINK answers: Operation not supported`, el kernel de ese notebook no trae el módulo `netem` (pasa en algunas versiones de WSL2 en Windows y de la VM de Docker Desktop en macOS; en Linux nativo casi nunca). En ese caso la latencia la simula el servidor en lugar de la red:

Segunda diferencia entre sistemas, solo la forma de definir la variable:

```bash
# Windows (PowerShell)
$env:SIMULAR_LATENCIA_MS = "200"
docker compose up -d --force-recreate servidor
c python cliente.py
```

```bash
# Linux / macOS
export SIMULAR_LATENCIA_MS=200
docker compose up -d --force-recreate servidor
c python cliente.py
```

Repetir con 50 y 500. Se pierden las mediciones de ping/iperf3 y las de pérdida de paquetes; las del cliente se mantienen. Anotar en `mediciones.md`: "Plan B: latencia simulada en el servidor".

## 7. Entregables

| Entregable | Formato | Plazo | Carácter |
|---|---|---|---|
| `semana02/mediciones.md` completo | Commit en el repositorio del equipo | Viernes 28-08, 15:50 | Obligatorio |
| Informe breve | `semana02/informe.md` o PDF en el repositorio, máximo 2 planas, por equipo | Miércoles 02-09, 23:59 | Formativo, sin nota; retroalimentación el jueves 03-09 |

### Estructura del informe

1. **Entorno y método** (¼ plana): equipo, sistema operativo y versión de Docker, cómo se midió, si se usó Plan B.
2. **Resultados** (½ plana): la tabla de `mediciones.md` y un gráfico de tiempo total versus latencia.
3. **Observado vs esperado** (½ plana): dónde coincidieron los cálculos y dónde no; explicación de las diferencias.
4. **La falacia que asumimos** (½ plana): cuál es, en qué línea de `cliente.py` se ve, y qué cambio la corregiría.
5. **Relación con la investigación** (¼ plana): qué falacia ha afectado a la aplicación que investigan para la Evaluación 1.

El análisis de este informe se reutiliza en la prueba parcial del 25-09.

## 8. Variables de entorno de `cliente.py` y `servidor.py`

| Variable | Contenedor | Por defecto | Uso |
|---|---|---|---|
| `SERVIDOR_HOST` | cliente | `servidor` | Nombre del nodo servidor en `sd_net` |
| `PUERTO` | ambos | `5000` | Puerto TCP |
| `N_LLAMADAS` | cliente | `100` | Cantidad de llamadas |
| `TIMEOUT_S` | cliente | `0` (sin límite) | Segundos máximos de espera por respuesta |
| `SIMULAR_LATENCIA_MS` | servidor | `0` | Plan B: retardo artificial por llamada |

Se pasan con `c env VARIABLE=valor python cliente.py` en el cliente (igual en todos los sistemas), o definiendo la variable en la terminal (`$env:VARIABLE="valor"` en PowerShell, `export VARIABLE=valor` en Linux/macOS) y luego `docker compose up -d --force-recreate servidor`.

## 9. Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `docker: command not found` o `error during connect` | Docker Desktop no está iniciado | Abrirlo y esperar a que arranque |
| `network sd_net already exists` | Red huérfana de la semana 1 | `docker network rm sd_net` |
| `ping: servidor: Name or service not known` | El servidor no está en la misma red o no arrancó | `docker compose ps`, luego `docker compose up -d` |
| `RTNETLINK answers: Operation not permitted` | Falta `cap_add: NET_ADMIN` | No editar `docker-compose.yml`; volver al original |
| `RTNETLINK answers: Operation not supported` | Kernel sin `netem` | Plan B (sección 6) |
| `Error: Exclusivity flag on, cannot modify` en `tc add` | Ya existe una regla | Usar `change`, o `del` y luego `add` |
| `iperf3: error - unable to connect` | El servidor iperf3 no está corriendo | `docker compose exec -d servidor iperf3 -s` |
| `c` no se reconoce como comando | Se cerró la terminal | Volver a definir la función (sección 4, paso 5) |
| `permission denied while trying to connect to the Docker daemon` (Linux) | El usuario no está en el grupo `docker` | `sudo usermod -aG docker $USER`, cerrar sesión y volver a entrar |

## 10. Bibliografía de la semana

- Tanenbaum, A., Van Steen, M. (2017). *Sistemas distribuidos, principios y paradigmas*. Prentice Hall. Capítulo 1, sección 1.2 (transparencias).
- Deutsch, P. / Gosling, J. *The Fallacies of Distributed Computing*.
- Documentación de `tc-netem` (`man tc-netem`) e `iperf3` (`iperf3 --help`).
