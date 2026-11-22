import importlib.metadata as metadatos
import re
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

RAIZ = Path(__file__).resolve().parent.parent
PAQUETES = RAIZ / "build" / "windows" / "site-packages"
DESTINO = RAIZ / "build" / "licencias"
PROPIOS = ["LICENSE", "MARCA.md", "LICENCIAS.md", "TERMINOS.md"]
ES_LICENCIA = re.compile(r"(licen[cs]e|copying|notice|authors)", re.IGNORECASE)


def paquetes_incluidos() -> list[str]:
    nombres = set()
    for carpeta in PAQUETES.glob("*.dist-info"):
        nombres.add(carpeta.name.removesuffix(".dist-info").rsplit("-", 1)[0])
    return sorted(nombres)


def textos_de(nombre: str) -> tuple[str, list[tuple[str, str]]]:
    dist = metadatos.distribution(nombre)
    datos = dist.metadata
    licencia = datos.get("License-Expression") or (datos.get("License") or "").splitlines()[:1] or "ver texto"
    if isinstance(licencia, list):
        licencia = licencia[0]
    textos = []
    for archivo in dist.files or []:
        if ".dist-info" not in str(archivo) or not ES_LICENCIA.search(archivo.name):
            continue
        ruta = Path(dist.locate_file(archivo))
        if ruta.is_file():
            textos.append((archivo.name, ruta.read_text(encoding="utf-8", errors="replace")))
    return f"{datos['Name']} {datos['Version']}\nLicencia: {licencia}\n", textos


def main() -> int:
    nombres = paquetes_incluidos()
    if not nombres:
        print("No hay paquetes en build/windows. Compila primero.")
        return 1
    shutil.rmtree(DESTINO, ignore_errors=True)
    DESTINO.mkdir(parents=True)

    sin_texto, ausentes = [], []
    for nombre in nombres:
        try:
            cabecera, textos = textos_de(nombre)
        except metadatos.PackageNotFoundError:
            ausentes.append(nombre)
            continue
        if not textos:
            sin_texto.append(nombre)
        cuerpo = "".join(f"\n===== {titulo} =====\n\n{texto}\n" for titulo, texto in textos)
        (DESTINO / f"{nombre}.txt").write_text(cabecera + cuerpo, encoding="utf-8")

    for archivo in PROPIOS:
        shutil.copy2(RAIZ / archivo, DESTINO / archivo)
    python = Path(sys.base_prefix) / "LICENSE.txt"
    if python.exists():
        shutil.copy2(python, DESTINO / "python.txt")
    version = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-version"],
                             capture_output=True, text=True, check=True).stdout
    (DESTINO / "ffmpeg-version.txt").write_text(version, encoding="utf-8")

    print(f"Licencias de {len(nombres) - len(ausentes)} paquetes en {DESTINO}")
    if sin_texto:
        print("Sin texto propio (solo se indica la licencia):", ", ".join(sin_texto))
    if ausentes:
        print("ERROR, no encontrados:", ", ".join(ausentes))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
