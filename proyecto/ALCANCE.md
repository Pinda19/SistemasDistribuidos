# Alcance del proyecto integrador — RepoSync

**Equipo / integrante:** Thomas Pinda. **Dominio:** 04, control de versiones distribuido.
**Preparado:** 20-11-2026. **Estado:** propuesta pendiente de aprobación docente.

## 1. Problema

Un equipo necesita publicar cambios sobre ramas compartidas sin sobrescribir el
trabajo ajeno y conocer el resultado de sus validaciones. RepoSync simulará la
publicación de revisiones, detectará bases desactualizadas y repartirá trabajos
de validación, haciendo visibles los efectos de caídas y reintentos.

## 2. Objetos remotos

| Clase | Nodo | Estado propio | Métodos |
|---|---|---|---|
| Repositorio | repositorio | Ramas/revisiones en almacenamiento duradero previsto | clonar, rama, push, historial, abrir_cambio |
| CambioEnCurso | repositorio | Autor, base y rutas temporales | agregar, ver, confirmar, cancelar |
| Validador | validacion | Configuración de reglas y resultados | validar_revision, consultar_resultado |

Repositorio y CambioEnCurso ya están implementados en semana12 en un único
servidor. Validador es trabajo futuro: vivirá en un segundo nodo de objetos.
Repositorio invocará remotamente Validador para comprobar metadatos antes de
aceptar una publicación, mostrando cooperación entre objetos de nodos distintos.

Ciclo de vida: abrir_cambio crea y registra CambioEnCurso, el cliente recibe un
Proxy, agrega rutas y confirma o cancela. El objeto se desregistra al terminar.
Un conflicto no lo elimina; el cliente puede inspeccionarlo y cancelarlo.
Se plantea expiración por lease para cambios abandonados.

## 3. Nodos previstos

| Servicio Compose | Rol | Se comunica con |
|---|---|---|
| nombres | Descubrimiento de objetos | cliente, repositorio, validacion, workers |
| repositorio | Publicación, ramas y objetos temporales | cliente, nombres, validacion, rabbitmq |
| validacion | Segundo objeto remoto y reglas de cambios | nombres, repositorio |
| rabbitmq | Cola de validación posterior a publicación | repositorio, worker1, worker2 |
| worker1 / worker2 | Trabajos consumidos en competencia | rabbitmq, validacion |
| cliente | CLI de uso y demostración | nombres, repositorio |

Red `sd_net`. Los nombres de objetos se resolverán mediante el directorio,
con hosts y puertos configurados por entorno.

## 4. Cola y coordinación

Semana 13: publicar un trabajo de validación de revisión simulada en RabbitMQ,
consumido por dos workers. Cada tarea llevará ID; se usarán ACK después de
guardar resultado y deduplicación para tolerar reentregas.

Semana 16: coordinar la publicación sobre una misma rama con exclusión mutua
distribuida o actualización condicional duradera por HEAD. El Lock de Python
actual protege solo un proceso y no constituye coordinación distribuida.
La elección final se ajustará al mecanismo exigido en el laboratorio de esa semana.

## 5. Falla a demostrar el 18-12

Terminar un worker mientras procesa una validación. El usuario verá la revisión
con validación pendiente; RabbitMQ reentregará el trabajo sin ACK al otro worker.
El resultado se guardará por ID para evitar duplicados. La revisión confirmada
deberá sobrevivir al reinicio del servidor mediante persistencia, aún pendiente.

## 6. Fuera de alcance

Implementación real de Git, clonación de archivos, merges, interfaz web,
autenticación de producción y servicio de alojamiento público. Se trabaja con
metadatos de revisiones y validaciones de laboratorio.

## 7. Riesgos

| Riesgo | Respuesta |
|---|---|
| Pérdida de RAM al reiniciar | Persistir revisiones y resultados; probar restauración |
| Cambios temporales abandonados | Cancelación explícita y posterior lease |
| Tareas duplicadas | ID único y deduplicación duradera antes del ACK |
| Caída del directorio | Re-registro y estudiar persistencia/replicación |
| Poco tiempo o recursos | Priorizar CLI y un flujo extremo a extremo con dos workers |

---

**Aprobación docente:** pendiente. **Fecha:** pendiente.
**Observaciones del docente:** pendiente.
