# RepoSync — Semana 12: objetos distribuidos con Pyro5

**Equipo / integrante:** Thomas Pinda. **Dominio:** 04, control de versiones distribuido.
Adaptación de la plantilla del curso; `dominio.py` se copió sin modificaciones de semana11.

## Inicio rápido en Windows

La carpeta `semana12/` debe quedar al lado de `semana11/` en el repositorio.
Con Docker Desktop iniciado, desde la raíz:

```powershell
cd semana12
docker compose up -d --build
docker compose exec cliente python cliente_pyro.py uri
```

Si el último comando se ejecuta antes del registro inicial, repetirlo unos segundos después.
No se fijan nombres globales de contenedor, para evitar choques con semanas anteriores.

## Ejecutar y guardar los cinco experimentos

Desde `semana12/`, usar Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\pruebas.ps1
```

Este script construye y recrea los contenedores de ESTA semana, ejecuta los pasos,
provoca las caídas del laboratorio y guarda `evidencias/docker.txt`,
`evidencias/vigilar.txt` y `evidencias/cambio.txt`. No requiere Python en Windows.
Reinicia las revisiones simuladas en RAM; usar sobre los datos de laboratorio.
Finaliza con `PRUEBAS TERMINADAS` si los comandos y comprobaciones terminan correctamente.
Docker conserva los registros adicionales en `docker compose logs`.

Las pruebas de Docker ya fueron ejecutadas el 20-11-2026. Sus resultados están
incorporados en `observaciones.md` y la lista de calidad está marcada. Los registros
originales están en `evidencias/`; `docker_utf8.txt` es una copia legible de la captura.
No es necesario repetir la ejecución para usar estas evidencias en la Evaluación 4.

## Pruebas manuales

```powershell
docker compose exec cliente python cliente_pyro.py clonar proyecto main
docker compose exec cliente python cliente_pyro.py rama proyecto desarrollo main
docker compose exec cliente python cliente_pyro.py push proyecto desarrollo 0 primer_cambio
docker compose exec cliente python cliente_pyro.py historial proyecto desarrollo
docker compose exec cliente python cliente_pyro.py cambio proyecto main Thomas README.md --mensaje documentacion
docker compose exec cliente python cliente_pyro.py quien --veces 2
docker compose exec cliente python cliente_pyro.py vivos
```

`cambio` muestra un Proxy, modifica el objeto remoto, confirma mediante `push`
y comprueba el rechazo al reutilizar la referencia desregistrada. `verificar.py`
comprueba también errores del dominio y cancelación.

Para `session` o `POR_VALOR=1`, editar `.env` y recrear **servidor**:

```powershell
docker compose up -d --force-recreate servidor
```

Las variables de entorno de PowerShell prevalecen sobre `.env`.
`pruebas.ps1` las configura temporalmente y restaura sus valores al terminar.

## Arquitectura

| Servicio | Rol | Puerto interno | Comunicación |
|---|---|---|---|
| nombres | Directorio de nombres en RAM | 9090/TCP | Registro y resolución Pyro5 |
| servidor | Daemon con Repositorio y CambioEnCurso | 9100/TCP | Llamadas a objetos por Pyro5/serpent |
| cliente | CLI y pruebas | Sin escucha | Resuelve nombres y llama al servidor |

Red bridge de Compose `sd_net`; DNS por nombres de servicio. No se publican puertos
al host. Nombre lógico `sd.pinda.repositorio`; URI `PYRO:repositorio@servidor:9100`.
El nombre de la red real recibe el prefijo del proyecto Compose.

## Alcance y limitaciones

RepoSync simula ramas, revisiones y conflictos; no implementa el protocolo Git ni
almacena contenido real de archivos. `CambioEnCurso` conserva autor, rutas y base;
al confirmar las rutas quedan como metadatos del mensaje de la revisión.
El dominio y los cambios viven en RAM. Los modos Pyro cambian la vida de la
instancia de entrada, no la ubicación del dominio compartido en el proceso.
Los objetos abandonados requieren cancelación explícita; no se implementa lease.
No hay reintentos automáticos de escrituras ni deduplicación en esta adaptación.
Un resultado perdido puede dejar al cliente sin saber si se aplicó el cambio.

## Cierre

Desde la raíz del repositorio, después de completar las evidencias:

```powershell
git add semana12
git commit -m "Semana 12: RepoSync con objetos remotos y alcance"
git push
```

Para detener el laboratorio: `docker compose down` desde `semana12/`.

## Referencias

- Material del curso: Semana 12, Objetos Distribuidos y Laboratorio, FDICI25, 2026.
- Pyro5: https://pyro5.readthedocs.io/en/latest/servercode.html
- Pyro5: https://pyro5.readthedocs.io/en/latest/clientcode.html
