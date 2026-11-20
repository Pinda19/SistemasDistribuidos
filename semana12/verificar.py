"""Pruebas remotas reproducibles; ejecutar dentro del contenedor cliente."""
import sys
from Pyro5.api import Proxy
from Pyro5.errors import CommunicationError, DaemonError, SerializeError
from cliente_pyro import repositorio
import dominio


def verificar(paso):
    with repositorio() as r:
        if paso in ("single", "session"):
            a1 = r.quien_soy()
            a2 = r.quien_soy()
            with repositorio() as b:
                b1 = b.quien_soy()
            assert a1["instancia"] == a2["instancia"]
            assert (a1["instancia"] == b1["instancia"]) == (paso == "single")
            assert a2["llamadas"] == a1["llamadas"] + 1
            print("Proxy A", a1, a2, "Proxy B", b1)
        elif paso == "valor":
            try:
                r.abrir_cambio("proyecto", "main", "Thomas")
            except SerializeError as e:
                print("Rechazo por valor esperado:", e)
            else:
                raise AssertionError("La clase sin registrar debió rechazarse")
        elif paso == "base":
            assert r.clonar("proyecto", "main")["head"] == 0
            print("Rama:", r.rama("proyecto", "demo", "main"))
            print("Push:", r.push("proyecto", "demo", 0, "primer_cambio"))
            try:
                r.push("proyecto", "demo", 0, "base_vieja")
            except dominio.ErrorDominio as e:
                print("ErrorDominio preservado:", e)
            else:
                raise AssertionError("Debió rechazar la base vieja")
            try:
                r.push("proyecto", "main", -1, "base_invalida")
            except dominio.ErrorParametros as e:
                print("ErrorParametros preservado:", e)
            else:
                raise AssertionError("Debió rechazar parámetros")
            cambio = r.abrir_cambio("proyecto", "main", "Thomas")
            assert isinstance(cambio, Proxy)
            with cambio:
                print("Referencia:", cambio._pyroUri)
                cambio.agregar("README.md")
                print("Estado:", cambio.ver())
                print("Confirmar:", cambio.confirmar("documentacion"))
                try:
                    cambio.ver()
                except (CommunicationError, DaemonError) as e:
                    assert "unknown object" in str(e)
                    print("Referencia colgante esperada:", e)
                else:
                    raise AssertionError("Debió desregistrarse")
            with r.abrir_cambio("proyecto", "main", "Thomas") as cancelado:
                print("Cancelar:", cancelado.cancelar())
            assert r.cambios_vivos() == 0
            print("Historial:", r.historial("proyecto", "main"))
        else:
            raise ValueError("Usar base, single, session o valor")
    print("OK", paso)


if __name__ == "__main__":
    verificar(sys.argv[1] if len(sys.argv) > 1 else "base")
