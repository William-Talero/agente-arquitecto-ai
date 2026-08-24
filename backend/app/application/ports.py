"""Puertos (interfaces) de la capa de aplicación.

En la arquitectura hexagonal, la aplicación define los puertos y la
infraestructura los implementa (adaptadores). Así el caso de uso no conoce el
SDK de Foundry ni el Agent Framework.
"""
from __future__ import annotations

from typing import Protocol

from ..domain.models import Consulta, Lineamiento, RespuestaAsesor


class AsesorPort(Protocol):
    """Puerto de salida: obtiene una asesoría de un especialista."""

    async def asesorar(self, consulta: Consulta) -> RespuestaAsesor: ...

    @property
    def listo(self) -> bool: ...


class LineamientosPort(Protocol):
    """Puerto de salida: persistencia de los lineamientos propios del negocio."""

    def listar(self) -> list[Lineamiento]: ...

    def guardar(self, lineamiento: Lineamiento) -> Lineamiento: ...

    def eliminar(self, lineamiento_id: str) -> bool: ...

    @property
    def version(self) -> str:
        """Huella del estado actual; cambia cuando se agrega o elimina un documento."""
        ...
