from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from zaynix.core.config import CARPETA_DATOS

ARCHIVO = CARPETA_DATOS / "historial.json"
MAXIMO = 100


@dataclass
class Entrada:
    tipo: str
    titulo: str
    ruta: str
    detalle: str
    fecha: str

    @property
    def archivo(self) -> Path:
        return Path(self.ruta)


class Historial:
    def __init__(self):
        self._lock = threading.Lock()
        self.entradas: list[Entrada] = []
        try:
            datos = json.loads(ARCHIVO.read_text(encoding="utf-8"))
            self.entradas = [Entrada(**d) for d in datos]
        except (OSError, ValueError, TypeError):
            pass

    def de_tipo(self, tipo: str) -> list[Entrada]:
        return [e for e in self.entradas if e.tipo == tipo and e.archivo.exists()]

    def agregar(self, tipo: str, titulo: str, ruta: Path, detalle: str) -> Entrada:
        entrada = Entrada(tipo, titulo, str(ruta), detalle, datetime.now().isoformat(timespec="seconds"))
        with self._lock:
            self.entradas.insert(0, entrada)
            del self.entradas[MAXIMO:]
            self._guardar()
        return entrada

    def limpiar(self, tipo: str) -> None:
        with self._lock:
            self.entradas = [e for e in self.entradas if e.tipo != tipo]
            self._guardar()

    def _guardar(self) -> None:
        ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
        ARCHIVO.write_text(json.dumps([asdict(e) for e in self.entradas], indent=1, ensure_ascii=False),
                           encoding="utf-8")


def fecha_corta(iso: str) -> str:
    try:
        f = datetime.fromisoformat(iso)
    except ValueError:
        return ""
    hoy = datetime.now().date()
    if f.date() == hoy:
        return f"Hoy {f:%H:%M}"
    if (hoy - f.date()).days == 1:
        return f"Ayer {f:%H:%M}"
    return f"{f:%d/%m/%Y}"
