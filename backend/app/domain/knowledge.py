"""Base de conocimiento del dominio: CAF, WAF y ciclo de vida de soluciones AI.

Estos datos son la "knowledge" curada que el asesor usa para estructurar sus
respuestas y para pintar tarjetas en la interfaz. La fuente autoritativa en
tiempo real proviene de las herramientas nativas de Foundry (Microsoft Learn y
Web); esta base aporta el andamiaje y el vocabulario común.
"""
from __future__ import annotations

from .models import Especialista

FASES_CAF: list[dict] = [
    {
        "id": "estrategia",
        "nombre": "Estrategia",
        "objetivo": "Definir motivaciones de negocio y resultados medibles de la iniciativa de IA.",
        "actividades": [
            "Identificar motivaciones y casos de uso de mayor valor",
            "Definir resultados de negocio y KPIs",
            "Evaluar riesgos, cumplimiento y consideraciones de IA responsable",
        ],
        "entregables": ["Caso de negocio", "Mapa de casos de uso priorizados"],
    },
    {
        "id": "plan",
        "nombre": "Plan",
        "objetivo": "Traducir la estrategia en un plan de adopción accionable.",
        "actividades": [
            "Inventario de datos, modelos y capacidades",
            "Evaluar habilidades y plan de capacitación",
            "Definir hoja de ruta y backlog de adopción",
        ],
        "entregables": ["Plan de adopción de IA", "Roadmap y backlog"],
    },
    {
        "id": "preparar",
        "nombre": "Preparar (Ready)",
        "objetivo": "Construir la zona de aterrizaje y las bases de plataforma para IA.",
        "actividades": [
            "Diseñar landing zone y perímetros de red",
            "Definir gestión de identidades y secretos",
            "Establecer plataforma de datos y de IA (Foundry, AI Search)",
        ],
        "entregables": ["Landing zone", "Plataforma de datos e IA"],
    },
    {
        "id": "gobernar",
        "nombre": "Gobernar",
        "objetivo": "Administrar riesgo con guardarraíles de seguridad, costos e IA responsable.",
        "actividades": [
            "Políticas de contenido y seguridad de modelos",
            "Controles de costo y cuotas",
            "Registro de modelos y trazabilidad",
        ],
        "entregables": ["Guardarraíles y políticas", "Marco de IA responsable"],
    },
    {
        "id": "gestionar",
        "nombre": "Gestionar",
        "objetivo": "Operar la solución de IA con confiabilidad y mejora continua.",
        "actividades": [
            "Monitoreo, evaluación continua y alertas",
            "Gestión de incidentes y ciclos de reentrenamiento",
            "Optimización de costo y rendimiento",
        ],
        "entregables": ["Operación (LLMOps)", "Tablero de salud y costos"],
    },
]

PILARES_WAF: list[dict] = [
    {
        "id": "confiabilidad",
        "nombre": "Confiabilidad",
        "pregunta_clave": "¿La carga de IA se recupera de fallos y cumple sus objetivos de servicio?",
        "consideraciones_ai": [
            "Reintentos, límites de tasa y degradación elegante ante 429/timeout",
            "Redundancia multi-región y balanceo de despliegues de modelo",
            "Estrategia de respaldo si un modelo o herramienta no responde",
        ],
        "antipatrones": ["Sin control de cuotas", "Punto único de fallo en el endpoint del modelo"],
    },
    {
        "id": "seguridad",
        "nombre": "Seguridad",
        "pregunta_clave": "¿Están protegidos datos, identidades, prompts y modelos?",
        "consideraciones_ai": [
            "Identidad administrada y mínimo privilegio (sin claves)",
            "Filtros de contenido y defensa ante inyección de prompts",
            "Aislamiento de red con private endpoints y protección de datos",
        ],
        "antipatrones": ["Claves embebidas", "Datos sensibles enviados a herramientas externas sin control"],
    },
    {
        "id": "costos",
        "nombre": "Optimización de costos",
        "pregunta_clave": "¿El gasto en tokens e infraestructura es proporcional al valor?",
        "consideraciones_ai": [
            "Elegir el modelo correcto por tarea (routing por costo/calidad)",
            "Caché semántica y control de longitud de contexto",
            "Cuotas, PTU vs. consumo y presupuestos con alertas",
        ],
        "antipatrones": ["Usar el modelo más grande para todo", "Sin límites de tokens"],
    },
    {
        "id": "operacion",
        "nombre": "Excelencia operativa",
        "pregunta_clave": "¿Hay automatización, evaluación y observabilidad de extremo a extremo?",
        "consideraciones_ai": [
            "CI/CD de prompts y agentes, con evaluaciones automatizadas",
            "Trazas, métricas y evaluación continua en producción",
            "Versionado de modelos, prompts y datasets",
        ],
        "antipatrones": ["Cambios de prompt sin evaluación", "Sin trazabilidad de ejecuciones"],
    },
    {
        "id": "rendimiento",
        "nombre": "Eficiencia del rendimiento",
        "pregunta_clave": "¿La solución responde con la latencia y escala esperadas?",
        "consideraciones_ai": [
            "Streaming, paralelización y tamaño de contexto adecuado",
            "Recuperación eficiente (índices, chunking y reranking)",
            "Escalado por demanda y selección de región cercana",
        ],
        "antipatrones": ["Contexto innecesariamente grande", "Recuperación sin reranking"],
    },
]

CICLO_VIDA: list[dict] = [
    {
        "id": "caso-uso",
        "nombre": "Caso de uso y valor",
        "descripcion": "Delimitar el problema, el usuario y las métricas de éxito.",
        "practicas": ["Definir métricas de calidad", "Criterios de aceptación", "Análisis de riesgo"],
    },
    {
        "id": "datos",
        "nombre": "Datos y conocimiento",
        "descripcion": "Preparar fuentes, ingesta e indexación para grounding.",
        "practicas": ["Curación y chunking", "Índice vectorial (AI Search)", "Gobierno de datos"],
    },
    {
        "id": "diseno",
        "nombre": "Diseño y arquitectura",
        "descripcion": "Elegir patrón: RAG, agentes, orquestación y herramientas.",
        "practicas": ["Selección de patrón", "Diseño de herramientas", "Well-Architected"],
    },
    {
        "id": "desarrollo",
        "nombre": "Desarrollo",
        "descripcion": "Construir prompts, agentes y herramientas con el Agent Framework.",
        "practicas": ["Ingeniería de prompts", "Herramientas y funciones", "Guardarraíles"],
    },
    {
        "id": "evaluacion",
        "nombre": "Evaluación",
        "descripcion": "Medir calidad, seguridad y adherencia antes de producción.",
        "practicas": ["Datasets de evaluación", "Evaluadores automáticos", "Red-teaming"],
    },
    {
        "id": "despliegue",
        "nombre": "Despliegue",
        "descripcion": "Publicar con IaC, CI/CD e identidad administrada.",
        "practicas": ["Infra como código", "CI/CD", "Estrategias de release"],
    },
    {
        "id": "operacion",
        "nombre": "Operación y mejora",
        "descripcion": "Monitorear, evaluar en continuo y optimizar costo y calidad.",
        "practicas": ["Observabilidad", "Evaluación continua", "Optimización de costos"],
    },
]

ESPECIALISTAS: dict[str, dict] = {
    Especialista.ESTRATEGIA.value: {
        "id": Especialista.ESTRATEGIA.value,
        "nombre": Especialista.ESTRATEGIA.titulo,
        "resumen": "Motivaciones, casos de uso, caso de negocio y hoja de ruta de adopción con el Cloud Adoption Framework.",
        "foco": "CAF · Estrategia, Plan, Preparar, Gobernar, Gestionar",
        "acento": "#0ea5e9",
    },
    Especialista.ARQUITECTURA.value: {
        "id": Especialista.ARQUITECTURA.value,
        "nombre": Especialista.ARQUITECTURA.titulo,
        "resumen": "Diseño alineado a los cinco pilares del Well-Architected Framework para cargas de IA.",
        "foco": "WAF · Confiabilidad, Seguridad, Costos, Operación, Rendimiento",
        "acento": "#6366f1",
    },
    Especialista.IMPLEMENTACION.value: {
        "id": Especialista.IMPLEMENTACION.value,
        "nombre": Especialista.IMPLEMENTACION.titulo,
        "resumen": "RAG, agentes, orquestación, herramientas y evaluación con el Microsoft Agent Framework.",
        "foco": "Ciclo de vida · Datos, Diseño, Desarrollo, Evaluación",
        "acento": "#22c55e",
    },
    Especialista.OPERACION.value: {
        "id": Especialista.OPERACION.value,
        "nombre": Especialista.OPERACION.titulo,
        "resumen": "LLMOps, observabilidad, seguridad de modelos e IA responsable en producción.",
        "foco": "Operación · Monitoreo, evaluación continua, gobierno",
        "acento": "#f59e0b",
    },
}


def _match(texto: str, items: list[dict]) -> dict | None:
    t = (texto or "").strip().lower()
    if not t:
        return None
    for item in items:
        if t in item["id"] or t in item["nombre"].lower() or item["nombre"].lower() in t:
            return item
    return None


def buscar_fase_caf(texto: str = "") -> dict | None:
    return _match(texto, FASES_CAF)


def buscar_pilar_waf(texto: str = "") -> dict | None:
    return _match(texto, PILARES_WAF)


def buscar_etapa_ciclo(texto: str = "") -> dict | None:
    return _match(texto, CICLO_VIDA)
