# Bitácora del proyecto integrador

## Entrada 1 — Semana 12 — Preparación del 20-11-2026

**Integrante:** Thomas Pinda. Entrada preparada a partir de la adaptación del
proyecto; no se atribuye asistencia ni aprobación docente del 13-11.

**Decisiones:** conservar el dominio RepoSync de semana11 sin cambios y exponer
Repositorio como entrada; CambioEnCurso representa autor, base y rutas mediante
una referencia remota. El proyecto integrador añadirá Validador en otro nodo.

**Motivos:** mantener las reglas de conflicto ya estudiadas y separar negocio de
transporte. Usar el inventario genérico no representaría el tema asignado.
La devolución de diccionarios basta para consultas, pero una referencia remota
permite estudiar vida y pérdida de un cambio temporal.

**Trabajo preparado:** objetos, cliente, servidor, Compose, pruebas automáticas,
observaciones de los cinco pasos y propuesta de alcance. Se validaron Pyro5,
referencias, modos y fallos entre procesos locales separados. El dominio se
comparó byte por byte con el de semana11.

**Validación recibida:** el 20-11-2026 se ejecutó pruebas.ps1 en Windows con
Docker Desktop. El registro concluye con PRUEBAS TERMINADAS; los cuatro bloques
de aserciones remotas terminaron en OK. Se comprobaron las tres situaciones
de falla del paso 5 y el re-registro periódico. Se incorporaron las salidas a
observaciones.md y se completó calidad.md.

**Problemas:** el entorno de preparación no dispone de Docker ni PowerShell.
La validación entre contenedores se realizó en el equipo del estudiante. Se contempló que la primera llamada de una conexión cortada
puede informar ConnectionClosedError antes de detectar la referencia colgante.
No se reintentan publicaciones automáticamente cuando el resultado es desconocido.

| Próximo paso | Responsable | Plazo |
|---|---|---|
| Pruebas Docker y documentación | Thomas Pinda | Completado 20-11-2026 |
| Solicitar revisión del alcance | Thomas Pinda / docente | Próxima instancia de revisión |
| Integrar RabbitMQ con dos workers | Thomas Pinda | 26-11-2026 |
| Añadir persistencia y segundo nodo de objetos | Thomas Pinda | Antes de la demostración final |
| Implementar coordinación y probar la falla | Thomas Pinda | 11-12-2026 |
