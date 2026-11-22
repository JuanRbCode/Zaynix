from __future__ import annotations

from typing import Callable

import flet as ft

from zaynix.ui import componentes as c
from zaynix.ui import tema
from zaynix.ui.tema import P

FORMATOS = {"mp3": "MP3", "wav": "WAV", "flac": "FLAC", "m4a": "M4A", "ogg": "OGG", "opus": "OPUS", "mp4": "MP4"}
DESCRIPCION = {
    "mp3": "Compatible con todo. Comprimido a 320 kbps.",
    "wav": "Sin compresión. Ideal para editar audio; archivos grandes.",
    "flac": "Sin pérdida de calidad y más liviano que WAV.",
    "m4a": "AAC a 256 kbps. Muy compatible con Apple y móviles.",
    "ogg": "Vorbis. Buena calidad con tamaño reducido.",
    "opus": "El códec más eficiente: gran calidad en poco espacio.",
    "mp4": "Video H.264 + audio AAC. Si el original es solo audio, queda un MP4 de audio.",
}


class VistaConvertir:
    def __init__(self):
        self.boton_agregar = c.boton_secundario("Agregar archivos", ft.Icons.ADD_ROUNDED)
        self.boton_limpiar = ft.TextButton("Quitar todos", visible=False)
        self.zona_vacia = ft.Container(
            border=ft.Border.all(1, P.borde_fuerte), border_radius=tema.RADIO, bgcolor=P.superficie_2,
            ink=True,
            content=c.estado_vacio(ft.Icons.AUDIO_FILE_OUTLINED, "Selecciona archivos de audio o video",
                                   "MP3, WAV, FLAC, M4A, OGG · MP4, MKV, WEBM, MOV, AVI…"),
        )
        self.lista_archivos = ft.Column(spacing=2)
        self.aviso = c.AvisoEnLinea()
        self.formato = c.Segmentado(FORMATOS, "wav", on_change=self._al_cambiar_formato)
        self.descripcion = c.texto(DESCRIPCION["wav"], tema.T_MINI, P.texto_tenue)
        self.texto_destino = c.texto("", tema.T_MINI, P.texto_tenue, expand=True)
        self.boton_convertir = c.boton_primario("Convertir", ft.Icons.SYNC_ALT_ROUNDED)
        self.boton_convertir.disabled = True
        self.boton_cancelar = c.boton_secundario("Cancelar")
        self.boton_cancelar.visible = False

        self.estado = c.texto("", tema.T_MINI, P.texto_suave, expand=True)
        self.porcentaje = c.texto("", tema.T_MINI, P.texto_suave)
        self.barra = c.barra_progreso()
        self.panel_progreso = ft.Column([ft.Row([self.estado, self.porcentaje]), self.barra],
                                        spacing=8, visible=False)

        self.recientes = c.ListaRecientes("Nada convertido aún", "Los archivos convertidos aparecerán aquí.",
                                          ft.Icons.AUDIO_FILE_OUTLINED)

        self.raiz = ft.Column(spacing=tema.ESPACIO + 4, controls=[
            c.encabezado("Convertir", "Cambia el formato de tus archivos de audio y video sin salir de la app."),
            c.tarjeta(ft.Column(spacing=14, controls=[
                ft.Row([c.etiqueta("Archivos"), ft.Row([self.boton_limpiar, self.boton_agregar], spacing=4)],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.zona_vacia,
                self.lista_archivos,
                self.aviso.control,
                c.separador(),
                c.fila("Formato", ft.Column([self.formato.control, self.descripcion], spacing=6)),
                self.panel_progreso,
                c.separador(),
                ft.Row([ft.Icon(ft.Icons.FOLDER_OUTLINED, size=15, color=P.texto_tenue), self.texto_destino,
                        self.boton_cancelar, self.boton_convertir], spacing=8),
            ])),
            self.recientes.control,
        ])

    def _al_cambiar_formato(self, clave: str) -> None:
        self.descripcion.value = DESCRIPCION[clave]
        c.refrescar(self.descripcion)

    def mostrar_destino(self, texto: str, ruta_completa: str | None = None) -> None:
        self.texto_destino.value = texto
        self.texto_destino.tooltip = ruta_completa

    def mostrar_archivos(self, archivos: list[tuple[str, str]], on_quitar: Callable[[int], None]) -> None:
        self.lista_archivos.controls = [
            c.item_lista(ft.Icons.AUDIO_FILE_OUTLINED, nombre, detalle,
                         [c.boton_icono(ft.Icons.CLOSE_ROUNDED, "Quitar", lambda e, i=i: on_quitar(i), 16)])
            for i, (nombre, detalle) in enumerate(archivos)
        ]
        hay = bool(archivos)
        self.zona_vacia.visible = not hay
        self.boton_limpiar.visible = hay
        self.boton_convertir.disabled = not hay

    def mostrar_aviso(self, mensaje: str, tipo: str = "error") -> None:
        self.aviso.mostrar(mensaje, tipo)

    def limpiar_aviso(self) -> None:
        self.aviso.ocultar()

    def mostrar_progreso(self, fraccion: float | None, mensaje: str) -> None:
        self.barra.value = fraccion
        self.estado.value = mensaje
        self.porcentaje.value = f"{fraccion:.0%}" if fraccion is not None else ""

    def poner_ocupado(self, ocupado: bool, hay_archivos: bool = True) -> None:
        self.boton_convertir.disabled = ocupado or not hay_archivos
        self.boton_agregar.disabled = ocupado
        self.boton_limpiar.disabled = ocupado
        self.formato.control.disabled = ocupado
        self.boton_cancelar.visible = ocupado
        self.panel_progreso.visible = ocupado
