"""Verificacion reproducible de la instalacion completa. No sustituye el ensayo de fallas.
Desde semana07/: docker compose exec cliente python verificar_semana07.py
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.getenv("API_URL", "http://nginx").rstrip("/")


def consultar(metodo, ruta, cuerpo=None):
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    solicitud = urllib.request.Request(
        BASE + ruta, data=datos, method=metodo,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(solicitud, timeout=8) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def verificar(condicion, texto):
    print(("OK " if condicion else "FALLO ") + texto)
    if not condicion:
        raise AssertionError(texto)


def main():
    print("RepoSync - prueba automatica del despliegue Semana 7")
    print("Endpoint:", BASE)
    replicas = []
    for _ in range(12):
        codigo, datos = consultar("GET", "/salud")
        verificar(codigo == 200, "GET /salud -> 200") if _ == 0 else None
        replicas.append(datos.get("replica"))
    print("Respuestas:", ", ".join(replicas))
    verificar({"api1", "api2"}.issubset(set(replicas)), "Nginx distribuye a ambas replicas")

    codigo, datos = consultar("GET", "/repos")
    verificar(codigo == 200 and "proyecto" in datos.get("repositorios", []), "GET /repos -> 200")

    codigo, datos = consultar("GET", "/repos/proyecto/ramas/main")
    verificar(codigo == 200 and isinstance(datos.get("head"), int), "Consulta de rama -> 200")

    codigo, datos = consultar("GET", "/repos/proyecto/ramas/main/historial")
    verificar(codigo == 200 and "inicio" in datos.get("historial", ""), "Historial -> 200")

    codigo, datos = consultar("GET", "/repos/inexistente/ramas/main")
    verificar(codigo == 404 and datos.get("detail", {}).get("error") == "REPO_NO_EXISTE", "Repositorio inexistente -> 404")

    nombre = "prueba_" + str(time.time_ns())
    codigo, datos = consultar("POST", "/repos/proyecto/ramas", {"nueva": nombre, "origen": "main"})
    verificar(codigo == 201 and datos.get("rama") == nombre, "Crear rama -> 201")
    head = datos["head"]

    ruta = "/repos/proyecto/ramas/" + nombre + "/commits"
    codigo, datos = consultar("POST", ruta, {"base": head, "mensaje": "prueba_rest"})
    verificar(codigo == 201 and datos.get("head") != head, "PUSH correcto -> 201")

    codigo, datos = consultar("POST", ruta, {"base": head, "mensaje": "obsoleto"})
    verificar(codigo == 409 and datos.get("detail", {}).get("error") == "CONFLICTO", "PUSH obsoleto -> 409")

    print("\nPRUEBA COMPLETA: todas las verificaciones pasaron.")
    print("Nota: rama temporal", nombre, "creada en la RAM del servidor.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PRUEBA FALLIDA:", exc, file=sys.stderr)
        sys.exit(1)
