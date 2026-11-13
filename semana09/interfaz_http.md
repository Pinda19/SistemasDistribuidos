# RepoSync — interfaz HTTP (Semana 7)

## 9.2. Contrato de operaciones: TCP ↔ REST

Las réplicas HTTP no almacenan ramas ni commits: traducen solicitudes hacia `servidor.py`.
`repo`, `rama`, `nueva` y `origen` admiten únicamente letras ASCII, números, `_` y `-` (1–30 caracteres).

| Método y ruta REST | TCP a servidor:5000 | HTTP correcto | Respuesta de ejemplo |
|---|---|---|---|
| `GET /salud` | Ninguno (salud API) | `200` | `{"estado":"ok","replica":"api1"}` |
| `GET /repos` | `REPOS` | `200` | `{"repositorios":["proyecto"],"replica":"api1"}` |
| `GET /repos/{repo}/ramas/{rama}` | `CLONAR repo rama` | `200` | `{"repositorio":"proyecto","rama":"main","head":0,"replica":"api1"}` |
| `GET /repos/{repo}/ramas/{rama}/historial` | `HISTORIAL repo rama` | `200` | `{"historial":"0:inicio",...}` |
| `POST /repos/{repo}/ramas` | `RAMA repo nueva origen` | `201` | `{"rama":"desarrollo","head":0,...}` |
| `POST /repos/{repo}/ramas/{rama}/commits` | `PUSH repo rama base mensaje` | `201` | `{"rama":"main","head":1,...}` |

Cuerpos de los POST:

```json
{"nueva":"desarrollo","origen":"main"}
```

```json
{"base":0,"mensaje":"primer_cambio"}
```

La respuesta de historial conserva la representación de texto del servidor TCP
(`"1:cambio | 0:inicio"`) y añade `repositorio`, `rama`, `replica`.

## 9.3. Errores TCP ↔ HTTP

| Respuesta TCP / condición | HTTP | Respuesta REST o significado |
|---|---|---|
| `ERROR REPO_NO_EXISTE` | 404 | `{"detail":{"error":"REPO_NO_EXISTE",...}}` |
| `ERROR RAMA_NO_EXISTE` | 404 | Rama inexistente |
| `ERROR RAMA_EXISTE` | 409 | Rama duplicada |
| `ERROR CONFLICTO HEAD=n` | 409 | Base obsoleta: `{"detail":{"error":"CONFLICTO","detalle":"HEAD=n",...}}` |
| `ERROR FORMATO` o validación FastAPI | 422 | Solicitud inválida |
| `ERROR HISTORIAL_INCONSISTENTE` | 500 | Inconsistencia interna |
| Falla de conexión TCP | 503 | `SERVIDOR_NO_DISPONIBLE` |
| Timeout de respuesta TCP | 504 | `SERVIDOR_NO_RESPONDE` |
| Respuesta inesperada del servidor TCP | 502 | `RESPUESTA_TCP_INVALIDA` |

Las respuestas HTTP de FastAPI incluyen el nombre de la réplica (`api1` o `api2`).
La documentación interactiva se publica en `http://localhost:8080/docs`.

## Seguridad y límites

- FastAPI valida identificadores y tipos; rechaza inyección de saltos de línea.
- El campo `mensaje` de PUSH acepta entre 1 y 80 caracteres y no puede contener CR/LF.
- REST es stateless: el cuerpo de PUSH contiene la base conocida por el cliente.
- `PUSH` utiliza control optimista de concurrencia (`base` contra `HEAD`) y Lock del backend.
- Se mantiene el timeout de 60 segundos en el socket TCP del servidor.
- No hay persistencia ni replicación del backend: al reiniciar servidor, `main` vuelve a HEAD=0.

## Pruebas

En Fedora, con los contenedores activos:

```bash
docker compose exec cliente python verificar_semana07.py
docker compose exec cliente python cliente_http.py --repetir 8 GET /salud
```

Los códigos HTTP (`200`, `201`, `404`, `409`) se verifican con el script incluido;
los resultados de fallas se registran en `observaciones.md` tras ejecutarlos.
