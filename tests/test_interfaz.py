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
