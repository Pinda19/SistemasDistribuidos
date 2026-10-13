# RepoSync — Tema 04: Control de versiones distribuido

Simulación didáctica de un **servidor remoto de revisiones**, desarrollada a partir de la plantilla oficial de Semana 6. **No implementa Git real** ni almacena archivos. Los clientes simulan conocer una revisión anterior del repositorio y envían esa base al servidor.

## Requisitos

Docker Engine con Docker Compose v2 o Docker Desktop en Windows 10. Usar PowerShell. Detener antes otros laboratorios que usen los mismos nombres `sd_servidor` y la red `sd_net`.

## Levantar

```powershell
docker compose up -d --build
docker compose ps
docker compose exec cliente python cliente.py
```

## Prueba interactiva (escribir uno por uno)

```text
HOLA equipo
REPOS
CLONAR proyecto main
PUSH proyecto main 0 primer_cambio
HISTORIAL proyecto main
RAMA proyecto desarrollo main
CLONAR proyecto desarrollo
PUSH proyecto main 0 intento_desactualizado
SALIR
```

Respuesta esperada del `PUSH` desactualizado: `ERROR CONFLICTO HEAD=1`.

## Competencia: 20 clientes con la misma base

En PowerShell:

```powershell
$env:SIN_LOCK="1"
docker compose up -d --force-recreate servidor
docker compose exec carga python cliente_carga.py --clientes 20 --comando "PUSH proyecto main 0 cambio"
```

Anotar `RESUMEN: OK=... ERROR=...`. Sin Lock, puede aparecer más de un OK para la misma base (resultado incorrecto).

```powershell
$env:SIN_LOCK="0"
docker compose up -d --force-recreate servidor
docker compose exec carga python cliente_carga.py --clientes 20 --comando "PUSH proyecto main 0 cambio"
```

Con Lock, **un** OK y **19** conflictos; consultar `CLONAR proyecto main` para confirmar `HEAD=1`. Repetir la prueba reiniciando servidor, tres veces.

## Prueba de operaciones lentas

```powershell
docker compose exec carga python cliente_carga.py --clientes 5 --comando "ESPERA 2"
```

El TOTAL esperado con hilos es aproximadamente 2 segundos (medir, no inventar).

## Falla provocada

```powershell
docker compose exec -d carga python cliente_carga.py --clientes 3 --comando "ESPERA 5"
Start-Sleep -Seconds 1
docker compose kill carga
docker compose logs --tail 30 servidor
docker compose up -d carga
docker compose exec cliente python cliente.py
```

Probar `CLONAR proyecto main`, `SALIR`; registrar lo que realmente aparezca.

## Trabajo autónomo y limpieza

Tras demostrar la carrera, quitar la pausa artificial de la sección crítica en la versión robusta:

```powershell
$env:PAUSA_CARRERA="0"
docker compose up -d --force-recreate servidor
```

Validar luego el funcionamiento normal, documentar errores y dejar evidencias en `observaciones.md`.

```powershell
docker compose down -v
```

## Nota sobre los archivos del curso

- `cliente.py` y `Dockerfile`: tomados de la plantilla del laboratorio.
- `cliente_carga.py`: plantilla con un contador adicional de respuestas OK/ERROR para la carrera.
- `docker-compose.yml`: plantilla con variable opcional `PAUSA_CARRERA`.
- `servidor.py`, `servidor_secuencial.py`, `protocolo.md`: adaptación al tema 04.
- No reemplazar la Semana 4 original sin revisarla: contiene un protocolo previo diferente.
