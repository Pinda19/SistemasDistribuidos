"""serializar.py — demo guiada 2 del jueves (Semana 9).

El mismo mensaje del dominio, AGREGAR tornillo 25, codificado de cinco formas.
Muestra los bytes y el tamaño de cada una. Antes de correrlo, pedir al curso
que prediga cuánto pesa cada formato.

  python serializar.py            muestra los cinco formatos
  python serializar.py 100000     además mide tiempo de codificar y decodificar N veces
"""
import json
import struct
import sys
import time
import xml.etree.ElementTree as ET

from mensajes import Solicitud
import codec

sol = Solicitud(operacion="AGREGAR", argumentos=["tornillo", "25"], id=7)


# 1. Texto por líneas, lo que usaban hasta la semana 7
def texto(s):
    return f"{s.operacion} {' '.join(s.argumentos)}\n".encode("utf-8")


# 2. JSON
def a_json(s):
    return codec.codificar_json(s)


# 3. XML
def a_xml(s):
    raiz = ET.Element("solicitud", version=str(s.version), id=str(s.id))
    ET.SubElement(raiz, "operacion").text = s.operacion
    args = ET.SubElement(raiz, "argumentos")
    for a in s.argumentos:
        ET.SubElement(args, "arg").text = a
    return ET.tostring(raiz, encoding="utf-8")


# 4. Binario propio con struct, el del laboratorio del viernes
def a_bin(s):
    return codec.codificar_bin(s)


# 5. Protocol Buffers, adelanto de la semana 11
def a_proto(s):
    import mensaje_pb2
    m = mensaje_pb2.Solicitud(version=s.version, id=s.id, operacion=s.operacion, argumentos=s.argumentos)
    return m.SerializeToString()


def de_proto(b):
    import mensaje_pb2
    m = mensaje_pb2.Solicitud()
    m.ParseFromString(b)
    return m


def hexdump(b, ancho=16):
    for i in range(0, len(b), ancho):
        trozo = b[i:i + ancho]
        hx = " ".join(f"{x:02x}" for x in trozo)
        asc = "".join(chr(x) if 32 <= x < 127 else "." for x in trozo)
        print(f"      {i:04x}  {hx:<{ancho * 3}}  {asc}")


FORMATOS = [
    ("texto (sem. 4-7)", texto, None),
    ("JSON", a_json, lambda b: codec.decodificar_json(b, Solicitud)),
    ("XML", a_xml, None),
    ("struct (viernes)", a_bin, lambda b: codec.decodificar_bin(b, Solicitud)),
    ("Protobuf (sem. 11)", a_proto, de_proto),
]


def main():
    print(f"Mensaje: {sol}\n")
    tam = {}
    for nombre, f, _ in FORMATOS:
        try:
            b = f(sol)
        except ImportError:
            print(f"  {nombre:20s}  (protobuf no instalado, pip install protobuf)\n")
            continue
        tam[nombre] = len(b)
        print(f"  {nombre:20s}  {len(b):3d} bytes")
        hexdump(b)
        print()

    print("  Resumen")
    base = tam.get("JSON", 1)
    for nombre, n in tam.items():
        barra = "█" * max(1, round(40 * n / max(tam.values())))
        print(f"    {nombre:20s} {n:3d} B  {barra}  {100 * n / base:5.0f}% de JSON")

    if len(sys.argv) > 1:
        N = int(sys.argv[1])
        print(f"\n  Tiempo para {N} codificaciones + decodificaciones")
        for nombre, f, g in FORMATOS:
            if g is None:
                continue
            try:
                t0 = time.perf_counter()
                for _ in range(N):
                    g(f(sol))
                dt = time.perf_counter() - t0
                print(f"    {nombre:20s} {dt * 1000:8.1f} ms  ({dt / N * 1e6:5.2f} µs por mensaje)")
            except ImportError:
                pass


if __name__ == "__main__":
    main()
