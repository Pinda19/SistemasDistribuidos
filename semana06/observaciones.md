# Semana 6 — Observaciones del laboratorio RepoSync

**Tema:** 04. Control de versiones distribuido (simulación RepoSync).  
**Equipo:** Thomas Pinda
**Entornos:** Windows 10 con PowerShell y Docker Desktop; Fedora Linux con Docker Compose. Los contenedores ejecutan Linux.  
**Origen de la evidencia:** salidas de terminal obtenidas durante las pruebas de RepoSync en ambos equipos; los resultados de la demo original del curso se mencionan por separado. Los resultados esperados no se presentan como mediciones.

## Definición del servicio

- Repositorio inicial: `proyecto`, rama `main`, revisión inicial `HEAD=0`.
- Estado compartido: mapa de ramas y commits en RAM, contador de revisión y contador de operaciones.
- Comandos propios: `REPOS`, `CLONAR`, `HISTORIAL`, `RAMA`, `PUSH`; también `HOLA`, `SALIR`, `ESPERA`.
- Operación crítica: `PUSH proyecto main 0 cambio`, que debe validar base=HEAD y actualizar historial/referencia de manera atómica.
- Predicción: al lanzar 20 clientes simultáneos con la misma base `0`, **solo uno** puede publicar; 19 deben recibir `ERROR CONFLICTO HEAD=1` cuando el Lock está habilitado.

## Paso 1 — Evidencia del problema secuencial

Se compararon los dos servidores **del propio RepoSync**, bajo la misma carga y con el mismo protocolo, no solamente las versiones de ejemplo del profesor.

Para la versión secuencial se detuvo `sd_servidor` y se inició temporalmente `servidor_secuencial.py` usando la misma red y el alias DNS del servicio `servidor`. Se verificó el contenedor temporal `reposync_secuencial` en estado `Up` y se ejecutó:

```bash
docker compose exec carga python cliente_carga.py --clientes 5 --comando "ESPERA 2"
```

**Resultado medido en RepoSync secuencial: `TOTAL: 10.02 s`; `RESUMEN: OK=5 ERROR=0`.** Los cinco clientes terminaron aproximadamente a los 2,01 s, 4,01 s, 6,02 s, 8,02 s y 10,02 s. Mientras se atendía a un cliente, los demás esperaban en la cola de conexiones establecidas pendientes de `accept()` del sistema operativo.

Como contexto, la demo original del curso había mostrado **10,01 s** para cinco operaciones `ESPERA 2`, pero el dato utilizado para la comparación definitiva de este informe es **10,02 s del servidor secuencial de RepoSync**.

## Paso 2 — Servidor concurrente con hilos, errores y timeout

Con `servidor.py` de RepoSync en ejecución, se lanzó la misma carga:

```bash
docker compose exec carga python cliente_carga.py --clientes 5 --comando "ESPERA 2"
```

**Resultado medido en RepoSync concurrente: `TOTAL: 2.01 s`; `RESUMEN: OK=5 ERROR=0`.** Los cinco clientes recibieron `OK ESPERA 2` alrededor de los 2,01 s. La variante con hilos fue **8,01 s más rápida** y tardó **aproximadamente 4,99 veces menos** que la variante secuencial (10,02 / 2,01), para esta carga I/O simulada.

| Servidor RepoSync | Clientes | Tiempo total | Respuestas correctas |
|---|---:|---:|---:|
| Secuencial | 5 | **10,02 s** | 5/5 |
| Concurrente | 5 | **2,01 s** | 5/5 |

El servidor concurrente crea un `threading.Thread` por conexión, configura `conn.settimeout(60)`, captura errores y registra los cierres en `finally`. A diferencia del secuencial, una operación lenta de un cliente no bloquea el `accept()` de los siguientes. En la demo genérica original del curso se obtuvieron 10,01 s frente a 2,00 s; son resultados distintos y no se han mezclado con los de RepoSync.

La prueba interactiva en Windows 10 verificó:

```text
HOLA equipo                   -> OK HOLA equipo
REPOS                         -> OK proyecto
CLONAR proyecto main          -> OK proyecto main HEAD=0
PUSH proyecto main 0 primer_cambio -> OK PUSH main HEAD=1
PUSH proyecto main 0 segundo_cambio -> ERROR CONFLICTO HEAD=1
HISTORIAL proyecto main       -> OK 1:primer_cambio | 0:inicio
SALIR                         -> OK CHAO
```

**Pendiente:** no se realizó una espera de 60 s sin enviar comandos para comprobar experimentalmente el timeout de inactividad del servidor. Su configuración y manejo se verifican en el código.

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

**Comprobación en Fedora:** el 14 de octubre se repitió `docker compose ps` y aparecieron `sd_servidor`, `sd_cliente` y `sd_carga` en estado `Up`, con el puerto 5000 publicado, antes de ejecutar la prueba de ramas.

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

**Disponibilidad comprobada tras el segundo intento:** desde un cliente nuevo se ejecutó:

```text
REPOS                 -> OK proyecto
CLONAR proyecto main  -> OK proyecto main HEAD=1
salir                 -> OK CHAO
```

El servidor atendió nuevas solicitudes y conservó `HEAD=1` en el proceso que seguía activo. **No se probó persistencia tras reiniciar el servidor**.

## Pruebas funcionales adicionales — ramas e historial

**Windows 10:**

```text
HOLA                         -> OK HOLA anonimo
REPOS                         -> OK proyecto
RAMA proyecto desarrollo name -> ERROR RAMA_NO_EXISTE
RAMA proyecto desarrollo main -> OK RAMA desarrollo HEAD=0
CLONAR proyecto desarrollo    -> OK proyecto desarrollo HEAD=0
HISTORIAL proyecto desarrollo -> OK 0:inicio
```

La prueba de rama origen inexistente produjo un error controlado y la sesión continuó funcionando.

**Fedora:** después de levantar RepoSync en otro equipo y de recrear `desarrollo` sobre `main` en `HEAD=0`, se obtuvo:

```text
REPOS                                    -> OK proyecto
RAMA proyecto desarrollo main            -> OK RAMA desarrollo HEAD=0
PUSH proyecto desarrollo 0 cambio_desarrollo -> OK PUSH desarrollo HEAD=1
CLONAR proyecto desarrollo               -> OK proyecto desarrollo HEAD=1
CLONAR proyecto main                     -> OK proyecto main HEAD=0
HISTORIAL proyecto desarrollo            -> OK 1:cambio_desarrollo | 0:inicio
SALIR                                    -> OK CHAO
```

Se comprobó que actualizar una rama no modifica automáticamente la referencia de otra. `CLONAR` aquí sólo consulta el HEAD; no realiza un clon Git auténtico.

## Conclusión

RepoSync simula una referencia remota de control de versiones con ramas y revisiones y hace visible un problema de coordinación: varios clientes intentan publicar sobre una base ya desactualizada. En la prueba sin Lock, **11 de 20** peticiones se aceptaron incorrectamente; con Lock, **1 de 20** se aceptó y **19** se rechazaron correctamente, en tres ejecuciones sucesivas. Con el mismo comando `5 × ESPERA 2`, el servidor secuencial de RepoSync tardó **10,02 s** y el concurrente **2,01 s**, conservando cinco respuestas correctas en ambos. Las dos pruebas de interrupción del contenedor de carga terminaron con el servidor operativo y disponible, aunque los logs no permitieron demostrar detección inmediata de la desconexión. Las pruebas de ramas confirmaron referencias independientes de `main` y `desarrollo`.

**Trabajo pendiente antes de considerar cerrada toda la entrega:** prueba cruzada con otro equipo (o alternativa validada por el profesor), documentación de la IP del host y de `docker compose config` para el servicio adaptado, prueba específica de timeout de 60 s y errores no ejercitados, y retirada de la pausa artificial `PAUSA_CARRERA=0.005` en la versión robustecida. Además, corresponde revisar Semana 4 para que represente el mismo dominio durante la evolución del semestre.

