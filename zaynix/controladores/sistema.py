from __future__ import annotations

import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse


def abrir(ruta: Path) -> None:
    if ruta.exists():
        os.startfile(ruta)


def mostrar_en_carpeta(ruta: Path) -> None:
    if ruta.exists():
        subprocess.Popen(["explorer", "/select,", str(ruta)])
    elif ruta.parent.exists():
        os.startfile(ruta.parent)


def abrir_web(url: str) -> None:
    import webbrowser
    webbrowser.open(url)


def validar_enlace(texto: str) -> str | None:
    if not texto:
        return "Pega un enlace para continuar."
    p = urlparse(texto)
    if p.scheme not in ("http", "https") or "." not in p.netloc:
        return "Ese enlace no es válido. Debe empezar con https://"
    return None


def tamano_legible(bytes_: int) -> str:
    mb = bytes_ / 1_048_576
    return f"{mb:.1f} MB" if mb >= 1 else f"{bytes_ / 1024:.0f} KB"
