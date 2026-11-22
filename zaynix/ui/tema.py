from __future__ import annotations

import winreg
from dataclasses import dataclass

import flet as ft


@dataclass(frozen=True)
class Paleta:
    modo: ft.ThemeMode
    fondo: str
    notch: str
    pestanas: str
    superficie: str
    superficie_2: str
    hover: str
    activo: str
    borde: str
    borde_fuerte: str
    foco: str
    texto: str
    texto_suave: str
    texto_tenue: str
    primario: str
    primario_hover: str
    sobre_primario: str
    exito: str
    aviso: str
    error: str
    logo: str


OSCURO = Paleta(
    modo=ft.ThemeMode.DARK,
    fondo="#0A0A0A",
    notch="#000000",
    pestanas="#141414",
    superficie="#111111",
    superficie_2="#161616",
    hover="#1C1C1C",
    activo="#262626",
    borde="#222222",
    borde_fuerte="#333333",
    foco="#5C5C5C",
    texto="#EDEDED",
    texto_suave="#A1A1A1",
    texto_tenue="#666666",
    primario="#FFFFFF",
    primario_hover="#D4D4D4",
    sobre_primario="#0A0A0A",
    exito="#4ADE80",
    aviso="#FBBF24",
    error="#F87171",
    logo="logo_zx_blanco.svg",
)

CLARO = Paleta(
    modo=ft.ThemeMode.LIGHT,
    fondo="#FAFAFA",
    notch="#FFFFFF",
    pestanas="#F4F4F5",
    superficie="#FFFFFF",
    superficie_2="#F7F7F8",
    hover="#F0F0F1",
    activo="#E4E4E7",
    borde="#E6E6E8",
    borde_fuerte="#D4D4D8",
    foco="#A1A1AA",
    texto="#0A0A0A",
    texto_suave="#52525B",
    texto_tenue="#8E8E96",
    primario="#0A0A0A",
    primario_hover="#2E2E2E",
    sobre_primario="#FFFFFF",
    exito="#16A34A",
    aviso="#B45309",
    error="#DC2626",
    logo="logo_zx.svg",
)

TEMAS = {"oscuro": OSCURO, "claro": CLARO}


def tema_del_sistema() -> str:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as k:
            return "claro" if winreg.QueryValueEx(k, "AppsUseLightTheme")[0] else "oscuro"
    except OSError:
        return "oscuro"


class _PaletaActiva:
    def __init__(self):
        self._actual = OSCURO

    def usar(self, nombre: str) -> None:
        self._actual = TEMAS[tema_del_sistema() if nombre == "sistema" else nombre]

    def __getattr__(self, nombre: str):
        return getattr(self._actual, nombre)


P = _PaletaActiva()

ICONO_VENTANA = "icono.ico"

RADIO = 8
RADIO_TARJETA = 12
ALTO_CONTROL = 40
ESPACIO = 16
ANCHO_CONTENIDO = 880

T_TITULO = 22
T_NORMAL = 14
T_PEQUENO = 13
T_MINI = 12

ANCHO_VENTANA, ALTO_VENTANA = 1200, 820
ANCHO_MIN, ALTO_MIN = 980, 660

ANIMACION = ft.Animation(150, ft.AnimationCurve.EASE_OUT)


def forma(radio: int = RADIO) -> ft.RoundedRectangleBorder:
    return ft.RoundedRectangleBorder(radius=radio)


def tema_global() -> ft.Theme:
    return ft.Theme(
        color_scheme_seed=P.primario,
        text_button_theme=ft.TextButtonTheme(style=ft.ButtonStyle(color=P.texto_suave, shape=forma())),
        icon_button_theme=ft.IconButtonTheme(style=ft.ButtonStyle(color=P.texto_suave, shape=forma())),
    )


def aplicar(page: ft.Page, nombre: str, icono: str | None = None) -> None:
    P.usar(nombre)
    page.title = "Zaynix"
    page.bgcolor = P.fondo
    page.theme_mode = P.modo
    page.theme = page.dark_theme = tema_global()
    page.padding = 0
    try:
        page.window.bgcolor = P.fondo
        if icono:
            page.window.icon = icono
    except AttributeError:
        pass


def tamano_ventana(page: ft.Page) -> None:
    try:
        page.window.width, page.window.height = ANCHO_VENTANA, ALTO_VENTANA
        page.window.min_width, page.window.min_height = ANCHO_MIN, ALTO_MIN
    except AttributeError:
        pass
