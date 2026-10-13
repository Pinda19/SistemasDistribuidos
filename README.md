# Semana 7, capas, niveles y servicios

Dos carpetas

- `demo/` material de la clase del jueves 08-10. El servidor TCP de la semana 6 con una puerta HTTP (FastAPI) delante y Nginx repartiendo entre dos réplicas. Sirve para reproducir en casa las tres demostraciones.
- `laboratorio/` plantilla del viernes 09-10. Cada equipo la copia como `semana07/` dentro de su repositorio, reemplaza `servidor.py` por el suyo de `semana06/` y adapta `api.py` a su dominio.

Convenciones del curso, red `sd_net`, servicios `servidor`, `api1`, `api2`, `nginx`, `cliente`. El servidor escucha en el 5000 (ya no se publica), la API en el 8000 y Nginx se publica en el 8080 del computador. Alias `c` = `docker compose exec cliente`.

## Comandos rápidos de la demo

```bash
cd demo
docker compose up -d --build

# Demo 1, dos réplicas con el inventario adentro (se parte en dos)
ESTADO=local docker compose up -d --force-recreate api1 api2
docker compose exec cliente python cliente_http.py POST /items/pera/entradas cantidad=50
docker compose exec cliente python cliente_http.py --repetir 4 GET /items/pera

# Demo 1, el inventario sale a su propio nivel (tres niveles, dato único)
ESTADO=servidor docker compose up -d --force-recreate api1 api2
docker compose exec cliente python cliente_http.py POST /items/pera/entradas cantidad=50
docker compose exec cliente python cliente_http.py --repetir 4 GET /items/pera

# Demo 2, el protocolo de texto traducido a HTTP
docker compose exec cliente python cliente_http.py GET /items
docker compose exec cliente python cliente_http.py POST /items/manzana/salidas cantidad=500    # 409
docker compose exec cliente python cliente_http.py POST /items/kiwi/salidas cantidad=1         # 404
# en el navegador  http://localhost:8080/docs

# Demo 3, falla en dos tiempos
docker compose kill api1
docker compose exec cliente python cliente_http.py --repetir 4 GET /items/pera                 # sigue, solo api2
docker compose kill servidor
docker compose exec cliente python cliente_http.py --repetir 2 GET /items/pera                 # 503

docker compose down -v
```

En PowerShell las variables se definen antes del comando, por ejemplo `$env:ESTADO="local"; docker compose up -d --force-recreate api1 api2`.
