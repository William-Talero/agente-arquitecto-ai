"""Caso de uso: gestionar los **lineamientos propios del negocio**.

Los documentos que sube el cliente (estándares internos, políticas de nube,
convenciones de nomenclatura, catálogos de servicios aprobados…) se convierten en
un bloque de contexto que se inyecta al especialista correspondiente, de forma que
sus recomendaciones queden alineadas a las reglas de la organización.
"""
from __future__ import annotations

from ..domain.models import AMBITO_GLOBAL, Especialista, Lineamiento
from .ports import LineamientosPort

_ENCABEZADO = (
    "LINEAMIENTOS PROPIOS DEL NEGOCIO (contexto interno del cliente). Estas son las reglas, "
    "estándares y buenas prácticas de la organización. Aplícalas como restricciones de diseño "
    "en TODAS tus recomendaciones y menciona explícitamente cuáles aplicaste. Si un lineamiento "
    "contradice una práctica oficial de Microsoft en materia de seguridad, cumplimiento o IA "
    "responsable, NO lo apliques en silencio: señala el conflicto, explica el riesgo y propone "
    "la alternativa alineada a Microsoft. En lo demás, los lineamientos internos tienen "
    "precedencia sobre las recomendaciones genéricas."
)


class LineamientosService:
    def __init__(self, repositorio: LineamientosPort, presupuesto_chars: int = 12000) -> None:
        self._repo = repositorio
        self._presupuesto = presupuesto_chars

    def listar(self, ambito: str | None = None) -> list[Lineamiento]:
        items = self._repo.listar()
        if ambito:
            return [l for l in items if l.ambito == ambito]
        return items

    def agregar(self, lineamiento: Lineamiento) -> Lineamiento:
        return self._repo.guardar(lineamiento)

    def eliminar(self, lineamiento_id: str) -> bool:
        return self._repo.eliminar(lineamiento_id)

    @property
    def version(self) -> str:
        return self._repo.version

    def para_especialista(self, especialista: Especialista) -> list[Lineamiento]:
        """Lineamientos globales primero, luego los específicos del especialista."""
        aplicables = [l for l in self._repo.listar() if l.aplica_a(especialista)]
        return sorted(aplicables, key=lambda l: 0 if l.ambito == AMBITO_GLOBAL else 1)

    def contexto(self, especialista: Especialista) -> str:
        """Bloque de texto listo para inyectar en el prompt del especialista."""
        aplicables = self.para_especialista(especialista)
        if not aplicables:
            return ""
        partes = [_ENCABEZADO]
        restante = self._presupuesto
        for item in aplicables:
            if restante <= 0:
                break
            cuerpo = item.texto[:restante]
            restante -= len(cuerpo)
            etiqueta = "todos los especialistas" if item.ambito == AMBITO_GLOBAL else item.ambito
            categoria = f" · {item.categoria}" if item.categoria else ""
            partes.append(f"### {item.nombre} (ámbito: {etiqueta}{categoria})\n{cuerpo}")
        return "\n\n".join(partes)

    def resumen(self, especialista: Especialista) -> list[dict]:
        """Metadatos de los lineamientos aplicados, para trazabilidad en la UI."""
        return [
            {"id": l.id, "nombre": l.nombre, "ambito": l.ambito, "categoria": l.categoria}
            for l in self.para_especialista(especialista)
        ]
