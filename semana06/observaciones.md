# Semana 6 — Observaciones del laboratorio RepoSync

**Tema:** 04. Control de versiones distribuido (simulación RepoSync).  
**Equipo:** Thomas Pinda
**Entorno:** Windows 10, PowerShell y Docker (contenedores Linux).  
**Origen de la evidencia:** salidas de consola aportadas durante las pruebas del estudiante; cuando se mencionan mediciones de la demo del profesor se indican por separado. No se presentan ejemplos esperados como mediciones.

## Definición del servicio

- Repositorio inicial: `proyecto`, rama `main`, revisión inicial `HEAD=0`.
- Estado compartido: mapa de ramas y commits en RAM, contador de revisión y contador de operaciones.
- Comandos propios: `REPOS`, `CLONAR`, `HISTORIAL`, `RAMA`, `PUSH`; también `HOLA`, `SALIR`, `ESPERA`.
- Operación crítica: `PUSH proyecto main 0 cambio`, que debe validar base=HEAD y actualizar historial/referencia de manera atómica.
- Predicción: al lanzar 20 clientes simultáneos con la misma base `0`, **solo uno** puede publicar; 19 deben recibir `ERROR CONFLICTO HEAD=1` cuando el Lock está habilitado.

## Paso 1 — Evidencia del problema secuencial

En la **demo original de Semana 6**, se ejecutó:

```bash
docker compose exec carga python cliente_carga.py --clientes 5 --comando "ESPERA 2"
```

**Resultado medido: `TOTAL: 10.01 s`.** Los cinco clientes fueron atendidos sucesivamente; la última petición terminó a los 10.01 s. Los clientes restantes esperaron en la cola de conexiones pendientes del sistema operativo mientras el proceso estaba ocupado con un cliente.

**Importante:** esta medición corresponde a la demo de Semana 6, no todavía al `servidor_secuencial.py` específico de RepoSync. La comparación con el mismo dominio sigue pendiente si el docente la exige.

## Paso 2 — Servidor concurrente con hilos, errores y timeout

En la **misma demo original**, tras cambiar a `MODELO=hilos`, se repitió la carga `5 × ESPERA 2`.

**Resultado medido: `TOTAL: 2.00 s`.** La diferencia respecto al secuencial fue **8.01 s menos**, aproximadamente **5 veces más rápido** para este tipo de operación bloqueante. La concurrencia permite atender varios clientes a la vez sin que una espera en una conexión bloquee el `accept()` de las demás.

En **RepoSync**, el servidor cuenta con `threading.Thread`, `conn.settimeout(60)`, `try/except`, `finally` y logs por cliente. La prueba interactiva de Windows 10 verificó:

```text
HOLA equipo                   -> OK HOLA equipo
REPOS                         -> OK proyecto
CLONAR proyecto main          -> OK proyecto main HEAD=0
PUSH proyecto main 0 primer_cambio -> OK PUSH main HEAD=1
PUSH proyecto main 0 segundo_cambio -> ERROR CONFLICTO HEAD=1
HISTORIAL proyecto main       -> OK 1:primer_cambio | 0:inicio
SALIR                         -> OK CHAO
```

**Pendiente:** medir `5 × ESPERA 2` en el RepoSync ya adaptado y registrar, si corresponde, evidencia directa del timeout de inactividad.

## Paso 3 — Estado compartido y Lock

Comando de carga (20 clientes, 1 operación cada uno):

```powershell
docker compose exec carga python cliente_carga.py --clientes 20 --comando "PUSH proyecto main 0 cambio"
```

El servidor se recreó entre ejecuciones para partir en `HEAD=0`, primero con `$env:SIN_LOCK="1"` y luego con `$env:SIN_LOCK="0"`.

| Ejecución | Lock | `OK` recibidos | `ERROR` recibidos | `TOTAL` |
|---|---|---:|---:|---:|
| Prueba sin Lock | No | **11** | **9** | **0,05 s** |
| Prueba con Lock 1 | Sí | **1** | **19** | **0,03 s** |
| Prueba con Lock 2 | Sí | **1** | **19** | **0,03 s** |
| Prueba con Lock 3 | Sí | **1** | **19** | No informado (solo se compartió `RESUMEN`) |

**Conclusión:** sin Lock se aceptaron 11 publicaciones utilizando la misma base obsoleta, aunque solo una debió aceptarse. La salida mostró revisiones publicadas hasta `HEAD=11`; no se hizo una consulta independiente del HEAD final. Con Lock, las tres ejecuciones generaron exactamente un `PUSH` correcto y 19 conflictos. La condición de carrera fue provocada y corregida experimentalmente.

**Sección crítica en `servidor.py` (`op_push`):**

1. Consultar la referencia HEAD de la rama.
2. Compararla con `base` proporcionada por el cliente.
3. Obtener y avanzar el ID de revisión siguiente.
4. Insertar el nuevo commit y actualizar HEAD.

Estos pasos están dentro de `with seccion_critica()` y usan `threading.Lock` cuando `SIN_LOCK=0`. `ESPERA` realiza `time.sleep()` fuera del Lock. `PAUSA_CARRERA` está configurada inicialmente a 0.005 s para hacer visible el error; debe establecerse a 0 al terminar las demostraciones.

## Paso 4 — Docker Compose, red y puerto

La salida de `docker compose ps` en Windows 10 confirmó:

```text
sd_servidor   semana06-servidor   Up    0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp
sd_cliente    semana06-cliente    Up
sd_carga      semana06-carga      Up
```

Se verificó que el cliente pudo conectar a `servidor:5000` dentro de Compose. El archivo `docker-compose.yml` define tres servicios en la red `sd_net` y publica el puerto `5000/tcp` del servidor al equipo anfitrión.

**Pendiente:** adjuntar salida de `docker compose config` del RepoSync en Windows y anotar la IP LAN del equipo si se realizará la prueba cruzada. La dirección `192.168.1.92` usada anteriormente pertenece al PC con Fedora y no identifica necesariamente al equipo Windows actual.

## Paso 5 — Prueba cruzada

- **Prueba con otro equipo del curso:** todavía no se ha realizado/documentado.
- **Checklist ajeno:** pendiente de respuesta real, no simulado.
- **Pruebas locales verificadas:** protocolo básico, `PUSH` obsoleto, `HISTORIAL`, ejecución concurrente con y sin Lock.

Se requiere coordinación con otro equipo o una alternativa aprobada por el profesor para cerrar este requisito.

## Falla provocada — caída abrupta del contenedor de carga

### Intento 1: tres clientes `ESPERA 5`

Se inició carga con tres clientes y se ejecutó `docker compose kill carga`. Los logs indicaron tres conexiones a las **18:27:14** desde `172.18.0.4`, puertos `41208`, `41206`, `41218`, y sus cierres alrededor de **18:27:19**. No se observó excepción explícita de desconexión.

**Prueba posterior de disponibilidad, efectivamente realizada:** otro cliente se conectó y recibió:

```text
HOLA prueba_recuperacion -> OK HOLA prueba_recuperacion
REPOS                    -> OK proyecto
CLONAR proyecto main     -> OK proyecto main HEAD=1
SALIR                    -> OK CHAO
```

Esto comprueba que el servidor siguió atendiendo nuevas solicitudes y preservó su estado en memoria después del primer intento.

### Intento 2: tres clientes `ESPERA 10`

Se ejecutó en PowerShell:

```powershell
docker compose up -d carga
docker compose exec -d carga python cliente_carga.py --clientes 3 --comando "ESPERA 10"
Start-Sleep -Seconds 1
docker compose kill carga
Start-Sleep -Seconds 11
docker compose logs --since 1m servidor
```

**Evidencia exacta de los logs del servidor (9 de octubre de 2026):**

```text
18:31:41,645 cli-36486 conexion de ('172.18.0.4', 36486)
18:31:41,645 cli-36498 conexion de ('172.18.0.4', 36498)
18:31:41,646 cli-36502 conexion de ('172.18.0.4', 36502)
18:31:51,646 cli-36486 cierre de ('172.18.0.4', 36486) | operaciones=28
18:31:51,647 cli-36498 cierre de ('172.18.0.4', 36498) | operaciones=28
18:31:51,648 cli-36502 cierre de ('172.18.0.4', 36502) | operaciones=28
```

**Interpretación:** la caída del contenedor fue provocada aproximadamente un segundo después de iniciar la operación. Las conexiones terminaron cerrándose **~10 s después de ser abiertas**, lo que indica que el servidor concluyó la espera bloqueante antes de registrar el cierre. No apareció `ConnectionResetError` ni `BrokenPipeError`; el cierre también puede deberse a EOF. No se afirma detección inmediata de la falla.

**Pendiente:** comprobar con una nueva solicitud `REPOS`/`CLONAR` que el servidor continúa accesible **después del segundo intento**. La comprobación anterior fue posterior al primer intento.

## Conclusión

RepoSync reproduce un problema de coordinación de revisiones propio del control de versiones distribuido: clientes que publican sobre una referencia ya obsoleta. El ensayo con 20 clientes mostró 11 aceptaciones incorrectas sin Lock, frente a 1 aceptación y 19 conflictos en tres ejecuciones con Lock. La concurrencia mediante hilos mejora la capacidad de atender operaciones lentas, como demuestra la comparación del laboratorio de referencia (10,01 s frente a 2,00 s). En la prueba de caída del contenedor de carga, el servidor registró el cierre de las conexiones luego de completar la espera, sin excepción específica visible; tras el primer intento pudo atender nuevos clientes.

**Trabajo pendiente para el cierre definitivo:** confirmar disponibilidad tras el segundo intento, medir `ESPERA 2` en RepoSync (y opcionalmente su variante secuencial), ejecutar o coordinar la prueba cruzada, registrar comprobación de Compose en Windows, y retirar la pausa artificial una vez documentada la carrera.

