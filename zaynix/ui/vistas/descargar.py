from __future__ import annotations

import flet as ft

from zaynix.core.descargador import FORMATOS_AUDIO, FORMATOS_VIDEO, KBPS, SIN_PERDIDA
from zaynix.ui import componentes as c
from zaynix.ui import tema
from zaynix.ui.tema import P

FORMATOS = {f: f.upper() for f in FORMATOS_AUDIO + FORMATOS_VIDEO}
CALIDADES = {k: f"{k} kbps" for k in KBPS["mp3"]}
DESCRIPCION = {
    "mp3": "Audio compatible con cualquier dispositivo.",
    "m4a": "Audio AAC, ideal para iPhone y Apple Music.",
    "wav": "Audio sin compresión, para editar. Archivos grandes.",
    "flac": "Audio sin pérdida, más liviano que WAV.",
    "ogg": "Audio Vorbis, buena calidad en poco espacio.",
    "opus": "El códec de audio más eficiente.",
    "mp4": "Video con audio, compatible con cualquier reproductor.",
}


def _texto_duracion(segundos: int | None) -> str:
    if not segundos:
        return ""
    h, r = divmod(segundos, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"


class VistaDescargar:
    def __init__(self, formato: str, calidad_mp3: str, carpeta: str):
        self.calidad_mp3 = calidad_mp3
        self.url = c.campo("Pega aquí el enlace", ft.Icons.LINK_ROUNDED)
        self.boton_pegar = c.boton_secundario("Pegar", ft.Icons.CONTENT_PASTE_ROUNDED)
        self.aviso = c.AvisoEnLinea()

        self._miniatura = ft.Image(src="", fit=ft.BoxFit.COVER, width=112, height=63)
        self._titulo_previa = c.texto("", tema.T_PEQUENO, peso=ft.FontWeight.W_500)
        self._detalle_previa = c.texto("", tema.T_MINI, P.texto_tenue)
        self.previa = c.vista_previa(self._miniatura, self._titulo_previa, self._detalle_previa)
        self.previa.visible = False
        self.analizando = ft.Row([ft.ProgressRing(width=12, height=12, stroke_width=2, color=P.texto_suave),
                                  c.texto("Analizando enlace…", tema.T_MINI, P.texto_suave)],
                                 spacing=8, visible=False)

        self.formato = c.Segmentado(FORMATOS, formato if formato in FORMATOS else "mp3",
                                    on_change=lambda k: self._al_cambiar_formato(k))
        self.descripcion_formato = c.texto("", tema.T_MINI, P.texto_tenue)
        self.rotulo_calidad = c.texto("Calidad", tema.T_PEQUENO, P.texto_suave)
        self.calidad = c.Segmentado({"": ""}, "")
        self.nota_calidad = c.texto("", tema.T_MINI, P.texto_tenue)
        self.alturas: list[int] = []

        self.playlist = c.interruptor(False)
        self.texto_destino = c.texto("", tema.T_MINI, P.texto_tenue, expand=True)
        self.boton_descargar = c.boton_primario("Descargar", ft.Icons.DOWNLOAD_ROUNDED)
        self.boton_cancelar = c.boton_secundario("Cancelar")
        self.boton_cancelar.visible = False

        self.estado = c.texto("", tema.T_MINI, P.texto_suave, expand=True)
        self.porcentaje = c.texto("", tema.T_MINI, P.texto_suave)
        self.barra = c.barra_progreso()
        self.panel_progreso = ft.Column([ft.Row([self.estado, self.porcentaje]), self.barra],
                                        spacing=8, visible=False)

        self.recientes = c.ListaRecientes("Sin descargas todavía", "Lo que descargues aparecerá aquí.",
                                          ft.Icons.DOWNLOAD_DONE_ROUNDED)
        self.mostrar_destino(carpeta)

        self.raiz = ft.Column(spacing=tema.ESPACIO + 4, controls=[
            c.encabezado("Descargar", "Pega un enlace de una plataforma compatible "
                                      "y guárdalo como audio o video."),
            c.tarjeta(ft.Column(spacing=14, controls=[
                ft.Column([
                    ft.Row([self.url, self.boton_pegar], spacing=8),
                    self.aviso.control,
                    self.analizando,
                    self.previa,
                ], spacing=10),
                c.separador(),
                c.fila("Formato", ft.Column([self.formato.control, self.descripcion_formato], spacing=6)),
                ft.Row([ft.Container(self.rotulo_calidad, width=96),
                        ft.Column([self.calidad.control, self.nota_calidad], spacing=6)]),
                c.fila("Playlist", ft.Row([self.playlist, c.texto("Descargar todos los elementos del enlace",
                                                                    tema.T_MINI, P.texto_tenue)], spacing=8)),
                self.panel_progreso,
                c.separador(),
                ft.Row([ft.Icon(ft.Icons.FOLDER_OUTLINED, size=15, color=P.texto_tenue), self.texto_destino,
                        self.boton_cancelar, self.boton_descargar], spacing=8),
            ])),
            self.recientes.control,
        ])
        self._al_cambiar_formato(self.formato.valor, avisar=False)

    def _al_cambiar_formato(self, formato: str, avisar: bool = True) -> None:
        self.descripcion_formato.value = DESCRIPCION[formato]
        self.boton_descargar.content = f"Descargar {formato.upper()}"
        self._actualizar_calidades()
        if avisar:
            c.refrescar(self.raiz)

    def _actualizar_calidades(self) -> None:
        formato = self.formato.valor
        self.calidad.control.visible = True
        self.nota_calidad.visible = True
        if formato in FORMATOS_VIDEO:
            self.rotulo_calidad.value = "Resolución"
            opciones = {"max": "Máxima"}
            opciones.update({str(r): f"{r}p" if r < 2160 else "4K" for r in self.alturas})
            self.calidad.cambiar_opciones(opciones, "max")
            self.nota_calidad.value = ("Resoluciones disponibles para este video." if self.alturas else
                                       "Pega un enlace para ver las resoluciones disponibles.")
        elif formato in SIN_PERDIDA:
            self.rotulo_calidad.value = "Calidad"
            self.calidad.control.visible = False
            self.nota_calidad.value = "Sin pérdida: se conserva la calidad original del audio."
        else:
            self.rotulo_calidad.value = "Calidad"
            preferida = self.calidad_mp3 if formato == "mp3" else KBPS[formato][0]
            self.calidad.cambiar_opciones({k: f"{k} kbps" for k in KBPS[formato]}, preferida)
            self.nota_calidad.visible = False

    def calidad_elegida(self) -> str | None:
        if self.formato.valor in SIN_PERDIDA:
            return None
        return None if self.calidad.valor == "max" else self.calidad.valor

    def texto_calidad(self) -> str:
        f, q = self.formato.valor, self.calidad_elegida()
        if f in SIN_PERDIDA:
            return "sin pérdida"
        if f in FORMATOS_VIDEO:
            return f"{q}p" if q else "máxima"
        return f"{q} kbps"

    def mostrar_analizando(self, activo: bool) -> None:
        self.analizando.visible = activo
        if activo:
            self.previa.visible = False

    def mostrar_info(self, titulo: str, autor: str, duracion: int | None, miniatura: str | None,
                     alturas: list[int], entradas: int = 0) -> None:
        self.alturas = alturas
        self._titulo_previa.value = titulo
        maxima = ""
        if alturas:
            maxima = "hasta 4K" if alturas[0] >= 2160 else f"hasta {alturas[0]}p"
        partes = [autor, _texto_duracion(duracion), f"{entradas} elementos" if entradas else "", maxima]
        self._detalle_previa.value = " · ".join(p for p in partes if p)
        self._miniatura.src = miniatura or ""
        self._miniatura.visible = bool(miniatura)
        self.previa.visible = True
        self.analizando.visible = False
        self._actualizar_calidades()

    def ocultar_info(self) -> None:
        self.alturas = []
        self.previa.visible = False
        self.analizando.visible = False
        self._actualizar_calidades()

    def mostrar_destino(self, carpeta: str) -> None:
        self.texto_destino.value = f"Se guardará en {carpeta}"
        self.texto_destino.tooltip = carpeta

    def mostrar_error(self, mensaje: str) -> None:
        self.aviso.mostrar(mensaje, "error")
        c.marcar_error(self.url, True)

    def mostrar_aviso(self, mensaje: str, tipo: str) -> None:
        self.aviso.mostrar(mensaje, tipo)
        c.marcar_error(self.url, False)

    def limpiar_aviso(self) -> None:
        self.aviso.ocultar()
        c.marcar_error(self.url, False)

    def mostrar_progreso(self, fraccion: float | None, mensaje: str) -> None:
        self.barra.value = fraccion
        self.estado.value = mensaje
        self.porcentaje.value = f"{fraccion:.0%}" if fraccion is not None else ""

    def poner_ocupado(self, ocupado: bool) -> None:
        for control in (self.boton_descargar, self.boton_pegar, self.url, self.formato.control,
                        self.calidad.control, self.playlist):
            control.disabled = ocupado
        self.boton_cancelar.visible = ocupado
        self.panel_progreso.visible = ocupado
        if ocupado:
            self.mostrar_progreso(None, "Conectando…")
