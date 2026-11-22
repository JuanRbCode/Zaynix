import pytest

from zaynix.core.config import VERSION, Config
from zaynix.ui import tema
from zaynix.ui.vistas.ajustes import VistaAjustes
from zaynix.ui.vistas.convertir import VistaConvertir
from zaynix.ui.vistas.descargar import VistaDescargar


@pytest.mark.parametrize("nombre", ["oscuro", "claro", "sistema"])
def test_vistas_se_construyen_en_cada_tema(nombre):
    tema.P.usar(nombre)
    cfg = Config()
    assert VistaDescargar(cfg.formato_descarga, cfg.calidad_mp3, cfg.carpeta_descargas).raiz
    assert VistaConvertir().raiz
    assert VistaAjustes(cfg, VERSION).contenido
    tema.P.usar("oscuro")


def test_calidades_cambian_segun_formato():
    v = VistaDescargar("mp3", "320", "C:/x")
    assert v.calidad_elegida() == "320"
    v.formato.elegir("wav", avisar=False)
    v._al_cambiar_formato("wav", avisar=False)
    assert v.calidad_elegida() is None and not v.calidad.control.visible
    v.formato.elegir("mp4", avisar=False)
    v._al_cambiar_formato("mp4", avisar=False)
    assert v.calidad_elegida() is None
    v.mostrar_info("Video", "Canal", 60, None, [1080, 720])
    assert set(v.calidad._botones) == {"max", "1080", "720"}


def test_paletas_completas():
    assert tema.OSCURO.__dataclass_fields__.keys() == tema.CLARO.__dataclass_fields__.keys()
    assert tema.OSCURO.fondo != tema.CLARO.fondo


def _luminancia(color):
    canales = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in canales]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


@pytest.mark.parametrize("paleta", tema.TEMAS.values(), ids=tema.TEMAS.keys())
def test_contraste_minimo_aa(paleta):
    for texto in ("texto", "texto_suave", "texto_tenue", "exito", "aviso", "error"):
        for fondo in ("fondo", "superficie", "superficie_2"):
            a, b = sorted((_luminancia(getattr(paleta, texto)), _luminancia(getattr(paleta, fondo))), reverse=True)
            assert (a + 0.05) / (b + 0.05) >= 4.5, f"{texto} sobre {fondo}"
