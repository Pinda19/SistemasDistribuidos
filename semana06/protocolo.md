# RepoSync — protocolo v2 (Semana 6)

**Dominio:** Tema 04, control de versiones distribuido (Git/GitHub).  
**Alcance:** simulación didáctica de un repositorio remoto con ramas e historial, **no** implementación de Git, almacenamiento de archivos ni clones completos. Cada cliente simula disponer de una revisión local conocida.  
**Estado del documento:** implementación probada parcialmente en Docker sobre Windows 10. Pruebas de conflicto y concurrencia registradas; quedan otras verificaciones pendientes (operación RAMA y errores específicos, prueba cruzada real y medición de ESPERA para RepoSync).

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

`CLONAR` **no copia objetos a disco**: devuelve el identificador del HEAD para que el cliente pueda simular su punto de partida. Si otro cliente publica primero, un `PUSH` que use la revisión anterior se rechaza por conflicto. Cada cliente puede mantener la conexión abierta para varios comandos. `SALIR` confirma y cierra la sesión.

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

**Pruebas de aceptación registradas (Windows 10):** `REPOS` → `OK proyecto`; `CLONAR proyecto main` → `OK proyecto main HEAD=0`; `PUSH proyecto main 0 primer_cambio` → `OK PUSH main HEAD=1`; un segundo `PUSH` sobre la misma base `0` → `ERROR CONFLICTO HEAD=1`; `HISTORIAL proyecto main` → `OK 1:primer_cambio | 0:inicio`. El servidor respondió también a `HOLA` y `SALIR`.

**Nota:** los restantes códigos `ERROR` son reglas de la implementación; todavía no hay pruebas individuales compartidas para todos ellos.

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
- **Desconexión abrupta:** el servidor captura errores de red, escribe logs con el nombre del hilo y siempre cierra la conexión en `finally`. Una conexión que se corta sin otro tráfico puede observarse como EOF, sin una excepción específica. **Evidencia de Windows 10:** después de iniciar `3 × ESPERA 10` y matar el contenedor de carga ~1 s más tarde, las tres conexiones se registraron a las 18:31:41 y se cerraron a las 18:31:51, aproximadamente **10 s** después. No hay un `ConnectionResetError`/`BrokenPipeError` explícito en los logs: `ESPERA` usa `time.sleep`, así que la detección no fue inmediata. Tras la prueba anterior `3 × ESPERA 5`, se verificó que un cliente nuevo obtenía `OK proyecto main HEAD=1`. Todavía debe comprobarse la respuesta después de la prueba de 10 s.
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

## Historial de versión

- **v1 (Semana 4):** servidor TCP secuencial del laboratorio base, con comandos de demostración como `ECO` y `CONTAR`.
- **v2 (Semana 6, RepoSync):** nuevo dominio de control de versiones, atención concurrente, estado compartido, `Lock`, conflictos de `PUSH` y manejo de errores.

**Compatibilidad:** los comandos de Semana 4 no son idénticos a los de RepoSync. Se necesitará adaptar la Semana 4 al mismo dominio para presentar una evolución coherente del servicio. Esta documentación no afirma retrocompatibilidad automática.

**Uso de IA:** apoyo de IA generativa para diseñar la adaptación de la plantilla, documentar el protocolo y preparar pruebas; el código debe ser revisado, ejecutado y comprendido por quien lo entrega.
