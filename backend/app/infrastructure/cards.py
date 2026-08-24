"""Emisión de tarjetas estructuradas durante una asesoría.

Las herramientas locales y el adaptador acumulan tarjetas en un ``ContextVar``
que el caso de uso recolecta al final de cada ejecución para entregarlas al
frontend, que las pinta con gráficas y componentes shadcn.
"""
from __future__ import annotations

import contextvars

from .. import metrics

_coleccion: contextvars.ContextVar = contextvars.ContextVar("tarjetas", default=None)


def iniciar() -> list[dict]:
    bucket: list[dict] = []
    _coleccion.set(bucket)
    return bucket


def emitir(card: dict) -> None:
    bucket = _coleccion.get()
    if bucket is not None:
        bucket.append(card)
        metrics.CARDS_EMITTED.labels(card.get("tipo", "desconocida")).inc()


def tipos_emitidos() -> set[str]:
    bucket = _coleccion.get() or []
    return {c.get("tipo", "") for c in bucket}
