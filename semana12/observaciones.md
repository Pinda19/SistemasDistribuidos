# Observaciones — Semana 12 — RepoSync

**Equipo / integrante:** Thomas Pinda. **Dominio:** 04, control de versiones distribuido.
**Ejecución Docker:** 20-11-2026, inicio 12:04:14, zona America/Santiago.
Los contenedores usaron UTC, tres horas por delante del host Windows.

**Evidencia:** pruebas.ps1 ejecutado en Windows con Docker Desktop; registros
recibidos en evidencias.rar. Se conservan `evidencias/docker.txt`, `vigilar.txt`
y `cambio.txt`. El registro termina con PRUEBAS TERMINADAS e incluye OK base,
OK single, OK valor y OK session. `docker_utf8.txt` convierte la codificación
mixta de la captura original a UTF-8, sin alterar su texto. Las observaciones siguientes corresponden a las pruebas Docker del equipo.

## Paso 1. Nombres y servidor arriba

Docker Compose mostró cliente, servidor y nombres como contenedores separados activos.

```text
15:04:31 sd.pinda.repositorio -> PYRO:repositorio@servidor:9100
15:04:31 nombres registrados ['Pyro.NameServer', 'sd.pinda.repositorio']
```

Partes de la URI: protocolo PYRO, ID estable repositorio, nodo servidor, puerto 9100.
El nombre lógico sd.pinda.repositorio se resuelve en el directorio: es diferente
del ID del objeto. El servidor anuncia su nombre DNS en Compose; localhost
identificaría al propio contenedor cliente. La red bridge sd_net del proyecto
transporta Pyro5 sobre TCP con serialización serpent, sin puertos publicados al host.

## Paso 2. Dominio como objetos remotos

| Clase | Método | ¿Modifica estado? |
|---|---|---|
| Repositorio | clonar, historial | Consultan dominio; incrementan instrumentación |
| Repositorio | rama, push, publicar_auto | Sí: ramas o revisiones |
| Repositorio | abrir_cambio | Sí: registra cambio temporal |
| Repositorio | quien_soy | Sí: contador de instancia |
| Repositorio | cambios_vivos | Consulta objetos; incrementa instrumentación |
| CambioEnCurso | agregar | Sí: rutas del cambio |
| CambioEnCurso | ver | No: copia de metadatos |
| CambioEnCurso | confirmar | Sí: publica y desregistra si tiene éxito |
| CambioEnCurso | cancelar | Sí: desregistra sin publicar |

Salida real de verificar.py base:

```text
Rama: {'repositorio': 'proyecto', 'rama': 'demo', 'head': 0}
Push: {'repositorio': 'proyecto', 'rama': 'demo', 'head': 1}
ErrorDominio preservado: CONFLICTO HEAD=1
ErrorParametros preservado: base debe ser entero >= 0
OK base
```

Se preservan las clases de excepciones mediante register_dict_to_class.
El dominio es idéntico byte por byte a semana11/dominio.py. RepoSync simula
revisiones y ramas: las rutas quedan como metadatos en el mensaje, sin guardar
contenidos reales de archivos ni implementar el protocolo Git.

## Paso 3. Referencias y ciclo de vida

```text
Referencia: PYRO:obj_1f0e6590141942d08172bfd15f7da4ac@servidor:9100
Confirmar: {'repositorio': 'proyecto', 'rama': 'main', 'head': 2}
Referencia colgante esperada: unknown object
Cancelar: cancelado
```

abrir_cambio crea y registra CambioEnCurso y devuelve un Proxy. Autor, base y
rutas viven en el servidor; ver devuelve datos por valor. Confirmar aplica push
y desregistra el objeto: reutilizar su URI falla. Cancelar también lo desregistra
sin publicar; la prueba comprobó cero cambios vivos al terminar ambos objetos.
HEAD=2 porque la revisión 1 ya se asignó a demo: la numeración pertenece al
repositorio completo, no a cada rama.

Con POR_VALOR=1:

```text
Rechazo por valor esperado: unsupported serialized class: objetos.CambioEnCurso
OK valor
```

Sin registrar, Pyro intenta enviar la instancia serializada y el cliente rechaza
la clase porque no tiene un deserializador permitido. Los diccionarios y las
referencias remotas registradas sí son admitidos. No hay recolector distribuido:
los cambios abandonados requieren cancelar, un lease futuro o el fin del proceso.

## Paso 4. Modo de instancia

Resultados efectivos de Docker:

| Modo | Proxy A, dos llamadas | Proxy B | ¿Comparten contador? |
|---|---|---|---|
| single | Instancia 1, llamadas 11 y 12 | Instancia 1, llamada 13 | Sí |
| session | Instancia 2, llamadas 1 y 2 | Instancia 3, llamada 1 | No |

single conserva una instancia compartida; session, una por conexión. Las
consultas previas explican que el contador single no empiece en 1 y que session
empiece en la instancia 2. Para estado de una conexión serviría session, pero
no implica identidad durable de usuario. Las ramas viven en dominio.py, compartido
por todas las instancias del proceso. Cambiar de modo no crea repositorios por
cliente; recrear servidor para aplicar la configuración sí reinicia su RAM.

## Paso 5. Falla en tres tiempos

Se publicó antes_caida y HEAD quedó en 1. vigilar conservó el mismo Proxy.
Otro cliente abrió un cambio con base 1 y esperó seis segundos antes de confirmar.

| Tiempo | Acción | Proxy existente | Cliente nuevo | Estado |
|---|---|---|---|---|
| 1. Servidor muerto | kill servidor | FALLA ConnectionClosedError | Error de comunicación | RAM deja de estar disponible |
| 2. Servidor vuelve | start servidor | Recupera consultas | Funciona con HEAD=0 | Revisiones y cambios temporales perdidos |
| 3a. Nombres muerto | kill nombres | Sigue consultando | Failed to locate the nameserver | Dominio accesible mediante conexión existente |
| 3b. Nombres vuelve | start nombres | Sigue consultando | unknown name: sd.pinda.repositorio | Directorio vacío |
| 3c. Servidor se registra | restart servidor | Entrada disponible | URI resuelve | Reinicio también reinicializa RAM |

### Servidor y cambio temporal

```text
15:04:47 ok {'repositorio': 'proyecto', 'rama': 'main', 'head': 1}
15:04:48 FALLA ConnectionClosedError: receiving: not enough data
15:04:56 sin reconexión: ConnectionClosedError
15:05:01 ok {'repositorio': 'proyecto', 'rama': 'main', 'head': 0}
```

La recuperación tuvo detección de conexión cerrada y un intento de reconexión
fallido antes de volver a consultar. Un cliente nuevo también recibió HEAD=0.
El cambio temporal mostró:

```text
15:04:46 recibí Proxy, referencia PYRO:obj_c04f356a3b694375a0ed0095f4314d9a@servidor:9100
15:04:46 estado remoto {'repositorio': 'proyecto', 'rama': 'main', 'autor': 'Thomas', 'base': 1, 'archivos': ['temporal.txt']}
15:04:52 ERROR de comunicación; resultado de una escritura puede ser DESCONOCIDO: receiving: not enough data
```

Esta salida demuestra conexión cortada; no se afirma que ese cliente recibió
unknown object después del reinicio. La referencia colgante tras confirmar sí
se demostró en el paso 3. 

### Directorio y re-registro

```text
15:05:10 ERROR de nombres: Failed to locate the nameserver
15:05:13 ERROR de nombres: unknown name: sd.pinda.repositorio
15:05:17 sd.pinda.repositorio -> PYRO:repositorio@servidor:9100
```

vigilar mantuvo consultas OK cada segundo entre 15:05:01 y 15:05:16, incluyendo
las dos fallas de clientes nuevos. La conexión previamente resuelta no necesita
buscar nuevamente el nombre para cada llamada.

Se repitió la caída de nombres con REREGISTRO=5. A las 15:05:29 se recuperó
la consulta URI sin reiniciar servidor entre esa caída y la consulta. El registro
periódico recupera descubrimiento a costa de una operación aproximadamente cada
cinco segundos; no replica el directorio ni preserva el dominio.

### Puntos únicos de falla y semántica

Servidor es punto único de falla de ejecución y estado; nombres lo es para
descubrimiento de clientes nuevos. Harían falta almacenamiento duradero,
recuperación de objetos y directorio persistente o replicado. Reiniciar servidor
recupera el registro pero también pierde el dominio en RAM.

La adaptación no implementa reintentos automáticos de escrituras ni deduplicación.
La respuesta perdida deja resultado desconocido para el cliente (maybe). La
comparación de base de push rechaza publicaciones desactualizadas, pero no
recupera la respuesta original ni garantiza exactamente una vez. publicar_auto
no es idempotente. El dominio requiere evitar revisiones duplicadas y conservar
las confirmadas mediante ID lógico, deduplicación persistente y actualización
transaccional del HEAD junto con la revisión.
