# Taller de trade-offs: plataforma académica multi-sede — Semana 3

**Sistemas Distribuidos (FDICI25 / INFO35) · Viernes 4 de septiembre de 2026**

Entregable: `semana03/taller_multisede/matriz_<equipo>.md` en el repositorio del
equipo, antes de las 16:00.

## 1. Escenario (ficticio)

La Universidad de Los Lagos quiere una plataforma académica única para sus sedes
de **Osorno**, **Puerto Montt**, **Chiloé (Castro)** y **Santiago**. La plataforma
maneja cuatro tipos de datos:

| Dato | Quién lo escribe | Quién lo lee | ¿Puede estar desactualizado unos minutos? |
|---|---|---|---|
| Notas | docentes | estudiantes, jefatura | decidan |
| Matrículas y cupos | estudiantes, admisión | todos | decidan |
| Asistencia | docentes (desde la sala) | jefatura | decidan |
| Material de clase (PDF, video) | docentes | estudiantes | decidan |

Red disponible:

- Osorno ⇄ Puerto Montt: fibra propia, 5 ms, muy estable.
- Puerto Montt ⇄ Chiloé: enlace de proveedor, 25 ms, **se corta varias veces al mes**.
- Santiago ⇄ Puerto Montt: 20 ms; Santiago aloja el centro de datos actual.
- Todas las sedes tienen Internet comercial como respaldo.

## 2. Tres decisiones obligatorias

1. **¿Dónde viven los datos?** Para cada tipo de dato: centralizado en Santiago,
   replicado en todas las sedes, o replicado solo en algunas.
2. **¿Qué se replica y cómo?** Copia sincrónica (se confirma cuando todas las
   sedes escribieron) o asincrónica (se confirma local y se propaga después).
3. **¿Qué se sacrifica cuando se corta el enlace a Chiloé** durante una prueba en
   línea y una inscripción de cupos? Para cada dato: ¿los usuarios de Chiloé pueden
   seguir leyendo? ¿escribiendo? ¿Qué eligió el equipo, AP o CP, y por qué?

## 3. Matriz de trade-offs (plantilla)

```markdown
# Matriz de trade-offs — Equipo <nombre>

| Dato | ¿Dónde vive? | Replicación | Con Chiloé aislado: ¿lee? | ¿escribe? | Elección (AP/CP) | Qué se pierde |
|---|---|---|---|---|---|---|
| Notas | | | | | | |
| Matrículas y cupos | | | | | | |
| Asistencia | | | | | | |
| Material de clase | | | | | | |

## Justificación (máx. 10 líneas)
¿Qué modelo de la matriz del jueves describe mejor la plataforma resultante y por qué?
¿Qué desafío domina? ¿Qué falacia de la Semana 2 estarían asumiendo si centralizaran todo?

## La decisión más incómoda
La celda de la matriz que más discutieron y qué argumento ganó.
```

## 4. Pistas para discutir

- Una inscripción de cupos con dos sedes escribiendo a la vez es el problema de
  concurrencia del jueves. ¿Puede resolverse sin un coordinador?
- El material de clase es el caso CDN: copias locales, TTL, un origen.
- La asistencia se toma en la sala, con o sin enlace. ¿Qué modelo lo permite?
- Nada de esto tiene una respuesta única. Se evalúa que la matriz sea coherente
  con lo que el equipo está dispuesto a perder, no que coincida con la del docente.
