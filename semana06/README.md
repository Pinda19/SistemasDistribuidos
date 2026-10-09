# Semana 6 — Modelos de concurrencia en el servidor

Dos carpetas

- `demo/` los cuatro servidores de la clase del jueves (secuencial, hilos, procesos, asyncio) con el protocolo común de la semana 4 más `ESPERA`, y el cliente de carga. Sirve para reproducir en casa las cuatro demostraciones.
- `laboratorio/` plantilla del viernes. Servidor hilo por cliente con estado compartido y Lock (dominio de referencia inventario), cliente, cliente de carga, `docker-compose.yml`, `protocolo.md` v2, `observaciones.md` y `pauta_prueba_cruzada.md`.

Cada equipo copia `laboratorio/` como `semana06/` dentro de su repositorio y reemplaza el dominio de referencia por el suyo.
Convenciones del curso: red `sd_net`, servicios `servidor`, `cliente`, `carga`; puerto 5000; alias `c` = `docker compose exec cliente`.

## Comandos rápidos (demo)

```bash
cd demo
docker compose up -d --build
docker compose exec carga python cliente_carga.py --clientes 5 --comando "ESPERA 2"      # secuencial ~10 s
MODELO=hilos docker compose up -d --force-recreate servidor
docker compose exec carga python cliente_carga.py --clientes 5 --comando "ESPERA 2"      # ~2 s
docker compose exec carga python cliente_carga.py --clientes 20 --comando CONTAR --repeticiones 50   # 1000
SIN_LOCK=1 MODELO=hilos docker compose up -d --force-recreate servidor
docker compose exec carga python cliente_carga.py --clientes 20 --comando CONTAR --repeticiones 50   # mucho menos de 1000
MODELO=procesos docker compose up -d --force-recreate servidor   # cada cliente ve su propio contador
MODELO=asyncio docker compose up -d --force-recreate servidor    # un solo hilo, ~2 s
docker compose down -v
```
