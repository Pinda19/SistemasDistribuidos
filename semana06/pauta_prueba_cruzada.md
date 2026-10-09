# Pauta de prueba cruzada — Semana 6

Cada equipo prueba el servidor de OTRO equipo usando únicamente su `protocolo.md`.
No se puede preguntar al otro equipo durante la prueba; todo lo que no esté escrito se reporta como hallazgo.

## Asignación (rotación circular)

| Equipo que prueba | Servidor probado |
|---|---|
| Streaming/CDN | E-commerce |
| E-commerce | Pagos |
| Pagos | Geolocalización |
| Geolocalización | Juegos |
| Juegos | IoT |
| IoT | Mensajería (o Streaming/CDN si el equipo 7 no está) |
| Mensajería | Streaming/CDN |

## Cómo conectarse

Ruta principal, por red del laboratorio

```bash
docker compose exec -e SERVIDOR_HOST=<IP_DEL_OTRO_EQUIPO> cliente python cliente.py
```

Ruta de respaldo, si la red del laboratorio aísla los equipos

```bash
git clone <repo_del_otro_equipo> otro && cd otro/semana06
docker compose up -d --build servidor
docker compose exec -e SERVIDOR_HOST=servidor cliente python cliente.py
```

## Checklist (marcar y anotar en observaciones.md)

| # | Verificación | Resultado |
|---|---|---|
| 1 | Con el protocolo.md se pudo saber puerto, formato y comando inicial sin preguntar | |
| 2 | Cada operación documentada responde como dice la tabla | |
| 3 | Un comando desconocido produce el error documentado | |
| 4 | Un argumento mal formado produce el error documentado (no un silencio ni una caída) | |
| 5 | Dos clientes simultáneos son atendidos a la vez (usar cliente_carga con ESPERA o la operación lenta del otro equipo) | |
| 6 | La operación que modifica estado compartido da el valor esperado bajo carga | |
| 7 | Desconectar un cliente abruptamente no afecta a los demás | |
| 8 | Algo que el protocolo NO dice y tuvimos que adivinar | |

## Cómo provocar la desconexión abrupta sobre el servidor ajeno

```bash
docker compose exec carga python cliente_carga.py --clientes 3 --comando "ESPERA 5" &
sleep 1; docker compose kill carga
docker compose exec cliente python cliente.py     # el servidor ajeno debe seguir respondiendo
```
