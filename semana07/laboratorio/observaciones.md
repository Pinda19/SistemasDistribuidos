# Observaciones de la Semana 7

Equipo
Integrantes
Dominio del servicio

## Paso 1  diagrama de despliegue v1 (el sistema de la semana 6)

Archivo entregado en `diagramas/`
Cantidad de nodos, redes y puertos representados

## Paso 2  revisión por pares

Equipo que revisó nuestro diagrama
Ítems de la pauta marcados como NO (copiar el número y el comentario)
Qué vamos a corregir primero y por qué

Equipo cuyo diagrama revisamos
Los dos hallazgos más importantes que les dejamos

## Paso 3  una operación como servicio REST

Operación del protocolo de texto elegida
Método y ruta HTTP
Salida de la prueba contra api1 (copiar la línea completa)
Salida de un caso de error y su código HTTP

## Paso 4  dos réplicas detrás de Nginx

Salida de `cliente_http.py --repetir 4` (copiar las cuatro líneas)
¿Qué réplica atendió cada petición?
¿El dato es el mismo sin importar la réplica? ¿Por qué?

## Paso 5  falla provocada en dos tiempos

### Tiempo 1, cae una réplica de la API
Predicción escrita ANTES de ejecutar
Comando usado
Qué respondió el sistema (copiar las líneas)
¿Cuánto tardó la primera petición después de la caída?

### Tiempo 2, cae el servidor TCP
Predicción escrita ANTES de ejecutar
Comando usado
Qué respondió el sistema y con qué código HTTP
¿Qué se perdió al volver a levantar el servidor?

### Conclusión en tres líneas
¿Qué nivel se pudo replicar sin problemas y cuál no? ¿Por qué?
