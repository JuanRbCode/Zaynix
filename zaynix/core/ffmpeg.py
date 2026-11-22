from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import imageio_ffmpeg


@lru_cache(maxsize=1)
def ffmpeg_exe() -> Path:
    return Path(imageio_ffmpeg.get_ffmpeg_exe())


def carpeta_ffmpeg() -> Path:
    return ffmpeg_exe()
