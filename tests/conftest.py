import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


@pytest.fixture(autouse=True)
def datos_aislados(tmp_path, monkeypatch):
    from zaynix.core import config, historial
    monkeypatch.setattr(config, "ARCHIVO", tmp_path / "config.json")
    monkeypatch.setattr(historial, "ARCHIVO", tmp_path / "historial.json")
    return tmp_path


@pytest.fixture
def tono_wav(tmp_path) -> Path:
    from zaynix.core.ffmpeg import ffmpeg_exe
    salida = tmp_path / "tono.wav"
    subprocess.run([str(ffmpeg_exe()), "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                    "-i", "sine=frequency=440:duration=2", str(salida)], check=True)
    return salida


@pytest.fixture
def video_corto(tmp_path) -> Path:
    from zaynix.core.ffmpeg import ffmpeg_exe
    salida = tmp_path / "clip.mkv"
    subprocess.run([str(ffmpeg_exe()), "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "testsrc=duration=2:size=320x240:rate=24",
                    "-f", "lavfi", "-i", "sine=duration=2", "-shortest", str(salida)], check=True)
    return salida
