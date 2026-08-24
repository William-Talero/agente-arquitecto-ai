"""Caso de uso principal: responder una consulta de asesoría.

Coordina el enrutamiento al especialista y la invocación del puerto de asesoría.
No conoce detalles de Foundry ni del Agent Framework (los provee el adaptador).
"""
from __future__ import annotations

from ..domain.models import Adjunto, Consulta, Especialista, RespuestaAsesor
from .ports import AsesorPort
from .router import EspecialistaRouter


class AsesoriaService:
    def __init__(self, asesor: AsesorPort, router: EspecialistaRouter | None = None) -> None:
        self._asesor = asesor
        self._router = router or EspecialistaRouter()

    @property
    def listo(self) -> bool:
        return self._asesor.listo

    async def responder(
        self, session_id: str, mensaje: str, adjuntos: tuple[Adjunto, ...] = ()
    ) -> RespuestaAsesor:
        especialista = self._elegir_especialista(mensaje, adjuntos)
        consulta = Consulta(
            session_id=session_id, mensaje=mensaje, especialista=especialista, adjuntos=adjuntos
        )
        return await self._asesor.asesorar(consulta)

    def especialista_para(self, mensaje: str) -> Especialista:
        return self._router.enrutar(mensaje)

    def _elegir_especialista(self, mensaje: str, adjuntos: tuple[Adjunto, ...]) -> Especialista:
        especialista = self._router.enrutar(mensaje)
        # Un diagrama de arquitectura sin señal temática clara lo evalúa Arquitectura.
        if especialista == Especialista.CONCIERGE and any(a.es_imagen for a in adjuntos):
            return Especialista.ARQUITECTURA
        return especialista
