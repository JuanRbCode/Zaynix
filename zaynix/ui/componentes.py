from __future__ import annotations

from typing import Callable

import flet as ft

from zaynix.ui import tema
from zaynix.ui.tema import P

CS = ft.ControlState


def refrescar(control: ft.Control) -> None:
    try:
        control.update()
    except RuntimeError:
        pass


def texto(valor: str = "", tamano: int = tema.T_NORMAL, color: str | None = None,
          peso: ft.FontWeight | None = None, expand: bool = False, cortar: bool = True,
          seleccionable: bool = False) -> ft.Text:
    return ft.Text(valor, size=tamano, color=color or P.texto, weight=peso, expand=expand,
                   overflow=ft.TextOverflow.ELLIPSIS if cortar else None, max_lines=1 if cortar else None,
                   selectable=seleccionable)


def encabezado(titulo: str, descripcion: str) -> ft.Column:
    return ft.Column([
        texto(titulo, tema.T_TITULO, peso=ft.FontWeight.W_600),
        texto(descripcion, tema.T_PEQUENO, P.texto_suave, cortar=False),
    ], spacing=4)


def etiqueta(valor: str) -> ft.Text:
    return texto(valor.upper(), tema.T_MINI - 1, P.texto_tenue, ft.FontWeight.W_600)


def separador() -> ft.Container:
    return ft.Container(height=1, bgcolor=P.borde)


def separador_vertical(alto: int = 18) -> ft.Container:
    return ft.Container(width=1, height=alto, bgcolor=P.borde_fuerte)


def boton_primario(valor: str, icono=None, on_click: Callable | None = None) -> ft.FilledButton:
    return ft.FilledButton(
        valor, icon=icono, height=tema.ALTO_CONTROL, on_click=on_click,
        style=ft.ButtonStyle(
            bgcolor={CS.DISABLED: P.activo, CS.HOVERED: P.primario_hover, CS.DEFAULT: P.primario},
            color={CS.DISABLED: P.texto_tenue, CS.DEFAULT: P.sobre_primario},
            icon_color={CS.DISABLED: P.texto_tenue, CS.DEFAULT: P.sobre_primario},
            shape=tema.forma(), padding=ft.Padding.symmetric(horizontal=18),
            text_style=ft.TextStyle(size=tema.T_NORMAL, weight=ft.FontWeight.W_600),
        ),
    )


def boton_secundario(valor: str, icono=None, on_click: Callable | None = None,
                     alto: int = tema.ALTO_CONTROL) -> ft.OutlinedButton:
    return ft.OutlinedButton(
        valor, icon=icono, height=alto, on_click=on_click,
        style=ft.ButtonStyle(
            bgcolor={CS.HOVERED: P.hover, CS.DEFAULT: P.superficie_2},
            overlay_color=f"{P.texto},0.04",
            color={CS.DISABLED: P.texto_tenue, CS.DEFAULT: P.texto},
            icon_color={CS.DEFAULT: P.texto_suave},
            side=ft.BorderSide(1, P.borde_fuerte), shape=tema.forma(),
            padding=ft.Padding.symmetric(horizontal=14),
            text_style=ft.TextStyle(size=tema.T_PEQUENO, weight=ft.FontWeight.W_500),
        ),
    )


def boton_icono(icono, tooltip: str, on_click: Callable | None = None, tamano: int = 18) -> ft.IconButton:
    return ft.IconButton(icono, tooltip=tooltip, on_click=on_click, icon_size=tamano,
                         icon_color=P.texto_suave,
                         style=ft.ButtonStyle(shape=tema.forma(), bgcolor={CS.HOVERED: P.hover}))


def campo(pista: str, icono=None, on_submit: Callable | None = None) -> ft.TextField:
    return ft.TextField(
        hint_text=pista, prefix_icon=icono, on_submit=on_submit, expand=True, autofocus=True,
        height=tema.ALTO_CONTROL, text_size=tema.T_NORMAL, color=P.texto, cursor_color=P.texto,
        bgcolor=P.superficie_2, filled=True, border_radius=tema.RADIO, border_width=1,
        border_color=P.borde_fuerte, focused_border_color=P.foco, focused_border_width=1,
        hint_style=ft.TextStyle(color=P.texto_tenue, size=tema.T_NORMAL),
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=0),
    )


def marcar_error(c: ft.TextField, con_error: bool) -> None:
    c.border_color = P.error if con_error else P.borde_fuerte
    c.focused_border_color = P.error if con_error else P.foco


def interruptor(valor: bool = False, on_change: Callable | None = None) -> ft.Switch:
    return ft.Switch(value=valor, on_change=on_change, active_color=P.primario,
                     active_track_color=P.foco, inactive_thumb_color=P.texto_tenue,
                     inactive_track_color=P.activo)


class Segmentado:
    def __init__(self, opciones: dict[str, str], valor: str, on_change: Callable[[str], None] | None = None,
                 fondo: str | None = None, borde: bool = True, compacto: bool = False):
        self._relleno = 9 if compacto else 12
        self.valor = valor
        self.on_change = on_change
        self._botones: dict[str, ft.Container] = {}
        self._fila = ft.Row(spacing=2, tight=True)
        self.control = ft.Container(
            content=self._fila,
            padding=3, border_radius=tema.RADIO, bgcolor=fondo or P.superficie_2,
            border=ft.Border.all(1, P.borde) if borde else None,
        )
        self.cambiar_opciones(opciones, valor)

    def cambiar_opciones(self, opciones: dict[str, str], valor: str | None = None) -> None:
        self._botones = {
            clave: ft.Container(
                content=ft.Text(rotulo, size=tema.T_PEQUENO),
                padding=ft.Padding.symmetric(horizontal=self._relleno, vertical=6), border_radius=6,
                animate=tema.ANIMACION, on_click=lambda e, k=clave: self.elegir(k),
            )
            for clave, rotulo in opciones.items()
        }
        self._fila.controls = list(self._botones.values())
        if valor in opciones:
            self.valor = valor
        elif self.valor not in opciones and opciones:
            self.valor = next(iter(opciones))
        self._pintar()

    def elegir(self, clave: str, avisar: bool = True) -> None:
        if self.control.disabled:
            return
        self.valor = clave
        self._pintar()
        refrescar(self.control)
        if avisar and self.on_change:
            self.on_change(clave)

    def _pintar(self) -> None:
        for clave, b in self._botones.items():
            activo = clave == self.valor
            b.bgcolor = P.activo if activo else None
            b.content.color = P.texto if activo else P.texto_suave
            b.content.weight = ft.FontWeight.W_500 if activo else None


class AvisoEnLinea:
    _ESTILO = {"error": (ft.Icons.ERROR_OUTLINE, P.error), "exito": (ft.Icons.CHECK_CIRCLE_OUTLINE, P.exito),
               "aviso": (ft.Icons.WARNING_AMBER_ROUNDED, P.aviso), "info": (ft.Icons.INFO_OUTLINE, P.texto_suave)}

    def __init__(self):
        self._icono = ft.Icon(ft.Icons.ERROR_OUTLINE, size=15)
        self._texto = ft.Text("", size=tema.T_MINI)
        self.control = ft.Row([self._icono, ft.Container(self._texto, expand=True)], spacing=6, visible=False,
                              vertical_alignment=ft.CrossAxisAlignment.START)

    def mostrar(self, mensaje: str, tipo: str = "error") -> None:
        icono, color = self._ESTILO[tipo]
        self._icono.icon, self._icono.color = icono, color
        self._texto.value, self._texto.color = mensaje, color
        self.control.visible = True

    def ocultar(self) -> None:
        self.control.visible = False


def tarjeta(contenido: ft.Control, padding: int | ft.Padding = 20) -> ft.Container:
    return ft.Container(content=contenido, padding=padding, bgcolor=P.superficie,
                        border_radius=tema.RADIO_TARJETA, border=ft.Border.all(1, P.borde))


def fila(rotulo: str, control: ft.Control, ancho_rotulo: int = 96) -> ft.Row:
    return ft.Row([ft.Container(texto(rotulo, tema.T_PEQUENO, P.texto_suave), width=ancho_rotulo), control],
                  vertical_alignment=ft.CrossAxisAlignment.CENTER)


def barra_progreso() -> ft.ProgressBar:
    return ft.ProgressBar(value=0, color=P.primario, bgcolor=P.activo, bar_height=4, border_radius=4)


def estado_vacio(icono, titulo: str, detalle: str) -> ft.Container:
    return ft.Container(
        padding=ft.Padding.symmetric(vertical=36), alignment=ft.Alignment(0, 0),
        content=ft.Column([
            ft.Icon(icono, size=26, color=P.texto_tenue),
            texto(titulo, tema.T_PEQUENO, P.texto_suave, ft.FontWeight.W_500),
            texto(detalle, tema.T_MINI, P.texto_tenue),
        ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
    )


def item_lista(icono, titulo: str, detalle: str, acciones: list[ft.Control]) -> ft.Container:
    caja = ft.Container(
        padding=ft.Padding.symmetric(horizontal=12, vertical=10), border_radius=tema.RADIO,
        animate=tema.ANIMACION,
        content=ft.Row([
            ft.Container(ft.Icon(icono, size=17, color=P.texto_suave), width=34, height=34,
                         border_radius=tema.RADIO, bgcolor=P.superficie_2, border=ft.Border.all(1, P.borde),
                         alignment=ft.Alignment(0, 0)),
            ft.Column([texto(titulo, tema.T_PEQUENO, peso=ft.FontWeight.W_500),
                       texto(detalle, tema.T_MINI, P.texto_tenue)], spacing=2, expand=True, tight=True),
            *acciones,
        ], spacing=12),
    )

    def hover(e):
        caja.bgcolor = P.hover if e.data in (True, "true") else None
        caja.update()
    caja.on_hover = hover
    return caja


def notch(logo_src: str, centro: ft.Control, actividad: ft.Control, derecha: ft.Control,
          ancho: int = tema.ANCHO_CONTENIDO) -> ft.Container:
    return ft.Container(
        width=ancho,
        bgcolor=P.notch,
        border_radius=ft.BorderRadius.only(bottom_left=18, bottom_right=18),
        border=ft.Border(left=ft.BorderSide(1, P.borde), right=ft.BorderSide(1, P.borde),
                         bottom=ft.BorderSide(1, P.borde)),
        padding=ft.Padding.only(left=18, right=10, top=9, bottom=9),
        content=ft.Row([
            ft.Container(expand=True, content=ft.Row([
                ft.Image(src=logo_src, width=22, height=22, fit=ft.BoxFit.CONTAIN),
                texto("Zaynix", tema.T_NORMAL, peso=ft.FontWeight.W_600),
            ], spacing=10)),
            centro,
            ft.Container(expand=True, content=ft.Row([actividad, derecha], spacing=12,
                                                     alignment=ft.MainAxisAlignment.END)),
        ]),
    )


def vista_previa(miniatura: ft.Image, titulo: ft.Text, detalle: ft.Text) -> ft.Container:
    return ft.Container(
        padding=10, border_radius=tema.RADIO, bgcolor=P.superficie_2, border=ft.Border.all(1, P.borde),
        content=ft.Row([
            ft.Container(miniatura, width=112, height=63, border_radius=6, bgcolor=P.activo,
                         clip_behavior=ft.ClipBehavior.ANTI_ALIAS),
            ft.Column([titulo, detalle], spacing=4, expand=True, tight=True),
        ], spacing=14),
    )


class PanelLateral:
    def __init__(self, titulo: str, contenido: ft.Control, pie: ft.Control | None = None, ancho: int = 440):
        self.ancho = ancho
        self.velo = ft.Container(left=0, top=0, right=0, bottom=0, bgcolor="#000000,0.55", visible=False,
                                 on_click=lambda e: self.cerrar())
        self.panel = ft.Container(
            top=0, bottom=0, right=-ancho - 2, width=ancho,
            animate_position=ft.Animation(220, ft.AnimationCurve.EASE_OUT_CUBIC),
            bgcolor=P.superficie, border=ft.Border(left=ft.BorderSide(1, P.borde)),
            content=ft.Column([
                ft.Container(ft.Row([texto(titulo, 16, peso=ft.FontWeight.W_600, expand=True),
                                     boton_icono(ft.Icons.CLOSE_ROUNDED, "Cerrar", lambda e: self.cerrar())]),
                             padding=ft.Padding.only(left=20, right=10, top=14, bottom=10)),
                separador(),
                ft.Column([ft.Container(contenido, padding=ft.Padding.only(left=24, right=24, top=20, bottom=24))],
                          scroll=ft.ScrollMode.AUTO, expand=True),
                *([separador(), ft.Container(pie, padding=ft.Padding.symmetric(horizontal=24, vertical=14))]
                  if pie else []),
            ], spacing=0, expand=True),
        )
        self.capas = [self.velo, self.panel]

    def abrir(self, e=None) -> None:
        self.velo.visible = True
        self.panel.right = 0
        self.panel.update()
        self.velo.update()

    def cerrar(self) -> None:
        self.velo.visible = False
        self.panel.right = -self.ancho - 2
        self.panel.update()
        self.velo.update()


class ListaRecientes:
    def __init__(self, titulo_vacio: str, detalle_vacio: str, icono_item):
        self.icono_item = icono_item
        self.contador = texto("", tema.T_MINI, P.texto_tenue)
        self.boton_limpiar = ft.TextButton("Limpiar", visible=False,
                                           style=ft.ButtonStyle(color=P.texto_tenue, shape=tema.forma(),
                                                                padding=ft.Padding.symmetric(horizontal=8)))
        self.lista = ft.Column(spacing=2)
        self.vacio = estado_vacio(ft.Icons.HISTORY_ROUNDED, titulo_vacio, detalle_vacio)
        self.control = ft.Column(spacing=10, controls=[
            ft.Row([ft.Row([etiqueta("Recientes"), self.contador], spacing=8), self.boton_limpiar],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN, height=28),
            tarjeta(ft.Column([self.vacio, self.lista], spacing=0), padding=6),
        ])

    def agregar(self, titulo: str, detalle: str, on_abrir: Callable, on_carpeta: Callable,
                al_final: bool = False) -> None:
        item = item_lista(self.icono_item, titulo, detalle, [
            boton_icono(ft.Icons.PLAY_ARROW_ROUNDED, "Reproducir", on_abrir),
            boton_icono(ft.Icons.FOLDER_OPEN_OUTLINED, "Mostrar en carpeta", on_carpeta),
        ])
        if al_final:
            self.lista.controls.append(item)
        else:
            self.lista.controls.insert(0, item)
        self._actualizar()

    def vaciar(self) -> None:
        self.lista.controls.clear()
        self._actualizar()

    def _actualizar(self) -> None:
        n = len(self.lista.controls)
        self.vacio.visible = n == 0
        self.boton_limpiar.visible = n > 0
        self.contador.value = f"{n}" if n else ""


def seccion_ajustes(titulo: str, filas: list[ft.Control]) -> ft.Column:
    return ft.Column([
        ft.Container(etiqueta(titulo), padding=ft.Padding.only(left=4)),
        ft.Container(
            content=ft.Column(filas, spacing=16),
            padding=16, border_radius=tema.RADIO_TARJETA,
            bgcolor=P.superficie_2, border=ft.Border.all(1, P.borde),
        ),
    ], spacing=10)


def ajuste(titulo: str, descripcion: str | None, control: ft.Control) -> ft.Row:
    return ft.Row([
        ft.Column([texto(titulo, tema.T_PEQUENO, peso=ft.FontWeight.W_500),
                   *([texto(descripcion, tema.T_MINI, P.texto_tenue, cortar=False)] if descripcion else [])],
                  spacing=2, expand=True, tight=True),
        control,
    ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12)
