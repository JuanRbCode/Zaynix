from __future__ import annotations

import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import yt_dlp
import yt_dlp.postprocessor.ffmpeg as _pp_ffmpeg
from yt_dlp.utils import DownloadCancelled

from zaynix.core.archivos import mover_sin_reemplazar, preparar_carpeta
from zaynix.core.errores import Cancelado, ErrorClaro, traducir_error
from zaynix.core.ffmpeg import carpeta_ffmpeg

FORMATOS_AUDIO = ["mp3", "m4a", "wav", "flac", "ogg", "opus"]
FORMATOS_VIDEO = ["mp4"]
SIN_PERDIDA = {"wav", "flac"}
CON_PORTADA = {"mp3", "m4a", "mp4", "flac", "ogg", "opus"}
KBPS = {
    "mp3": ["320", "256", "192", "128"],
    "m4a": ["256", "192", "128"],
    "ogg": ["256", "192", "128"],
    "opus": ["192", "160", "128"],
}
RESOLUCIONES = [2160, 1440, 1080, 720, 480, 360]
_CODEC_YTDLP = {"ogg": "vorbis"}
_hilo = threading.local()


class _Corte(DownloadCancelled):
    pass


class _PopenCancelable(_pp_ffmpeg.Popen):
    def communicate_or_kill(self, *args, **kwargs):
        cancelar = getattr(_hilo, "cancelar", None)
        if cancelar is None or "timeout" in kwargs and kwargs["timeout"] is not None:
            return super().communicate_or_kill(*args, **kwargs)
        kwargs.pop("timeout", None)
        while True:
            try:
                return self.communicate(*args, timeout=0.25, **kwargs)
            except subprocess.TimeoutExpired:
                if cancelar():
                    self.kill(timeout=None)
                    raise _Corte()


_pp_ffmpeg.Popen = _PopenCancelable


class _Avisos:
    def __init__(self):
        self.errores: list[str] = []

    def debug(self, mensaje: str) -> None:
        pass

    def info(self, mensaje: str) -> None:
        pass

    def warning(self, mensaje: str) -> None:
        pass

    def error(self, mensaje: str) -> None:
        self.errores.append(mensaje)


@dataclass
class Resultado:
    titulo: str
    archivo: Path


@dataclass
class Info:
    titulo: str
    autor: str
    duracion: int | None
    miniatura: str | None
    alturas: list[int] = field(default_factory=list)
    es_playlist: bool = False
    entradas: int = 0


def _js_runtimes() -> dict:
    try:
        import deno
        candidatos = [Path(deno.__file__).resolve().parent.parent / "bin" / "deno.exe"]
        try:
            candidatos.insert(0, Path(deno.find_deno_bin()))
        except Exception:
            pass
        for ruta in candidatos:
            if ruta.exists():
                return {"deno": {"path": str(ruta)}}
    except Exception:
        pass
    return {"deno": {}}


def _base() -> dict:
    return {"quiet": True, "no_warnings": True, "noprogress": True, "js_runtimes": _js_runtimes()}


def analizar(url: str, playlist: bool = False) -> Info:
    opciones = {**_base(), "noplaylist": not playlist, "extract_flat": "in_playlist", "skip_download": True}
    with yt_dlp.YoutubeDL(opciones) as ydl:
        i = ydl.extract_info(url, download=False)
    if i.get("_type") == "playlist":
        entradas = list(i.get("entries") or [])
        miniaturas = i.get("thumbnails") or []
        return Info(i.get("title") or "Playlist", i.get("uploader") or i.get("channel") or "",
                    None, miniaturas[-1]["url"] if miniaturas else None, [], True, len(entradas))
    alturas = sorted({f["height"] for f in i.get("formats") or []
                      if f.get("height") and f.get("vcodec") not in (None, "none")}, reverse=True)
    return Info(i.get("title") or "Sin título", i.get("uploader") or i.get("channel") or "",
                int(i["duration"]) if i.get("duration") else None, i.get("thumbnail"), alturas)


def opciones_resolucion(alturas: list[int]) -> list[int]:
    if not alturas:
        return []
    maxima = alturas[0]
    return [r for r in RESOLUCIONES if r <= maxima and any(r * 0.85 <= a <= r * 1.15 for a in alturas)]


def descargar(
    url: str,
    carpeta: Path,
    formato: str = "mp3",
    calidad: str | None = None,
    playlist: bool = False,
    al_progreso: Callable[[float | None, str], None] | None = None,
    cancelar: Callable[[], bool] | None = None,
    portada: bool = True,
    al_terminar: Callable[[Resultado], None] | None = None,
    al_fallar: Callable[[str], None] | None = None,
) -> list[Resultado]:
    preparar_carpeta(carpeta)
    try:
        temporal = Path(tempfile.mkdtemp(prefix=".zaynix-", dir=carpeta))
    except OSError as ex:
        raise ErrorClaro("No se puede escribir en la carpeta de destino. Elige otra en Ajustes.") from ex
    avisos = _Avisos()
    resultados: list[Resultado] = []
    avisar = al_progreso or (lambda f, t: None)
    es_video = formato in FORMATOS_VIDEO
    incrustar = portada and formato in CON_PORTADA

    def hook_descarga(d: dict) -> None:
        if cancelar and cancelar():
            raise _Corte()
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            hecho = d.get("downloaded_bytes", 0)
            info = d.get("info_dict") or {}
            parte = ""
            if es_video and info.get("vcodec") not in (None, "none") and info.get("acodec") in (None, "none"):
                parte = " (video)"
            elif es_video and info.get("vcodec") in (None, "none"):
                parte = " (audio)"
            nombre = (info.get("title") or Path(d.get("filename", "")).stem)[:70]
            avisar(hecho / total if total else None, f"Descargando{parte} · {nombre}")
        elif d["status"] == "finished":
            avisar(None, "Uniendo video y audio…" if es_video else f"Convirtiendo a {formato.upper()}…")

    def hook_post(d: dict) -> None:
        if d["status"] == "started" and cancelar and cancelar():
            raise _Corte()
        if d["status"] == "finished" and d.get("postprocessor") == "MoveFiles":
            info = d["info_dict"]
            origen = Path(info.get("filepath") or info.get("_filename", ""))
            archivo = mover_sin_reemplazar(origen, carpeta)
            resultado = Resultado(info.get("title", archivo.stem), archivo)
            resultados.append(resultado)
            if al_terminar:
                al_terminar(resultado)

    post: list[dict] = []
    opciones = {
        **_base(),
        "outtmpl": str(temporal / "%(autonumber)s-%(id).40B" / "%(title).150B.%(ext)s"),
        "windowsfilenames": True,
        "noplaylist": not playlist,
        "ignoreerrors": playlist,
        "logger": avisos,
        "ffmpeg_location": str(carpeta_ffmpeg()),
        "writethumbnail": incrustar,
        "concurrent_fragment_downloads": 4,
        "progress_hooks": [hook_descarga],
        "postprocessor_hooks": [hook_post],
    }

    if es_video:
        altura = int(calidad) if calidad and calidad.isdigit() else None
        opciones["format"] = "bv*+ba/b"
        opciones["format_sort"] = [f"res:{altura}" if altura else "res", "vcodec:h264", "acodec:aac", "ext:mp4:m4a"]
        opciones["merge_output_format"] = "mp4"
    else:
        opciones["format"] = "bestaudio/best"
        extraer = {"key": "FFmpegExtractAudio", "preferredcodec": _CODEC_YTDLP.get(formato, formato)}
        if formato not in SIN_PERDIDA and calidad:
            extraer["preferredquality"] = calidad
        post.append(extraer)

    if formato != "wav":
        post.append({"key": "FFmpegMetadata", "add_metadata": True})
    if incrustar:
        post.append({"key": "EmbedThumbnail"})
    opciones["postprocessors"] = post

    _hilo.cancelar = cancelar
    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download([url])
    except DownloadCancelled as ex:
        raise Cancelado() from ex
    finally:
        _hilo.cancelar = None
        shutil.rmtree(temporal, ignore_errors=True)
    if not resultados:
        detalle = avisos.errores[0] if avisos.errores else "No se encontró nada para descargar."
        raise ErrorClaro(traducir_error(Exception(detalle)))
    if al_fallar:
        for mensaje in avisos.errores:
            al_fallar(mensaje)
    return resultados
