from __future__ import annotations

from pathlib import Path

from zaynix.core.errores import ErrorClaro


def preparar_carpeta(carpeta: Path) -> None:
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
    except PermissionError as ex:
        raise ErrorClaro("Sin permiso para escribir en la carpeta de destino. Elige otra en Ajustes.") from ex
    except OSError as ex:
        raise ErrorClaro("La carpeta de destino no está disponible. Elige otra en Ajustes.") from ex


def mover_sin_reemplazar(origen: Path, carpeta: Path) -> Path:
    n = 0
    while True:
        destino = carpeta / (f"{origen.stem} ({n}){origen.suffix}" if n else origen.name)
        if not destino.exists():
            try:
                origen.rename(destino)
                return destino
            except FileExistsError:
                pass
        n += 1
