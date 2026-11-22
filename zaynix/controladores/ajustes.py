from __future__ import annotations

import threading
from typing import Callable

import flet as ft

from zaynix.core import actualizador
from zaynix.controladores.sistema import abrir_web
from zaynix.core.config import Config
from zaynix.core.errores import traducir_error
from zaynix.core.registro import log
from zaynix.ui.vistas.ajustes import VistaAjustes
from zaynix.ui.vistas.descargar import VistaDescargar


INTERVALO_REVISION = 6 * 60 * 60


class ControladorAjustes:
    def __init__(self, page: ft.Page, vista: VistaAjustes, cfg: Config, selector: ft.FilePicker,
                 descargar: VistaDescargar, al_cambiar_conversion: Callable[[], None],
                 al_cambiar_tema: Callable[[str], None], al_nueva_version: Callable[[dict], None]):
        self.page, self.vista, self.cfg, self.selector = page, vista, cfg, selector
        self.v_descargar = descargar
        self.al_cambiar_conversion = al_cambiar_conversion
        self.al_cambiar_tema = al_cambiar_tema
        self.al_nueva_version = al_nueva_version
        self._avisada: str | None = None
        self._bloqueo = threading.Lock()
        self._nueva: dict | None = None

        vista.boton_descargas.on_click = self.elegir_carpeta_descargas
        vista.boton_conversiones.on_click = self.elegir_carpeta_conversiones
        vista.junto_al_original.on_change = self._cambiar_junto
        vista.calidad.on_change = self._cambiar_calidad
        vista.formato.on_change = self._cambiar_formato
        vista.portada.on_change = lambda e: self._guardar(incrustar_portada=vista.portada.value)
        vista.abrir_al_terminar.on_change = lambda e: self._guardar(abrir_al_terminar=vista.abrir_al_terminar.value)
        vista.boton_buscar.on_click = lambda e: page.run_thread(self.buscar_version, True)
        vista.boton_obtener.on_click = lambda e: abrir_web(actualizador.enlace_descarga(self._nueva))
        vista.enlace_sitio.on_click = lambda e: abrir_web(actualizador.ENLACES["sitio"])
        vista.enlace_cambios.on_click = lambda e: abrir_web(actualizador.ENLACES["novedades"])
        vista.enlace_licencias.on_click = lambda e: abrir_web(actualizador.ENLACES["licencias"])
        vista.enlace_problema.on_click = lambda e: abrir_web(actualizador.ENLACES["problema"])
        for clave, tarjeta in vista.temas.items():
            tarjeta.on_click = lambda e, k=clave: self._elegir_tema(k)

        vista.mostrar_estado_version("")
        threading.Thread(target=actualizador.actualizar_motor_en_segundo_plano, daemon=True).start()
        self._vigilar()

    def _guardar(self, **cambios):
        for k, v in cambios.items():
            setattr(self.cfg, k, v)
        self.cfg.guardar()
        self.page.update()

    def _elegir_tema(self, clave: str):
        if clave == self.cfg.tema:
            return
        self.cfg.tema = clave
        self.cfg.guardar()
        self.al_cambiar_tema(clave)

    activo: "ControladorAjustes | None" = None
    _vigilando = False

    def _vigilar(self):
        ControladorAjustes.activo = self
        if not ControladorAjustes._vigilando:
            ControladorAjustes._vigilando = True
            _ciclo_revision()
        else:
            self.page.run_thread(self.buscar_version, False)

    def buscar_version(self, manual: bool):
        if not self._bloqueo.acquire(blocking=False):
            return
        v = self.vista
        try:
            if manual:
                v.mostrar_estado_version("Buscando actualizaciones…", buscando=True)
                self.page.update()
            self._nueva = actualizador.hay_version_app()
            if self._nueva:
                version = str(self._nueva["version"])
                v.mostrar_estado_version(f"Nueva versión {version} disponible.", "exito", disponible=True)
                if self._avisada != version or manual:
                    self._avisada = version
                    self.al_nueva_version(self._nueva)
            elif manual:
                v.mostrar_estado_version("Estás al día. Tienes la última versión.", "exito")
        except Exception as ex:
            log.warning("No se pudo comprobar la versión: %s", ex)
            if manual:
                v.mostrar_estado_version(f"No se pudo comprobar. {traducir_error(ex)}", "error")
        finally:
            self._bloqueo.release()
            self.page.update()

    async def elegir_carpeta_descargas(self, e=None):
        ruta = await self.selector.get_directory_path("Carpeta de descargas", self.cfg.carpeta_descargas)
        if ruta:
            self.vista.mostrar_carpeta_descargas(ruta)
            self.v_descargar.mostrar_destino(ruta)
            self._guardar(carpeta_descargas=ruta)

    async def elegir_carpeta_conversiones(self, e=None):
        ruta = await self.selector.get_directory_path("Carpeta de conversiones", self.cfg.carpeta_conversiones)
        if ruta:
            self.vista.mostrar_carpeta_conversiones(ruta)
            self.cfg.carpeta_conversiones = ruta
            self.al_cambiar_conversion()
            self._guardar()

    def _cambiar_junto(self, e=None):
        activo = self.vista.junto_al_original.value
        self.vista.mostrar_junto_al_original(activo)
        self.cfg.junto_al_original = activo
        self.al_cambiar_conversion()
        self._guardar()

    def _cambiar_calidad(self, clave: str):
        self.v_descargar.calidad_mp3 = clave
        if self.v_descargar.formato.valor == "mp3":
            self.v_descargar.calidad.elegir(clave, avisar=False)
        self._guardar(calidad_mp3=clave)

    def _cambiar_formato(self, clave: str):
        self.v_descargar.formato.elegir(clave)
        self._guardar(formato_descarga=clave)


def _ciclo_revision():
    controlador = ControladorAjustes.activo
    if controlador:
        controlador.page.run_thread(controlador.buscar_version, False)
    temporizador = threading.Timer(INTERVALO_REVISION, _ciclo_revision)
    temporizador.daemon = True
    temporizador.start()
