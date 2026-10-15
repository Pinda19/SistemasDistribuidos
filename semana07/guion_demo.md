# Evaluación 3 — Guion de demostración RepoSync (9 minutos + 3 de preguntas)

**Tema:** Control de versiones distribuido. Es una simulación de repositorio
remoto para estudiar concurrencia, ramas y fallos, no un servidor Git completo.

| Minuto | Qué mostrar | Acción |
|---|---|---|
| 0–2 | Diagrama v2, capas y niveles; identificar único nodo con estado | `diagramas/despliegue_v2.png` |
| 2–3 | Protocolo TCP y su traducción REST; códigos 200/201/409 | `interfaz_http.md` |
| 3–4 | Servicios y estado de salud; dos réplicas | `docker compose ps` |
| 4–5 | Balanceo, endpoints REST y docs automáticas | `docker compose exec cliente python verificar_semana07.py` |
| 5–6 | Múltiples clientes TCP atendidos en paralelo | `docker compose exec cliente python cliente_carga.py --clientes 5 --comando "ESPERA 2"` |
| 6–7 | Falla 1: matar una API. Predicción: permanece HTTP 200 | `docker compose kill api1` y `... cliente_http.py --repetir 4 GET /repos` |
| 7–8 | Falla 2: matar servidor. Predicción: HTTP 503 | `docker compose kill servidor` y `... cliente_http.py --repetir 2 GET /repos` |
| 8–9 | Recuperación y límite de estado en RAM | `docker compose up -d` y `... cliente_http.py GET /repos/proyecto/ramas/main` |

## Predicciones escritas ANTES de la falla

- Muere `api1`: Nginx cambia a `api2` y `GET /repos` sigue con 200.
- Muere `servidor`: `api1`/`api2` no tienen historial propio; `GET /repos` da 503.
- Se reinicia `servidor`: vuelve HEAD=0 porque RAM no es almacenamiento persistente.

## Explicación técnica breve

- 3 niveles funcionales: Nginx entrada, API HTTP escalable sin estado,
  servidor TCP con lógica de dominio y estado único en memoria.
- 5 contenedores (`servidor`, `api1`, `api2`, `nginx`, `cliente`) en `sd_net`.
- Nginx publica 8080→80; API usa 8000 interno, TCP usa 5000 interno.
- Con Lock, dos PUSH sobre la misma base no se aceptan ambos: segundo es 409.
- `zone api 64k` comparte estado round-robin entre workers Nginx.

## Plan B

Si una demostración falla en vivo: mostrar logs con `docker compose logs --tail 80
nginx api1 api2 servidor`, verificar servicios con `docker compose ps` y
explicar dónde está el problema usando el diagrama. Mostrar también las pruebas
ya documentadas (señalando cuáles fueron ejecutadas realmente).

## Preguntas posibles

- **¿Por qué no se divide el estado?** Ambas API hablan con el mismo servidor TCP.
- **¿Qué pasa si cae nginx?** No queda puerta HTTP pública; API/backend pueden seguir vivos.
- **¿Qué pasa si cae servidor?** No hay réplica del estado: API devuelve 503.
- **¿Por qué REST es stateless?** Cada petición trae repo, rama y base; la API
  no mantiene una sesión ni recuerda revisiones entre peticiones.
- **¿Es Git real?** No: solo simula ramas, historial y publicación condicional.
