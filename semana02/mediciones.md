# Mediciones — Laboratorio N°1 (Semana 2)

**Equipo:** _______________   **Integrantes:** Thomas Pinda 
**Fecha:** 28-08-2026   **Entorno:** Fedora Linux + Docker Engine

## Paso 1 — Línea base

| Métrica | Valor |
|---|---|
| RTT ping (promedio) | 0.050 ms |
| Throughput iperf3 | 38.5 Gbit/s |

## Pasos 2 y 3 — Latencia inyectada (100 llamadas)

| Latencia `tc` | Total (s) | Promedio (ms) | Máx (ms) | ¿Esperado? (sí/no, por qué) |
|---|---:|---:|---:|---|
| 0 ms (base) | 0.003 | 0.0 | 0.3 | Sí. Al ejecutarse cliente y servidor en la misma máquina y sin latencia artificial, los tiempos fueron prácticamente nulos. |
| 50 ms | 5.017 | 50.2 | 50.6 | Sí. Se esperaban aproximadamente 5 s, ya que 100 llamadas secuenciales × 50 ms ≈ 5 s. |
| 200 ms | 20.020 | 200.2 | 200.5 | Sí. Se esperaban aproximadamente 20 s, ya que 100 × 200 ms ≈ 20 s. |
| 500 ms | 50.022 | 500.2 | 500.5 | Sí. Se esperaban aproximadamente 50 s, ya que 100 × 500 ms ≈ 50 s. |

**Observación adicional:** con 1000 llamadas en la red sana se obtuvo un total de 0.027 s, promedio de 0.0 ms y máximo de 0.2 ms. El promedio aparece como 0.0 ms por redondeo, ya que los tiempos individuales son extremadamente pequeños.

## Paso 4 — Pérdida de paquetes

| Pérdida `tc` | Throughput iperf3 | Total cliente (s) | Observación |
|---|---|---:|---|
| 1% | 11.4 Gbit/s | 0.003 | El throughput cayó notablemente respecto de la línea base. En esta ejecución las 100 llamadas del cliente casi no se vieron afectadas: promedio 0.0 ms y máximo 0.1 ms. |
| 5% | 462 Mbit/s | 1.453 | El rendimiento cayó fuertemente. El cliente siguió funcionando, pero el promedio subió a 14.5 ms y el máximo llegó a 210.0 ms debido a retransmisiones TCP. |
| 20% | 1.01 Mbit/s | 6.432 | La red quedó casi inutilizable. El cliente siguió completando las 100 llamadas, pero con promedio de 64.3 ms y máximo de 824.1 ms. |
| 100% (falla provocada) | — | — | Sin timeout, el cliente terminó con `[Errno 113] No route to host`, en vez de quedar esperando indefinidamente como en el ejemplo. Con `TIMEOUT_S=3`, terminó correctamente tras 3.0 s indicando `TIMEOUT` y 0 llamadas completadas. |

## Falacia que asumimos sin advertirlo

El cliente asume que la red es confiable y que el servidor terminará respondiendo. Al no definir un timeout por defecto, una falla de red puede dejar a la aplicación esperando o depender de que el sistema operativo detecte el problema. La solución es establecer un tiempo máximo de espera y definir explícitamente qué debe hacer la aplicación cuando vence: reintentar, informar el error o abortar la operación.
