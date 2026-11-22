# Licencias

## Zaynix

Copyright © 2026 JuanRbCode.

Zaynix es software libre: puedes redistribuirlo y modificarlo según la [Licencia Pública General de GNU](LICENSE), versión 3 o, a tu elección, cualquier versión posterior. Se distribuye sin ninguna garantía. El nombre y el logo tienen [reglas propias](MARCA.md).

Las versiones hasta la 0.7.1 se publicaron con licencia MIT y la conservan.

Código fuente de cada versión: https://github.com/JuanRbCode/Zaynix/tags

## Componentes incluidos en el instalador

| Componente | Licencia | Código fuente |
|---|---|---|
| FFmpeg (compilación "essentials" de gyan.dev) | GPL-3.0-or-later | https://ffmpeg.org/releases/ y https://www.gyan.dev/ffmpeg/builds/ |
| mutagen | GPL-2.0-or-later | https://github.com/quodlibet/mutagen |
| yt-dlp | Unlicense | https://github.com/yt-dlp/yt-dlp |
| yt-dlp-ejs | Unlicense, MIT e ISC | https://github.com/yt-dlp/ejs |
| Deno | MIT | https://github.com/denoland/deno |
| Flet | Apache-2.0 | https://github.com/flet-dev/flet |
| Flutter | BSD-3-Clause | https://github.com/flutter/flutter |
| imageio-ffmpeg | BSD-2-Clause | https://github.com/imageio/imageio-ffmpeg |
| Python | PSF-2.0 | https://www.python.org/downloads/source/ |

El instalador copia los textos completos de las librerías de Python, incluidas las indirectas, en la carpeta `licencias` del programa. Los avisos de Flutter van dentro de `data\flutter_assets`.

FFmpeg se ejecuta como un programa independiente y no se ha modificado. La versión exacta y sus opciones de compilación están en `licencias\ffmpeg-version.txt`.

¿No encuentras el código fuente de algún componente? [Abre un aviso](https://github.com/JuanRbCode/Zaynix/issues/new).
