# Proyecto integrador, Sistemas Distribuidos (FDICI25)

Es el producto de RA2. Se presenta en la **Evaluación 6, viernes 18-12-2026 (20%)**,
con demostración en vivo y falla provocada. La rúbrica se publica aparte.

## Qué construyen

Una aplicación distribuida orientada a objetos sobre el **mismo dominio** que el equipo
viene trabajando desde la semana 4. El servicio que hoy expone `Inventario` y `Pedido`
(o sus equivalentes) crece hasta ser una aplicación con varios nodos que cooperan.
Si el equipo quiere otro dominio, lo propone en `ALCANCE.md` y lo justifica.

## Requisitos mínimos

1. Al menos **tres nodos** (contenedores) con roles distintos en la red `sd_net`.
2. Al menos **dos clases de objeto remoto alojadas en nodos distintos**, y al menos una
   llamada en que un objeto de un nodo invoca a un objeto de otro nodo.
3. Al menos un objeto que viaja **por referencia** y tiene un ciclo de vida explícito
   (se crea, se usa y se termina).
4. Los objetos se localizan por **servidor de nombres**. Sin direcciones escritas en el código.
5. Una **cola de mensajes** (RabbitMQ, semana 13) que reparte trabajo entre al menos dos workers.
6. Un **mecanismo de coordinación** (semana 16), exclusión mutua distribuida o elección de líder.
7. Una **falla provocada** con comportamiento esperado documentado (qué se cae, qué ve el
   usuario y cómo se recupera).
8. Repositorio documentado con `README.md` (levantar en tres comandos), diagrama en draw.io
   y bitácora al día.

## Hitos

| Fecha | Hito |
|---|---|
| Vie 13-11 | `ALCANCE.md` aprobado en clase y primera entrada de la bitácora |
| Jue 26-11, 18.00 | Cola de mensajes integrada al proyecto (trabajo autónomo de la semana 13) |
| Jue 26-11 | Encuesta de avance del proyecto |
| Vie 11-12 | Mecanismo de coordinación funcionando (laboratorio de la semana 16) |
| Vie 18-12 | Evaluación 6, presentación con demo en vivo y falla provocada |

## Bitácora

Una entrada por semana en `proyecto/bitacora.md`, desde la semana 12. La entrada de cada
semana se sube a más tardar el jueves siguiente a las 18.00 (la de la semana 12 se escribe en
clase el 13-11, la de la semana 13 vence el jueves 26-11). Es formativa y obligatoria. Lo que importa es que se lean las
**decisiones** y **por qué** se tomaron, no un resumen de horas.

## Ideas de objetos por dominio

| Dominio | Objeto de entrada | Objeto con estado (por referencia) |
|---|---|---|
| Streaming y CDN | `Catalogo` | `SesionReproduccion` (posición, calidad) |
| E-commerce | `Tienda` | `Carro` (líneas, total) |
| Pagos electrónicos | `Pasarela` | `Transaccion` (pendiente, autorizada, rechazada) |
| Geolocalización y despacho | `Central` | `Despacho` (repartidor, posición, estado) |
| Juegos multijugador | `Lobby` | `Partida` (jugadores, puntaje) |
| Redes de sensores IoT | `Gateway` | `LoteLecturas` (lecturas pendientes de procesar) |
| Mensajería instantánea | `Directorio` | `Conversacion` (participantes, mensajes) |
| Control de versiones | `Repositorio` | `CambioEnCurso` (archivos, autor) |
