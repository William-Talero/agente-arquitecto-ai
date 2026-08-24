"""Modelos de dominio del Arquitecto de Soluciones AI.

Capa de dominio pura (arquitectura hexagonal): no depende de frameworks web,
de Azure ni del SDK del agente. Solo describe los conceptos del negocio: la
consulta de un cliente, la respuesta del asesor y sus artefactos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Especialista(str, Enum):
    """Especialistas del asesor, alineados al ciclo de vida de soluciones AI."""

    ESTRATEGIA = "estrategia"
    ARQUITECTURA = "arquitectura"
    IMPLEMENTACION = "implementacion"
    OPERACION = "operacion"
    CONCIERGE = "concierge"

    @property
    def titulo(self) -> str:
        return {
            Especialista.ESTRATEGIA: "Estrategia y adopción (CAF)",
            Especialista.ARQUITECTURA: "Arquitectura (Well-Architected)",
            Especialista.IMPLEMENTACION: "Implementación y desarrollo",
            Especialista.OPERACION: "Operación e IA responsable",
            Especialista.CONCIERGE: "Asesor general",
        }[self]

    @property
    def corto(self) -> str:
        """Etiqueta breve para selectores y chips de la interfaz."""
        return {
            Especialista.ESTRATEGIA: "Estrategia",
            Especialista.ARQUITECTURA: "Arquitectura",
            Especialista.IMPLEMENTACION: "Implementación",
            Especialista.OPERACION: "Operación",
            Especialista.CONCIERGE: "Asesor general",
        }[self]


AMBITO_GLOBAL = "global"


@dataclass(frozen=True)
class Adjunto:
    """Archivo adjunto a una consulta: imagen de arquitectura o archivo de texto."""

    nombre: str
    mime_type: str
    data: bytes | None = None
    texto: str | None = None

    @property
    def es_imagen(self) -> bool:
        return self.mime_type.startswith("image/") and self.data is not None


@dataclass(frozen=True)
class Lineamiento:
    """Documento de buenas prácticas o lineamientos propios del negocio.

    Personaliza las reglas de arquitectura del asesor con los estándares internos
    del cliente. El ``ambito`` es ``"global"`` (aplica a todos los especialistas)
    o el valor de un :class:`Especialista`.
    """

    id: str
    nombre: str
    ambito: str
    texto: str
    creado_en: str
    mime_type: str = "text/plain"
    categoria: str = ""
    caracteres: int = 0

    def aplica_a(self, especialista: "Especialista") -> bool:
        return self.ambito in (AMBITO_GLOBAL, especialista.value)


@dataclass(frozen=True)
class Consulta:
    """Petición de un cliente atendida por un especialista."""

    session_id: str
    mensaje: str
    especialista: Especialista
    adjuntos: tuple[Adjunto, ...] = ()


@dataclass(frozen=True)
class Cita:
    """Fuente citada por una herramienta nativa (Web o Microsoft Learn)."""

    titulo: str
    url: str
    fuente: str = "web"


@dataclass
class Paso:
    """Traza de un paso ejecutado durante la asesoría."""

    titulo: str
    detalle: str = ""


@dataclass
class RespuestaAsesor:
    """Resultado de una asesoría: texto, tarjetas visuales, citas y trazas."""

    especialista: Especialista
    texto: str
    runtime: str = "Azure AI Foundry · Prompt Agent"
    tarjetas: list[dict] = field(default_factory=list)
    citas: list[Cita] = field(default_factory=list)
    pasos: list[Paso] = field(default_factory=list)
    duracion_ms: float = 0.0
