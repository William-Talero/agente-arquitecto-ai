"""Línea base de **estándares vigentes (GA) de Microsoft**.

Capa de dominio pura. Fija el punto de partida sobre qué es *actual* y qué está
*retirado o en preview*, para que el asesor nunca recomiende tecnología obsoleta.

Es deliberadamente **una línea base, no la verdad final**: la fuente autoritativa
sigue siendo Microsoft Learn en tiempo real (herramienta nativa MCP). Los agentes
deben re-verificar el estado (GA / Preview / retirado) antes de recomendar.
"""
from __future__ import annotations

# Fecha de la última revisión manual de esta línea base contra Microsoft Learn.
REVISADO = "2026-04"

DOC_GA_FOUNDRY = "https://learn.microsoft.com/azure/foundry/concepts/general-availability"

# Cada entrada: qué usar hoy (GA), qué evitar, y por qué.
ESTANDARES_VIGENTES: list[dict] = [
    {
        "id": "agentes",
        "area": "Frameworks de agentes",
        "vigente": "Microsoft Agent Framework (GA)",
        "detalle": (
            "Sucesor directo y unificado de Semantic Kernel y AutoGen, creado por los mismos "
            "equipos. Aporta agentes, Harness Agent, workflows con grafo, sesiones "
            "(AgentSession), context providers, middleware y telemetría OpenTelemetry."
        ),
        "evitar": [
            "Semantic Kernel para desarrollo nuevo (migrar a Agent Framework)",
            "AutoGen para desarrollo nuevo (migrar a Agent Framework)",
            "Workflows del portal de Foundry: preview y en retiro el 1-dic-2026",
        ],
        "url": "https://learn.microsoft.com/agent-framework/overview/",
    },
    {
        "id": "plataforma",
        "area": "Plataforma de IA",
        "vigente": "Microsoft Foundry (antes Azure AI Foundry) · Foundry Agent Service (GA)",
        "detalle": (
            "Agentes (core), herramientas, toolboxes, evaluaciones, fine-tuning y tracing de "
            "prompt/hosted agents están GA. Foundry Hosted Agents está GA. Foundry IQ "
            "(Knowledge) es GA a nivel de API y preview en portal."
        ),
        "evitar": [
            "Azure OpenAI Assistants API (migrar a Foundry Agent Service)",
            "Depender de features en Preview para cargas productivas sin excepción aprobada",
        ],
        "url": DOC_GA_FOUNDRY,
    },
    {
        "id": "interoperabilidad",
        "area": "Interoperabilidad de herramientas y agentes",
        "vigente": "Model Context Protocol (MCP) para herramientas · A2A para agente-a-agente",
        "detalle": (
            "MCP es el estándar para exponer y consumir herramientas (incluido Microsoft Learn "
            "MCP). Agent Framework consume MCP hospedado y local; Foundry expone herramientas "
            "MCP con aprobación configurable."
        ),
        "evitar": ["Integraciones de herramientas propietarias sin contrato ni esquema"],
        "url": "https://learn.microsoft.com/agent-framework/agents/tools/hosted-mcp-tools",
    },
    {
        "id": "identidad",
        "area": "Identidad y secretos",
        "vigente": "Microsoft Entra ID con identidades administradas y RBAC (sin claves)",
        "detalle": (
            "Autenticación con DefaultAzureCredential/identidad administrada, "
            "`disableLocalAuth` en los recursos y secretos en Key Vault con rotación."
        ),
        "evitar": [
            "Claves de API embebidas o en variables de entorno de larga vida",
            "Service principals con secretos cuando hay identidad administrada disponible",
        ],
        "url": "https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry",
    },
    {
        "id": "iac",
        "area": "Infraestructura como código",
        "vigente": "Bicep o Terraform con Azure Verified Modules (AVM)",
        "detalle": (
            "AVM son los módulos verificados por Microsoft, alineados al Well-Architected "
            "Framework, con soporte y versionado. Despliegue por pipelines con validación "
            "what-if/plan."
        ),
        "evitar": ["Plantillas ARM JSON escritas a mano para desarrollo nuevo"],
        "url": "https://azure.github.io/Azure-Verified-Modules/",
    },
    {
        "id": "observabilidad",
        "area": "Observabilidad y evaluación",
        "vigente": "OpenTelemetry + Foundry Observability (tracing, evaluaciones, red teaming)",
        "detalle": (
            "Tracing GA para prompt y hosted agents, evaluaciones GA, monitoreo continuo y "
            "conversión de trazas a datasets de evaluación (preview). Exportar a Azure Monitor / "
            "Application Insights."
        ),
        "evitar": ["Desplegar agentes a producción sin evaluación ni trazas"],
        "url": "https://learn.microsoft.com/azure/foundry/observability/",
    },
    {
        "id": "ia-responsable",
        "area": "IA responsable y seguridad de contenido",
        "vigente": "Microsoft Responsible AI Standard · Azure AI Content Safety · Prompt Shields",
        "detalle": (
            "Filtros de contenido, detección de jailbreak/prompt injection, groundedness, "
            "red teaming automatizado y controles de datos según el marco de IA responsable."
        ),
        "evitar": ["Desactivar filtros de contenido sin análisis de riesgo aprobado"],
        "url": "https://learn.microsoft.com/azure/ai-foundry/responsible-use-of-ai-overview",
    },
    {
        "id": "marcos",
        "area": "Marcos de arquitectura y adopción",
        "vigente": "Cloud Adoption Framework (incl. adopción de IA) · Azure Well-Architected Framework",
        "detalle": (
            "CAF para estrategia, plan, preparación, gobierno y gestión. WAF con sus cinco "
            "pilares y la guía específica de cargas de trabajo de IA. Landing zones (incl. AI "
            "Landing Zone) como base de plataforma."
        ),
        "evitar": ["Diseñar sin landing zone ni guardarraíles de gobierno"],
        "url": "https://learn.microsoft.com/azure/well-architected/ai/",
    },
]

# Regla de comportamiento que se inyecta en las instrucciones de todos los agentes.
POLITICA_VIGENCIA = (
    "POLÍTICA DE VIGENCIA (OBLIGATORIA): asesora SIEMPRE con lo más reciente en "
    "disponibilidad general (GA) de Microsoft. Antes de recomendar un servicio, SDK, API o "
    "patrón DEBES verificar su estado actual en Microsoft Learn con microsoft_docs_search "
    "(y microsoft_docs_fetch si necesitas la página completa), porque esta línea base puede "
    f"haber quedado desactualizada (última revisión: {REVISADO}). Reglas: "
    "(1) Prioriza SIEMPRE componentes en GA; si propones algo en Preview, márcalo "
    "explícitamente como «Preview», explica el riesgo y ofrece la alternativa GA. "
    "(2) NUNCA recomiendes tecnología retirada, en deprecación o sucedida por otra: usa "
    "Microsoft Agent Framework en lugar de Semantic Kernel o AutoGen para desarrollo nuevo; "
    "Foundry Agent Service en lugar de la API de Assistants; Microsoft Foundry es el nombre "
    "actual de Azure AI Foundry; Bicep/Terraform con Azure Verified Modules en lugar de ARM "
    "JSON a mano; identidades administradas de Entra ID en lugar de claves. "
    "(3) En toda tabla comparativa de servicios o SDKs incluye una columna «Estado» con "
    "GA / Preview / Retirado y la fecha o versión de referencia. "
    "(4) Si detectas que el usuario está usando algo obsoleto, dilo de forma explícita y "
    "propón la ruta de migración oficial con su enlace de Learn. "
    "(5) Cita la versión o fecha del artículo de Learn en el que te apoyas cuando sea relevante."
)


def buscar_estandar(texto: str) -> dict | None:
    """Devuelve el estándar cuyo área o identificador coincide con el texto."""
    consulta = (texto or "").strip().lower()
    if not consulta:
        return None
    for estandar in ESTANDARES_VIGENTES:
        if estandar["id"] in consulta or consulta in estandar["id"]:
            return estandar
    for estandar in ESTANDARES_VIGENTES:
        if any(palabra in consulta for palabra in estandar["area"].lower().split() if len(palabra) > 4):
            return estandar
    return None
