"""Punto de composición de la aplicación (arquitectura hexagonal).

Ensambla dominio, aplicación e infraestructura, y expone la API HTTP con FastAPI.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from . import metrics
from .application.asesoria_service import AsesoriaService
from .application.lineamientos_service import LineamientosService
from .config import settings
from .infrastructure.foundry_advisor import FoundryAdvisorAdapter
from .infrastructure.lineamientos_repo import LineamientosRepositorio
from .interfaces.http import crear_router

logging.basicConfig(level=logging.INFO)
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.identity").setLevel(logging.WARNING)
log = logging.getLogger("arqai")

_servicio: AsesoriaService | None = None
_adaptador: FoundryAdvisorAdapter | None = None
_lineamientos: LineamientosService | None = None


def _obtener_servicio() -> AsesoriaService | None:
    return _servicio


def _obtener_lineamientos() -> LineamientosService | None:
    return _lineamientos


@asynccontextmanager
async def _ciclo_vida(_: FastAPI):
    global _servicio, _adaptador, _lineamientos
    _lineamientos = LineamientosService(
        LineamientosRepositorio(), presupuesto_chars=settings.lineamientos_max_chars_prompt
    )
    try:
        _adaptador = await run_in_threadpool(FoundryAdvisorAdapter, _lineamientos)
        _servicio = AsesoriaService(_adaptador)
        metrics.ADVISOR_READY.set(1)
        log.info("Asesor inicializado correctamente.")
    except Exception as exc:  # noqa: BLE001
        _servicio = None
        metrics.ADVISOR_READY.set(0)
        log.exception("No se pudo inicializar el asesor: %s", exc)
    try:
        yield
    finally:
        if _adaptador is not None:
            await _adaptador.cerrar()


app = FastAPI(
    title="Arquitecto de Soluciones AI · Microsoft Foundry Prompt Agents",
    lifespan=_ciclo_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/metrics")
async def prometheus_metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(crear_router(_obtener_servicio, _obtener_lineamientos))

# En producción el backend sirve el SPA compilado (si existe) desde el mismo origen.
if settings.frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=settings.frontend_dist, html=True), name="frontend")
