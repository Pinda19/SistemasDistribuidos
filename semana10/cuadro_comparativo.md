# Cuadro comparativo — RMI, CORBA, DCOM y JSON-RPC 2.0

**Equipo:** Thomas Pinda **Integrantes:** Thomas Pinda **Proyecto estudiado:** RepoSync

> Borrador de estudio basado en las fuentes primarias indicadas al final. Revisar y expresar con las palabras del equipo antes de entregar. Los cuatro sistemas resuelven invocación remota, pero tienen contratos y niveles de acoplamiento distintos.

| Criterio | Java RMI | CORBA | DCOM | JSON-RPC 2.0 |
|---|---|---|---|---|
| Año y origen | Introducido por Sun para Java 1.1 (1997): invocar objetos Java desde otra JVM. | Impulsado por OMG desde comienzos de los 90: integrar aplicaciones de distintos proveedores y lenguajes. | Desarrollado por Microsoft en los 90 para extender COM a objetos remotos en red. | Especificación publicada en 2010 por el grupo JSON-RPC para invocar métodos remotamente de forma sencilla. |
| Modelo | Objetos remotos con identidad y métodos; pueden conservar estado. | Objetos distribuidos a través de un ORB; identidad y estado remotos. | Componentes/objetos COM activados e invocados desde otra máquina. | Llamadas a métodos identificados por nombre; no define identidades ni referencias de objetos remotos. |
| Contrato o IDL | Interfaz Java que extiende `Remote`, con métodos que pueden lanzar `RemoteException`. | OMG IDL independiente del lenguaje, a partir del cual se generan interfaces para cada lenguaje. | Interfaces COM descritas normalmente mediante MIDL/IDL y bibliotecas de tipos. | No exige IDL: el contrato lo forman `method`, `params` y la documentación de cada método. |
| Transporte y formato | Normalmente JRMP sobre TCP, con serialización propia de Java; hay variantes históricas RMI-IIOP. | GIOP/IIOP (habitualmente sobre TCP) y formato binario CDR. | ORPC apoyado en RPC de Microsoft (MS-RPCE); representación binaria. | JSON; no fija transporte. En RepoSync Semana 10 se envía mediante HTTP POST. |
| Lenguajes y plataformas | Principalmente Java/JVM, con acoplamiento a su modelo de objetos. | Múltiples lenguajes y sistemas operativos con ORB compatibles. | Predominantemente ecosistema COM/Windows. | Cualquier lenguaje/plataforma que produzca y lea JSON. |
| Referencias remotas y estado | Los clientes mantienen stubs/referencias; contempla gestión de vida de objetos remotos y recolección distribuida. | Referencias interoperables (IOR) y objetos servidos por ORB; gestión de vida según políticas del servidor. | Referencias de interfaces COM a distancia y gestión de vida mediante referencias remotas. | No incluye referencias de objetos ni estado de sesión en la especificación; el servidor puede tener estado propio, como nuestro diccionario en RAM. |
| Manejo de errores | Excepciones Java de ejecución remota (`RemoteException`) y excepciones del dominio. | Excepciones de usuario y del sistema definidas en el contrato/ORB. | Códigos de resultado (HRESULT) y errores de las llamadas remotas/COM. | Respuesta con objeto `error` que incluye `code`, `message` y `data` opcional. |
| Cinco decisiones (enmarcado, versión, id, errores y tipos) | La infraestructura RMI/JRMP determina encuadre, formato y correspondencia; tipos Java, excepciones y referencias remotas. | GIOP/IIOP determina enmarcado, versión e identificadores de petición; IDL define tipos y excepciones. | El soporte RPC/ORPC aporta estructura y correlación de llamadas; COM define contratos, tipos y manejo de errores. | HTTP aporta enmarcado en RepoSync; `jsonrpc:"2.0"` fija versión; `id` correlaciona; `error` codifica fallos; tipos JSON en `params/result`. |
| Estado actual | Integrado en Java, pero menos habitual en servicios web heterogéneos nuevos. | Tecnología heredada aún presente en sistemas empresariales antiguos; suele elegirse REST/gRPC para desarrollos nuevos. | Sigue existiendo en infraestructura Windows/COM, pero no suele ser primera opción en nuevas APIs multiplataforma. | Protocolo liviano todavía utilizado; compite con REST, GraphQL y gRPC según el tipo de integración. |
| Caso típico | Aplicación Java distribuida con objetos remotos y un registro RMI. | Sistemas empresariales legados que integran programas escritos en C++, Java u otros lenguajes. | Administración o componentes remotos en redes Windows tradicionales. | Un endpoint `/rpc` que permite crear y consultar ramas de RepoSync mediante `rama` y `clonar`. |

## Conclusión del equipo (borrador; personalizar a 5–8 líneas)

De las tecnologías estudiadas, JSON-RPC 2.0 es la que más se parece al protocolo v3 de RepoSync.
Ambos identifican operaciones, parámetros y respuestas, y distinguen errores de ejecución.
En Semana 9 diseñamos nuestro propio enmarcado e identificador; ahora JSON-RPC fija gran parte del contrato.
Para un servicio interno con múltiples lenguajes y alto tráfico valoraríamos gRPC, aunque no forma parte de las cuatro columnas.
Si debemos elegir solo entre las cuatro, JSON-RPC simplifica la integración en nuestro prototipo.
Para una API pública convencional, también consideraríamos REST por sus herramientas y adopción.
RMI, CORBA y DCOM aportaron conceptos valiosos, pero suelen imponer un modelo de objetos remotos más acoplado.

## Fuentes primarias consultadas

1. Oracle, *An Overview of RMI Applications*, tutorial de Java RMI, https://docs.oracle.com/javase/tutorial/rmi/overview.html (consulta: noviembre de 2026).
2. Object Management Group, *Introduction to OMG Specifications*, sección CORBA, https://www.omg.org/gettingstarted/specintro.htm (consulta: noviembre de 2026).
3. Microsoft, *[MS-DCOM]: Distributed Component Object Model (DCOM) Remote Protocol*, https://learn.microsoft.com/openspecs/windows_protocols/ms-dcom (consulta: noviembre de 2026).
4. JSON-RPC Working Group (2010, actualizado 2013), *JSON-RPC 2.0 Specification*, https://www.jsonrpc.org/specification (consulta: noviembre de 2026).
5. Universidad de Los Lagos (2026), *Guía de trabajo autónomo — Semana 10*, secciones 3–6 (material del curso).
