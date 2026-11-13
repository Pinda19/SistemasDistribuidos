# RepoSync — Semana 9 · Serialización JSON y binaria

Implementación del laboratorio **Serialización explícita** para el dominio «control de versiones simplificado». Se adaptó la plantilla oficial de la Semana 9 manteniendo las operaciones de RepoSync: `HOLA`, `REPOS`, `CLONAR`, `RAMA`, `PUSH`, `HISTORIAL`, `ESPERA` y `SALIR`.

> Este es un simulador educativo. No es Git real: el repositorio `proyecto` y su rama `main` se crean al iniciar, los commits y ramas viven en RAM y el reinicio del servidor borra los cambios.

## Arquitectura y alcance

- Contenedor `sd_cliente` → TCP `servidor:5000` → contenedor `sd_servidor`; ambos en red Docker `sd_net`.
- Un `threading.Thread` por conexión; `threading.Lock` protege el estado compartido y la comparación/actualización de HEAD.
- Solicitud y respuesta estructuradas (`mensajes.py`), con versión `2`, ID de correlación y cuerpo codificado en JSON o binario (`codec.py`). Cada mensaje va precedido por 4 bytes de longitud.
- La aplicación REST de la Semana 7 (`api.py`, `nginx.conf` y otros archivos heredados) se **conserva como fuente**, pero **no se ejecuta** en este `docker-compose.yml`: aún utiliza el protocolo de texto por líneas. Adaptarla es opcional y requeriría cambiar la comunicación al nuevo codec.

## Preparación y pruebas (PowerShell, desde `semana09/`)

Detener cualquier despliegue anterior de `semana07` para evitar conflictos con los nombres de los contenedores.

```powershell
$env:CODEC = "json"
docker compose config -q
docker compose up -d --build servidor cliente
docker compose ps
docker compose exec cliente python codec.py
```

**Operaciones de dominio JSON (estado recién iniciado):**

```powershell
docker compose exec cliente python cliente.py HOLA estudiante
docker compose exec cliente python cliente.py REPOS
docker compose exec cliente python cliente.py RAMA proyecto demo main
docker compose exec cliente python cliente.py PUSH proyecto demo 0 primer_cambio
docker compose exec cliente python cliente.py HISTORIAL proyecto demo
docker compose exec cliente python cliente.py PUSH proyecto demo 0 segundo_cambio
```

La última línea debe devolver `ERROR CONFLICTO HEAD=1`. Si `demo` ya existe, reiniciar el servidor o elegir otro nombre de rama para la prueba.

**Medición de los dos codecs (sin utilizar la red):**

```powershell
docker compose exec cliente python bench_codec.py 10000
```

En `observaciones.md` y `protocolo.md` se registraron **los resultados reales suministrados por el estudiante**. No deben confundirse con la salida de una ejecución futura: cada computador puede dar tiempos diferentes.

**Cambiar a binario:**

```powershell
$env:CODEC = "bin"
docker compose up -d --force-recreate servidor cliente
docker compose logs servidor --tail 5
docker compose exec cliente python cliente.py REPOS
```

La recreación reinicia el estado en RAM. Se probó en el equipo con binario: `REPOS`, `RAMA`, `PUSH`, conflicto y los cuatro modos de `cliente_malo.py`. La prueba `HOLA` en binario es opcional como comprobación adicional, ya que no se ha recibido su salida del equipo.

**Fallas del protocolo (repetir en JSON y binario):**

```powershell
docker compose exec cliente python cliente_malo.py version
docker compose exec cliente python cliente_malo.py largo
docker compose exec cliente python cliente_malo.py basura
docker compose exec cliente python cliente_malo.py cruzado
docker compose exec cliente python cliente.py REPOS
```

`version` envía un mensaje de versión antigua; `largo`, un enmarcado incompleto; `basura`, bytes corruptos; `cruzado`, el codec contrario. Un `REPOS` correcto después comprueba que el servidor no cayó.

## Archivos que se entregan

- `mensajes.py`, `codec.py`: esquema de mensajes y ambos codecs.
- `servidor.py`, `cliente.py`: servicio funcional de RepoSync en los dos modos.
- `cliente_malo.py`, `bench_codec.py`: fallas y mediciones.
- `docker-compose.yml`: servicios TCP con `CODEC=${CODEC:-json}`.
- `protocolo.md`: contrato y operaciones (documento v3; mensajes versión 2).
- `observaciones.md`: pruebas, tabla de mediciones y evidencia real.
- Archivos heredados de Semana 7: documentación, diagramas y REST (no activados en este laboratorio).

## Entrega al repositorio

Desde la raíz de `SistemasDistribuidos`:

```powershell
git status
git add semana09
git commit -m "Semana 9: serializacion JSON y binaria de RepoSync"
git pull --rebase
git push
```

Si ya existe un commit con esos cambios, `git commit` puede indicar que no hay nada por registrar; en ese caso basta comprobar `git status` y `git push`. Completar los datos del equipo y la fecha de ejecución que permanecen como campos vacíos en `observaciones.md`.
