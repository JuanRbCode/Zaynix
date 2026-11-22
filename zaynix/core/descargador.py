from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import yt_dlp

from zaynix.core.errores import Cancelado
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
        from deno import find_deno_bin
        return {"deno": {"path": find_deno_bin()}}
    except Exception:
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
) -> list[Resultado]:
    carpeta.mkdir(parents=True, exist_ok=True)
    resultados: list[Resultado] = []
    avisar = al_progreso or (lambda f, t: None)
    es_video = formato in FORMATOS_VIDEO
    incrustar = portada and formato in CON_PORTADA

    def hook_descarga(d: dict) -> None:
        if cancelar and cancelar():
            raise Cancelado()
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
        if d["status"] == "finished" and d.get("postprocessor") == "MoveFiles":
            info = d["info_dict"]
            archivo = Path(info.get("filepath") or info.get("_filename", ""))
            resultados.append(Resultado(info.get("title", archivo.stem), archivo))

    post: list[dict] = []
    opciones = {
        **_base(),
        "outtmpl": str(carpeta / "%(title)s.%(ext)s"),
        "windowsfilenames": True,
        "noplaylist": not playlist,
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

    with yt_dlp.YoutubeDL(opciones) as ydl:
        ydl.download([url])
    return resultados
