from __future__ import annotations

import re
import subprocess
from collections import deque
from pathlib import Path
from typing import Callable

from zaynix.core.archivos import preparar_carpeta
from zaynix.core.errores import Cancelado, ErrorClaro
from zaynix.core.ffmpeg import ffmpeg_exe


FORMATOS: dict[str, list[str]] = {
    "mp3": ["-c:a", "libmp3lame", "-b:a", "320k"],
    "wav": ["-c:a", "pcm_s16le"],
    "flac": ["-c:a", "flac", "-compression_level", "5"],
    "m4a": ["-c:a", "aac", "-b:a", "256k"],
    "ogg": ["-c:a", "libvorbis", "-q:a", "6"],
    "opus": ["-c:a", "libopus", "-b:a", "192k"],
    "mp4": ["-map", "0:v:0?", "-map", "0:a:0?", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"],
}
FORMATOS_VIDEO = {"mp4"}

EXTENSIONES_AUDIO = ["mp3", "wav", "flac", "m4a", "aac", "ogg", "opus", "wma", "aiff", "aif", "alac"]
EXTENSIONES_VIDEO = ["mp4", "mkv", "webm", "mov", "avi", "flv", "wmv", "m4v", "3gp", "ts"]
EXTENSIONES_ENTRADA = EXTENSIONES_AUDIO + EXTENSIONES_VIDEO

_PROGRESO = re.compile(r"^(frame|fps|stream_|bitrate|total_size|out_time|dup_frames|drop_frames|speed|progress)\w*=")
_SIN_VENTANA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _duracion(archivo: Path) -> float | None:
    r = subprocess.run([str(ffmpeg_exe()), "-hide_banner", "-i", str(archivo)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       creationflags=_SIN_VENTANA)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", r.stderr)
    if not m:
        return None
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def _ruta_salida(entrada: Path, formato: str, carpeta: Path) -> Path:
    salida = carpeta / f"{entrada.stem}.{formato}"
    n = 1
    while salida.exists() or salida.resolve() == entrada.resolve():
        salida = carpeta / f"{entrada.stem} ({n}).{formato}"
        n += 1
    return salida


def convertir_archivo(
    entrada: Path,
    formato: str,
    carpeta: Path | None = None,
    al_progreso: Callable[[float | None], None] | None = None,
    cancelar: Callable[[], bool] | None = None,
) -> Path:
    if formato not in FORMATOS:
        raise ValueError(f"Formato no soportado: {formato}")
    if not entrada.is_file():
        raise ErrorClaro("El archivo original ya no está en su carpeta.")
    carpeta = carpeta or entrada.parent
    preparar_carpeta(carpeta)
    salida = _ruta_salida(entrada, formato, carpeta)
    total = _duracion(entrada)

    cmd = [str(ffmpeg_exe()), "-hide_banner", "-loglevel", "error", "-y", "-i", str(entrada),
           *([] if formato in FORMATOS_VIDEO else ["-vn"]), "-map_metadata", "0", *FORMATOS[formato], "-progress", "pipe:1", "-nostats", str(salida)]
    proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", creationflags=_SIN_VENTANA)
    errores: deque[str] = deque(maxlen=20)
    try:
        for linea in proc.stdout:
            if linea.strip() and not _PROGRESO.match(linea):
                errores.append(linea.strip())
            if cancelar and cancelar():
                proc.kill()
                raise Cancelado()
            if linea.startswith("out_time_us=") and total and al_progreso:
                try:
                    al_progreso(min(int(linea.split("=")[1]) / 1e6 / total, 1.0))
                except ValueError:
                    pass
        proc.wait()
    except Cancelado:
        proc.wait()
        salida.unlink(missing_ok=True)
        raise
    if proc.returncode != 0:
        salida.unlink(missing_ok=True)
        raise RuntimeError(errores[-1] if errores else "ffmpeg falló al convertir el archivo")
    return salida
