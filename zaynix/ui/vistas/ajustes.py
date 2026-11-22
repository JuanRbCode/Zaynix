from __future__ import annotations

import flet as ft

from zaynix.core.config import Config
from zaynix.ui import componentes as c
from zaynix.ui import tema
from zaynix.ui.tema import P
from zaynix.ui.vistas.descargar import CALIDADES, FORMATOS

TEMAS = [
    ("oscuro", "Oscuro", "#0A0A0A", True),
    ("claro", "Claro", "#F5F5F5", True),
    ("sistema", "Sistema", None, True),
]


def _tarjeta_tema(nombre: str, muestra: str | None, activo: bool, disponible: bool) -> ft.Container:
    if muestra:
        vista_previa = ft.Container(height=52, border_radius=6, bgcolor=muestra,
                                    border=ft.Border.all(1, P.borde_fuerte))
    else:
        vista_previa = ft.Container(height=52, border_radius=6, border=ft.Border.all(1, P.borde_fuerte),
                                    gradient=ft.LinearGradient(colors=["#0A0A0A", "#0A0A0A", "#F5F5F5", "#F5F5F5"],
                                                               stops=[0, 0.5, 0.5, 1]))
    return ft.Container(
        expand=True, padding=8, border_radius=tema.RADIO, opacity=1 if disponible else 0.45, ink=True,
        bgcolor=P.superficie, border=ft.Border.all(1, P.texto if activo else P.borde),
        tooltip=None if disponible else "Próximamente",
        content=ft.Column([
            vista_previa,
            ft.Row([c.texto(nombre, tema.T_MINI, P.texto if activo else P.texto_suave, ft.FontWeight.W_500),
                    ft.Icon(ft.Icons.CHECK_ROUNDED, size=14, color=P.texto, visible=activo)],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ], spacing=8),
    )


def _bloque_carpeta(titulo: str, descripcion: str, ruta: ft.Text, boton: ft.Control) -> ft.Column:
    return ft.Column([
        c.ajuste(titulo, descripcion, boton),
        ft.Container(
            ft.Row([ft.Icon(ft.Icons.FOLDER_OUTLINED, size=14, color=P.texto_tenue), ruta], spacing=8),
            bgcolor=P.superficie, border=ft.Border.all(1, P.borde), border_radius=tema.RADIO,
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
        ),
    ], spacing=10)


class VistaAjustes:
    def __init__(self, cfg: Config, version: str):
        self.temas = {k: _tarjeta_tema(n, m, k == cfg.tema, d) for k, n, m, d in TEMAS}
        self.tarjetas_tema = ft.Row(list(self.temas.values()), spacing=8)
        self.aviso_tema = c.AvisoEnLinea()

        self.texto_version = c.texto(f"Zaynix {version}", tema.T_PEQUENO, peso=ft.FontWeight.W_500)
        self.estado_version = c.texto("", tema.T_MINI, P.texto_tenue, cortar=False)
        self.boton_buscar = c.boton_secundario("Buscar actualizaciones", ft.Icons.REFRESH_ROUNDED, alto=32)
        self.boton_obtener = c.boton_primario("Descargar", ft.Icons.DOWNLOAD_ROUNDED)
        self.boton_obtener.height = 32
        self.boton_obtener.visible = False
        self.buscando = ft.ProgressBar(value=None, color=P.primario, bgcolor=P.activo, bar_height=3,
                                       border_radius=3, visible=False)
        self.enlace_sitio = c.fila_enlace(ft.Icons.LANGUAGE_ROUNDED, "Sitio web")
        self.enlace_cambios = c.fila_enlace(ft.Icons.NEW_RELEASES_OUTLINED, "Novedades")
        self.enlace_licencias = c.fila_enlace(ft.Icons.DESCRIPTION_OUTLINED, "Licencias")
        self.enlace_problema = c.fila_enlace(ft.Icons.BUG_REPORT_OUTLINED, "Reportar un problema")

        self.texto_descargas = c.texto(cfg.carpeta_descargas, tema.T_MINI, P.texto_suave, expand=True)
        self.boton_descargas = c.boton_secundario("Cambiar", alto=32)
        self.formato = c.Segmentado(FORMATOS, cfg.formato_descarga, fondo=P.superficie, compacto=True)
        self.calidad = c.Segmentado({k: v.replace(" kbps", "") for k, v in CALIDADES.items()}, cfg.calidad_mp3,
                                    fondo=P.superficie)
        self.portada = c.interruptor(cfg.incrustar_portada)

        self.texto_conversiones = c.texto(cfg.carpeta_conversiones, tema.T_MINI, P.texto_suave, expand=True)
        self.boton_conversiones = c.boton_secundario("Cambiar", alto=32)
        self.junto_al_original = c.interruptor(cfg.junto_al_original)
        self.bloque_conversiones = _bloque_carpeta(
            "Carpeta de conversiones", "Dónde se guardan los archivos convertidos",
            self.texto_conversiones, self.boton_conversiones)
        self.bloque_conversiones.visible = not cfg.junto_al_original

        self.abrir_al_terminar = c.interruptor(cfg.abrir_al_terminar)

        self.contenido = ft.Column(spacing=30, controls=[
            c.seccion_ajustes("Apariencia", [
                c.texto("Tema", tema.T_PEQUENO, peso=ft.FontWeight.W_500),
                self.tarjetas_tema,
                self.aviso_tema.control,
            ]),
            c.seccion_ajustes("Descargas", [
                _bloque_carpeta("Carpeta de descargas", "Dónde se guarda lo que descargas de enlaces",
                                self.texto_descargas, self.boton_descargas),
                ft.Column([
                    c.ajuste("Formato predeterminado", "Formato seleccionado al abrir la app", ft.Container()),
                    self.formato.control,
                ], spacing=8),
                ft.Column([
                    c.ajuste("Calidad MP3 predeterminada", "Kbps seleccionados al abrir la app", ft.Container()),
                    self.calidad.control,
                ], spacing=8),
                c.ajuste("Incrustar portada", "Agrega la carátula y los datos al archivo", self.portada),
            ]),
            c.seccion_ajustes("Conversión", [
                c.ajuste("Guardar junto al original", "El archivo convertido queda en la misma carpeta",
                         self.junto_al_original),
                self.bloque_conversiones,
            ]),
            c.seccion_ajustes("General", [
                c.ajuste("Abrir carpeta al terminar", "Muestra el archivo en el Explorador", self.abrir_al_terminar),
            ]),
            c.seccion_ajustes("Acerca de", [
                ft.Row([
                    ft.Column([self.texto_version, self.estado_version], spacing=2, expand=True, tight=True),
                    self.boton_obtener,
                    self.boton_buscar,
                ], spacing=8),
                self.buscando,
                c.separador(),
                ft.Column([self.enlace_sitio, self.enlace_cambios, self.enlace_licencias, self.enlace_problema],
                          spacing=0),
            ]),
        ])
        self.pie = ft.Row([
            c.texto(f"Zaynix v{version}", tema.T_MINI, P.texto_suave, ft.FontWeight.W_500),
            c.texto("Software libre · GPLv3 · Sin garantía", tema.T_MINI, P.texto_tenue),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def mostrar_aviso_tema(self, mensaje: str) -> None:
        self.aviso_tema.mostrar(mensaje, "aviso")

    def mostrar_carpeta_descargas(self, ruta: str) -> None:
        self.texto_descargas.value = ruta

    def mostrar_carpeta_conversiones(self, ruta: str) -> None:
        self.texto_conversiones.value = ruta

    def mostrar_junto_al_original(self, activo: bool) -> None:
        self.bloque_conversiones.visible = not activo

    def mostrar_estado_version(self, mensaje: str, tipo: str = "normal", buscando: bool = False,
                               disponible: bool = False) -> None:
        colores = {"normal": P.texto_tenue, "exito": P.exito, "error": P.error, "aviso": P.aviso}
        self.estado_version.value = mensaje
        self.estado_version.color = colores[tipo]
        self.buscando.visible = buscando
        self.boton_buscar.disabled = buscando
        self.boton_obtener.visible = disponible
