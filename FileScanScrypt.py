#!/usr/bin/env python3
"""
FileScanCrypt v1.0
==================

Descripción:
    Este script recorre recursivamente un directorio y sus subdirectorios, 
    contabilizando el total de archivos, carpetas y acumulando el tamaño total (en MB) 
    de todos los archivos encontrados. Además, estima el tiempo necesario para cifrar 
    el volumen total de datos basado en una velocidad de cifrado en MB/s, que puede 
    ser especificada mediante un argumento (por defecto 50 MB/s).

Uso:
    python filescancrypt.py <ruta_del_directorio> [-v VELOCIDAD_EN_MB/s]

Ejemplo:
    python filescancrypt.py /home/usuario/Documents -v 60

Nota:
    Para obtener una estimación precisa, se recomienda ingresar la velocidad real de 
    cifrado de su PC usando el argumento -v.
"""

import os
import sys
import time
import threading
import argparse
import colorama
from colorama import Fore, Style
from tqdm import tqdm

# Inicializar colorama para manejo de colores en consola
colorama.init(autoreset=True)

# Variables globales para el escaneo
total_files = 0          # Número total de archivos encontrados
total_dirs = 0           # Suma de todos los subdirectorios encontrados
total_size_MB = 0.0      # Tamaño acumulado de archivos en MB
scanned_dirs = 0         # Contador de directorios visitados (para la barra de progreso)
scan_complete = False    # Bandera para indicar que el escaneo ha finalizado

def scan_directory(root_path):
    """
    Recorre de forma recursiva el directorio indicado, contabilizando archivos, carpetas
    y acumulando el tamaño total de archivos en MB.
    """
    global total_files, total_dirs, total_size_MB, scanned_dirs, scan_complete
    try:
        for root, dirs, files in os.walk(root_path):
            scanned_dirs += 1
            total_dirs += len(dirs)
            total_files += len(files)
            for file_name in files:
                file_path = os.path.join(root, file_name)
                try:
                    total_size_MB += os.path.getsize(file_path) / (1024 * 1024)
                except Exception:
                    continue
        scan_complete = True
    except Exception as e:
        print(f"{Fore.RED}Error durante el escaneo: {e}")
        scan_complete = True

def progress_bar(total_dir_count):
    """
    Muestra y actualiza en tiempo real la barra de progreso del escaneo.
    La barra se actualiza con la cantidad de directorios visitados, archivos contados y
    tamaño acumulado hasta el momento.
    """
    global total_files, total_size_MB, scanned_dirs, scan_complete
    with tqdm(total=total_dir_count, desc=f"{Fore.CYAN}Escaneando directorios", unit="dir",
              bar_format="{l_bar}{bar} {n_fmt}/{total_fmt} | {postfix}") as pbar:
        last_scanned = 0
        while not scan_complete:
            delta = scanned_dirs - last_scanned
            if delta > 0:
                pbar.update(delta)
                last_scanned = scanned_dirs
            pbar.set_postfix_str(f"Archivos: {total_files} | Tamaño: {total_size_MB:.2f} MB")
            time.sleep(0.1)
        # Actualizar el progreso final en caso de haber quedado pendiente
        if scanned_dirs - last_scanned > 0:
            pbar.update(scanned_dirs - last_scanned)
        pbar.set_postfix_str(f"Archivos: {total_files} | Tamaño: {total_size_MB:.2f} MB")
        pbar.close()

def main():
    parser = argparse.ArgumentParser(
        description="FileScanCrypt: Escaneo de directorios y estimación de tiempo de cifrado",
        epilog="Ejemplo: python filescancrypt.py /ruta/del/directorio -v 60\n"
               "Nota: Ingrese la velocidad real de cifrado de su PC para obtener una estimación precisa."
    )
    parser.add_argument("path", help="Ruta del directorio a escanear")
    parser.add_argument("-v", "--speed", type=float, default=50.0,
                        help="Velocidad de cifrado en MB/s (default: 50).")
    args = parser.parse_args()

    root_path = args.path
    encryption_speed = args.speed

    if not os.path.exists(root_path):
        print(f"{Fore.RED}Error: La ruta '{root_path}' no existe.")
        sys.exit(1)

    # Banner de bienvenida
    print(f"\n{Fore.CYAN}{'*'*50}")
    print(f"{Fore.CYAN}{'FileScanCrypt v1.0'.center(50)}")
    print(f"{Fore.CYAN}{'*'*50}\n")
    print(f"{Fore.YELLOW}Iniciando escaneo en: {Fore.WHITE}{root_path}")
    print(f"{Fore.YELLOW}Velocidad de cifrado (MB/s): {Fore.WHITE}{encryption_speed}  "
          f"{Fore.YELLOW}(Para mayor precisión, especifique la velocidad real con -v)\n")

    start_time = time.time()

    # Precalcular el total de directorios para establecer el límite de la barra de progreso
    try:
        total_dir_list = [d for d, _, _ in os.walk(root_path)]
    except Exception as e:
        print(f"{Fore.RED}Error al calcular el total de directorios: {e}")
        sys.exit(1)
    total_dir_count = len(total_dir_list)

    # Iniciar el escaneo en un hilo separado
    scan_thread = threading.Thread(target=scan_directory, args=(root_path,))
    scan_thread.start()

    # Mostrar la barra de progreso en el hilo principal
    progress_bar(total_dir_count)
    scan_thread.join()

    end_time = time.time()
    elapsed_time = end_time - start_time

    # Calcular tiempo estimado de cifrado
    encryption_time_sec = total_size_MB / encryption_speed if total_size_MB > 0 else 0
    encryption_time_min = encryption_time_sec / 60

    # Mostrar resultados finales con formato y colores
    print(f"\n{Fore.MAGENTA}{'='*50}")
    print(f"{Fore.GREEN}Resultados del escaneo:")
    print(f"{Fore.BLUE}Total de archivos encontrados: {Fore.WHITE}{total_files}")
    print(f"{Fore.BLUE}Total de carpetas encontradas: {Fore.WHITE}{total_dirs}")
    print(f"{Fore.BLUE}Tamaño total de archivos: {Fore.WHITE}{total_size_MB:.2f} MB")
    print(f"{Fore.BLUE}Tiempo total de escaneo: {Fore.WHITE}{elapsed_time:.2f} segundos")
    print(f"{Fore.RED}{'-'*50}")
    if total_size_MB > 0:
        print(f"{Fore.RED}Tiempo estimado para cifrar todos los archivos:")
        print(f"{Fore.WHITE}- Aproximadamente {encryption_time_sec:.2f} segundos "
              f"({encryption_time_min:.2f} minutos)")
    else:
        print(f"{Fore.RED}No se encontraron archivos para cifrar.")
    print(f"{Fore.MAGENTA}{'='*50}\n")

if __name__ == "__main__":
    main()
