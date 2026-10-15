# Semana 7 — Observaciones RepoSync

**Tema asignado:** 04, control de versiones distribuido (simulación).
**Estado:** artefactos preparados para volver a probar el despliegue completo en Docker.
No se presentan predicciones ni resultados de ejemplo como mediciones reales.

## Paso 1 — Diagrama de despliegue

Se incluyen diagramas v1 y v2 en formato `.drawio` editable y `.png`.
V1: tres contenedores TCP; V2: cinco contenedores, tres niveles funcionales,
`sd_net`, única entrada pública Nginx 8080→80, API 8000 y TCP 5000 internos.
El estado (ramas, commits y HEAD) vive sólo en RAM del servidor TCP con Lock.

## Paso 2 — Revisión por pares

**Pendiente:** no hay revisión externa documentada. La pauta de cotejo del docente
está en `diagramas/pauta_cotejo_diagramas.md`. No inventar una evaluación de otro equipo.

## Paso 3 — Adaptación de operación REST

Pruebas realmente comunicadas sobre el despliegue anterior en Fedora:

| Solicitud | HTTP | Evidencia |
|---|---:|---|
| `GET /repos` directo a api1 | 200 | `repositorios:["proyecto"]` |
| `POST /repos/proyecto/ramas/main/commits`, base 0 | 201 | `head:1` |
| Repetir POST sobre base 0 | 409 | `CONFLICTO HEAD=1` |
| `GET /salud` directo a api2 | 200 | `replica:api2` |

El código de la puerta traduce TCP `OK` a JSON y TCP `ERROR` a códigos HTTP.
Se incluye la API completa con los recursos descritos en `interfaz_http.md`.

## Paso 4 — Dos réplicas y Nginx

En el despliegue anterior, cuatro consultas por Nginx devolvieron `api1` cuatro veces,
aunque `api2` respondía directamente. El comando `nginx -T` mostró ambas réplicas
y se observaron 14 workers. **Corrección preparada:** `zone api 64k;` en Nginx,
para compartir el estado de Round Robin entre workers.

**Pendiente registrar el nuevo resultado real:**

```bash
docker compose exec cliente python cliente_http.py --repetir 8 GET /salud
docker compose exec cliente python verificar_semana07.py
```

Con ambas réplicas activas, deben verse respuestas de `api1` y `api2` y el mismo
valor `HEAD` en ambas, porque consultan un backend TCP compartido.

## Paso 5 — Falla en dos tiempos

**Predicción ANTES de ejecutar:**

1. `docker compose kill api1`: Nginx seguirá atendiendo `GET /repos` mediante
   `api2` (HTTP 200); la primera solicitud puede demorar por detección del fallo.
2. `docker compose kill servidor`: `GET /repos` no tendrá backend TCP y
   devolverá HTTP 503, aunque `GET /salud` de API seguirá respondiendo 200.
3. Recuperación con `docker compose up -d`: servicio accesible otra vez; la RAM
   del servidor reiniciado se restablecerá y `main` tendrá HEAD=0.

**Resultados del nuevo ensayo:** pendientes de ejecutar y registrar.

```bash
docker compose kill api1
docker compose exec cliente python cliente_http.py --repetir 4 GET /repos
docker compose kill servidor
docker compose exec cliente python cliente_http.py --repetir 2 GET /repos
docker compose up -d
docker compose exec cliente python cliente_http.py GET /repos/proyecto/ramas/main
```

## Conclusión prevista y límites

La separación de la API sin estado permite replicar la puerta REST sin dividir
las revisiones; `servidor.py` sigue siendo el único punto de falla y no persiste
ninguna revisión en disco. Un 200 en `/salud` prueba la puerta API, no el backend.
La continuidad ante la caída de una API y la respuesta 503 del servidor caído
requieren confirmación en la nueva ejecución.

**IA generativa:** se utilizó para preparar la adaptación de la plantilla,
los diagramas y pruebas; el estudiante debe revisar su funcionamiento.
