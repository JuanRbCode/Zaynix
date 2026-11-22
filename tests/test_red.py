import pytest

from zaynix.core import actualizador
from zaynix.core.descargador import analizar, descargar
from zaynix.core.ffmpeg import ffmpeg_exe

pytestmark = pytest.mark.red

VIDEO = "https://www.youtube.com/watch?v=jNQXAC9IVRw"


def test_ultima_version_motor():
    version = actualizador.ultima_version()
    assert actualizador._tupla(version) >= (2025,)


def test_analizar_video():
    info = analizar(VIDEO)
    assert info.titulo == "Me at the zoo"
    assert info.duracion and info.alturas


def test_enlace_inexistente_falla():
    with pytest.raises(Exception):
        analizar("https://www.youtube.com/watch?v=xxxxxxxxxxx")


@pytest.mark.parametrize("formato,calidad", [("mp3", "128"), ("m4a", "128"), ("mp4", None)])
def test_descargar(tmp_path, formato, calidad):
    resultados = descargar(VIDEO, tmp_path, formato, calidad)
    assert len(resultados) == 1
    archivo = resultados[0].archivo
    assert archivo.exists() and archivo.suffix == f".{formato}"
    assert ffmpeg_exe().exists()
