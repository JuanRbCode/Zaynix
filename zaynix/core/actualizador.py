from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import urllib.request
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from zaynix.core.config import CARPETA_DATOS, REPOSITORIO, SITIO_WEB, VERSION

REPO = "https://github.com/yt-dlp/yt-dlp/releases"
CARPETA_MOTOR = CARPETA_DATOS / "motor"
ARCHIVO_MOTOR = CARPETA_MOTOR / "yt-dlp.zip"
ARCHIVO_ESTADO = CARPETA_MOTOR / "estado.json"
AGENTE = {"User-Agent": "Zaynix-Updater"}
INTERVALO = timedelta(hours=12)


def _tupla(version: str) -> tuple[int, ...]:
    try:
        return tuple(int(p) for p in version.strip().lstrip("v").split("."))
    except ValueError:
        return (0,)


def _leer_estado() -> dict:
    try:
        return json.loads(ARCHIVO_ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _guardar_estado(**cambios) -> None:
    estado = _leer_estado() | cambios
    CARPETA_MOTOR.mkdir(parents=True, exist_ok=True)
    ARCHIVO_ESTADO.write_text(json.dumps(estado, indent=2), encoding="utf-8")


def version_incluida() -> str:
    try:
        return importlib.metadata.version("yt-dlp")
    except importlib.metadata.PackageNotFoundError:
        return "0"


def version_local() -> str | None:
    if not ARCHIVO_MOTOR.exists():
        return None
    return _leer_estado().get("version")


def activar_motor_local() -> None:
    local = version_local()
    if local and _tupla(local) > _tupla(version_incluida()) and zipfile.is_zipfile(ARCHIVO_MOTOR):
        sys.path.insert(0, str(ARCHIVO_MOTOR))


def version_activa() -> str:
    import yt_dlp
    return yt_dlp.version.__version__


def ultima_version() -> str:
    pedido = urllib.request.Request(f"{REPO}/latest", headers=AGENTE, method="HEAD")
    with urllib.request.urlopen(pedido, timeout=15) as r:
        return r.geturl().rstrip("/").rsplit("/", 1)[-1]


def _descargar(url: str, al_progreso: Callable[[float | None], None] | None = None) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=AGENTE), timeout=60) as r:
        total = int(r.headers.get("Content-Length") or 0)
        partes, hecho = [], 0
        while bloque := r.read(65536):
            partes.append(bloque)
            hecho += len(bloque)
            if al_progreso:
                al_progreso(hecho / total if total else None)
    return b"".join(partes)


def hay_actualizacion() -> str | None:
    ultima = ultima_version()
    _guardar_estado(revisado=datetime.now().isoformat(timespec="seconds"))
    actual = max(version_activa(), version_local() or "0", key=_tupla)
    return ultima if _tupla(ultima) > _tupla(actual) else None


def instalar(version: str, al_progreso: Callable[[float | None], None] | None = None) -> None:
    sumas = _descargar(f"{REPO}/download/{version}/SHA2-256SUMS").decode()
    esperado = next((l.split()[0] for l in sumas.splitlines() if l.strip().endswith(" yt-dlp")), None)
    if not esperado:
        raise RuntimeError("No se encontró la firma de la nueva versión.")
    datos = _descargar(f"{REPO}/download/{version}/yt-dlp", al_progreso)
    if hashlib.sha256(datos).hexdigest() != esperado:
        raise RuntimeError("La descarga está dañada (la firma no coincide). Inténtalo de nuevo.")
    CARPETA_MOTOR.mkdir(parents=True, exist_ok=True)
    temporal = ARCHIVO_MOTOR.with_suffix(".tmp")
    temporal.write_bytes(datos)
    with zipfile.ZipFile(temporal) as z:
        if "yt_dlp/__init__.py" not in z.namelist():
            temporal.unlink(missing_ok=True)
            raise RuntimeError("El archivo descargado no es válido.")
    os.replace(temporal, ARCHIVO_MOTOR)
    _guardar_estado(version=version)


def actualizar_motor_en_segundo_plano(forzar: bool = False) -> None:
    from zaynix.core.registro import log
    if not forzar and not toca_revisar():
        return
    try:
        nueva = hay_actualizacion()
        if nueva:
            instalar(nueva)
            log.info("Motor actualizado a %s", nueva)
    except Exception as ex:
        log.warning("No se pudo actualizar el motor: %s", ex)


def consultar_version_app() -> dict:
    pedido = urllib.request.Request(f"{SITIO_WEB}/version.json", headers=AGENTE)
    with urllib.request.urlopen(pedido, timeout=15) as r:
        datos = json.loads(r.read().decode("utf-8-sig"))
    if not isinstance(datos, dict) or "version" not in datos:
        raise ValueError("Respuesta de versión inválida")
    return datos


def hay_version_app() -> dict | None:
    datos = consultar_version_app()
    return datos if _tupla(str(datos["version"])) > _tupla(VERSION) else None


def enlace_descarga(datos: dict | None) -> str:
    return (datos or {}).get("descarga") or SITIO_WEB


ENLACES = {
    "novedades": f"https://github.com/{REPOSITORIO}/blob/main/CHANGELOG.md",
    "licencias": f"https://github.com/{REPOSITORIO}/blob/main/LICENCIAS.md",
    "problema": f"https://github.com/{REPOSITORIO}/issues/new",
    "sitio": SITIO_WEB,
}


def toca_revisar() -> bool:
    revisado = _leer_estado().get("revisado")
    try:
        return datetime.now() - datetime.fromisoformat(revisado) > INTERVALO
    except (TypeError, ValueError):
        return True


def reiniciar_app() -> None:
    if getattr(sys, "frozen", False):
        comando = [sys.executable, *sys.argv[1:]]
    else:
        comando = [sys.executable, os.path.abspath(sys.argv[0]), *sys.argv[1:]]
    subprocess.Popen(comando, cwd=os.getcwd(), close_fds=True)
