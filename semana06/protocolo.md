# Protocolo de aplicación — versión 2.0

> **Semana 6 — Laboratorio N.º 2: servidor concurrente.** Documento basado en la implementación de referencia `servidor.py` del laboratorio y contrastado con las pruebas realizadas. Se utiliza **inventario como dominio provisional**, mientras se confirma la asignación definitiva.

## 1. Identificación

| Campo | Valor |
|---|---|
| Equipo | Pendiente de asignación |
| Integrantes | Pendiente de completar |
| Dominio del servicio | Inventario (referencia provisional del laboratorio) |
| Versión del protocolo | 2.0 |
| Transporte | TCP sobre IPv4 |
| Dirección dentro de Docker | `servidor:5000` |
| Puerto publicado en el equipo anfitrión | `5000/tcp` |
| Dirección IPv4 del anfitrión durante la prueba | `192.168.1.92` (dinámica; puede cambiar) |
| Codificación | UTF-8 |
| Delimitación | Una solicitud por línea terminada en `\n`; una respuesta por línea |
| Modelo del servidor | Un hilo por conexión TCP |
| Timeout por inactividad del servidor | 60 s (`TIMEOUT_CLIENTE=60`) |
| Timeout de conexión/lectura del cliente de referencia | 5 s |
| Red de Docker | `sd_net` |

Los servicios de `docker-compose.yml` son `servidor`, `cliente` y `carga`; sus contenedores se llaman `sd_servidor`, `sd_cliente` y `sd_carga`. El servicio es accesible por el nombre DNS `servidor` entre contenedores y por la dirección del anfitrión y puerto `5000` desde una máquina con acceso a ese puerto.

## 2. Formato general de los mensajes

**Solicitud:**

```text
COMANDO [argumentos]\n
```

**Respuesta exitosa (formato habitual):**

```text
OK [datos]\n
```

**Respuesta de error:**

```text
ERROR CODIGO [detalle]\n
```

- Los comandos no distinguen mayúsculas ni minúsculas: `LISTAR`, `listar` y `LiStAr` realizan la misma operación.
- Los nombres de ítems usados por `AGREGAR` y `QUITAR` se normalizan a minúsculas. El texto del nombre en `HOLA` se conserva.
- Los argumentos se separan con espacios. Cada mensaje debe terminar con un salto de línea (`\n`).
- En funcionamiento normal, el servidor devuelve **una respuesta por cada solicitud**. Ante un cierre de conexión o una excepción inesperada, puede terminar la sesión sin devolver respuesta.
- La conexión permanece abierta para nuevas operaciones hasta `SALIR`, desconexión, error no recuperable o timeout.
- El servidor mantiene el inventario en memoria. Los clientes comparten ese mismo estado.

**Ejemplo observado en el laboratorio:**

```text
CLIENTE > HOLA equipo
SERVIDOR < OK HOLA equipo
CLIENTE > LISTAR
SERVIDOR < OK manzana:100 pera:100
CLIENTE > salid
SERVIDOR < ERROR COMANDO_DESCONOCIDO
CLIENTE > salir
SERVIDOR < OK CHAO
```

## 3. Secuencia de una sesión

```text
Cliente                            Servidor
   |---- conexión TCP :5000 --------->|
   |<--- conexión establecida --------|
   |---- HOLA equipo ---------------->|
   |<--- OK HOLA equipo --------------|
   |---- LISTAR --------------------->|
   |<--- OK manzana:100 pera:100 -----|
   |---- QUITAR manzana 1 ----------->|
   |<--- OK manzana 99 -------------- |
   |---- SALIR ---------------------->|
   |<--- OK CHAO ---------------------|
   |         conexión cerrada         |
```

La operación `QUITAR` anterior es **un ejemplo ilustrativo del protocolo**, no una transcripción de la prueba inicial. `HOLA` **no es obligatorio**: el servidor permite `LISTAR`, `AGREGAR`, `QUITAR` y `ESPERA` sin un saludo previo. Si se envía `HOLA` sin nombre, responde `OK HOLA anonimo`.

El servidor acepta conexiones en un bucle y crea un hilo independiente por cliente. Por ello, un cliente que mantiene abierta su sesión no impide que otro sea atendido.

## 4. Operaciones disponibles

| Comando | Argumentos | Respuesta exitosa | Errores previstos | ¿Modifica estado compartido? |
|---|---|---|---|---|
| `HOLA` | Nombre libre (opcional) | `OK HOLA <nombre>` o `OK HOLA anonimo` | — | No |
| `LISTAR` | Ninguno requerido | `OK manzana:100 pera:100` (valores según inventario actual) | — | No |
| `AGREGAR` | `<item> <cantidad>` | `OK <item> <nuevo_total>` | `ERROR FORMATO AGREGAR <item> <cantidad>` | Sí: inventario |
| `QUITAR` | `<item> <cantidad>` | `OK <item> <nuevo_total>` | `ERROR FORMATO QUITAR <item> <cantidad>`, `ERROR ITEM_NO_EXISTE`, `ERROR STOCK_INSUFICIENTE <actual>` | Sí: inventario |
| `ESPERA` | `<segundos>` | `OK ESPERA <segundos>` | `ERROR FORMATO ESPERA <segundos>` | No: solamente introduce una espera |
| `SALIR` | Ninguno requerido | `OK CHAO` | — | No |

**Reglas implementadas:**

- `LISTAR` muestra los productos ordenados por nombre, separados por espacios, como `OK manzana:20 pera:100`.
- `AGREGAR` suma la cantidad al producto; si el producto no existe, lo crea desde cero.
- `QUITAR` resta la cantidad si el producto existe y tiene unidades suficientes. Nunca debería dejar stock negativo con `SIN_LOCK=0`.
- Las cantidades de `AGREGAR` y `QUITAR` deben estar escritas como enteros sin signo; **la implementación actual también acepta `0`**. No se admiten cantidades negativas ni fraccionarias.
- `ESPERA` acepta un número convertible a `float`, en segundos. Se recomienda un número no negativo y suficientemente pequeño para no superar el timeout de 5 segundos del cliente de referencia.
- `HOLA` y `SALIR` no alteran el inventario. `SALIR` cierra la sesión después de enviar `OK CHAO`.
- El comando desconocido `salid` devolvió, en la prueba real, `ERROR COMANDO_DESCONOCIDO`.

Las operaciones de inventario y `ESPERA` incrementan el contador global `operaciones`, incluso cuando una operación del dominio devuelve un error. `HOLA`, `SALIR` y los comandos desconocidos no incrementan ese contador.

## 5. Códigos de error

| Código | Causa | Ejemplo de respuesta |
|---|---|---|
| `COMANDO_DESCONOCIDO` | Comando que no pertenece al protocolo o línea vacía recibida | `ERROR COMANDO_DESCONOCIDO` |
| `FORMATO` | Argumentos inválidos, faltantes o cantidades con formato incorrecto | `ERROR FORMATO QUITAR <item> <cantidad>` |
| `ITEM_NO_EXISTE` | Intento de quitar un producto no registrado | `ERROR ITEM_NO_EXISTE` |
| `STOCK_INSUFICIENTE` | Se solicita una cantidad mayor que el stock disponible | `ERROR STOCK_INSUFICIENTE 3` |

Estas respuestas están definidas en la implementación de la plantilla. De ellas, el laboratorio proporcionado verificó directamente `ERROR COMANDO_DESCONOCIDO`; **no se adjuntaron pruebas específicas de todos los demás códigos**.

Una excepción inesperada en el procesamiento puede registrar un error en el servidor y cerrar la conexión; no necesariamente genera una respuesta `ERROR` al cliente.

## 6. Comportamiento ante situaciones anómalas

| Situación | Comportamiento |
|---|---|
| Línea vacía enviada realmente por TCP | El servidor devuelve `ERROR COMANDO_DESCONOCIDO`. El cliente interactivo suministrado omite las líneas vacías antes de enviarlas. |
| Cliente inactivo durante 60 segundos | El servidor tiene `conn.settimeout(60)` y cierra la sesión al vencer el timeout, registrándolo en los logs. |
| Desconexión abrupta del cliente | La sesión se cierra; el servidor maneja `ConnectionResetError` y `BrokenPipeError`, además de registrar el cierre en `finally`. |
| Dos clientes modifican el mismo ítem | Con `SIN_LOCK=0`, un `threading.Lock` protege la actualización del inventario. |
| `SIN_LOCK=1` | Modo experimental: no se protege la sección crítica y pueden perderse actualizaciones concurrentes. **No utilizar en producción.** |
| Comando desconocido | Responde `ERROR COMANDO_DESCONOCIDO` sin terminar la sesión. |
| Bytes UTF-8 inválidos | El lector usa `errors="replace"`: sustituye secuencias inválidas por el carácter de reemplazo; la operación resultante se procesa normalmente, si es válida. |
| `ESPERA` demasiado larga | El cliente de referencia puede agotar su timeout de lectura de 5 segundos antes de recibir la respuesta. |
| Reinicio del proceso servidor | Se pierde el inventario en memoria y vuelve a sus valores iniciales. No hay persistencia en base de datos. |

**Evidencia observada de concurrencia y Lock:**

| Prueba | Clientes × operaciones | Stock esperado de manzanas | Stock observado | Tiempo total de carga |
|---|---|---:|---:|---:|
| `SIN_LOCK=1` | 20 × 4 = 80 retiros de 1 | 20 | **91** | **0.03 s** |
| `SIN_LOCK=0` | 20 × 4 = 80 retiros de 1 | 20 | **20** | **0.09 s** |

La prueba sin Lock perdió el efecto de **71 de los 80 retiros esperados**, mientras que la ejecución con Lock conservó correctamente las 80 actualizaciones. Estos tiempos y valores corresponden a las ejecuciones aportadas; no sustituyen las repeticiones adicionales solicitadas por la guía.

**Evidencia observada de desconexión:** se iniciaron tres clientes con `ESPERA 5` y luego se ejecutó `docker compose kill carga`. Los logs muestran tres conexiones desde `172.18.0.3` (puertos `44392`, `44398` y `44406`) y sus respectivos cierres. En las últimas 20 líneas aportadas no aparece un mensaje explícito de `ConnectionResetError` o `BrokenPipeError`; por tanto, **no se afirma que se haya registrado esa excepción en la prueba**. El servidor siguió funcionando: un cliente nuevo ejecutó `listar` y recibió `OK manzana:20 pera:100`.

## 7. Estado compartido y sincronización

| Dato | Tipo | Valor al iniciar servidor | Quién lo utiliza o modifica | Protección |
|---|---|---|---|---|
| `inventario` | Diccionario `item → cantidad` | `{"manzana": 100, "pera": 100}` | `AGREGAR` y `QUITAR` modifican; `LISTAR` consulta | `threading.Lock` si `SIN_LOCK=0` |
| `operaciones` | Entero | `0` | Incrementado en `procesar()` por las operaciones del dominio | `threading.Lock` si `SIN_LOCK=0` |

La sección crítica de `QUITAR` abarca la lectura del stock actual, la comprobación de existencia y suficiencia, y la escritura del nuevo valor. La de `AGREGAR` abarca la lectura, suma y escritura. `LISTAR` toma el Lock mientras obtiene la instantánea del inventario.

La plantilla utiliza una pausa artificial de `0.001 s` dentro de `AGREGAR` y `QUITAR` para hacer visible la condición de carrera cuando se desactiva el Lock. **Debe eliminarse al robustecer el servidor**, porque no forma parte de la lógica del inventario.

El `Lock` coordina solamente los hilos **dentro del mismo proceso**. Si se levantan varias réplicas independientes, cada una tendrá su propio estado; se requerirá almacenamiento externo o un mecanismo de coordinación entre nodos.

## 8. Historial de cambios

| Versión | Etapa | Cambios |
|---|---|---|
| 1.0 | Semana 4 | Servidor TCP secuencial, una conexión atendida a la vez, comandos de sesión y pruebas de caída/red. |
| 2.0 | Semana 6 | Servidor con un hilo por cliente, inventario compartido, operaciones `LISTAR`, `AGREGAR`, `QUITAR`, `ESPERA`, protección mediante `Lock`, timeout de inactividad y logging por hilo. |


