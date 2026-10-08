# Guía de análisis de casos — Semana 3

**Sistemas Distribuidos (FDICI25 / INFO35) · Viernes 4 de septiembre de 2026 · Laboratorio de Informática**

Instrumento de la sesión de análisis de casos (RA1). Cada equipo trabaja **un** caso,
completa la plantilla de la sección 2 y la guarda como
`semana03/guia_analisis_casos/caso_<nombre>.md` en el repositorio del equipo.
Se expone en 3 minutos y se responde una pregunta cruzada de otro equipo.

Herramienta de referencia: la matriz de la clase del jueves (seis modelos × cinco preguntas).

---

## 1. Los cuatro casos

### Caso A — BitTorrent

Protocolo de distribución de archivos entre pares. Un archivo se divide en trozos;
cada nodo que descarga (*leecher*) también sirve los trozos que ya tiene; un nodo
con el archivo completo es un *seeder*. Un *tracker* o una DHT (tabla hash
distribuida) responde "quién tiene qué". Los nodos entran y salen constantemente.

Preguntas guía: ¿Qué pasa cuando el último seeder se desconecta? ¿Quién decide qué
trozo se pide primero? ¿Cómo sabe un peer que el trozo recibido no está corrupto?

### Caso B — Kubernetes

Orquestador de contenedores. Un *plano de control* (API server, scheduler, etcd)
decide en qué nodo *worker* corre cada contenedor, vigila que la cantidad de
réplicas declarada se cumpla y reemplaza los que mueren. Los workers son
homogéneos y se gestionan como una sola máquina. Ejemplo de uso: Mercado Libre.

Preguntas guía: ¿Qué pasa si muere un worker? ¿Y si muere el plano de control?
¿Por qué etcd guarda el estado del cluster y qué elige (AP o CP) cuando hay partición?

### Caso C — Red de distribución de contenidos (CDN)

Copias de contenido (video, imágenes, archivos estáticos) ubicadas en puntos de
presencia cercanos al usuario. El DNS dirige a cada cliente al nodo más cercano;
si el nodo no tiene el objeto, lo pide al *origen* y lo guarda en caché por un
tiempo (TTL). Ejemplo de uso: streaming de los Juegos Panamericanos Santiago 2023.

Preguntas guía: ¿Qué pasa cuando el origen cambia un archivo y la copia de
Santiago aún tiene la versión anterior? ¿Qué se sacrifica a cambio de la baja
latencia? ¿Qué ocurre si cae el nodo de Santiago?

### Caso D — Red de sensores IoT

Boyas con sensores de oxígeno y temperatura en cada balsa de una salmonera del
Reloncaví. Transmiten por radio de bajo consumo a un *gateway* en la balsa, que
sube los datos por 4G intermitente a una plataforma central que emite alertas.
Las boyas tienen batería limitada y pueden desaparecer sin aviso.

Preguntas guía: ¿Qué pasa cuando una boya se queda sin batería? ¿Y cuando el
gateway pierde el 4G durante dos horas? ¿Dónde debe decidirse una alerta de
oxígeno bajo: en la boya, en el gateway o en la plataforma?

---

## 2. Plantilla (copiar a `caso_<nombre>.md` y completar)

```markdown
# Análisis de caso: <nombre del caso>

**Equipo:** <integrantes>  ·  **Fecha:** 04-09-2026

## 1. Modelo dominante
<cluster | grid | cloud | edge | P2P | ubicuo>

Justificación con las preguntas de la matriz (marcar la que más pesó):
- ¿Quién manda?:
- ¿Los nodos son parecidos?:
- ¿Qué tan lejos están?:
- ¿Qué pasa si uno desaparece?:

Modelos secundarios presentes (si los hay) y por qué no dominan:

## 2. Nodos y roles
| Nodo | Rol | ¿Cuántos? | ¿Estado o sin estado? |
|---|---|---|---|
| | | | |

## 3. Diagrama de interacciones
(Cajas = nodos, flechas etiquetadas con el protocolo o el tipo de mensaje.
Puede ser ASCII, una foto de la pizarrón o un archivo draw.io exportado a PNG.)

## 4. Desafío dominante
<heterogeneidad | apertura | escalabilidad | tolerancia a fallos | concurrencia | seguridad>

¿Cómo lo resuelve el sistema? ¿Qué falacia de la Semana 2 estaría asumiendo si no lo hiciera?

## 5. ¿Qué pasa si cae X?
Elegir el nodo cuya caída más duele y describir:
- Qué siguen viendo los usuarios:
- Qué deja de funcionar:
- ¿El sistema elige responder (AP) o no equivocarse (CP)? ¿Cómo lo saben?

## 6. La desventaja que vamos a defender
Una desventaja concreta del modelo elegido para este caso, con un ejemplo.
(Es la respuesta que preparan para la pregunta cruzada.)
```

---

## 3. Exposición y pregunta cruzada

- **3 minutos** por equipo: modelo dominante, diagrama, desafío dominante, qué pasa si cae X.
- **1 minuto** de pregunta cruzada: otro equipo pregunta por una desventaja o un
  escenario de falla. El equipo expositor responde con la sección 6 de su guía.
- Criterios formativos (sin nota): la clasificación está justificada con la matriz;
  el diagrama tiene nodos y flechas etiquetadas; la desventaja es concreta, no genérica.
