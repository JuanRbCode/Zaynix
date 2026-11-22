# Zaynix

Aplicación de escritorio para Windows que descarga audio desde enlaces (YouTube, SoundCloud y cientos de sitios más) y lo guarda como MP3, y que convierte archivos de audio entre formatos.

Gratuita y de código abierto.

## Funciones

- **Descargar**: pega un enlace y obtén un MP3 (128–320 kbps) con título, artista y portada incrustados. Soporta playlists completas.
- **Convertir**: transforma archivos locales a MP3, WAV, FLAC, M4A, OGG u OPUS, en lote.
- **Recientes**: historial persistente de descargas y conversiones.
- **Ajustes**: carpetas de destino, calidad predeterminada, portada, tema.

## Requisitos

- Windows 10/11
- Python 3.12 o superior

ffmpeg viene incluido (paquete `imageio-ffmpeg`), no hay que instalarlo aparte.

## Instalación

```powershell
git clone https://github.com/JuanRbCode/Zaynix.git
cd Zaynix
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

## Uso

```powershell
.venv\Scripts\python main.py
```

O doble clic en `Zaynix.bat`.

Modo desarrollo (se recarga al guardar): `.venv\Scripts\flet run -r main.py`, o `Ctrl+Shift+B` en VS Code.

## Pruebas

```powershell
.venv\Scripts\python -m pip install pytest
.venv\Scripts\python -m pytest              # todas
.venv\Scripts\python -m pytest -m "not red" # sin internet
```

## Ramas

- `main`: versiones publicadas. Cada versión lleva su etiqueta (`v0.6.0`).
- `develop`: desarrollo diario. Se fusiona en `main` al publicar.

## Estructura

```
zaynix/
├── core/            Lógica sin interfaz
│   ├── descargador.py   Enlace → MP3 (yt-dlp + ffmpeg)
│   ├── conversor.py     Conversión entre formatos (ffmpeg)
│   ├── config.py        Ajustes del usuario y versión
│   ├── historial.py     Historial persistente
│   ├── errores.py       Mensajes de error legibles
│   └── ffmpeg.py        Ubicación de ffmpeg
├── controladores/   Conectan cada vista con el núcleo
├── ui/
│   ├── tema.py          Colores, tamaños y tipografía
│   ├── componentes.py   Piezas reutilizables
│   ├── shell.py         Notch de navegación y panel de ajustes
│   └── vistas/          Pantallas: descargar, convertir, ajustes
└── app.py           Arranque
assets/              Logo e icono
tools/               Scripts auxiliares (generar_icono.py)
```

Los ajustes y el historial se guardan en `%APPDATA%\Zaynix\`.

## Compilar un ejecutable

```powershell
.venv\Scripts\flet build windows
```

## Uso responsable

Zaynix es una herramienta. Eres responsable de descargar solo contenido que te pertenezca, que sea de dominio público, con licencia libre o cuya descarga esté permitida por su autor y por los términos del sitio. Lee [TERMINOS.md](TERMINOS.md).

## Licencia

Código bajo licencia [MIT](LICENSE).

Dependencias de terceros, cada una con su propia licencia:

| Componente | Licencia |
|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Unlicense |
| [Flet](https://github.com/flet-dev/flet) | Apache 2.0 |
| [FFmpeg](https://ffmpeg.org) (vía imageio-ffmpeg) | GPL/LGPL |
| [Pillow](https://github.com/python-pillow/Pillow) | MIT-CMU |

Si distribuyes un ejecutable que incluya FFmpeg, debes respetar su licencia (incluir el aviso y un enlace a su código fuente).
