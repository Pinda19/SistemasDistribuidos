# Semana 7 — Observaciones del laboratorio RepoSync

**Tema asignado:** 04. Control de versiones distribuido (Git como caso de estudio).  
**Servicio propio:** RepoSync, simulación de un repositorio remoto con ramas, revisiones e historial. No implementa Git completo.  
**Entorno de prueba:** Fedora Linux, Docker Compose, contenedores Linux, red `sd_net`.  
**Estado del registro:** pruebas funcionales, balanceo y fallas realizadas; revisión por otro equipo **pendiente**. Los resultados que siguen proceden de salidas de consola obtenidas durante el laboratorio, no de ejemplos hipotéticos.

## Paso 1 — Diagramas de despliegue

Se prepararon los diagramas editables y sus imágenes en `diagramas/despliegue_v1.drawio`, `despliegue_v1.png`, `despliegue_v2.drawio` y `despliegue_v2.png`.

- **v1 (Semana 6):** `sd_cliente`, `sd_carga` y `sd_servidor` dentro de `sd_net`; protocolo TCP de texto por el puerto `5000` publicado en el anfitrión. El servidor atiende una conexión por hilo y protege operaciones críticas mediante `threading.Lock`.
- **v2 (Semana 7):** `sd_nginx`, `sd_api1`, `sd_api2`, `sd_servidor` y `sd_cliente` dentro de `sd_net`. Nginx publica `8080:80`, las API FastAPI escuchan en `8000` (interno) y el servidor TCP escucha en `5000` (interno). Las dos API traducen HTTP/JSON al protocolo TCP y no almacenan ramas ni commits localmente.
- **Estado compartido:** repositorio `proyecto`, referencias de ramas, commits, historial y `HEAD` en la RAM de `sd_servidor`, protegido por Lock. Los datos no son persistentes. `sd_servidor` constituye un punto único de falla.

Las flechas y puertos muestran el recorrido **cliente → Nginx → api1/api2 → servidor TCP**. El archivo `docker-compose.yml` define los cinco servicios y la única publicación exterior `8080:80`.

## Paso 2 — Revisión por pares

**Pendiente:** no se realizó ni se recibió una revisión documentada por otro equipo. Se conserva la pauta de cotejo del docente en `diagramas/pauta_cotejo_diagramas.md`. No se presenta una revisión propia como si fuera realizada por terceros.

## Paso 3 — Adaptación del protocolo TCP a REST

Se adaptó `api.py` al dominio RepoSync sin reemplazar la lógica del servidor TCP de Semana 6. Las peticiones HTTP se traducen a `REPOS`, `CLONAR`, `HISTORIAL`, `RAMA` y `PUSH` por TCP; sus resultados se convierten en JSON y códigos HTTP.

**Pruebas manuales verificadas en Fedora:**

| Solicitud u operación | Resultado observado | Interpretación |
|---|---|---|
| `GET /repos` dirigido a `api1` | `200`, `{"repositorios":["proyecto"],"replica":"api1"}` | Consulta de repositorio |
| `POST /repos/proyecto/ramas/main/commits` con `base=0`, `mensaje=primer_commit_rest` | `201`, `head:1` | Publicación aceptada |
| Repetir `POST` con `base=0` | `409`, `CONFLICTO`, `HEAD=1` | Revisión base obsoleta; operación rechazada |
| `GET /salud` dirigido directamente a `api2` | `200`, `replica:api2` | Segunda réplica disponible |

**Prueba automática efectivamente ejecutada:**

```bash
docker compose exec cliente python verificar_semana07.py
```

El programa terminó con `PRUEBA COMPLETA: todas las verificaciones pasaron`. Comprobó doce respuestas de salud, disponibilidad de ambas réplicas, `GET /repos` (200), consulta de rama (200), historial (200), repositorio inexistente (404), creación de rama (201), `PUSH` correcto (201) y `PUSH` obsoleto (409). Creó una rama temporal `prueba_1792034905529014928` en la RAM del servidor.

## Paso 4 — Balanceo entre dos réplicas y Nginx

Inicialmente, cuatro solicitudes `GET /salud` mediante Nginx fueron atendidas por `api1`, pese a que `api2` funcionaba. `nginx -T` confirmó que ambas figuraban en el `upstream`; se observaron 14 workers. Se incorporó `zone api 64k;` al bloque `upstream api` para compartir el estado del balanceo entre workers.

**Resultado real posterior a la corrección:** el verificador ejecutó doce solicitudes a `http://nginx/salud` y recibió exactamente:

```text
api1, api2, api1, api2, api1, api2,
api1, api2, api1, api2, api1, api2
```

Todas fueron exitosas (`200`); Nginx distribuyó efectivamente las solicitudes. Ambas API consultan el mismo servidor TCP, por lo que las revisiones y ramas del dominio no se duplican ni divergen en cada réplica. La alternancia de `/salud` comprueba el reparto, mientras que la prueba REST confirma el acceso al backend compartido; no constituye por sí sola una prueba de persistencia ni de alta disponibilidad del servidor TCP.

## Paso 5 — Falla provocada en dos tiempos

### Tiempo 1 — Caída de una réplica REST

**Predicción anotada antes de la prueba:** tras ejecutar `docker compose kill api1`, Nginx debería continuar respondiendo por `api2`, posiblemente con una demora o error transitorio mientras detecta la caída.

**Ejecución:** se detuvo `api1` y se ejecutó:

```bash
docker compose exec cliente python cliente_http.py --repetir 4 GET /salud
```

**Resultado observado:** cuatro respuestas `HTTP 200`, todas desde `api2`, con duraciones indicadas por el cliente de `0.01 s`, `0.00 s`, `0.00 s` y `0.00 s`. En esta serie no se observó un error HTTP ni una demora significativa de la primera solicitud.

**Conclusión:** Nginx siguió sirviendo el endpoint de salud cuando cayó una de las dos réplicas. Este resultado demuestra redundancia del nivel REST, no del backend TCP.

### Tiempo 2 — Caída del servidor TCP central

**Predicción anotada antes de la prueba:** al detener `sd_servidor`, las solicitudes de repositorios recibirían `HTTP 503`, porque ninguna de las API puede acceder al estado del dominio.

**Ejecución:** se inició nuevamente `api1`, se detuvo `servidor` y se consultó:

```bash
docker compose up -d api1
docker compose kill servidor
docker compose exec cliente python cliente_http.py --repetir 2 GET /repos
```

**Resultados observados:**

```text
503   4.89 s  {"detail":{"error":"SERVIDOR_NO_DISPONIBLE","detalle":"gaierror","replica":"api1"}}
503   7.53 s  {"detail":{"error":"SERVIDOR_NO_DISPONIBLE","detalle":"gaierror","replica":"api1"}}
```

**Interpretación:** `gaierror` representa un fallo al resolver el nombre del servidor desde la API tras la caída del contenedor. El cliente recibió errores controlados HTTP 503. Se registraron demoras de `4.89 s` y `7.53 s` para las dos solicitudes observadas. El resultado confirma que el servidor TCP es un punto único de falla: disponer de dos API no evita la indisponibilidad de las operaciones sobre repositorios.

### Recuperación y persistencia

**Predicción anotada antes de la prueba:** el servidor volverá a estar accesible al iniciarlo, pero se perderá la rama temporal porque las referencias y commits sólo están en RAM.

**Ejecución:**

```bash
docker compose up -d servidor
docker compose exec cliente python cliente_http.py GET /repos/proyecto/ramas/prueba_1792034905529014928
```

**Resultado observado:**

```text
404   0.01 s  {"detail":{"error":"RAMA_NO_EXISTE","detalle":"","replica":"api1"}}
```

**Conclusión:** una consulta llegó nuevamente al servidor y éste pudo responder; sin embargo, la rama creada antes del reinicio ya no existía. Esto verifica la pérdida de estado de RAM. No se implementó persistencia en disco, recuperación de commits ni réplicas del backend en Semana 7.

## Conclusión general y pendientes

La arquitectura de tres niveles de RepoSync separa una entrada HTTP mediante Nginx, dos puertas REST sin estado y un único servidor TCP con estado. Se verificaron el balanceo entre `api1` y `api2`, los códigos HTTP de dominio (`200`, `201`, `404`, `409`), la continuidad tras la caída de una API, el `503` cuando cae el backend y la pérdida de ramas tras el reinicio del servidor.
