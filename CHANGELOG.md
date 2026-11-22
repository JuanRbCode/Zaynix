# Historial de versiones

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versiones según [SemVer](https://semver.org/lang/es/).

## [0.7.0] - 2026-11-21

### Añadido
- Aviso de nueva versión dentro de la app (notificación flotante y punto en Ajustes), consultando `version.json` del sitio web cada 6 horas.
- Enlaces a sitio web, novedades, licencias y reporte de problemas en "Acerca de".
- Registro de errores en `%APPDATA%\Zaynix\zaynix.log`.

### Corregido
- La app se bloqueaba al pulsar "Reportar un problema".
- Distribución de los botones de "Acerca de".

## [0.6.0] - 2026-11-21

### Añadido
- Sección "Acerca de" en Ajustes con búsqueda de nuevas versiones de Zaynix, novedades, licencias y reporte de problemas.
- Suite de pruebas automáticas (pytest) en `tests/`.

### Cambiado
- El motor yt-dlp se actualiza solo en segundo plano, sin intervención del usuario.

### Corregido
- Error al cambiar el formato o la calidad predeterminados desde Ajustes estando en la pestaña Convertir.
- Se ofrecían resoluciones que el video no tenía.

## [0.5.0] - 2026-11-21

### Añadido
- Tema claro y tema "Sistema" (sigue el modo de Windows). Se cambia al instante desde Ajustes.
- Actualización automática del motor yt-dlp desde GitHub, con verificación de firma SHA-256 y botón "Buscar actualizaciones".
- Deno como motor de JavaScript para YouTube (más formatos y menos fallos).
- Atajos de teclado: Ctrl+V pega y analiza, Ctrl+1/Ctrl+2 cambian de sección, Ctrl+O agrega archivos, Ctrl+, abre Ajustes, Esc lo cierra.

### Cambiado
- El contenido pasa por debajo de la barra superior al desplazarse.
- Mensaje claro cuando un sitio cambia y hace falta actualizar el motor.

## [0.4.0] - 2026-11-21

### Añadido
- Descarga en MP3, M4A, WAV, FLAC, OGG, OPUS y MP4.
- Selector de resolución para MP4 con las calidades reales del video (hasta 4K).
- Vista previa del enlace: miniatura, título, autor, duración y resolución máxima.
- Conversión a MP4 y archivos de video como entrada.
- Formato de descarga predeterminado en Ajustes.

### Cambiado
- Barra superior del mismo ancho que el contenido: logo a la izquierda, pestañas al centro, ajustes a la derecha.
- Ajustes agrupados en tarjetas por sección.

## [0.3.0] - 2026-11-21

### Añadido
- Historial persistente de descargas y conversiones, con opción de limpiar.
- Carpeta de conversiones propia y opción "Guardar junto al original".
- Ruta real de destino visible en la sección Convertir.
- README, licencia MIT y términos de uso.

### Cambiado
- Ventana y contenido más anchos.
- Panel de ajustes más ancho, con la barra de desplazamiento pegada al borde.
- Nombres más claros: "Carpeta de descargas" y "Carpeta de conversiones".

## [0.2.0] - 2026-11-21

### Añadido
- Sección Convertir (MP3, WAV, FLAC, M4A, OGG, OPUS).
- Navegación tipo notch y panel de ajustes lateral.
- Mensajes de error debajo del campo (enlace inválido, sin conexión, contenido privado…).
- Icono propio en la ventana y la barra de tareas.

### Cambiado
- Tema oscuro en negro y blanco.

## [0.1.0] - 2026-11-21

### Añadido
- Primera versión: descarga de enlaces a MP3 con yt-dlp y ffmpeg.
