import pytest

from zaynix.core.conversor import FORMATOS, _duracion, convertir_archivo
from zaynix.core.errores import Cancelado


@pytest.mark.parametrize("formato", sorted(FORMATOS))
def test_convierte_audio_a_cada_formato(tono_wav, tmp_path, formato):
    progreso = []
    salida = convertir_archivo(tono_wav, formato, tmp_path / "salida", progreso.append)
    assert salida.exists() and salida.suffix == f".{formato}"
    assert salida.stat().st_size > 0
    assert abs((_duracion(salida) or 0) - 2) < 0.3
    if progreso:
        assert progreso[-1] == pytest.approx(1.0, abs=0.05)


def test_video_a_mp4_y_mp3(video_corto, tmp_path):
    mp4 = convertir_archivo(video_corto, "mp4", tmp_path / "salida")
    mp3 = convertir_archivo(video_corto, "mp3", tmp_path / "salida")
    assert mp4.exists() and mp3.exists()


def test_no_sobrescribe_archivos(tono_wav):
    primero = convertir_archivo(tono_wav, "mp3")
    segundo = convertir_archivo(tono_wav, "mp3")
    assert primero != segundo and primero.exists() and segundo.exists()


def test_misma_extension_no_pisa_el_original(tono_wav):
    salida = convertir_archivo(tono_wav, "wav")
    assert salida != tono_wav and tono_wav.exists()


def test_cancelar_borra_el_archivo_a_medias(tono_wav, tmp_path):
    with pytest.raises(Cancelado):
        convertir_archivo(tono_wav, "flac", tmp_path / "salida", cancelar=lambda: True)
    assert not list((tmp_path / "salida").glob("*.flac"))


def test_formato_invalido(tono_wav):
    with pytest.raises(ValueError):
        convertir_archivo(tono_wav, "xyz")


def test_archivo_danado(tmp_path):
    roto = tmp_path / "roto.mp3"
    roto.write_bytes(b"esto no es audio")
    with pytest.raises(RuntimeError):
        convertir_archivo(roto, "wav")
