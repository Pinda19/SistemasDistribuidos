"""bench_codec.py — medición comparada JSON vs binario (Semana 9, paso 3).

Codifica y decodifica N solicitudes del dominio del equipo con cada codec y
reporta tamaño promedio y tiempo total. No usa la red, mide solo el costo de
serializar. Copien la tabla resultante en observaciones.md.

Uso:  python bench_codec.py [N]
"""
import random
import sys
import time

from mensajes import Solicitud, Respuesta, OPERACIONES
import codec

N = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
random.seed(9)

# Argumentos de ejemplo. Cambien PRODUCTOS por los datos de su dominio.
PRODUCTOS = ["tornillo", "tuerca", "golilla", "perno", "clavo", "remache", "bisagra", "tarugo"]
OPS = [o for o in OPERACIONES if o not in ("HOLA", "SALIR", "ESPERA")] or ["ECO"]


def solicitud_aleatoria(i):
    op = random.choice(OPS)
    if op in ("AGREGAR", "QUITAR"):
        args = [random.choice(PRODUCTOS), str(random.randint(1, 500))]
    elif op == "ECO":
        args = [" ".join(random.choice(PRODUCTOS) for _ in range(3))]
    else:
        args = []
    return Solicitud(operacion=op, argumentos=args, id=i)


def respuesta_aleatoria(i):
    return Respuesta(id=i, estado="OK", datos=[f"{p}={random.randint(0, 999)}" for p in random.sample(PRODUCTOS, 4)])


def medir(nombre, mensajes, clase):
    cod, dec = codec.CODECS[nombre]
    t0 = time.perf_counter()
    cuerpos = [cod(m) for m in mensajes]
    t1 = time.perf_counter()
    for c in cuerpos:
        dec(c, clase)
    t2 = time.perf_counter()
    bytes_total = sum(len(c) for c in cuerpos)
    return {
        "bytes_prom": bytes_total / len(mensajes),
        "bytes_total": bytes_total,
        "t_cod_ms": (t1 - t0) * 1000,
        "t_dec_ms": (t2 - t1) * 1000,
    }


def main():
    sols = [solicitud_aleatoria(i) for i in range(N)]
    resps = [respuesta_aleatoria(i) for i in range(N)]
    print(f"N = {N} solicitudes y {N} respuestas del dominio\n")
    print("| Mensaje   | Codec | Bytes promedio | Bytes totales | Codificar (ms) | Decodificar (ms) |")
    print("|-----------|-------|---------------:|--------------:|---------------:|-----------------:|")
    filas = {}
    for etiqueta, msgs, clase in (("Solicitud", sols, Solicitud), ("Respuesta", resps, Respuesta)):
        for nombre in ("json", "bin"):
            r = medir(nombre, msgs, clase)
            filas[(etiqueta, nombre)] = r
            print(f"| {etiqueta:9s} | {nombre:5s} | {r['bytes_prom']:14.1f} | {r['bytes_total']:13d} | {r['t_cod_ms']:14.1f} | {r['t_dec_ms']:16.1f} |")
    print()
    for etiqueta in ("Solicitud", "Respuesta"):
        j, b = filas[(etiqueta, "json")], filas[(etiqueta, "bin")]
        ahorro = 100 * (1 - b["bytes_total"] / j["bytes_total"])
        print(f"{etiqueta}: el binario ocupa {ahorro:.0f}% menos bytes que JSON "
              f"(JSON {j['bytes_prom']:.0f} B vs bin {b['bytes_prom']:.0f} B por mensaje)")
    print("\nEjemplo de una misma solicitud en cada codec")
    s = sols[0]
    for nombre in ("json", "bin"):
        c = codec.codificar(s, nombre)
        print(f"  {nombre:5s} {len(c):3d} B  {c!r}")


if __name__ == "__main__":
    main()
