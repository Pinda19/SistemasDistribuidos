# Interfaz HTTP del servicio (anexo de protocolo.md)

> Plantilla de la Semana 7. Este documento se agrega a `protocolo.md` v2 como sección 9.
> Regla de oro, la misma de la semana 6. Otro equipo debe poder usar la API leyendo SOLO este documento.

## 9.1 Identificación

| Campo | Valor |
|---|---|
| Equipo | (nombre del equipo) |
| Entrada única | `http://localhost:8080` (Nginx) |
| Formato | JSON, UTF-8 |
| Documentación interactiva | `http://localhost:8080/docs` |
| Réplicas de la API | api1, api2 |
| Dónde vive el estado | en el servidor TCP, la API no guarda nada |

## 9.2 Tabla de traducción, operación por operación

| Comando del protocolo de texto | Método y ruta HTTP | Cuerpo JSON | Respuesta correcta | Código |
|---|---|---|---|---|
| `LISTAR` | `GET /items` | (sin cuerpo) | `{"items": {"manzana": 100}, "replica": "api1"}` | 200 |
| `LISTAR` (un ítem) | `GET /items/{item}` | (sin cuerpo) | `{"item": "pera", "cantidad": 100, "replica": "api2"}` | 200 |
| `AGREGAR <item> <cantidad>` | `POST /items/{item}/entradas` | `{"cantidad": 5}` | `{"item": "pera", "cantidad": 105, "replica": "api1"}` | 201 |
| `QUITAR <item> <cantidad>` | `POST /items/{item}/salidas` | `{"cantidad": 3}` | `{"item": "pera", "cantidad": 102, "replica": "api2"}` | 201 |

(Reemplazar por las operaciones del dominio. Mínimo una de lectura y una que modifique estado.)

## 9.3 Tabla de errores

| Situación | Respuesta del protocolo de texto | Código HTTP | Quién responde |
|---|---|---|---|
| El recurso no existe | `ERROR ITEM_NO_EXISTE` | 404 | la API |
| La petición choca con el estado actual | `ERROR STOCK_INSUFICIENTE <actual>` | 409 | la API |
| Cuerpo o ruta mal formados | (no llega al servidor) | 422 | la API, antes de traducir |
| El servidor TCP no está disponible | (sin respuesta) | 503 | la API |
| El servidor TCP no responde a tiempo | (sin respuesta) | 504 | la API |
| No queda ninguna réplica de la API | (sin respuesta) | 502 | Nginx |

## 9.4 Decisiones de diseño (dos o tres líneas cada una)

- ¿Por qué esos sustantivos como recursos?
- ¿Qué operación NO expusieron por HTTP y por qué?
- ¿Qué valida la API antes de traducir, y qué pasaría si no lo validara?
