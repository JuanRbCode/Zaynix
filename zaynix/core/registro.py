from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from zaynix.core.config import CARPETA_DATOS, VERSION

ARCHIVO_LOG = CARPETA_DATOS / "zaynix.log"


def _crear() -> logging.Logger:
    log = logging.getLogger("zaynix")
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    try:
        CARPETA_DATOS.mkdir(parents=True, exist_ok=True)
        manejador = RotatingFileHandler(ARCHIVO_LOG, maxBytes=1_000_000, backupCount=2, encoding="utf-8")
        manejador.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(manejador)
    except OSError:
        log.addHandler(logging.NullHandler())
    log.info("Zaynix %s iniciado", VERSION)
    return log


log = _crear()
