from __future__ import annotations

import shutil
from pathlib import Path

import imageio_ffmpeg

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "bin"


def ffmpeg_exe() -> Path:
    destino = BIN / "ffmpeg.exe"
    if not destino.exists():
        BIN.mkdir(parents=True, exist_ok=True)
        shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(), destino)
    return destino


def carpeta_ffmpeg() -> Path:
    return ffmpeg_exe().parent
