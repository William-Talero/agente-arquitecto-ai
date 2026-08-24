"""Controladores HTTP (capa de interfaces).

Traducen las peticiones/respuestas HTTP a/desde el caso de uso de aplicación.
No contienen lógica de negocio ni detalles de infraestructura.
"""
from __future__ import annotations

import base64
import binascii
import logging

from fastapi import APIRouter, HTTPException

from ..application.asesoria_service import AsesoriaService
from ..application.lineamientos_service import LineamientosService
from ..domain.estandares import ESTANDARES_VIGENTES, REVISADO
from ..domain.knowledge import CICLO_VIDA, ESPECIALISTAS, FASES_CAF, PILARES_WAF
from ..domain.models import AMBITO_GLOBAL, Adjunto, Especialista, RespuestaAsesor
from ..infrastructure.lineamientos_repo import nuevo_lineamiento
from .. import metrics
from .schemas import (
    AttachmentDTO,
    ChatRequest,
    ChatResponse,
    CitaDTO,
    LineamientoCrearDTO,
    LineamientoDTO,
    LineamientosResponse,
    PasoDTO,
)

log = logging.getLogger("arqai.http")

MAX_IMAGEN_BYTES = 12 * 1024 * 1024

AMBITOS = [{"id": AMBITO_GLOBAL, "nombre": "Todos los especialistas", "corto": "Todos"}] + [
    {"id": e.value, "nombre": e.titulo, "corto": e.corto} for e in Especialista
]


def crear_router(obtener_servicio, obtener_lineamientos=None) -> APIRouter:
    router = APIRouter(prefix="/api")

    def _lineamientos() -> LineamientosService:
        servicio = obtener_lineamientos() if obtener_lineamientos else None
        if servicio is None:
            raise HTTPException(status_code=503, detail="Gestión de lineamientos no disponible.")
        return servicio

    @router.get("/health")
    async def health() -> dict:
        servicio = obtener_servicio()
        return {"status": "ok", "advisor_ready": bool(servicio and servicio.listo)}

    @router.get("/catalogo")
    async def catalogo() -> dict:
        return {
            "especialistas": list(ESPECIALISTAS.values()),
            "fases_caf": FASES_CAF,
            "pilares_waf": PILARES_WAF,
            "ciclo_vida": CICLO_VIDA,
            "estandares": ESTANDARES_VIGENTES,
            "estandares_revisado": REVISADO,
        }

    @router.get("/lineamientos", response_model=LineamientosResponse)
    async def listar_lineamientos() -> LineamientosResponse:
        items = _lineamientos().listar()
        return LineamientosResponse(
            ambitos=AMBITOS,
            lineamientos=[_a_lineamiento_dto(l) for l in items],
        )

    @router.post("/lineamientos", response_model=LineamientoDTO, status_code=201)
    async def crear_lineamiento(req: LineamientoCrearDTO) -> LineamientoDTO:
        if not req.texto.strip():
            raise HTTPException(status_code=400, detail="El documento está vacío.")
        if req.ambito not in {a["id"] for a in AMBITOS}:
            raise HTTPException(status_code=400, detail=f"Ámbito no válido: {req.ambito}")
        creado = _lineamientos().agregar(
            nuevo_lineamiento(
                nombre=req.nombre,
                ambito=req.ambito,
                texto=req.texto,
                mime_type=req.mime_type,
                categoria=req.categoria,
            )
        )
        metrics.LINEAMIENTOS_CARGADOS.labels(creado.ambito).inc()
        return _a_lineamiento_dto(creado)

    @router.delete("/lineamientos/{lineamiento_id}", status_code=204)
    async def eliminar_lineamiento(lineamiento_id: str) -> None:
        if not _lineamientos().eliminar(lineamiento_id):
            raise HTTPException(status_code=404, detail="Lineamiento no encontrado.")

    @router.post("/chat", response_model=ChatResponse)
    async def chat(req: ChatRequest) -> ChatResponse:
        servicio: AsesoriaService | None = obtener_servicio()
        if servicio is None or not servicio.listo:
            raise HTTPException(
                status_code=503,
                detail="El asesor no está disponible. Verifica 'az login' y FOUNDRY_PROJECT_ENDPOINT.",
            )
        adjuntos = _a_adjuntos(req.attachments)
        if not req.message.strip() and not adjuntos:
            raise HTTPException(status_code=400, detail="Escribe una consulta o adjunta un archivo.")
        mensaje = req.message.strip() or "Evalúa la arquitectura adjunta según el Well-Architected Framework y las mejores prácticas de Microsoft."
        especialista = servicio.especialista_para(mensaje)
        with metrics.CHAT_LATENCY.labels(especialista.value).time():
            try:
                respuesta = await servicio.responder(req.session_id, mensaje, adjuntos)
            except Exception as exc:  # noqa: BLE001
                metrics.CHAT_REQUESTS.labels(especialista.value, "error").inc()
                log.exception("Error en la asesoría: %s", exc)
                raise HTTPException(status_code=500, detail=f"Error al generar la asesoría: {exc}") from exc
        metrics.CHAT_REQUESTS.labels(respuesta.especialista.value, "ok").inc()
        return _a_dto(respuesta)

    return router


def _a_lineamiento_dto(l) -> LineamientoDTO:
    return LineamientoDTO(
        id=l.id,
        nombre=l.nombre,
        ambito=l.ambito,
        categoria=l.categoria,
        caracteres=l.caracteres,
        creado_en=l.creado_en,
        mime_type=l.mime_type,
    )


def _a_adjuntos(attachments: list[AttachmentDTO]) -> tuple[Adjunto, ...]:
    adjuntos: list[Adjunto] = []
    for a in attachments:
        if a.mime_type.startswith("image/") and a.data_base64:
            try:
                datos = base64.b64decode(a.data_base64, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise HTTPException(status_code=400, detail=f"Imagen inválida: {a.name}") from exc
            if len(datos) > MAX_IMAGEN_BYTES:
                raise HTTPException(status_code=413, detail=f"La imagen '{a.name}' supera 12 MB.")
            adjuntos.append(Adjunto(nombre=a.name, mime_type=a.mime_type, data=datos))
        elif a.text:
            adjuntos.append(Adjunto(nombre=a.name, mime_type=a.mime_type or "text/plain", texto=a.text))
    return tuple(adjuntos)


def _a_dto(r: RespuestaAsesor) -> ChatResponse:
    return ChatResponse(
        especialista=r.especialista.value,
        especialista_titulo=r.especialista.titulo,
        runtime=r.runtime,
        texto=r.texto,
        tarjetas=r.tarjetas,
        citas=[CitaDTO(titulo=c.titulo, url=c.url, fuente=c.fuente) for c in r.citas],
        pasos=[PasoDTO(titulo=p.titulo, detalle=p.detalle) for p in r.pasos],
        duracion_ms=round(r.duracion_ms, 1),
    )
