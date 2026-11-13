# Observaciones — Semana 9, serialización explícita

**Equipo:** _(nombre)_  **Integrantes:** _(nombres)_  **Fecha:** 23-10-2026

## Paso 2 — Ida y vuelta de los codecs

Salida de `python codec.py`:

```
(pegar aquí)
```

Tamaño de la misma solicitud en JSON ____ bytes y en bin ____ bytes.

## Paso 3 — Medición

Salida de `python bench_codec.py 10000`:

```
(pegar aquí la tabla)
```

Conclusión en dos líneas (cuánto ahorra el binario, cuál es más rápido, qué sacrificamos a cambio):

_(escribir)_

## Paso 4 — Integración

| Prueba | codec=json | codec=bin |
|---|---|---|
| `HOLA` | | |
| `AGREGAR ...` (del dominio) | | |
| `LISTAR` | | |
| Error del dominio (por ejemplo stock insuficiente) | | |

## Paso 5 — Falla provocada

| Modo de `cliente_malo.py` | Qué vio el cliente | Qué dice el log del servidor | ¿El servidor siguió atendiendo? |
|---|---|---|---|
| `version` | | | |
| `largo` | | | |
| `basura` (codec json) | | | |
| `basura` (codec bin) | | | |
| `cruzado` | | | |

¿Cuál de los dos codecs falló de forma más clara ante la basura y por qué?

_(escribir)_

## Para la semana autónoma

Una pregunta que nos quedó sobre serialización o protocolos:

_(escribir)_
