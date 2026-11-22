from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import flet as ft

from zaynix.controladores.sistema import abrir, mostrar_en_carpeta, tamano_legible, validar_enlace
from zaynix.core import actualizador
from zaynix.core.config import Config
from zaynix.core.descargador import analizar, descargar, opciones_resolucion
from zaynix.core.errores import SITIO_CAMBIO, Cancelado, traducir_error
from zaynix.core.historial import Entrada, Historial, fecha_corta
from zaynix.core.registro import log
from zaynix.ui.vistas.descargar import VistaDescargar

TIPO = "descarga"
ESPERA_ANALISIS = 0.7


class ControladorDescargar:
    def __init__(self, page: ft.Page, vista: VistaDescargar, cfg: Config, historial: Historial,
                 portapapeles: ft.Clipboard, actividad: Callable[[str | None], None]):
        self.page, self.vista, self.cfg, self.historial = page, vista, cfg, historial
        self.portapapeles = portapapeles
        self.actividad = actividad
        self._cancelar = threading.Event()
        self._temporizador: threading.Timer | None = None
        self._turno = 0
        self._analizado = ""
        self.ocupado = False
        self.campo_enfocado = False

        vista.url.on_focus = lambda e: setattr(self, "campo_enfocado", True)
        vista.url.on_blur = lambda e: setattr(self, "campo_enfocado", False)
        vista.boton_descargar.on_click = self.iniciar
        vista.url.on_submit = self.iniciar
        vista.url.on_change = self._al_escribir
        vista.boton_pegar.on_click = self.pegar
        vista.boton_cancelar.on_click = lambda e: self._cancelar.set()
        vista.playlist.on_change = lambda e: self._programar_analisis(0)
        vista.recientes.boton_limpiar.on_click = self.limpiar_historial

        for entrada in historial.de_tipo(TIPO):
            self._mostrar(entrada, al_final=True)

    def _mostrar(self, entrada: Entrada, al_final: bool = False):
        self.vista.recientes.agregar(
            entrada.titulo, f"{entrada.detalle} · {fecha_corta(entrada.fecha)}",
            on_abrir=lambda e, a=entrada.archivo: abrir(a),
            on_carpeta=lambda e, a=entrada.archivo: mostrar_en_carpeta(a),
            al_final=al_final,
        )

    def limpiar_historial(self, e=None):
        self.historial.limpiar(TIPO)
        self.vista.recientes.vaciar()
        self.page.update()

    def _al_escribir(self, e=None):
        if self.vista.aviso.control.visible:
            self.vista.limpiar_aviso()
        self._programar_analisis(ESPERA_ANALISIS)
        self.page.update()

    def _programar_analisis(self, espera: float, forzar: bool = True):
        if self._temporizador:
            self._temporizador.cancel()
        if forzar:
            self._analizado = ""
        self._temporizador = threading.Timer(espera, self._analizar)
        self._temporizador.daemon = True
        self._temporizador.start()

    def _analizar(self):
        link = (self.vista.url.value or "").strip()
        if self.ocupado or link == self._analizado:
            return
        self._turno += 1
        turno = self._turno
        if validar_enlace(link):
            self.vista.ocultar_info()
            self.page.update()
            return
        self.vista.mostrar_analizando(True)
        self.page.update()
        try:
            info = analizar(link, self.vista.playlist.value)
        except Exception as ex:
            if turno == self._turno:
                self.vista.ocultar_info()
                self.vista.mostrar_error(traducir_error(ex))
                self.page.update()
            return
        if turno != self._turno:
            return
        self._analizado = link
        self.vista.mostrar_info(info.titulo, info.autor, info.duracion, info.miniatura,
                                opciones_resolucion(info.alturas), info.entradas)
        self.page.update()

    async def pegar(self, e=None):
        if self.ocupado:
            return
        texto = (await self.portapapeles.get() or "").strip()
        if not texto:
            self.vista.mostrar_aviso("El portapapeles está vacío.", "aviso")
        else:
            self.vista.url.value = texto
            self.vista.limpiar_aviso()
            self._programar_analisis(0)
        self.page.update()

    def iniciar(self, e=None):
        if self.ocupado:
            return
        link = (self.vista.url.value or "").strip()
        error = validar_enlace(link)
        if error:
            self.vista.mostrar_error(error)
            self.page.update()
            return
        if self._temporizador:
            self._temporizador.cancel()
        self._turno += 1
        self.vista.limpiar_aviso()
        self.ocupado = True
        self._cancelar.clear()
        self.page.run_thread(self._trabajar, link)

    def _progreso(self, fraccion, mensaje):
        self.vista.mostrar_progreso(fraccion, mensaje)
        self.actividad(f"{fraccion:.0%}" if fraccion is not None else "Procesando")
        self.page.update()

    def _trabajar(self, link: str):
        v = self.vista
        v.mostrar_analizando(False)
        v.poner_ocupado(True)
        self.actividad("Conectando")
        self.page.update()
        formato, calidad, rotulo = v.formato.valor, v.calidad_elegida(), v.texto_calidad()
        fallidos: list[str] = []

        def terminado(r):
            peso = tamano_legible(r.archivo.stat().st_size) if r.archivo.exists() else "—"
            self._mostrar(self.historial.agregar(TIPO, r.titulo, r.archivo,
                                                 f"{formato.upper()} · {rotulo} · {peso}"))
            self.page.update()

        try:
            resultados = descargar(link, Path(self.cfg.carpeta_descargas), formato, calidad, v.playlist.value,
                                   self._progreso, self._cancelar.is_set, portada=self.cfg.incrustar_portada,
                                   al_terminar=terminado, al_fallar=fallidos.append)
            for f in fallidos:
                log.warning("Elemento de la lista no descargado: %s", f)
            n = len(resultados)
            listo = (f"Listo: {n} archivo{'s' if n != 1 else ''} guardado{'s' if n != 1 else ''} "
                     f"en {self.cfg.carpeta_descargas}")
            if fallidos:
                v.mostrar_aviso(f"{listo}. {len(fallidos)} no se pudo descargar." if len(fallidos) == 1 else
                                f"{listo}. {len(fallidos)} no se pudieron descargar.", "aviso")
            else:
                v.mostrar_aviso(listo, "exito")
            v.url.value = ""
            v.ocultar_info()
            self._analizado = ""
            if resultados and self.cfg.abrir_al_terminar:
                mostrar_en_carpeta(resultados[-1].archivo)
        except Cancelado:
            v.mostrar_aviso("Descarga cancelada.", "aviso")
        except Exception as ex:
            mensaje = traducir_error(ex)
            log.warning("Falló la descarga desde %s (%s): %s", urlparse(link).netloc, formato, ex)
            v.mostrar_error(mensaje)
            if mensaje == SITIO_CAMBIO:
                threading.Thread(target=actualizador.actualizar_motor_en_segundo_plano, args=(True,),
                                 daemon=True).start()
        finally:
            self.ocupado = False
            v.poner_ocupado(False)
            self.actividad(None)
            self.page.update()
