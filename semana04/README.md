# Semana 4 — Primer socket TCP entre dos nodos

Sistemas Distribuidos FDICI25 / INFO35 · viernes 11-09-2026 · Laboratorio de Informática

## 1. Qué es este material

Un servidor TCP y un cliente TCP mínimos, cada uno en su propio contenedor, conectados por la red `sd_net`. A diferencia de la semana 2, esta vez **el código es de ustedes**. Lo que reciben es el punto de partida del servicio Cliente-Servidor propio que van a hacer evolucionar durante todo el semestre. A partir de hoy este directorio vive en el repositorio del equipo y cambia semana a semana.

El servidor atiende **un cliente a la vez**. Eso es a propósito. Hoy van a ver por qué es un problema y en la semana 6 lo van a resolver.

## 2. Contenido

| Archivo | Qué es | ¿Se modifica hoy? |
|---|---|---|
| `docker-compose.yml` | Define los dos nodos (`servidor`, `cliente`) y la red `sd_net`. El código se monta como volumen, así que editar y volver a ejecutar no requiere rebuild. | No |
| `Dockerfile` | Imagen `python:3.12-slim` con `ping` e `iproute2`. Sin dependencias externas, solo biblioteca estándar. | No |
| `servidor/servidor.py` | Servidor TCP secuencial en el puerto 5000. Protocolo de texto por líneas. | **Sí**, en el paso 3 agregan una operación propia |
| `cliente/cliente.py` | Cliente interactivo o con guion. Mide el tiempo de cada llamada y reporta timeouts y cortes. | **Sí**, en el paso 3 |
| `protocolo.md` | Plantilla para documentar el protocolo de aplicación del equipo. | **Sí**, es el entregable |
| `observaciones.md` | Plantilla para registrar lo observado en las fallas provocadas. | **Sí**, es el entregable |

## 3. Requisitos previos

- Docker Desktop iniciado antes de las 14.15. `docker compose version` debe responder.
- Repositorio del equipo clonado y con el avance de la semana 3 en `main`.
- Roles definidos. Un integrante opera la terminal del servidor, el otro la del cliente. Rotan en el paso 3.

## 4. Instalación

1. Descargar `semana04.zip` desde la plataforma y descomprimirlo **dentro del repositorio del equipo**, al mismo nivel que `semana02/` y `semana03/`.
2. Abrir **dos** terminales en la carpeta `semana04/`. Una será la del servidor y otra la del cliente.
3. Construir y levantar (la primera vez demora 1 a 3 minutos)

```powershell
docker compose up -d --build
docker compose ps          # servidor Up, cliente Up
```

4. Definir el atajo `c` en la terminal del cliente. Dura mientras la ventana esté abierta.

```powershell
function c { docker compose exec cliente @args }        # PowerShell
c() { docker compose exec cliente "$@"; }               # bash / zsh
```

5. Verificar que el cliente ve al servidor por nombre

```powershell
c ping -c 2 servidor
```

Si el ping falla, `docker compose down`, `docker network rm sd_net`, y volver a levantar.

6. Ver quién está en la red

```powershell
docker network inspect sd_net | findstr Name      # PowerShell
docker network inspect sd_net | grep Name         # bash / zsh
```

## 5. Los cinco pasos

Los detalles, comandos y resultados esperados están en la guía de laboratorio (PPTX). Resumen

1. **Estructura y red.** Levantar los dos contenedores, verificar la red y leer los dos archivos Python.
2. **Servidor.** Seguir los logs del servidor y entender el ciclo `bind`, `listen`, `accept`, `recv`, `send`.
3. **Cliente.** Conectarse desde el otro contenedor, probar el protocolo, abrir un segundo cliente y observar qué pasa, y agregar una operación propia al protocolo en ambos lados.
4. **Falla provocada.** Matar el servidor con el cliente conectado, y luego desconectar el cliente de `sd_net`. Registrar qué error aparece y cuánto tarda en aparecer en cada caso.
5. **Cierre.** Completar `protocolo.md` y `observaciones.md`, bajar los contenedores, commit y push.

## 6. Qué se entrega

En el repositorio del equipo, antes del jueves 24-09 a las 18.00

- `semana04/servidor/servidor.py` y `semana04/cliente/cliente.py` con la operación propia funcionando.
- `semana04/protocolo.md` completo.
- `semana04/observaciones.md` con las dos fallas registradas (error, tiempo hasta detectarla, qué vio cada lado).

## 7. Trabajo autónomo hasta el 24-09

La próxima sesión es el jueves 24-09 (la semana del 14 al 18 es receso). Además de la entrega anterior

- Guía de estudio para la prueba parcial del viernes 25-09, publicada en la plataforma.
- Tanenbaum y Van Steen (2017), capítulo 2 (arquitecturas) y capítulo 4, sección de sockets.
- Documentación del módulo `socket` de Python, https://docs.python.org/3/library/socket.html
