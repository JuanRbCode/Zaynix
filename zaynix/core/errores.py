from __future__ import annotations


class Cancelado(Exception):
    pass


_SIN_RED = ("getaddrinfo", "failed to resolve", "name or service not known", "network is unreachable",
            "no address associated", "timed out", "connection reset", "connection aborted",
            "unable to connect", "winerror 10060", "winerror 11001", "winerror 10051", "temporary failure")


def traducir_error(ex: BaseException) -> str:
    m = str(ex)
    b = m.lower()
    if any(k in b for k in _SIN_RED):
        return "Sin conexión a internet. Revisa tu red e inténtalo de nuevo."
    if any(k in b for k in ("unable to extract", "nsig", "signature", "player response", "requested format is not")):
        return "El sitio cambió su funcionamiento. Actualiza el motor de descargas en Ajustes e inténtalo de nuevo."
    if "unsupported url" in b:
        return "Este enlace no es compatible con Zaynix."
    if any(k in b for k in ("private video", "video unavailable", "not available", "has been removed")):
        return "El contenido no está disponible o es privado."
    if "sign in to confirm" in b:
        return "El sitio pide iniciar sesión para este contenido (restricción de edad o verificación)."
    if "http error 404" in b:
        return "No se encontró el contenido (error 404). Revisa el enlace."
    if "http error 403" in b or "http error 429" in b:
        return "El sitio rechazó la descarga temporalmente. Inténtalo de nuevo en unos minutos."
    if "no space left" in b:
        return "No hay espacio suficiente en el disco."
    if "permission denied" in b or "winerror 5" in b:
        return "Sin permiso para escribir en la carpeta de destino. Elige otra carpeta."
    detalle = m.replace("ERROR: ", "").strip().splitlines()[0] if m.strip() else type(ex).__name__
    return f"No se pudo completar: {detalle[:160]}"
