from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path

VERSION = "0.6.0"
REPOSITORIO = "JuanRbCode/zaynix"
CARPETA_DATOS = Path(os.environ.get("APPDATA", Path.home())) / "Zaynix"
ARCHIVO = CARPETA_DATOS / "config.json"
MUSICA = Path.home() / "Music" / "Zaynix"


@dataclass
class Config:
    tema: str = "oscuro"
    carpeta_descargas: str = str(MUSICA / "Descargas")
    formato_descarga: str = "mp3"
    calidad_mp3: str = "320"
    incrustar_portada: bool = True
    carpeta_conversiones: str = str(MUSICA / "Convertidos")
    junto_al_original: bool = False
    abrir_al_terminar: bool = False

    @classmethod
    def cargar(cls) -> "Config":
        try:
            datos = json.loads(ARCHIVO.read_text(encoding="utf-8"))
            validos = {f.name for f in fields(cls)}
            return cls(**{k: v for k, v in datos.items() if k in validos})
        except (OSError, ValueError, TypeError):
            return cls()

    def guardar(self) -> None:
        ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
        ARCHIVO.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
