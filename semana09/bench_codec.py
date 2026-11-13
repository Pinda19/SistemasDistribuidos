"""Compara tamaño y tiempo de JSON vs binario con mensajes del dominio RepoSync.

Solo mide serialización local, no latencia ni ancho de banda de la red.
"""
import random
import sys
import time
from mensajes import Solicitud, Respuesta
import codec

N = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
if not 1 <= N <= 100000:
    raise SystemExit("N debe estar entre 1 y 100000")
random.seed(9)
RAMAS = ["main", "desarrollo", "pruebas", "documentacion"]
MENSAJES = ["inicio", "ajuste_conflicto", "nueva_funcion", "revisar_rama"]


def solicitud_aleatoria(i):
    rama = random.choice(RAMAS)
    tipo = i % 4
    if tipo == 0:
        return Solicitud("REPOS", [], id=i + 1)
    if tipo == 1:
        return Solicitud("CLONAR", ["proyecto", rama], id=i + 1)
    if tipo == 2:
        return Solicitud("RAMA", ["proyecto", f"{rama}_{i}", "main"], id=i + 1)
    return Solicitud("PUSH", ["proyecto", rama, str(i % 10), random.choice(MENSAJES)], id=i + 1)


def respuesta_aleatoria(i):
    if i % 4 == 3:
        return Respuesta(id=i + 1, estado="ERROR", error="CONFLICTO HEAD=12")
    rama = random.choice(RAMAS)
    return Respuesta(id=i + 1, estado="OK", datos=["proyecto", rama, f"HEAD={i % 12}"])


def medir(nombre, mensajes, clase):
    cod, dec = codec.CODECS[nombre]
    t0 = time.perf_counter()
    cuerpos = [cod(m) for m in mensajes]
    t1 = time.perf_counter()
    recuperados = [dec(c, clase) for c in cuerpos]
    t2 = time.perf_counter()
    assert recuperados == mensajes
    bytes_total = sum(len(c) for c in cuerpos)
    return bytes_total / len(mensajes), bytes_total, (t1 - t0) * 1000, (t2 - t1) * 1000


def main():
    solicitudes = [solicitud_aleatoria(i) for i in range(N)]
    respuestas = [respuesta_aleatoria(i) for i in range(N)]
    print(f"N = {N} solicitudes y {N} respuestas del dominio RepoSync")
    print("| Mensaje | Codec | Bytes prom | Bytes totales | Codif (ms) | Decod (ms) |")
    print("|---|---|---:|---:|---:|---:|")
    resultados = {}
    for etiqueta, mensajes, clase in (("Solicitud", solicitudes, Solicitud), ("Respuesta", respuestas, Respuesta)):
        for nombre in ("json", "bin"):
            promedio, total, cod_ms, dec_ms = medir(nombre, mensajes, clase)
            resultados[(etiqueta, nombre)] = total
            print(f"| {etiqueta} | {nombre} | {promedio:.1f} | {total} | {cod_ms:.2f} | {dec_ms:.2f} |")
    for etiqueta in ("Solicitud", "Respuesta"):
        j = resultados[(etiqueta, "json")]
        b = resultados[(etiqueta, "bin")]
        print(f"{etiqueta}: binario ocupa {100 * (1 - b/j):.1f}% menos bytes que JSON")
    print("Tiempos obtenidos en esta máquina; no son constantes universales.")


if __name__ == "__main__":
    main()
