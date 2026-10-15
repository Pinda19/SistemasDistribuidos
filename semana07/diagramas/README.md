# Diagramas del servicio

Herramienta del curso, draw.io (https://app.diagrams.net o la aplicación de escritorio).

## Qué se entrega

| Archivo | Qué muestra | Cuándo |
|---|---|---|
| `despliegue_v1.drawio` y `despliegue_v1.png` | El sistema tal como quedó en la semana 6, cliente y servidor en `sd_net` | Viernes 09-10, en clases |
| `despliegue_v2.drawio` y `despliegue_v2.png` | El sistema en tres niveles, con Nginx, las réplicas de la API y el servidor, corregido según la pauta | Jueves 15-10, 18.00 |

## Notación mínima

- Un rectángulo por contenedor, con el nombre del servicio y el del contenedor (`servidor` / `sd_servidor`).
- Un contenedor grande o una zona de color para la red `sd_net`, y otra para el computador anfitrión.
- Una flecha por conexión, desde quien la inicia. Rótulo con protocolo y puerto, por ejemplo `TCP 5000` o `HTTP 8000`.
- Los puertos publicados al anfitrión se anotan como `8080 -> 80`.
- Una nota en el nodo que guarda estado (qué dato guarda) y otra con el modelo de concurrencia.

## Cómo exportar

Archivo, Exportar como, PNG, con fondo blanco y escala 200%. Guardar el `.drawio` y el `.png` con el mismo nombre.

`despliegue_base.drawio` es un punto de partida con el dominio de referencia. Se puede abrir y modificar.
