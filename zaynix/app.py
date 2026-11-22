from pathlib import Path

import flet as ft

from zaynix.controladores.ajustes import ControladorAjustes
from zaynix.controladores.convertir import ControladorConvertir
from zaynix.controladores.descargar import ControladorDescargar
from zaynix.controladores.sistema import abrir_web
from zaynix.core.actualizador import enlace_descarga
from zaynix.core.config import VERSION, Config
from zaynix.core.historial import Historial
from zaynix.ui import componentes as c
from zaynix.ui import tema
from zaynix.ui.shell import Shell
from zaynix.ui.vistas.ajustes import VistaAjustes
from zaynix.ui.vistas.convertir import VistaConvertir
from zaynix.ui.vistas.descargar import VistaDescargar

ASSETS = Path(__file__).resolve().parent.parent / "assets"


class Aplicacion:
    def __init__(self, page: ft.Page):
        self.page = page
        self.cfg = Config.cargar()
        self.historial = Historial()
        tema.tamano_ventana(page)
        page.on_keyboard_event = self._teclado

    def construir(self, abrir_ajustes: bool = False) -> None:
        page, cfg = self.page, self.cfg
        page.controls.clear()
        page.services.clear()
        tema.aplicar(page, cfg.tema, icono=str(ASSETS / tema.ICONO_VENTANA))

        selector, self.portapapeles = ft.FilePicker(), ft.Clipboard()
        page.services.extend([selector, self.portapapeles])

        v_descargar = VistaDescargar(cfg.formato_descarga, cfg.calidad_mp3, cfg.carpeta_descargas)
        v_convertir = VistaConvertir()
        v_ajustes = VistaAjustes(cfg, VERSION)
        self.panel = c.PanelLateral("Ajustes", v_ajustes.contenido, v_ajustes.pie)
        self.shell = Shell({"descargar": v_descargar.raiz, "convertir": v_convertir.raiz}, self.panel)

        self.descargar = ControladorDescargar(page, v_descargar, cfg, self.historial, self.portapapeles,
                                              self.shell.mostrar_actividad)
        self.convertir = ControladorConvertir(page, v_convertir, cfg, self.historial, selector,
                                              self.shell.mostrar_actividad)
        page.add(self.shell.raiz)
        ControladorAjustes(page, v_ajustes, cfg, selector, v_descargar, self.convertir.actualizar_destino,
                           self._cambiar_tema, self._hay_tarea, self._nueva_version)
        page.update()
        if abrir_ajustes:
            self.panel.abrir()

    def _hay_tarea(self) -> bool:
        return self.descargar.ocupado or self.convertir.ocupado

    def _cambiar_tema(self) -> None:
        self.construir(abrir_ajustes=True)

    def _nueva_version(self, datos: dict) -> None:
        self.shell.mostrar_insignia(True)
        self.shell.aviso.mostrar(f"Zaynix {datos['version']} disponible", datos.get("notas", ""))
        self.shell.aviso.boton.on_click = lambda e: abrir_web(enlace_descarga(datos))
        self.page.update()

    async def _teclado(self, e: ft.KeyboardEvent) -> None:
        tecla = (e.key or "").lower()
        if tecla == "escape" and self.panel.panel.right == 0:
            self.panel.cerrar()
        elif e.ctrl and tecla == "v" and not self.descargar.campo_enfocado:
            self.shell.ir("descargar")
            await self.descargar.pegar()
        elif e.ctrl and tecla == "1":
            self.shell.ir("descargar")
        elif e.ctrl and tecla == "2":
            self.shell.ir("convertir")
        elif e.ctrl and tecla == ",":
            self.panel.abrir()
        elif e.ctrl and tecla == "o":
            self.shell.ir("convertir")
            await self.convertir.agregar()


async def main(page: ft.Page) -> None:
    Aplicacion(page).construir()


def arrancar():
    ft.run(main, assets_dir=str(ASSETS))
