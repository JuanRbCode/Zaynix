from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

import flet as ft

from zaynix.controladores.sistema import abrir, mostrar_en_carpeta, tamano_legible
from zaynix.core.config import Config
from zaynix.core.conversor import EXTENSIONES_ENTRADA, convertir_archivo
from zaynix.core.errores import Cancelado, traducir_error
from zaynix.core.historial import Entrada, Historial, fecha_corta
from zaynix.ui.vistas.convertir import VistaConvertir

TIPO = "conversion"


class ControladorConvertir:
    def __init__(self, page: ft.Page, vista: VistaConvertir, cfg: Config, historial: Historial,
                 selector: ft.FilePicker, actividad: Callable[[str | None], None]):
        self.page, self.vista, self.cfg, self.historial = page, vista, cfg, historial
        self.selector = selector
        self.actividad = actividad
        self.archivos: list[Path] = []
        self._cancelar = threading.Event()

        vista.boton_agregar.on_click = self.agregar
        vista.zona_vacia.on_click = self.agregar
        vista.boton_limpiar.on_click = self.limpiar
        vista.boton_convertir.on_click = self.iniciar
        vista.boton_cancelar.on_click = lambda e: self._cancelar.set()
        vista.recientes.boton_limpiar.on_click = self.limpiar_historial

        for entrada in historial.de_tipo(TIPO):
            self._mostrar(entrada, al_final=True)
        self.actualizar_destino()

    def _mostrar(self, entrada: Entrada, al_final: bool = False):
        self.vista.recientes.agregar(
            entrada.titulo, f"{entrada.detalle} · {fecha_corta(entrada.fecha)}",
            on_abrir=lambda e, a=entrada.archivo: abrir(a),
            on_carpeta=lambda e, a=entrada.archivo: mostrar_en_carpeta(a),
            al_final=al_final,
        )

    def _destino_de(self, archivo: Path) -> Path:
        return archivo.parent if self.cfg.junto_al_original else Path(self.cfg.carpeta_conversiones)

    def actualizar_destino(self):
        if not self.cfg.junto_al_original:
            ruta = self.cfg.carpeta_conversiones
            self.vista.mostrar_destino(f"Se guardará en {ruta}", ruta)
            return
        carpetas = sorted({str(a.parent) for a in self.archivos})
        if not carpetas:
            self.vista.mostrar_destino("Se guardará en la misma carpeta que cada archivo original")
        elif len(carpetas) == 1:
            self.vista.mostrar_destino(f"Se guardará en {carpetas[0]}", carpetas[0])
        else:
            self.vista.mostrar_destino(f"Se guardará junto a cada original ({len(carpetas)} carpetas)",
                                       "\n".join(carpetas))

    def limpiar_historial(self, e=None):
        self.historial.limpiar(TIPO)
        self.vista.recientes.vaciar()
        self.page.update()

    async def agregar(self, e=None):
        elegidos = await self.selector.pick_files("Elige archivos de audio", allow_multiple=True,
                                                  allowed_extensions=EXTENSIONES_ENTRADA)
        nuevos = [Path(f.path) for f in (elegidos or []) if f.path and Path(f.path) not in self.archivos]
        self.archivos.extend(nuevos)
        self._refrescar()

    def quitar(self, indice: int):
        self.archivos.pop(indice)
        self._refrescar()

    def limpiar(self, e=None):
        self.archivos.clear()
        self._refrescar()

    def _refrescar(self):
        datos = []
        for a in self.archivos:
            peso = tamano_legible(a.stat().st_size) if a.exists() else "no encontrado"
            datos.append((a.name, f"{a.suffix[1:].upper()} · {peso} · {a.parent}"))
        self.vista.mostrar_archivos(datos, self.quitar)
        self.vista.limpiar_aviso()
        self.actualizar_destino()
        self.page.update()

    def iniciar(self, e=None):
        if not self.archivos:
            self.vista.mostrar_aviso("Agrega al menos un archivo para convertir.")
            self.page.update()
            return
        self.page.run_thread(self._trabajar, list(self.archivos), self.vista.formato.valor)

    def _trabajar(self, archivos: list[Path], formato: str):
        v = self.vista
        self._cancelar.clear()
        v.limpiar_aviso()
        v.poner_ocupado(True)
        self.page.update()
        total, hechos, fallidos = len(archivos), [], []
        try:
            for i, archivo in enumerate(archivos):
                def progreso(f, i=i, nombre=archivo.name):
                    avance = (i + (f or 0)) / total
                    v.mostrar_progreso(avance, f"Convirtiendo {i + 1} de {total} · {nombre}")
                    self.actividad(f"{avance:.0%}")
                    self.page.update()
                progreso(0)
                try:
                    salida = convertir_archivo(archivo, formato, self._destino_de(archivo), progreso,
                                               self._cancelar.is_set)
                except Cancelado:
                    raise
                except Exception as ex:
                    fallidos.append(f"{archivo.name}: {traducir_error(ex)}")
                    continue
                hechos.append(salida)
                self._mostrar(self.historial.agregar(
                    TIPO, salida.name, salida,
                    f"{archivo.suffix[1:].upper()} → {formato.upper()} · {tamano_legible(salida.stat().st_size)}"))
            if fallidos:
                v.mostrar_aviso(f"{len(hechos)} convertido(s), {len(fallidos)} con error. " + fallidos[0], "aviso")
            else:
                carpeta = hechos[0].parent if hechos else ""
                v.mostrar_aviso(f"Listo: {len(hechos)} archivo(s) convertido(s) a {formato.upper()} en {carpeta}",
                                "exito")
                self.archivos.clear()
                v.mostrar_archivos([], self.quitar)
                self.actualizar_destino()
            if hechos and self.cfg.abrir_al_terminar:
                mostrar_en_carpeta(hechos[-1])
        except Cancelado:
            v.mostrar_aviso("Conversión cancelada.", "aviso")
        finally:
            v.poner_ocupado(False, bool(self.archivos))
            self.actividad(None)
            self.page.update()
