"""DTOs de entrada/salida de la API HTTP (capa de interfaces)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class AttachmentDTO(BaseModel):
    name: str = Field(max_length=200)
    mime_type: str = Field(max_length=120)
    data_base64: str | None = None
    text: str | None = Field(default=None, max_length=40000)


class ChatRequest(BaseModel):
    session_id: str = Field(default="default", max_length=120)
    message: str = Field(default="", max_length=4000)
    attachments: list[AttachmentDTO] = Field(default_factory=list, max_length=6)


class CitaDTO(BaseModel):
    titulo: str
    url: str
    fuente: str


class PasoDTO(BaseModel):
    titulo: str
    detalle: str = ""


class ChatResponse(BaseModel):
    especialista: str
    especialista_titulo: str
    runtime: str
    texto: str
    tarjetas: list[dict]
    citas: list[CitaDTO]
    pasos: list[PasoDTO]
    duracion_ms: float


class LineamientoDTO(BaseModel):
    """Documento de lineamientos propios del negocio (sin el cuerpo del texto)."""

    id: str
    nombre: str
    ambito: str
    categoria: str = ""
    caracteres: int = 0
    creado_en: str
    mime_type: str = "text/plain"


class LineamientoCrearDTO(BaseModel):
    nombre: str = Field(max_length=200)
    ambito: str = Field(default="global", max_length=40)
    categoria: str = Field(default="", max_length=80)
    mime_type: str = Field(default="text/plain", max_length=120)
    texto: str = Field(max_length=200000)


class LineamientosResponse(BaseModel):
    ambitos: list[dict]
    lineamientos: list[LineamientoDTO]
