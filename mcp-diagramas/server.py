"""Servidor MCP que genera diagramas de arquitectura de Azure en formato draw.io.

Expone la generación de diagramas (con iconos oficiales de Azure, estilo de
arquitectura de referencia y estructura de AI Landing Zone) como herramientas MCP
sobre transporte **Streamable HTTP**, para conectarlo desde **Microsoft Copilot
Studio** (Tools → Add a tool → Model Context Protocol) o cualquier cliente MCP.

Reutiliza la lógica de ``backend/app/infrastructure/diagram.py`` sin duplicarla.
Ejecutar:  python server.py   →  endpoint MCP en http://127.0.0.1:8071/mcp
"""
from __future__ import annotations

import importlib.util
import os

from mcp.server.fastmcp import FastMCP

# --- Carga el generador de diagramas existente (fuente única) ---------------
_AQUI = os.path.dirname(os.path.abspath(__file__))
_CANDIDATOS = [
    os.path.join(_AQUI, "diagram.py"),  # copia local (para despliegue standalone)
    os.path.join(_AQUI, "..", "backend", "app", "infrastructure", "diagram.py"),
]
_ruta = next((p for p in _CANDIDATOS if os.path.exists(p)), None)
if _ruta is None:
    raise RuntimeError(
        "No se encontró diagram.py. Colócalo junto a server.py o mantén el repo "
        "con backend/app/infrastructure/diagram.py."
    )
_spec = importlib.util.spec_from_file_location("arqai_diagram", _ruta)
_diagram = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_diagram)  # type: ignore[union-attr]

construir_diagrama = _diagram.construir_diagrama
ICONOS: dict[str, str] = _diagram.ICONOS
PLANTILLA = _diagram.PLANTILLA_AI_LANDING_ZONE

HOST = os.getenv("MCP_HOST", "127.0.0.1")
PORT = int(os.getenv("MCP_PORT", "8071"))

mcp = FastMCP("diagramas-azure", host=HOST, port=PORT)


@mcp.tool()
def generar_diagrama_arquitectura(
    titulo: str,
    zonas: list[dict],
    conexiones: list[dict] | None = None,
) -> dict:
    """Genera un diagrama de arquitectura de Azure en formato draw.io (.drawio) con
    iconos oficiales de Azure, estilo de arquitectura de referencia de Microsoft y
    estructura basada en la Azure AI Landing Zone (CAF + Well-Architected).

    Úsala cuando el usuario pida crear, dibujar, generar o diseñar una arquitectura
    o un diagrama. Devuelve el XML .drawio listo para abrir en draw.io/diagrams.net.

    :param titulo: Título del diagrama (p. ej. "Chat RAG empresarial sobre Azure OpenAI").
    :param zonas: Lista ordenada de zonas/carriles. Cada zona es un objeto
        {"nombre": str, "servicios": [ {"id": str, "tipo": str, "nombre": str}, ... ]}.
        "tipo" debe ser una de las claves de icono válidas (usa la herramienta
        tipos_de_icono_disponibles). Ejemplos frecuentes: users, browser, front_door,
        waf, firewall, app_gateway, vnet, private_endpoint, app_service, functions,
        aks, container_apps, apim, azure_openai, ai_foundry, ai_search, content_safety,
        cosmos, azure_sql, storage, key_vault, entra_id, monitor, log_analytics.
    :param conexiones: Lista opcional de flechas entre servicios:
        {"desde": str, "hacia": str, "etiqueta": str}. "desde"/"hacia" referencian el
        "id" (o el "nombre") de un servicio ya definido en alguna zona.
    """
    spec = {"titulo": titulo, "zonas": zonas, "conexiones": conexiones or []}
    res = construir_diagrama(spec)
    return {
        "drawio_xml": res["xml"],
        "titulo": res["titulo"],
        "zonas": res["zonas"],
        "n_servicios": res["n_servicios"],
        "n_conexiones": res["n_conexiones"],
        "instrucciones": "Guarda 'drawio_xml' como archivo .drawio y ábrelo en https://app.diagrams.net.",
    }


@mcp.tool()
def tipos_de_icono_disponibles() -> list[str]:
    """Devuelve las claves de "tipo" válidas para los servicios de un diagrama.
    Úsala antes de generar_diagrama_arquitectura para elegir iconos correctos de Azure."""
    return sorted(set(ICONOS.keys()))


@mcp.tool()
def plantilla_ai_landing_zone() -> dict:
    """Devuelve una especificación de ejemplo (zonas + servicios + conexiones) de la
    Azure AI Landing Zone que puedes ajustar y pasar a generar_diagrama_arquitectura."""
    return PLANTILLA


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
