from __future__ import annotations

import flet as ft

from zaynix.ui import componentes as c
from zaynix.ui import tema
from zaynix.ui.tema import P

SECCIONES = {"descargar": "Descargar", "convertir": "Convertir"}
ALTO_BARRA = 58


class Shell:
    def __init__(self, vistas: dict[str, ft.Control], ajustes: c.PanelLateral):
        self.vistas = vistas
        self.ajustes = ajustes

        self.pestanas = c.Segmentado(SECCIONES, "descargar", on_change=self.ir, fondo=P.pestanas, borde=False)
        self._anillo = ft.ProgressRing(width=12, height=12, stroke_width=2, color=P.texto)
        self._actividad_texto = c.texto("", tema.T_MINI, P.texto_suave)
        self.actividad = ft.Row([self._anillo, self._actividad_texto], spacing=6, tight=True, visible=False)
        self.insignia = ft.Container(width=8, height=8, border_radius=4, bgcolor=P.exito, right=8, top=8,
                                     visible=False)
        self.boton_ajustes = ft.Stack([c.boton_icono(ft.Icons.SETTINGS_OUTLINED, "Ajustes", ajustes.abrir),
                                       self.insignia])

        self.contenedor = ft.Container(content=vistas["descargar"], width=tema.ANCHO_CONTENIDO)

        desplazable = ft.Column(
            [ft.Container(ft.Row([self.contenedor], alignment=ft.MainAxisAlignment.CENTER),
                          padding=ft.Padding.only(left=24, right=24, top=ALTO_BARRA + 36, bottom=32))],
            scroll=ft.ScrollMode.AUTO, expand=True,
        )
        desvanecido = ft.Container(
            left=0, top=0, right=0, height=ALTO_BARRA + 24,
            gradient=ft.LinearGradient(begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                                       colors=[P.fondo, P.fondo, f"{P.fondo},0"], stops=[0, 0.6, 1]),
        )
        barra = ft.Container(
            ft.Row([c.notch(P.logo, self.pestanas.control, self.actividad, self.boton_ajustes)],
                   alignment=ft.MainAxisAlignment.CENTER),
            left=0, top=0, right=0,
        )
        self.aviso = c.AvisoFlotante()
        self.raiz = ft.Stack(expand=True, controls=[
            ft.Container(desplazable, left=0, top=0, right=0, bottom=0),
            desvanecido,
            barra,
            self.aviso.control,
            *ajustes.capas,
        ])

    def ir(self, clave: str) -> None:
        self.contenedor.content = self.vistas[clave]
        if self.pestanas.valor != clave:
            self.pestanas.elegir(clave, avisar=False)
        self.contenedor.update()

    def mostrar_insignia(self, visible: bool) -> None:
        self.insignia.visible = visible

    def mostrar_actividad(self, texto: str | None) -> None:
        self.actividad.visible = texto is not None
        self._actividad_texto.value = texto or ""
