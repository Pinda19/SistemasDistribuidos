"""Adaptadores Pyro5 de RepoSync; el dominio de semana11 se conserva intacto."""
import os
import threading
from Pyro5.api import behavior, expose
import dominio

MODO = os.environ.get("MODO", "single")
POR_VALOR = os.environ.get("POR_VALOR", "0") == "1"
_contador = 0
_lock_contador = threading.Lock()


def _texto(valor, nombre):
    if not isinstance(valor, str) or not valor.strip():
        raise dominio.ErrorParametros(f"{nombre} debe ser texto no vacio")
    return valor.strip()


@expose
class CambioEnCurso:
    """Cambio remoto temporal: autor, rutas y base; vive hasta confirmar/cancelar.

    Simula metadatos de archivos. No almacena contenidos ni implementa Git real.
    Un conflicto conserva el objeto para consultar o cancelar; confirmar con
    éxito o cancelar lo desregistra. Un reinicio también destruye el objeto.
    """

    def __init__(self, repo, rama, autor):
        self.repo, self.rama = repo, rama
        self.autor = _texto(autor, "autor")
        self.base = dominio.clonar(repo, rama)["head"]
        self.archivos = []
        self._lock = threading.Lock()
        self._terminado = False

    def __getstate__(self):
        # El experimento POR_VALOR debe fallar por clase no admitida en el
        # cliente, sin intentar serializar el Lock privado del servidor.
        return {"repo": self.repo, "rama": self.rama, "autor": self.autor,
                "base": self.base, "archivos": list(self.archivos)}

    def _activo(self):
        if self._terminado:
            raise dominio.ErrorDominio("CAMBIO_TERMINADO")

    def agregar(self, ruta):
        """Modifica las rutas del cambio temporal; no modifica el repositorio."""
        ruta = _texto(ruta, "ruta")
        with self._lock:
            self._activo()
            if ruta not in self.archivos:
                self.archivos.append(ruta)
            return len(self.archivos)

    def ver(self):
        """Consulta el cambio y devuelve sus metadatos por valor."""
        with self._lock:
            self._activo()
            return {"repositorio": self.repo, "rama": self.rama,
                    "autor": self.autor, "base": self.base,
                    "archivos": list(self.archivos)}

    def confirmar(self, mensaje):
        """Modifica HEAD mediante push y desregistra el cambio si tuvo éxito."""
        with self._lock:
            self._activo()
            if not self.archivos:
                raise dominio.ErrorParametros("CAMBIO_SIN_ARCHIVOS")
            mensaje = _texto(mensaje, "mensaje")
            resultado = dominio.push(self.repo, self.rama, self.base,
                                     f"{self.autor}: {mensaje} [{', '.join(self.archivos)}]")
            self._terminar()
            return resultado

    def cancelar(self):
        """Modifica el ciclo de vida: desregistra sin publicar una revisión."""
        with self._lock:
            self._activo()
            self._terminar()
            return "cancelado"

    def _terminar(self):
        self._terminado = True
        self._pyroDaemon.unregister(self)


@expose
@behavior(instance_mode=MODO)
class Repositorio:
    """Entrada de RepoSync: delega en dominio.py y fabrica cambios por referencia."""

    def __init__(self):
        global _contador
        with _lock_contador:
            _contador += 1
            self.numero = _contador
        self.llamadas = 0
        self._lock = threading.Lock()

    def _contar(self):
        with self._lock:
            self.llamadas += 1
            return self.llamadas

    def clonar(self, repo, rama):
        """Consulta HEAD; solo cambia el contador de instrumentación."""
        self._contar()
        return dominio.clonar(repo, rama)

    def rama(self, repo, nueva, origen):
        """Modifica el dominio creando una rama desde otra existente."""
        self._contar()
        return dominio.rama(repo, nueva, origen)

    def push(self, repo, rama, base, mensaje):
        """Modifica HEAD si la base coincide; rechaza publicaciones desactualizadas."""
        self._contar()
        return dominio.push(repo, rama, base, mensaje)

    def historial(self, repo, rama):
        """Consulta revisiones; solo cambia el contador de instrumentación."""
        self._contar()
        return dominio.historial(repo, rama)

    def publicar_auto(self, repo, rama, mensaje):
        """Modifica HEAD sin base; es no idempotente y no tiene deduplicación."""
        self._contar()
        return dominio.publicar_auto(repo, rama, mensaje)

    def abrir_cambio(self, repo, rama, autor):
        """Crea estado temporal en el servidor y devuelve un Proxy por referencia."""
        self._contar()
        cambio = CambioEnCurso(repo, rama, autor)
        if not POR_VALOR:
            self._pyroDaemon.register(cambio)
        return cambio

    def cambios_vivos(self):
        """Consulta objetos temporales registrados; modifica solo instrumentación."""
        self._contar()
        return sum(isinstance(o, CambioEnCurso)
                   for o in list(self._pyroDaemon.objectsById.values()))

    def quien_soy(self):
        """Modifica y consulta el contador propio para comparar modos de instancia."""
        llamadas = self._contar()
        return {"modo": MODO, "instancia": self.numero, "llamadas": llamadas}
