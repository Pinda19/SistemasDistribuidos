# RepoSync — Semana 7: REST, FastAPI y Nginx

**Tema 04:** Control de versiones distribuido. Simulación didáctica de referencias HEAD,
ramas, commits e historial. No implementa Git real ni almacena archivos de repositorio.

## Instalación (Fedora / Docker Compose)

**Esta carpeta `semana07/` está completa; no copiar ni combinar con la plantilla de inventario.**
Desde la raíz del repositorio, descomprimir el ZIP para reemplazar `semana07/`.
Si Semana 6 sigue activa, detenerla antes porque utiliza `sd_servidor` y `sd_cliente`.

```bash
cd ~/Escritorio/SistemasDistribuidos/semana06
# Solo si estaba levantada: docker compose down
cd ../semana07
docker compose down --remove-orphans
# Descomprimir el ZIP en la raiz del repositorio ANTES de los comandos siguientes.
docker compose config -q
docker compose up -d --build --force-recreate
docker compose ps
```

**Prueba en un solo comando:**

```bash
docker compose exec cliente python verificar_semana07.py
```

Prueba manual del balanceo (en las respuestas deben verse `api1` y `api2`):

```bash
docker compose exec cliente python cliente_http.py --repetir 8 GET /salud
```

Otras pruebas:

```bash
docker compose exec cliente python cliente_http.py GET /repos
docker compose exec cliente python cliente_http.py GET /repos/proyecto/ramas/main
docker compose exec cliente python cliente_http.py GET /repos/proyecto/ramas/main/historial
docker compose exec cliente python cliente_http.py POST /repos/proyecto/ramas nueva=desarrollo origen=main
```

En navegador: http://localhost:8080/docs (documentación FastAPI generada automáticamente).

## Arquitectura

Cliente/navegador -> `nginx:80` (publicado en `localhost:8080`) ->
`api1:8000` o `api2:8000` (FastAPI, **sin estado**) ->
`servidor:5000` (TCP UTF-8, hilos y Lock, **única fuente del estado**).
Todos los contenedores están en `sd_net`; no se publica el puerto TCP 5000.
El estado está únicamente en la RAM del servidor, por lo que se reinicia al recrearlo.

`nginx.conf` incluye `zone api 64k` para compartir el reparto Round Robin entre
múltiples procesos worker (la corrección al caso de 14 workers observado).
Las consultas HTTP de `/salud` prueban la disponibilidad de cada API, **no** la del servidor TCP.
Para verificar el servidor TCP, usar `GET /repos`.

**Importante:** `servidor.py` es el servidor de Semana 6, sin reescritura de su dominio.
Compose fuerza `SIN_LOCK=0` y `PAUSA_CARRERA=0`: modo correcto para Semana 7.

## Ensayo de fallos (predicción previa en `observaciones.md`)

```bash
# Tiempo 1: falla una API; la otra responde
docker compose kill api1
docker compose exec cliente python cliente_http.py --repetir 4 GET /repos

# Tiempo 2: falla el unico servidor TCP; ambas API responden 503
docker compose kill servidor
docker compose exec cliente python cliente_http.py --repetir 2 GET /repos

# Recuperación: la RAM se restablece
docker compose up -d
docker compose exec cliente python cliente_http.py GET /repos/proyecto/ramas/main
```

La primera solicitud tras la caída de `api1` puede tardar por detección de fallo
antes de que Nginx enrute a `api2`.

## Contenido

- `servidor.py`: servidor TCP concurrente RepoSync (copiado de Semana 6).
- `api.py`: puerta REST sin estado.
- `nginx.conf`: balanceo de dos API, zona compartida.
- `docker-compose.yml`: cinco servicios y comprobaciones de salud.
- `cliente_http.py` y `cliente.py`: clientes HTTP y TCP.
- `cliente_carga.py`: cliente concurrente TCP reutilizado.
- `verificar_semana07.py`: prueba automatizada de toda la cadena HTTP.
- `diagramas/despliegue_v1.*` y `diagramas/despliegue_v2.*`: diagramas editables draw.io + PNG.
- `interfaz_http.md`, `observaciones.md`, `guion_demo.md`: documentación de entrega.

## Uso de IA

Se utilizó asistencia de IA para adaptar la plantilla del curso al tema RepoSync,
redactar documentación y crear verificaciones automáticas. Los resultados reales
se deben confirmar en el equipo del estudiante antes de declararlos aprobados.
