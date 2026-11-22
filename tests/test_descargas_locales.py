import functools
import http.server
import subprocess
import threading
import time

import pytest

from zaynix.core.conversor import convertir_archivo
from zaynix.core.descargador import descargar
from zaynix.core.errores import Cancelado, ErrorClaro, traducir_error
from zaynix.core.ffmpeg import ffmpeg_exe
from zaynix.ui import tema
from zaynix.ui.vistas.descargar import VistaDescargar


def _audio(ruta, fuente, *extra):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(ffmpeg_exe()), "-loglevel", "error", "-y", "-f", "lavfi", "-i", fuente, *extra, str(ruta)],
                   check=True)


@pytest.fixture
def servidor(tmp_path):
    raiz = tmp_path / "web"
    _audio(raiz / "a" / "tema.wav", "sine=frequency=300:duration=1")
    _audio(raiz / "b" / "tema.wav", "sine=frequency=900:duration=3")

    class Manejador(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Manejador, directory=str(raiz)))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    s.raiz, s.url = raiz, f"http://127.0.0.1:{s.server_port}"
    yield s
    s.shutdown()
    s.server_close()


def _lista(servidor, *rutas):
    items = "".join(f"<item><title>{r}</title><link>{servidor.url}/{r}</link></item>" for r in rutas)
    (servidor.raiz / "lista.rss").write_text(
        f'<?xml version="1.0"?><rss version="2.0"><channel><title>L</title><link>x</link>{items}</channel></rss>',
        encoding="utf-8")
    return f"{servidor.url}/lista.rss"


def test_mismo_titulo_no_reemplaza(servidor, tmp_path):
    destino = tmp_path / "d"
    uno = descargar(f"{servidor.url}/a/tema.wav", destino, "mp3", "128", portada=False)[0].archivo
    antes = uno.read_bytes()
    dos = descargar(f"{servidor.url}/b/tema.wav", destino, "mp3", "128", portada=False)[0].archivo
    assert uno != dos and uno.read_bytes() == antes and dos.stat().st_size > uno.stat().st_size
    assert sorted(p.name for p in destino.iterdir()) == ["tema (1).mp3", "tema.mp3"]


def test_lista_sigue_si_falla_un_elemento(servidor, tmp_path):
    fallos, listos = [], []
    r = descargar(_lista(servidor, "a/tema.wav", "no-existe.wav", "b/tema.wav"), tmp_path / "d", "mp3", "128", True,
                  portada=False, al_terminar=listos.append, al_fallar=fallos.append)
    assert len(r) == 2 and len(listos) == 2 and len(fallos) == 1
    assert len({x.archivo for x in r}) == 2 and all(x.archivo.exists() for x in r)


def test_lista_sin_nada_descargable_da_error(servidor, tmp_path):
    with pytest.raises(ErrorClaro):
        descargar(_lista(servidor, "x.wav", "y.wav"), tmp_path / "d", "mp3", "128", True, portada=False)


@pytest.mark.parametrize("playlist", [False, True])
def test_cancelar_descarga_no_deja_restos(servidor, tmp_path, playlist):
    destino = tmp_path / "d"
    with pytest.raises(Cancelado):
        descargar(f"{servidor.url}/a/tema.wav", destino, "mp3", "128", playlist, cancelar=lambda: True)
    assert list(destino.iterdir()) == []


@pytest.mark.parametrize("playlist", [False, True])
def test_cancelar_durante_la_conversion(servidor, tmp_path, playlist):
    _audio(servidor.raiz / "largo.flac", "anullsrc=r=44100:cl=stereo", "-t", "14400")
    cancelado = threading.Event()
    inicio = []

    def progreso(fraccion, texto):
        if texto.startswith("Convirtiendo") and not inicio:
            inicio.append(time.monotonic())
            threading.Timer(0.8, cancelado.set).start()

    destino = tmp_path / "d"
    with pytest.raises(Cancelado):
        descargar(f"{servidor.url}/largo.flac", destino, "mp3", "320", playlist, progreso, cancelado.is_set,
                  portada=False)
    assert time.monotonic() - inicio[0] < 4
    assert list(destino.iterdir()) == []


def test_carpeta_no_disponible(tmp_path):
    estorbo = tmp_path / "archivo"
    estorbo.write_text("x")
    for accion in (lambda: descargar("http://127.0.0.1:9/x.mp3", estorbo / "sub", "mp3", "128"),):
        with pytest.raises(ErrorClaro) as e:
            accion()
        assert "carpeta de destino" in traducir_error(e.value)


def test_convertir_archivo_que_ya_no_existe(tmp_path):
    with pytest.raises(ErrorClaro):
        convertir_archivo(tmp_path / "perdido.wav", "mp3")


def test_nota_cuando_no_hay_resoluciones():
    tema.P.usar("oscuro")
    v = VistaDescargar("mp4", "320", "C:/x")
    assert v.nota_calidad.value.startswith("Pega un enlace")
    v.mostrar_info("Video", "Canal", 60, None, [])
    assert "no informa" in v.nota_calidad.value
    v.ocultar_info()
    assert v.nota_calidad.value.startswith("Pega un enlace")


def test_no_cambia_de_tema_con_tarea_en_curso():
    from zaynix.controladores.ajustes import ControladorAjustes
    from zaynix.core.config import Config
    from zaynix.ui.vistas.ajustes import VistaAjustes

    class Pagina:
        def update(self):
            pass

    c = object.__new__(ControladorAjustes)
    c.cfg, c.page = Config(), Pagina()
    c.vista = VistaAjustes(c.cfg, "0")
    cambios = []
    c.al_cambiar_tema = lambda: cambios.append(1)
    c.hay_tarea = lambda: True
    c._elegir_tema("claro")
    assert c.cfg.tema == "oscuro" and not cambios and c.vista.aviso_tema.control.visible
    c.hay_tarea = lambda: False
    c._elegir_tema("claro")
    assert c.cfg.tema == "claro" and cambios
