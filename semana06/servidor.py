"""RepoSync: servidor TCP concurrente de control de versiones (simulación didáctica).

Replica la interfaz de un repositorio remoto simplificado: ramas, historial y
publicación condicional de revisiones. No ejecuta Git ni almacena archivos reales.

Compatible con el esqueleto exigido en Semana 6: hilos, Lock, timeout, logs,
Docker Compose, UTF-8 y mensajes delimitados por salto de línea.
"""
import logging
import os
import socket
import threading
import time

HOST = os.environ.get('HOST', '0.0.0.0')
PUERTO = int(os.environ.get('PUERTO', '5000'))
SIN_LOCK = os.environ.get('SIN_LOCK', '0') == '1'
TIMEOUT_CLIENTE = int(os.environ.get('TIMEOUT_CLIENTE', '60'))
# Ventana didáctica: establecer 0 para quitarla tras la prueba de carrera.
PAUSA_CARRERA = float(os.environ.get('PAUSA_CARRERA', '0.005'))

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [servidor] %(threadName)s %(message)s')

estado = {
    'repos': {
        'proyecto': {
            'ramas': {'main': 0},
            'commits': {0: {'padre': None, 'mensaje': 'inicio'}},
            'siguiente': 1,
        }
    },
    'operaciones': 0,
}
lock = threading.Lock()


class SinLock:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


def seccion_critica():
    return SinLock() if SIN_LOCK else lock


def op_repos(arg):
    if arg.strip():
        return 'ERROR FORMATO REPOS'
    with seccion_critica():
        nombres = sorted(estado['repos'])
    return 'OK ' + ' '.join(nombres)


def op_clonar(arg):
    partes = arg.split()
    if len(partes) != 2:
        return 'ERROR FORMATO CLONAR <repo> <rama>'
    nombre, rama = partes
    with seccion_critica():
        repo = estado['repos'].get(nombre)
        if repo is None:
            return 'ERROR REPO_NO_EXISTE'
        if rama not in repo['ramas']:
            return 'ERROR RAMA_NO_EXISTE'
        cabeza = repo['ramas'][rama]
    return f'OK {nombre} {rama} HEAD={cabeza}'


def op_historial(arg):
    partes = arg.split()
    if len(partes) != 2:
        return 'ERROR FORMATO HISTORIAL <repo> <rama>'
    nombre, rama = partes
    with seccion_critica():
        repo = estado['repos'].get(nombre)
        if repo is None:
            return 'ERROR REPO_NO_EXISTE'
        if rama not in repo['ramas']:
            return 'ERROR RAMA_NO_EXISTE'
        # Seguir padres desde HEAD; entregar los últimos 10 registros visibles.
        cabeza = repo['ramas'][rama]
        entradas = []
        while cabeza is not None and len(entradas) < 10:
            commit = repo['commits'].get(cabeza)
            if commit is None:
                return 'ERROR HISTORIAL_INCONSISTENTE'
            entradas.append(f'{cabeza}:{commit["mensaje"]}')
            cabeza = commit['padre']
    return 'OK ' + ' | '.join(entradas)


def op_rama(arg):
    partes = arg.split()
    if len(partes) != 3:
        return 'ERROR FORMATO RAMA <repo> <nueva> <origen>'
    nombre, nueva, origen = partes
    with seccion_critica():
        repo = estado['repos'].get(nombre)
        if repo is None:
            return 'ERROR REPO_NO_EXISTE'
        if origen not in repo['ramas']:
            return 'ERROR RAMA_NO_EXISTE'
        if nueva in repo['ramas']:
            return 'ERROR RAMA_EXISTE'
        repo['ramas'][nueva] = repo['ramas'][origen]
        cabeza = repo['ramas'][nueva]
    return f'OK RAMA {nueva} HEAD={cabeza}'


def op_push(arg):
    partes = arg.split(' ', 3)
    if (len(partes) != 4 or not partes[2].isdigit() or
            not partes[3].strip() or len(partes[3]) > 80):
        return 'ERROR FORMATO PUSH <repo> <rama> <base> <mensaje>'
    nombre, rama, base_str, mensaje = partes
    base = int(base_str)
    with seccion_critica():
        repo = estado['repos'].get(nombre)
        if repo is None:
            return 'ERROR REPO_NO_EXISTE'
        if rama not in repo['ramas']:
            return 'ERROR RAMA_NO_EXISTE'
        actual = repo['ramas'][rama]
        if base != actual:
            return f'ERROR CONFLICTO HEAD={actual}'
        # La espera amplifica deliberadamente la carrera cuando SIN_LOCK=1.
        # En el trabajo autónomo se configura PAUSA_CARRERA=0.
        if PAUSA_CARRERA > 0:
            time.sleep(PAUSA_CARRERA)
        nuevo = repo['siguiente']
        repo['siguiente'] = nuevo + 1
        repo['commits'][nuevo] = {'padre': base, 'mensaje': mensaje}
        repo['ramas'][rama] = nuevo
    return f'OK PUSH {rama} HEAD={nuevo}'


def op_espera(arg):
    try:
        segundos = float(arg)
        if not (0 <= segundos <= 10):
            raise ValueError
    except ValueError:
        return 'ERROR FORMATO ESPERA <segundos>'
    time.sleep(segundos)  # nunca dentro del Lock
    return f'OK ESPERA {arg}'


OPERACIONES = {
    'REPOS': op_repos,
    'CLONAR': op_clonar,
    'HISTORIAL': op_historial,
    'RAMA': op_rama,
    'PUSH': op_push,
    'ESPERA': op_espera,
}


def procesar(linea):
    partes = linea.strip().split(' ', 1)
    cmd = partes[0].upper() if partes and partes[0] else ''
    arg = partes[1] if len(partes) > 1 else ''
    if cmd == 'HOLA':
        return f'OK HOLA {arg or "anonimo"}', True
    if cmd == 'SALIR':
        return 'OK CHAO', False
    if cmd in OPERACIONES:
        with seccion_critica():
            estado['operaciones'] += 1
        return OPERACIONES[cmd](arg), True
    return 'ERROR COMANDO_DESCONOCIDO', True


def atender(conn, addr):
    logging.info('conexion de %s', addr)
    conn.settimeout(TIMEOUT_CLIENTE)
    try:
        with conn, conn.makefile('r', encoding='utf-8', errors='replace') as entrada:
            for linea in entrada:
                respuesta, seguir = procesar(linea)
                conn.sendall((respuesta + '\n').encode('utf-8'))
                if not seguir:
                    break
    except (ConnectionResetError, BrokenPipeError) as exc:
        logging.warning('cliente %s se desconecto abruptamente (%s)',
                        addr, exc.__class__.__name__)
    except socket.timeout:
        logging.warning('cliente %s inactivo %ss, cerrando', addr, TIMEOUT_CLIENTE)
    except Exception as exc:
        logging.exception('error con %s: %r', addr, exc)
    finally:
        logging.info('cierre de %s | operaciones=%s', addr, estado['operaciones'])


def main():
    logging.info('RepoSync SIN_LOCK=%s PAUSA_CARRERA=%s timeout=%ss',
                 SIN_LOCK, PAUSA_CARRERA, TIMEOUT_CLIENTE)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PUERTO))
        srv.listen(64)
        logging.info('escuchando en %s:%s', HOST, PUERTO)
        while True:
            conn, addr = srv.accept()
            threading.Thread(target=atender, args=(conn, addr),
                             name=f'cli-{addr[1]}', daemon=True).start()


if __name__ == '__main__':
    main()
