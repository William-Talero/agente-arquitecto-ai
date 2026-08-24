"""Métricas Prometheus para observabilidad del asesor."""
from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

CHAT_REQUESTS = Counter(
    "arqai_chat_requests_total",
    "Consultas atendidas por especialista y estado.",
    ["especialista", "status"],
)

CHAT_LATENCY = Histogram(
    "arqai_chat_latency_seconds",
    "Latencia de la asesoría por especialista.",
    ["especialista"],
)

TOOL_CALLS = Counter(
    "arqai_tool_calls_total",
    "Uso de herramientas nativas del asesor.",
    ["tool"],
)

CARDS_EMITTED = Counter(
    "arqai_cards_emitted_total",
    "Tarjetas estructuradas emitidas.",
    ["tipo"],
)

ADVISOR_READY = Gauge(
    "arqai_advisor_ready",
    "1 si el adaptador de asesoría está inicializado.",
)

LINEAMIENTOS_CARGADOS = Counter(
    "arqai_lineamientos_cargados_total",
    "Documentos de lineamientos propios cargados por ámbito.",
    ["ambito"],
)
