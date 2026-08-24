"""Enrutador de especialistas basado en palabras clave.

Decide qué especialista atiende cada consulta. Es determinista y explicable,
lo que facilita las pruebas y la trazabilidad.
"""
from __future__ import annotations

from ..domain.models import Especialista

_REGLAS: list[tuple[Especialista, tuple[str, ...]]] = [
    (
        Especialista.ESTRATEGIA,
        (
            "caf", "cloud adoption", "adopción", "adopcion", "estrategia", "negocio",
            "caso de uso", "roadmap", "hoja de ruta", "madurez", "gobierno", "gobernanza",
            "landing zone", "zona de aterrizaje", "presupuesto", "valor", "motivación",
            "lineamiento", "lineamientos", "política interna", "politica interna", "normativa",
        ),
    ),
    (
        Especialista.ARQUITECTURA,
        (
            "waf", "well-architected", "well architected", "arquitectura", "pilar",
            "confiabilidad", "resiliencia", "seguridad", "costos", "costo", "rendimiento",
            "latencia", "escala", "diseño", "diagrama", "referencia", "topología", "red",
            "genera una arquitectura", "genérame", "generame", "dibuja", "diséñame", "diseña",
            "draw.io", "drawio", "landing zone", "ai landing zone", "diagrama de arquitectura",
        ),
    ),
    (
        Especialista.IMPLEMENTACION,
        (
            "rag", "agente", "agentes", "prompt", "orquestación", "orquestacion", "herramienta",
            "función", "funcion", "código", "codigo", "implementar", "desarrollo", "sdk",
            "embedding", "vector", "chunk", "índice", "indice", "evaluación", "evaluacion",
            "fine-tuning", "foundry", "agent framework", "mcp",
            "semantic kernel", "autogen", "assistants", "obsoleto", "obsoleta", "deprecado",
            "deprecada", "retirado", "migrar", "migración", "migracion", "actualizar", "upgrade",
            "disponibilidad general", "preview", "vigente", "última versión", "ultima version",
        ),
    ),
    (
        Especialista.OPERACION,
        (
            "operación", "operacion", "llmops", "mlops", "observabilidad", "monitoreo",
            "monitorización", "telemetría", "telemetria", "responsable", "responsible ai",
            "content safety", "seguridad de contenido", "cumplimiento", "producción", "produccion",
            "incidente", "alerta", "drift", "reentrenamiento",
        ),
    ),
]


class EspecialistaRouter:
    """Selecciona el especialista según el contenido del mensaje."""

    def enrutar(self, mensaje: str) -> Especialista:
        texto = (mensaje or "").lower()
        puntajes: dict[Especialista, int] = {}
        for especialista, claves in _REGLAS:
            puntajes[especialista] = sum(1 for clave in claves if clave in texto)
        mejor = max(puntajes, key=puntajes.get)
        if puntajes[mejor] == 0:
            return Especialista.CONCIERGE
        return mejor
