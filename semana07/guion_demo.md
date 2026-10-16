# Evaluación 3 — Guion de demostración de RepoSync

**Tema asignado:** 04. Control de versiones distribuido, con Git como caso de estudio.  
**Servicio:** RepoSync.
**Entorno:** Fedora, Windows, Docker Compose, cinco servicios en `sd_net`.

## Preparación previa (antes de presentar)

Desde la carpeta `~/Escritorio/SistemasDistribuidos/semana07`:

```bash
docker compose up -d --build
docker compose ps
docker compose exec cliente python verificar_semana07.py
```

Verificar que estén activos `sd_servidor`, `sd_api1`, `sd_api2`, `sd_nginx` y `sd_cliente` y que la prueba termine con **`PRUEBA COMPLETA`**. La prueba automática crea una rama temporal en RAM; eso es normal. Abrir `diagramas/despliegue_v2.png` y, si se desea, `http://localhost:8080/docs` antes de comenzar.

**No reiniciar el servidor entre la creación de la rama de demostración y la falla final**, pues eso borraría su estado y arruinaría la evidencia de recuperación.

## Guion por minutos

| Momento aproximado | Mostrar | Qué explicar |
|---|---|---|
| 0:00–1:30 | `diagramas/despliegue_v2.png` | Nginx recibe HTTP; `api1` y `api2` son puertas FastAPI sin estado; `sd_servidor` atiende TCP, aplica reglas y guarda ramas/commits en RAM con `threading.Lock`. |
| 1:30–2:30 | `docker compose ps` y `/docs` | Cinco contenedores en `sd_net`. Solo Nginx publica `8080:80`; API `8000` y TCP `5000` son internos. |
| 2:30–4:00 | Verificador y una operación REST | Nginx reparte entre API; FastAPI convierte HTTP/JSON en comandos de texto (`REPOS`, `CLONAR`, `RAMA`, `PUSH`, `HISTORIAL`). `PUSH` con base obsoleta recibe HTTP 409. |
| 4:00–5:00 | Crear una rama de demostración | Dejar evidencia de un dato en RAM antes del fallo. |
| 5:00–6:00 | `docker compose kill api1` | Primera falla: Nginx mantiene el servicio con `api2`; se esperan HTTP 200. |
| 6:00–7:30 | Recuperar `api1`, matar `servidor` | Segunda falla: ambas API dependen del mismo backend; se esperan HTTP 503 en `/repos`. |
| 7:30–9:00 | Levantar servidor y consultar rama | El servicio se recupera, pero la rama anterior ya no existe: HTTP 404, por falta de persistencia. Conclusiones y límites. |

## Secuencia de comandos para la demostración

Ejecutarlos desde `semana07` y **esperar cada resultado** antes de continuar.

### A. Arquitectura y balanceo

```bash
docker compose ps
docker compose exec cliente python cliente_http.py --repetir 6 GET /salud
```

**Predicción:** seis respuestas HTTP 200 procedentes de `api1` y `api2` (pueden alternarse); esto verifica la distribución de la puerta HTTP, **no** por sí solo el estado del backend. El estado lo conserva únicamente el servidor TCP.

```bash
docker compose exec cliente python cliente_http.py GET /repos
docker compose exec cliente python cliente_http.py GET /repos/proyecto/ramas/main
```

**Predicción:** HTTP 200. El repositorio inicial es `proyecto`, rama `main`.

**Si el profesor pide el conflicto:** ejecutar `docker compose exec cliente python verificar_semana07.py`. El script crea una rama temporal, publica un commit y comprueba que intentar otro `PUSH` con la base antigua obtiene 409, sin modificar `main`.

### B. Crear una rama para demostrar pérdida de datos

```bash
docker compose exec cliente python cliente_http.py POST /repos/proyecto/ramas nueva=demo_eval3 origen=main
docker compose exec cliente python cliente_http.py GET /repos/proyecto/ramas/demo_eval3
```

**Predicción:** creación HTTP 201 y consulta HTTP 200. Conservar el nombre **`demo_eval3`** para la última prueba. Si existe por un ensayo anterior, usar otro nombre (por ejemplo `demo_eval3_b`) y emplearlo también en la consulta final.

### C. Falla 1: cae una puerta REST

**Antes del comando, decir:** «Predigo que caerá una réplica FastAPI, pero el servicio HTTP seguirá disponible a través de la otra réplica. Podría existir un retardo transitorio».

```bash
docker compose kill api1
docker compose exec cliente python cliente_http.py --repetir 4 GET /repos
```

**Esperado:** HTTP 200, atendido por `api2`. **Evidencia histórica ya obtenida:** al probar cuatro solicitudes a `/salud` después de matar `api1`, todas fueron `200` desde `api2` (0,01; 0,00; 0,00; 0,00 s). Si una primera consulta a `/repos` demora, explicar detección de fallo y reintento de Nginx; no prometer tiempo exacto.

### D. Falla 2: cae el único servidor TCP con estado

Recuperar primero la otra puerta REST para demostrar que ambas siguen dependiendo del backend:

```bash
docker compose up -d api1
docker compose kill servidor
docker compose exec cliente python cliente_http.py --repetir 2 GET /repos
```

**Antes de matar el servidor, decir:** «Predigo que el servicio de repositorios dejará de responder satisfactoriamente, aunque las API sigan levantadas, porque no hay réplica del estado TCP».

**Esperado:** dos HTTP 503 (`SERVIDOR_NO_DISPONIBLE`). **Evidencia histórica:** 503 en 4,89 s y otro 503 en 7,53 s, ambos con detalle `gaierror`. Esos tiempos **fueron los de la prueba anterior**, no una garantía para la nueva ejecución. `GET /salud` podría seguir devolviendo 200 porque comprueba la API, no el TCP.

### E. Recuperación y límite de persistencia

**Antes de levantar el servidor, decir:** «Predigo que volverá a funcionar, pero perderá la rama creada antes, porque el estado se guarda solamente en RAM».

```bash
docker compose up -d servidor
docker compose exec cliente python cliente_http.py GET /repos
docker compose exec cliente python cliente_http.py GET /repos/proyecto/ramas/demo_eval3
```

**Esperado:** `GET /repos` devuelve 200; `GET /repos/proyecto/ramas/demo_eval3` devuelve **404 `RAMA_NO_EXISTE`**. La prueba real anterior confirmó esta pérdida con la rama temporal `prueba_1792034905529014928` y un HTTP 404 en 0,01 s.

**Cierre sugerido:** «Nuestra arquitectura tolera la caída de una réplica HTTP, pero el servidor TCP sigue siendo un punto único de falla. Y, al guardar los datos en RAM, carece de durabilidad. Replicar y persistir el estado serían mejoras futuras. RepoSync simula conflictos y ramas de Git; no es Git implementado».

## Conceptos que debes poder explicar

- **Capas frente a niveles:** las capas son responsabilidades del código; los niveles son nodos o procesos que se comunican por red. La arquitectura de la semana 7 separa entrada, puerta REST y servidor de estado en tres niveles funcionales.
- **Concurrencia:** `sd_servidor` crea hilos para atender clientes. El Lock protege la modificación de referencias y commits. En Semana 6, 20 `PUSH` con la misma base dieron 11 aceptaciones sin Lock y solo 1 con Lock (19 conflictos), en tres ejecuciones con protección.
- **REST sin estado:** `api1` y `api2` no almacenan ramas ni commits. Cada `PUSH` HTTP lleva repositorio, rama y revisión base, de modo que puede atenderlo cualquiera de las dos.
- **Balanceo:** Nginx distribuye solicitudes a las API y usa `zone api 64k` para compartir la información de reparto entre varios workers.
- **Código 409:** indica que el HEAD real ya difiere de la revisión que el cliente usó como base; el servidor rechaza esa publicación.
- **Disponibilidad:** caer una API no equivale a caer el servidor TCP. Nginx proporciona redundancia en el nivel REST, no de datos.
- **Pérdida de datos:** sin almacenamiento persistente, reiniciar `sd_servidor` restablece `main` a HEAD=0 y borra ramas creadas durante la ejecución.
- **Git frente a RepoSync:** Git es distribuido, con repositorios completos en clones locales; RepoSync es deliberadamente una simulación cliente-servidor de referencias y conflictos para el laboratorio. No fingir que RepoSync implementa el modelo completo de Git.

## Plan B si algo falla durante la exposición

1. Revisar contenedores: `docker compose ps`.
2. Inspeccionar errores: `docker compose logs --tail 40 nginx api1 api2 servidor`.
3. Recuperar servicios: `docker compose up -d` y repetir `GET /repos`.
4. Si no se recupera a tiempo, mostrar `observaciones.md` con los resultados reales registrados y explicar en el diagrama cuál nodo falla; **no presentar esos registros históricos como ejecuciones nuevas**.

## Pendientes honestos

- **Revisión por pares:** todavía no se ha documentado; pedir al profesor cómo completarla si es obligatoria.
- **Ensayo desde un clon limpio:** verificarlo antes de la evaluación si el tiempo lo permite; no declararlo ejecutado sin realizarlo.
- **Duración oficial de la Evaluación 3:** el profesor no la especificó en el correo compartido; estos tiempos son una propuesta para ensayar, no una regla de la evaluación.

