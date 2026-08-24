"""Repositorio en disco de los **lineamientos propios del negocio**.

Adaptador del puerto :class:`LineamientosPort`. Guarda cada documento como texto
plano más un índice JSON, de modo que sobrevive a reinicios sin depender de una
base de datos. Es seguro para uso concurrente desde el servidor web.
"""
from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..config import settings
from ..domain.models import Lineamiento

log = logging.getLogger("arqai.lineamientos")

_INDICE = "indice.json"


class LineamientosRepositorio:
    def __init__(self, directorio: Path | None = None) -> None:
        self._dir = Path(directorio or settings.lineamientos_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._items: dict[str, Lineamiento] = {}
        self._version = "0"
        self._cargar()

    # -- lectura -----------------------------------------------------------
    def listar(self) -> list[Lineamiento]:
        with self._lock:
            return sorted(self._items.values(), key=lambda l: l.creado_en, reverse=True)

    @property
    def version(self) -> str:
        return self._version

    # -- escritura ---------------------------------------------------------
    def guardar(self, lineamiento: Lineamiento) -> Lineamiento:
        item = lineamiento
        if not item.id:
            item = Lineamiento(**{**lineamiento.__dict__, "id": uuid.uuid4().hex[:12]})
        with self._lock:
            self._archivo(item.id).write_text(item.texto, encoding="utf-8")
            self._items[item.id] = item
            self._persistir_indice()
        log.info("Lineamiento guardado: %s (%s)", item.nombre, item.ambito)
        return item

    def eliminar(self, lineamiento_id: str) -> bool:
        with self._lock:
            if lineamiento_id not in self._items:
                return False
            self._items.pop(lineamiento_id)
            self._archivo(lineamiento_id).unlink(missing_ok=True)
            self._persistir_indice()
        return True

    # -- internos ----------------------------------------------------------
    def _archivo(self, lineamiento_id: str) -> Path:
        return self._dir / f"{lineamiento_id}.txt"

    def _persistir_indice(self) -> None:
        datos = [
            {k: v for k, v in item.__dict__.items() if k != "texto"} for item in self._items.values()
        ]
        (self._dir / _INDICE).write_text(
            json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._version = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _cargar(self) -> None:
        indice = self._dir / _INDICE
        if not indice.exists():
            return
        try:
            datos = json.loads(indice.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            log.warning("No se pudo leer el índice de lineamientos: %s", exc)
            return
        for meta in datos if isinstance(datos, list) else []:
            archivo = self._archivo(meta.get("id", ""))
            if not archivo.exists():
                continue
            try:
                self._items[meta["id"]] = Lineamiento(
                    **{**meta, "texto": archivo.read_text(encoding="utf-8")}
                )
            except (KeyError, TypeError, OSError) as exc:
                log.warning("Lineamiento inválido en el índice: %s", exc)
        self._version = datetime.now(timezone.utc).isoformat(timespec="seconds")
        log.info("Lineamientos cargados: %d", len(self._items))


def nuevo_lineamiento(
    nombre: str, ambito: str, texto: str, mime_type: str = "text/plain", categoria: str = ""
) -> Lineamiento:
    """Construye un lineamiento normalizado y recortado al límite configurado."""
    limpio = (texto or "").strip()[: settings.lineamientos_max_chars_doc]
    return Lineamiento(
        id=uuid.uuid4().hex[:12],
        nombre=nombre.strip()[:200] or "Lineamiento",
        ambito=ambito,
        texto=limpio,
        creado_en=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        mime_type=mime_type or "text/plain",
        categoria=categoria.strip()[:80],
        caracteres=len(limpio),
    )
