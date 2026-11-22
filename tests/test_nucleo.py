from pathlib import Path

import pytest

from zaynix.controladores.sistema import tamano_legible, validar_enlace
from zaynix.core import actualizador
from zaynix.core.config import Config
from zaynix.core.descargador import opciones_resolucion
from zaynix.core.errores import traducir_error
from zaynix.core.historial import Historial, fecha_corta


@pytest.mark.parametrize("texto,valido", [
    ("https://www.youtube.com/watch?v=abc", True),
    ("http://soundcloud.com/x/y", True),
    ("", False),
    ("hola", False),
    ("ftp://algo.com/archivo", False),
    ("https://localhost", False),
])
def test_validar_enlace(texto, valido):
    assert (validar_enlace(texto) is None) == valido


def test_tamano_legible():
    assert tamano_legible(500 * 1024) == "500 KB"
    assert tamano_legible(3 * 1_048_576) == "3.0 MB"


@pytest.mark.parametrize("mensaje,esperado", [
    ("ERROR: <urlopen error [Errno 11001] getaddrinfo failed>", "Sin conexión"),
    ("ERROR: Unsupported URL: https://x.com", "no es compatible"),
    ("ERROR: [youtube] abc: Private video", "privado"),
    ("ERROR: [youtube] Unable to extract nsig function", "Cierra Zaynix"),
    ("HTTP Error 403: Forbidden", "rechazó"),
    ("[Errno 28] No space left on device", "espacio"),
])
def test_traducir_error(mensaje, esperado):
    assert esperado in traducir_error(Exception(mensaje))


def test_config_guarda_y_carga():
    cfg = Config.cargar()
    cfg.tema = "claro"
    cfg.calidad_mp3 = "192"
    cfg.guardar()
    otra = Config.cargar()
    assert otra.tema == "claro" and otra.calidad_mp3 == "192"


def test_config_ignora_claves_desconocidas(datos_aislados):
    (datos_aislados / "config.json").write_text('{"tema": "claro", "clave_vieja": 1}', encoding="utf-8")
    assert Config.cargar().tema == "claro"


def test_config_corrupta_usa_valores_por_defecto(datos_aislados):
    (datos_aislados / "config.json").write_text("{no es json", encoding="utf-8")
    assert Config.cargar().tema == "oscuro"


def test_historial(datos_aislados):
    archivo = datos_aislados / "cancion.mp3"
    archivo.write_bytes(b"x")
    h = Historial()
    h.agregar("descarga", "Canción", archivo, "MP3")
    h.agregar("conversion", "Otra", archivo, "WAV")
    assert len(Historial().de_tipo("descarga")) == 1
    h.limpiar("descarga")
    assert Historial().de_tipo("descarga") == []
    assert len(Historial().de_tipo("conversion")) == 1


def test_historial_omite_archivos_borrados(datos_aislados):
    h = Historial()
    h.agregar("descarga", "Fantasma", datos_aislados / "no_existe.mp3", "MP3")
    assert h.de_tipo("descarga") == []


def test_fecha_corta():
    assert fecha_corta("2020-01-02T10:00:00") == "02/01/2020"
    assert fecha_corta("basura") == ""


def test_opciones_resolucion():
    assert opciones_resolucion([2160, 1440, 1080, 720, 480, 360, 240]) == [2160, 1440, 1080, 720, 480, 360]
    assert opciones_resolucion([1080, 720]) == [1080, 720]
    assert opciones_resolucion([240, 144]) == []
    assert opciones_resolucion([]) == []


def test_comparar_versiones():
    assert actualizador._tupla("2026.10.26") > actualizador._tupla("2026.9.30")
    assert actualizador._tupla("2026.10.26.1") > actualizador._tupla("2026.10.26")
    assert actualizador._tupla("v1.2.0") == (1, 2, 0)
    assert actualizador._tupla("raro") == (0,)


def test_motor_local_no_se_activa_si_es_viejo(monkeypatch, tmp_path):
    monkeypatch.setattr(actualizador, "version_local", lambda: "2000.1.1")
    antes = list(__import__("sys").path)
    actualizador.activar_motor_local()
    assert __import__("sys").path == antes


def test_detecta_version_nueva_de_la_app(monkeypatch):
    monkeypatch.setattr(actualizador, "consultar_version_app", lambda: {"version": "99.0.0", "descarga": "x"})
    assert actualizador.hay_version_app()["version"] == "99.0.0"
    monkeypatch.setattr(actualizador, "consultar_version_app", lambda: {"version": "0.0.1"})
    assert actualizador.hay_version_app() is None


def test_enlace_descarga_por_defecto():
    assert actualizador.enlace_descarga(None) == actualizador.SITIO_WEB
    assert actualizador.enlace_descarga({"descarga": "https://a/b.exe"}) == "https://a/b.exe"
