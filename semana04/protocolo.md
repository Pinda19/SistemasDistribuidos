# Protocolo de aplicación — Semana 4 - Equipo Thomas Pinda

Versión 0.1 · semana 4 · Documento basado en el servicio TCP ejecutado y las pruebas registradas.

## 1. Transporte

- Protocolo de transporte: TCP.
- Puerto del servidor: `5000`.
- Codificación: UTF-8.
- Delimitador de mensaje: una línea terminada en `\n`.
- Quién inicia: el cliente establece la conexión y envía comandos; el servidor responde a cada comando.
- Dirección del servidor dentro de Docker: nombre DNS `servidor`, en la red `sd_net`.
- Implementación actual: servidor secuencial, una conexión atendida a la vez.
- Timeout configurado en el cliente: `5.0` segundos esperando respuesta.

## 2. Mensajes

Los comandos se envían como texto, uno por línea. Las respuestas también terminan en salto de línea.

| Comando (cliente → servidor) | Argumentos | Respuesta (servidor → cliente) | ¿Cambia el estado de la conexión? |
|---|---|---|---|
| `HOLA <nombre>` | Nombre o texto libre | `OK hola <nombre>` | Sí. Guarda el nombre y aumenta el contador de mensajes. |
| `ECO <texto>` | Texto libre | `ECO <texto>` | Sí. Aumenta el contador de mensajes; no modifica el nombre ni el acumulado. |
| `CONTAR` | Ninguno | `OK <n>` | Sí. Incrementa y devuelve el número de mensajes recibidos en esta conexión, incluido `CONTAR`. |
| `SALIR` | Ninguno | `ADIOS` | Sí. Cuenta el mensaje y termina la sesión; el servidor cierra la conexión. |
| Cualquier comando desconocido | Variable | `ERROR comando desconocido` | Sí. Cuenta el mensaje, pero la sesión continúa. |
| `ACUMULAR <numero>` (operación propia) | Número entero | `OK acumulado <total>` | Sí. Suma el número al acumulador de esta conexión y aumenta el contador de mensajes. |

**Pruebas observadas:** `ACUMULAR 3` → `OK acumulado 3`, seguido por `ACUMULAR 5` → `OK acumulado 8`. También se probó `ACUMULAR 10` → `OK acumulado 10` en otra sesión. No se registró una prueba de argumentos inválidos, por lo que no se afirma aquí su respuesta exacta.

## 3. Estado

- **¿Qué recuerda el servidor de cada conexión?** El nombre enviado mediante `HOLA`, la cantidad de mensajes recibidos en esa conexión (`recibidos`) y el valor acumulado por `ACUMULAR`. Son datos asociados a la sesión; no forman una base de datos persistente.
- **¿Qué pasa con ese estado cuando el cliente se desconecta?** Se pierde al terminar la función que atiende la conexión. La siguiente sesión empieza con contador y acumulador nuevos.
- **Si el servidor se reinicia mientras un cliente está conectado, ¿qué pierde el cliente?** Se corta la conexión y se pierde el estado temporal de esa sesión. Después de reiniciar el servidor, una conexión nueva que ejecutó `CONTAR` recibió `OK 1`, confirmando que el contador anterior no se recuperó.

## 4. Secuencia típica

La siguiente sesión corresponde al guion ejecutado con éxito después de agregar `ACUMULAR`:

```text
cliente                                  servidor
   |------------ connect TCP ---------------->|
   |------------ HOLA equipo ---------------->|
   |<----------- OK hola equipo ---------------|
   |------------ ECO hola mundo ------------->|
   |<----------- ECO hola mundo ---------------|
   |------------ CONTAR --------------------->|
   |<----------- OK 3 -------------------------|
   |------------ NOEXISTE ------------------->|
   |<----------- ERROR comando desconocido ---|
   |------------ ACUMULAR 3 ----------------->|
   |<----------- OK acumulado 3 --------------|
   |------------ ACUMULAR 5 ----------------->|
   |<----------- OK acumulado 8 --------------|
   |------------ SALIR ---------------------->|
   |<----------- ADIOS ------------------------|
   |                (cierre TCP)              |
```

Los tiempos reportados para ese guion fueron de aproximadamente `0.1 ms` por operación, en la red Docker sin falla inducida.

## 5. Errores

| Situación | Qué ve el cliente | Qué ve el servidor |
|---|---|---|
| Comando desconocido | `ERROR comando desconocido` (ejemplo: `NOEXISTE`). | Log: `NOEXISTE` → `ERROR comando desconocido`; la sesión continúa. |
| Servidor caído durante la sesión | `CONEXIÓN PERDIDA: ConnectionError: el servidor cerró la conexión sin responder`, al intentar `CONTAR` después de matar el servidor. | El proceso fue terminado con `docker compose kill servidor`; los registros indican salida con código `137`. No hay cierre normal de la sesión interrumpida. |
| Cliente sin red durante la sesión | `TIMEOUT: el servidor no respondió en 5 s. ¿Caído, sin red o lento? No se puede saber.` al enviar `ECO Sigues ahi`. | En los logs aparece `ECO Sigues ahi` → `ECO Sigues ahi` y después el cierre de la conexión. Esto evidencia que procesar el comando no garantizó que el cliente recibiera la respuesta a tiempo. |
| Cliente corta sin `SALIR` (`Ctrl+C`) | `corte abrupto desde el cliente (sin SALIR)`. | Para la conexión observada tras el corte, el log registra su cierre con `0 mensajes`; no muestra un error adicional. |
| Segundo cliente mientras el primero permanece conectado | Se establece TCP (`conectado desde ...`), pero `HOLA Cliente2` termina en el mismo timeout de `5 s` sin respuesta. | Atiende primero `HOLA Cliente1` y `SALIR`. Inmediatamente después registra `HOLA Cliente2`, cuando el primer cliente ya había terminado. |

**Límite de estas observaciones:** no se cronometra de forma independiente el tiempo del corte del servidor, y no se dispone de marcas de tiempo de los comandos `docker network disconnect/connect` para medir la duración exacta de la interrupción.
