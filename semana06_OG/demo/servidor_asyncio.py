"""Modelo 3 — servidor ASÍNCRONO MONOHILO (asyncio).
Un solo hilo atiende a todos los clientes. Nunca bloquea: cuando una operación
espera (red, sleep), cede el control con `await` y el bucle de eventos atiende
a otro cliente. No hay Lock porque nunca hay dos clientes ejecutando
código al mismo tiempo.
"""
import asyncio
import logging
from protocolo_comun import HOST, PUERTO, procesar

logging.basicConfig(level=logging.INFO, format="%(asctime)s [asyncio] %(message)s")
estado = {"contador": 0}


async def atender(reader, writer):
    addr = writer.get_extra_info("peername")
    logging.info("conexion de %s", addr)
    try:
        while True:
            try:
                datos = await asyncio.wait_for(reader.readline(), timeout=60)
            except asyncio.TimeoutError:
                logging.warning("cliente %s inactivo, cerrando por timeout", addr)
                break
            if not datos:
                break
            linea = datos.decode("utf-8")
            respuesta, seguir = await procesar_async(linea)
            writer.write((respuesta + "\n").encode("utf-8"))
            await writer.drain()
            if not seguir:
                break
    except (ConnectionResetError, BrokenPipeError) as e:
        logging.warning("cliente %s se desconecto abruptamente (%s)", addr, e.__class__.__name__)
    finally:
        writer.close()
        logging.info("cierre de %s | contador=%s", addr, estado["contador"])


async def procesar_async(linea):
    # Reutiliza la lógica común, pero las esperas se hacen con await asyncio.sleep
    partes = linea.strip().split(" ", 1)
    cmd = partes[0].upper() if partes and partes[0] else ""
    arg = partes[1] if len(partes) > 1 else ""
    if cmd == "ESPERA":
        try:
            seg = float(arg)
        except ValueError:
            return "ERROR ESPERA_REQUIERE_SEGUNDOS", True
        await asyncio.sleep(seg)             # <-- cede el control, no bloquea
        return f"OK ESPERA {arg}", True
    return procesar(linea, estado, dormir=lambda s: None)


async def main():
    servidor = await asyncio.start_server(atender, HOST, PUERTO)
    logging.info("escuchando en %s:%s", HOST, PUERTO)
    async with servidor:
        await servidor.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
