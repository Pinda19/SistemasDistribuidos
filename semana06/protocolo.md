# RepoSync — protocolo v2 (Semana 6)

**Dominio:** Tema 04, control de versiones distribuido (Git/GitHub).  
**Alcance:** simulación didáctica de un repositorio remoto con ramas e historial, **no** implementación de Git, almacenamiento de archivos ni clones completos. Cada cliente simula disponer de una revisión local conocida.  
**Estado del documento:** versión 2 actualizada con pruebas reales en Windows 10 y Fedora (Docker): funcionamiento del protocolo, ramas, condiciones de carrera, recuperación del servicio y comparación de tiempos secuencial/concurrente. Quedan pendientes la prueba cruzada real, la verificación de algunos errores de formato y la prueba de inactividad de 60 segundos.

## 1. Formato

- TCP en puerto `5000`; servidor `servidor`, cliente y generador de carga en `sd_net` (contenedores distintos).
- UTF-8; una solicitud por línea terminada en `\n` y una respuesta por solicitud.
- Solicitud: `COMANDO [argumentos]`. Los nombres de comandos se convierten a mayúsculas; los identificadores de repositorio y rama distinguen mayúsculas y minúsculas.
- Respuestas: `OK datos` o `ERROR CODIGO [detalle]`.
- Las respuestas `HISTORIAL` representan hasta **10 revisiones** de la rama, de más reciente a más antigua, separadas por ` | `.

## 2. Secuencia

No es obligatorio saludar. Flujo recomendado de un cliente:

```text
> HOLA equipo
< OK HOLA equipo
> REPOS
< OK proyecto
> CLONAR proyecto main
< OK proyecto main HEAD=0
> PUSH proyecto main 0 cambio_A
< OK PUSH main HEAD=1
> HISTORIAL proyecto main
< OK 1:cambio_A | 0:inicio
> SALIR
< OK CHAO
```

`CLONAR` **no copia objetos a disco**: devuelve el identificador del HEAD para que el cliente pueda simular su punto de partida. Si otro cliente publica primero, un `PUSH` que use la revisión anterior se rechaza por conflicto. Cada cliente puede mantener la conexión abierta para varios comandos. `HOLA` admite un nombre opcional (`HOLA` sin argumentos respondió `OK HOLA anonimo`); `SALIR` confirma y cierra la sesión.

**Prueba de ramas, verificada en Fedora:**

```text
> RAMA proyecto desarrollo main
< OK RAMA desarrollo HEAD=0
> PUSH proyecto desarrollo 0 cambio_desarrollo
< OK PUSH desarrollo HEAD=1
> CLONAR proyecto desarrollo
< OK proyecto desarrollo HEAD=1
> CLONAR proyecto main
< OK proyecto main HEAD=0
> HISTORIAL proyecto desarrollo
< OK 1:cambio_desarrollo | 0:inicio
```

La creación de una rama nueva copia la referencia HEAD de la rama origen en ese instante; los cambios posteriores sobre `desarrollo` no avanzan automáticamente la referencia de `main`. No hay transferencia de archivos ni réplicas completas entre los clientes.

## 3. Operaciones del dominio

| Comando | Argumentos | Respuesta exitosa | Errores | ¿Estado compartido? |
|---|---|---|---|---|
| `REPOS` | ninguno | `OK proyecto` | `ERROR FORMATO REPOS` | Consulta |
| `CLONAR` | `repo rama` | `OK proyecto main HEAD=0` | `FORMATO`, `REPO_NO_EXISTE`, `RAMA_NO_EXISTE` | Consulta |
| `HISTORIAL` | `repo rama` | `OK 1:cambio_A \| 0:inicio` | `FORMATO`, `REPO_NO_EXISTE`, `RAMA_NO_EXISTE`, `HISTORIAL_INCONSISTENTE` | Consulta |
| `RAMA` | `repo nueva_rama rama_origen` | `OK RAMA feature HEAD=1` | `FORMATO`, `REPO_NO_EXISTE`, `RAMA_NO_EXISTE`, `RAMA_EXISTE` | Modifica referencias |
| `PUSH` | `repo rama base mensaje` | `OK PUSH main HEAD=1` | `FORMATO`, `REPO_NO_EXISTE`, `RAMA_NO_EXISTE`, `CONFLICTO HEAD=n` | Modifica commits y HEAD |
| `ESPERA` | `segundos` entre 0 y 10 | `OK ESPERA 2` | `FORMATO` | No; operación lenta |
| `HOLA` | nombre opcional | `OK HOLA nombre` | — | No |
| `SALIR` | ninguno | `OK CHAO` | — | No |

El argumento `base` de `PUSH` es la revisión que el cliente cree vigente. El `mensaje` admite espacios (máximo 80 caracteres), pero no saltos de línea. La revisión inicial de `proyecto/main` es `0`. Los IDs de revisión son enteros consecutivos asignados por el servidor dentro de cada repositorio. El servicio inicia con **un solo repositorio**, `proyecto`, y no ofrece aún crear repositorios nuevos.

## 4. Errores

| Código | Cuándo aparece |
|---|---|
| `COMANDO_DESCONOCIDO` | Comando no reconocido (incluida línea vacía enviada por TCP) |
| `FORMATO` | Argumentos incompletos, sobrantes, base no numérica, mensaje vacío o superior a 80 caracteres; espera fuera de 0–10 segundos |
| `REPO_NO_EXISTE` | Identificador de repositorio desconocido |
| `RAMA_NO_EXISTE` | Rama consultada o rama origen inexistente |
| `RAMA_EXISTE` | Intento de crear una rama que ya existe |
| `CONFLICTO HEAD=n` | El HEAD real ya no coincide con la base enviada en `PUSH`; el cliente debe recuperar la referencia actual y resolver el conflicto antes de reintentar |
| `HISTORIAL_INCONSISTENTE` | Una revisión apuntada por el historial no existe (integridad interna) |

**Pruebas de aceptación registradas (Windows 10):** `REPOS` → `OK proyecto`; `CLONAR proyecto main` → `OK proyecto main HEAD=0`; `PUSH proyecto main 0 primer_cambio` → `OK PUSH main HEAD=1`; un segundo `PUSH` sobre la misma base `0` → `ERROR CONFLICTO HEAD=1`; `HISTORIAL proyecto main` → `OK 1:primer_cambio | 0:inicio`. También se verificó `HOLA`, `SALIR` y `HOLA` sin nombre → `OK HOLA anonimo`.

**Pruebas de ramas:** en Windows, `RAMA proyecto desarrollo name` devolvió `ERROR RAMA_NO_EXISTE`; `RAMA proyecto desarrollo main` devolvió `OK RAMA desarrollo HEAD=0`. En Fedora, una rama de desarrollo creada desde `main` aceptó un `PUSH`, avanzó a `HEAD=1` y mantuvo `main` en `HEAD=0`.

**Nota:** se comprobaron de forma directa `COMANDO_DESCONOCIDO` en la plantilla previa, `CONFLICTO` y `RAMA_NO_EXISTE` en RepoSync. Los demás códigos de error figuran en el código, pero no todos cuentan aún con una prueba individual registrada en este servicio.

## 5. Estado y concurrencia

Estado global compartido, mantenido **en RAM**:

```python
estado = {
    'repos': {'proyecto': {
        'ramas': {'main': 0},
        'commits': {0: {'padre': None, 'mensaje': 'inicio'}},
        'siguiente': 1}},
    'operaciones': 0
}
```

- Cada conexión se atiende mediante un `threading.Thread` distinto.
- `threading.Lock` protege la lectura y escritura de referencias de ramas, el diccionario de revisiones y el siguiente identificador. `ESPERA` no retiene el Lock.
- `PUSH` verifica **dentro del Lock** si `base` coincide con HEAD; si coincide registra una revisión nueva y actualiza la rama. Dos `PUSH` con la misma base **no pueden ser aceptados ambos** cuando el Lock está habilitado.
- La variable `SIN_LOCK=1` deshabilita intencionalmente la sincronización para observar condiciones de carrera. `PAUSA_CARRERA=0.005` amplía la ventana de competencia durante el laboratorio; debe cambiarse a `0` para la versión robustecida final.
- El estado no es persistente; reiniciar el servidor devuelve el repositorio `proyecto/main` a HEAD=0. Los clientes no realizan commits locales auténticos: el ejercicio simula la sincronización de referencias del repositorio remoto.

## 6. Anomalías y fallos

- **Comando inválido:** `ERROR ...`; la sesión continúa si la conexión es válida.
- **Cliente mudo:** timeout de 60 s en el socket del servidor; se registra el cierre.
- **Desconexión abrupta:** el servidor contempla errores de red, registra cada conexión con el nombre del hilo y ejecuta el cierre de la sesión en `finally`. Si el extremo desaparece, la lectura puede finalizar por EOF sin lanzar una excepción específica. **Evidencia en Windows 10:** con `3 × ESPERA 10`, se ejecutó `docker compose kill carga` aproximadamente 1 s después de iniciar las operaciones. Los logs registraron tres conexiones a las 18:31:41 y sus cierres a las 18:31:51, aproximadamente **10 s** después. No apareció un `ConnectionResetError` ni `BrokenPipeError` explícito: `ESPERA` usa `time.sleep` y la detección del corte no fue inmediata. Después de esta segunda prueba, un cliente nuevo obtuvo `REPOS` → `OK proyecto` y `CLONAR proyecto main` → `OK proyecto main HEAD=1`; el servidor seguía operativo y retenía el estado en RAM. También se había verificado la recuperación tras la primera prueba (`3 × ESPERA 5`). La prueba **no demuestra persistencia frente a un reinicio del servidor**, porque se apagó el contenedor de carga, no el del servidor.
- **Pérdida de conectividad durante `PUSH`:** el cliente puede desconocer si el servidor ya aplicó la operación. Debe consultar `CLONAR`/`HISTORIAL` antes de reintentar; no se prometen reintentos idempotentes ni transacciones distribuidas.
- **Actualizaciones simultáneas:** con Lock, una avanza la rama; otra con base obsoleta recibe `ERROR CONFLICTO HEAD=n`. Sin Lock, la misma base puede aceptarse en varias solicitudes (inconsistencia intencional de la demo).
- **Servidor caído/reiniciado:** no hay réplica ni persistencia en este hito. El servicio está indisponible durante el fallo y pierde el estado al reiniciar.
- **Clientes en contenedores separados:** el acceso entre contenedores se realiza por DNS `servidor:5000`; el puerto se publica al anfitrión para pruebas cruzadas.

### Evidencia concurrente del servicio RepoSync

Veinte clientes intentaron simultáneamente `PUSH proyecto main 0 cambio`, una única vez por cliente, reiniciando el servidor antes de cada prueba.

| Configuración | OK | Conflictos | Duración |
|---|---:|---:|---:|
| `SIN_LOCK=1` | 11 | 9 | 0,05 s |
| `SIN_LOCK=0`, prueba 1 | 1 | 19 | 0,03 s |
| `SIN_LOCK=0`, prueba 2 | 1 | 19 | 0,03 s |
| `SIN_LOCK=0`, prueba 3 | 1 | 19 | No informado |

En la ejecución sin Lock se comunicaron respuestas exitosas hasta `HEAD=11` (sin consulta final independiente). La misma revisión base fue aceptada más de una vez: esto constituye la condición de carrera. Con Lock las tres ejecuciones devolvieron exactamente un `OK` y 19 errores `CONFLICTO HEAD=1`.

### Rendimiento observado: servidor secuencial frente a concurrente

Se usó el mismo código de RepoSync y su comando `ESPERA 2`, con cinco clientes simultáneos. La variante `servidor_secuencial.py` llama a `atender()` antes de aceptar otra conexión; la variante `servidor.py` crea un hilo por cliente.

| Versión RepoSync | Clientes | Comando | Respuestas | Duración total |
|---|---:|---|---|---:|
| Secuencial | 5 | `ESPERA 2` | 5 `OK`, 0 `ERROR` | **10,02 s** |
| Concurrente | 5 | `ESPERA 2` | 5 `OK`, 0 `ERROR` | **2,01 s** |

El modelo con hilos tardó **8,01 s menos**, aproximadamente **4,99 veces menos tiempo** en este ensayo de espera de E/S simulada. Son mediciones del RepoSync adaptado, distintas de la demo genérica de la clase.

### Verificaciones pendientes

- Prueba cruzada con otro equipo del curso y checklist firmado/registrado; no se ha realizado.
- Prueba directa del timeout por inactividad de 60 s y de todos los códigos de error individuales; están implementados, pero no todos fueron ejercitados en las salidas aportadas.
- Retirar la pausa artificial `PAUSA_CARRERA=0.005` para la versión robustecida, después de documentar la condición de carrera.

## Historial de versión

- **v1 (Semana 4):** servidor TCP secuencial del laboratorio base, con comandos de demostración como `ECO` y `CONTAR`.
- **v2 (Semana 6, RepoSync):** nuevo dominio de control de versiones, atención concurrente, estado compartido, `Lock`, conflictos de `PUSH` y manejo de errores.

**Compatibilidad:** los comandos de Semana 4 no son idénticos a los de RepoSync. 
