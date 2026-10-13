# Pauta de cotejo de diagramas, Semana 7

Cada equipo revisa el diagrama de despliegue de OTRO equipo con esta pauta.
Se responde SÍ o NO en cada ítem. Todo NO lleva un comentario de una línea que diga qué falta.
La revisión se hace mirando solo el diagrama, sin preguntarle al equipo autor.

## Asignación (la misma rotación de la prueba cruzada)

| Equipo que revisa | Diagrama revisado |
|---|---|
| Streaming/CDN | E-commerce |
| E-commerce | Pagos |
| Pagos | Geolocalización |
| Geolocalización | Juegos |
| Juegos | IoT |
| IoT | Mensajería (o Streaming/CDN si el equipo 7 no está) |
| Mensajería | Streaming/CDN |

## Pauta

| N° | Ítem | SÍ / NO | Comentario |
|---|---|---|---|
| 1 | Cada contenedor aparece como un nodo propio, con el mismo nombre que tiene en `docker-compose.yml` | | |
| 2 | La red `sd_net` está dibujada y se ve qué nodos están dentro de ella | | |
| 3 | Se distingue qué está dentro del computador del equipo y qué queda fuera (otro equipo, el navegador) | | |
| 4 | Cada flecha tiene dirección, de quien inicia la conexión hacia quien la recibe | | |
| 5 | Cada flecha está rotulada con el protocolo (TCP, HTTP) y el puerto | | |
| 6 | Los puertos publicados al computador anfitrión están marcados y se distinguen de los internos | | |
| 7 | Se indica en qué nodo vive el estado compartido y cuál es ese estado | | |
| 8 | Se indica el modelo de concurrencia del servidor (hilo por cliente u otro) | | |
| 9 | Mirando solo el diagrama se puede decir qué pasa si se cae cada nodo | | |
| 10 | El diagrama coincide con el `docker-compose.yml` del repositorio (mismos servicios, mismos puertos) | | |

## Cierre de la revisión

Los dos hallazgos más importantes para el equipo autor

1.
2.

Una cosa que este diagrama hace mejor que el nuestro
