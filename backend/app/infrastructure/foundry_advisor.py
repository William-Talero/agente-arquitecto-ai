"""Adaptador de asesoría sobre Azure AI Foundry con **agentes persistentes**.

Implementa el puerto :class:`AsesorPort`. Crea un **prompt agent versionado** por
especialista en el proyecto de Foundry (``project.agents.create_version``), de modo
que **aparecen en el portal de Foundry**, y los invoca por la **Responses API**
(``agent_reference``). Cada agente lleva las **herramientas nativas de Foundry**
—búsqueda Web y Microsoft Learn (MCP)— más las herramientas locales de conocimiento
(CAF/WAF/ciclo de vida y generación de diagramas), que se ejecutan en el backend.
"""
from __future__ import annotations

import json
import logging
import re
import threading
import time

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool, MCPTool, PromptAgentDefinition, WebSearchTool
from azure.identity import DefaultAzureCredential

from ..config import settings
from ..application.lineamientos_service import LineamientosService
from ..domain.knowledge import (
    CICLO_VIDA,
    FASES_CAF,
    PILARES_WAF,
    buscar_etapa_ciclo,
    buscar_fase_caf,
    buscar_pilar_waf,
)
from ..domain.models import Cita, Consulta, Especialista, Paso, RespuestaAsesor
from .. import metrics
from . import agent_tools, cards

log = logging.getLogger("arqai.foundry")

MAX_TOOL_ROUNDS = 6
GROUNDING_AGENT = "arqai-fuentes"

# GPT-5 con herramientas hospedadas (MCP/web) inserta marcadores de cita inline
# delimitados por caracteres del Área de Uso Privado Unicode (U+E200…U+E20F).
# Las citas reales ya se extraen aparte por annotations/mcp_call, así que estos
# marcadores se eliminan del texto para que no aparezcan como símbolos raros.
_CITA_INLINE = re.compile("\ue200[\\s\\S]*?\ue201")
_PUA_RESTANTE = re.compile("[\ue000-\uf8ff]")
_CITA_TEXTO = re.compile(r"\bcite\b(?:\s*(?:mcp_)?[\w.]+#\d+)+", re.IGNORECASE)
_ESPACIO_ANTES_PUNTUACION = re.compile(r"[ \t]+([.,;:)\]!?»”])")
_ESPACIOS_MULTIPLES = re.compile(r"[ \t]{2,}")
_ESPACIO_FIN_LINEA = re.compile(r"[ \t]+(?=\n)")
_SALTOS_MULTIPLES = re.compile(r"\n{3,}")


def _limpiar_texto(texto: str) -> str:
    """Elimina los marcadores de cita inline (PUA + ``cite …#n``) que el modelo
    intercala en el texto y normaliza los espacios sobrantes."""
    if not texto:
        return texto
    texto = _CITA_INLINE.sub("", texto)
    texto = _CITA_TEXTO.sub("", texto)
    texto = _PUA_RESTANTE.sub("", texto)
    texto = _ESPACIO_ANTES_PUNTUACION.sub(r"\1", texto)
    texto = _ESPACIOS_MULTIPLES.sub(" ", texto)
    texto = _ESPACIO_FIN_LINEA.sub("", texto)
    texto = _SALTOS_MULTIPLES.sub("\n\n", texto)
    return texto.strip()

_ESPECIALISTA_A_FASE = {
    Especialista.ESTRATEGIA: "caf",
    Especialista.ARQUITECTURA: "waf",
    Especialista.IMPLEMENTACION: "ciclo",
    Especialista.OPERACION: "waf",
}

_REFERENCIA_OFICIAL: dict[Especialista, tuple[str, str]] = {
    Especialista.ESTRATEGIA: (
        "Cloud Adoption Framework para Azure",
        "https://learn.microsoft.com/azure/cloud-adoption-framework/",
    ),
    Especialista.ARQUITECTURA: (
        "Azure Well-Architected Framework",
        "https://learn.microsoft.com/azure/well-architected/",
    ),
    Especialista.IMPLEMENTACION: (
        "Documentación de Azure AI Foundry",
        "https://learn.microsoft.com/azure/ai-foundry/",
    ),
    Especialista.OPERACION: (
        "IA responsable en Azure AI Foundry",
        "https://learn.microsoft.com/azure/ai-foundry/responsible-use-of-ai-overview",
    ),
    Especialista.CONCIERGE: (
        "Azure Architecture Center",
        "https://learn.microsoft.com/azure/architecture/",
    ),
}


class FoundryAdvisorAdapter:
    def __init__(self, lineamientos: LineamientosService | None = None) -> None:
        if not settings.project_endpoint:
            raise RuntimeError("Falta FOUNDRY_PROJECT_ENDPOINT en la configuración (.env).")

        self._lineamientos = lineamientos
        self._credential = DefaultAzureCredential()
        self.project = AIProjectClient(endpoint=settings.project_endpoint, credential=self._credential)
        self.client = self.project.get_openai_client()

        self._nativas = self._herramientas_nativas()
        self.agent_names: dict[Especialista, str] = {}
        for especialista, spec in agent_tools.SPECIALISTS.items():
            self._crear_agente(spec["nombre"], spec["instructions"], spec["tools"])
            self.agent_names[especialista] = spec["nombre"]
            log.info("Agente persistente listo: %s", spec["nombre"])

        # Agente de fundamentación (solo tools nativas) para garantizar referencias.
        self._grounding_ok = bool(self._nativas)
        if self._grounding_ok:
            self._crear_agente(
                GROUNDING_AGENT,
                "Eres un localizador de fuentes oficiales de Microsoft. Para la consulta dada, usa "
                "SIEMPRE la herramienta de Microsoft Learn (microsoft_docs_search) y, si aporta, la "
                "búsqueda web, para encontrar de 3 a 6 documentos oficiales relevantes. Responde con "
                "una sola frase; no inventes URLs.",
                [],
            )

        self._sessions: dict[tuple[str, Especialista], str] = {}
        self._contexto_inyectado: dict[tuple[str, Especialista], str] = {}
        self._lock = threading.Lock()
        self._ready = True

    def _herramientas_nativas(self) -> list:
        herramientas: list = []
        if settings.web_search_enabled:
            herramientas.append(WebSearchTool())
            log.info("Herramienta nativa Web habilitada.")
        if settings.learn_mcp_enabled:
            herramientas.append(
                MCPTool(
                    server_label="microsoft_learn",
                    server_url=settings.learn_mcp_url,
                    require_approval="never",
                )
            )
            log.info("Herramienta nativa Microsoft Learn (MCP) habilitada.")
        return herramientas

    def _crear_agente(self, nombre: str, instrucciones: str, funciones: list[str]) -> None:
        funcion_tools = [
            FunctionTool(**agent_tools.function_tool_spec(agent_tools.HERRAMIENTAS_LOCALES[f]))
            for f in funciones
        ]
        definicion = PromptAgentDefinition(
            model=settings.model,
            instructions=instrucciones,
            tools=[*self._nativas, *funcion_tools],
        )
        self.project.agents.create_version(agent_name=nombre, definition=definicion)

    @property
    def listo(self) -> bool:
        return self._ready

    async def asesorar(self, consulta: Consulta) -> RespuestaAsesor:
        from fastapi.concurrency import run_in_threadpool

        return await run_in_threadpool(self._asesorar_sync, consulta)

    def _asesorar_sync(self, consulta: Consulta) -> RespuestaAsesor:
        especialista = consulta.especialista
        nombre = self.agent_names[especialista]
        coleccion = cards.iniciar()
        inicio = time.perf_counter()

        aplicados = self._publicar_lineamientos(especialista)

        ref = {"agent_reference": {"name": nombre, "type": "agent_reference"}}
        with self._lock:
            prev_id = self._sessions.get((consulta.session_id, especialista))

        entrada = self._construir_entrada(consulta, self._bloque_lineamientos(consulta, especialista))
        citas: list[Cita] = []
        vistas: set[str] = set()
        uso = {"learn": False, "web": False}

        tool_choice = None
        if especialista in (Especialista.ARQUITECTURA, Especialista.IMPLEMENTACION, Especialista.CONCIERGE) \
                and self._es_peticion_diagrama(consulta.mensaje):
            tool_choice = {"type": "function", "name": "generar_diagrama_arquitectura"}

        response = self._crear_respuesta(ref, entrada, prev_id, tool_choice)
        self._acumular_citas(response, citas, vistas, uso)
        for _ in range(MAX_TOOL_ROUNDS):
            salidas = self._ejecutar_funciones(response)
            if not salidas:
                break
            response = self.client.responses.create(
                extra_body=ref, previous_response_id=response.id, input=salidas
            )
            self._acumular_citas(response, citas, vistas, uso)

        with self._lock:
            self._sessions[(consulta.session_id, especialista)] = response.id

        texto = _limpiar_texto(getattr(response, "output_text", "") or "")

        # Garantiza que TODA respuesta lleve citas reales de Microsoft Learn: si el
        # especialista no citó Learn, se hace una búsqueda dedicada en Learn.
        if not any(c.fuente == "learn" for c in citas):
            self._fundamentar(consulta.mensaje, citas, vistas, uso)
        if not citas:
            citas.append(self._referencia_por_defecto(especialista))
            uso["learn"] = True
        for fuente in ("learn", "web"):
            if uso.get(fuente):
                metrics.TOOL_CALLS.labels(fuente).inc()

        if not coleccion:
            fallback = self._tarjeta_por_defecto(especialista, consulta.mensaje)
            if fallback:
                coleccion.append(fallback)

        pasos = self._construir_pasos(especialista, coleccion, uso)
        if aplicados:
            pasos.insert(
                1,
                Paso(
                    titulo=f"Lineamientos propios aplicados ({len(aplicados)})",
                    detalle=", ".join(l["nombre"] for l in aplicados[:3]),
                ),
            )
        if any(a.es_imagen for a in consulta.adjuntos):
            pasos.insert(1, Paso(titulo="Imagen analizada", detalle="visión"))
        duracion = (time.perf_counter() - inicio) * 1000
        return RespuestaAsesor(
            especialista=especialista,
            texto=texto or "He preparado un análisis basado en las mejores prácticas de Microsoft.",
            tarjetas=list(coleccion),
            citas=citas[:8],
            pasos=pasos,
            duracion_ms=duracion,
        )

    def _crear_respuesta(self, ref: dict, entrada, prev_id: str | None, tool_choice: dict | None = None):
        kwargs = {"extra_body": ref, "input": entrada}
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
        if prev_id:
            kwargs["previous_response_id"] = prev_id
        try:
            return self.client.responses.create(**kwargs)
        except Exception as exc:  # noqa: BLE001
            if not prev_id:
                raise
            log.warning("previous_response_id inválido, reiniciando contexto: %s", exc)
            kwargs.pop("previous_response_id", None)
            return self.client.responses.create(**kwargs)

    @staticmethod
    def _es_peticion_diagrama(mensaje: str) -> bool:
        t = (mensaje or "").lower()
        verbos = ("genera", "genér", "gener", "dibuj", "diseñ", "disen", "crea", "haz", "arma")
        objetos = ("arquitectura", "diagrama", "diseño", "landing zone", "draw.io", "drawio", "topología")
        return any(v in t for v in verbos) and any(o in t for o in objetos)

    def _ejecutar_funciones(self, response) -> list[dict]:
        salidas: list[dict] = []
        for item in getattr(response, "output", []) or []:
            if getattr(item, "type", None) != "function_call":
                continue
            resultado = self._ejecutar_tool(item.name, getattr(item, "arguments", None))
            salidas.append(
                {"type": "function_call_output", "call_id": item.call_id, "output": resultado}
            )
        return salidas

    @staticmethod
    def _ejecutar_tool(nombre: str, argumentos: str | None) -> str:
        fn = agent_tools.FUNCTION_REGISTRY.get(nombre)
        if fn is None:
            return json.dumps({"error": f"Función '{nombre}' no disponible."})
        try:
            resultado = fn(**json.loads(argumentos or "{}"))
            metrics.TOOL_CALLS.labels(nombre).inc()
            return resultado
        except Exception as exc:  # noqa: BLE001
            log.exception("Error ejecutando %s", nombre)
            return json.dumps({"error": str(exc)})

    def _publicar_lineamientos(self, especialista: Especialista) -> list[dict]:
        """Expone los lineamientos del cliente a la herramienta local y devuelve su resumen."""
        if self._lineamientos is None:
            agent_tools.publicar_lineamientos([])
            return []
        aplicables = self._lineamientos.para_especialista(especialista)
        agent_tools.publicar_lineamientos([dict(l.__dict__) for l in aplicables])
        return [
            {"id": l.id, "nombre": l.nombre, "ambito": l.ambito, "categoria": l.categoria}
            for l in aplicables
        ]

    def _bloque_lineamientos(self, consulta: Consulta, especialista: Especialista) -> str:
        """Contexto de lineamientos a inyectar: completo la primera vez de la sesión y
        cada vez que el cliente cambia sus documentos; vacío mientras no cambien."""
        if self._lineamientos is None:
            return ""
        version = self._lineamientos.version
        clave = (consulta.session_id, especialista)
        with self._lock:
            if self._contexto_inyectado.get(clave) == version:
                return ""
            self._contexto_inyectado[clave] = version
        return self._lineamientos.contexto(especialista)

    def _construir_entrada(self, consulta: Consulta, bloque_lineamientos: str = ""):
        """Entrada para la Responses API: texto simple o contenido multimodal
        (texto + imágenes) cuando la consulta trae adjuntos. Los lineamientos del
        negocio viajan como mensaje ``developer`` previo al mensaje del usuario."""
        texto = consulta.mensaje
        for adjunto in consulta.adjuntos:
            if not adjunto.es_imagen and adjunto.texto:
                texto += f"\n\n--- Archivo adjunto: {adjunto.nombre} ---\n{adjunto.texto}"

        imagenes = [a for a in consulta.adjuntos if a.es_imagen and a.data]
        if not imagenes and not bloque_lineamientos:
            return texto

        import base64

        contenido: list[dict] = [{"type": "input_text", "text": texto}]
        for adjunto in imagenes:
            b64 = base64.b64encode(adjunto.data).decode()
            contenido.append(
                {"type": "input_image", "image_url": f"data:{adjunto.mime_type};base64,{b64}"}
            )
        mensajes: list[dict] = []
        if bloque_lineamientos:
            mensajes.append(
                {
                    "type": "message",
                    "role": "developer",
                    "content": [{"type": "input_text", "text": bloque_lineamientos}],
                }
            )
        mensajes.append({"type": "message", "role": "user", "content": contenido})
        return mensajes

    def _fundamentar(self, mensaje: str, citas: list[Cita], vistas: set[str], uso: dict[str, bool]) -> None:
        """Consulta Microsoft Learn para adjuntar fuentes cuando la respuesta
        principal no citó ninguna, de modo que toda respuesta lleve referencias."""
        if not self._grounding_ok:
            return
        try:
            ref = {"agent_reference": {"name": GROUNDING_AGENT, "type": "agent_reference"}}
            response = self.client.responses.create(
                extra_body=ref,
                input=f"Documentación oficial de Microsoft Learn relevante para: {mensaje}",
            )
            self._acumular_citas(response, citas, vistas, uso)
        except Exception as exc:  # noqa: BLE001
            log.warning("Fundamentación de fuentes falló: %s", exc)

    def _acumular_citas(self, response, citas: list[Cita], vistas: set[str], uso: dict[str, bool]) -> None:
        """Recorre los items de salida de la Responses API acumulando citas de
        Microsoft Learn (``mcp_call``) y de la búsqueda web (anotaciones)."""
        def agregar(titulo: str, url: str, fuente: str) -> None:
            if not url or "learn.microsoft.com/answers/" in url:
                return
            clave = url.split("#")[0]
            if clave not in vistas and len(citas) < 8:
                vistas.add(clave)
                citas.append(Cita(titulo=titulo or url, url=url, fuente=fuente))

        for item in getattr(response, "output", []) or []:
            tipo = getattr(item, "type", None)
            if tipo == "mcp_call":
                servidor = (getattr(item, "server_label", "") or "").lower()
                fuente = "learn" if "learn" in servidor else "web"
                uso[fuente] = True
                for titulo, url in self._citas_mcp(getattr(item, "output", None)):
                    agregar(titulo, url, fuente)
            elif tipo and "web_search" in tipo:
                uso["web"] = True
            elif tipo == "message":
                for content in getattr(item, "content", []) or []:
                    for anotacion in getattr(content, "annotations", None) or []:
                        url = getattr(anotacion, "url", None)
                        if not url:
                            continue
                        fuente = "learn" if "learn.microsoft.com" in url else "web"
                        uso[fuente] = True
                        agregar(getattr(anotacion, "title", "") or "", url, fuente)

    @staticmethod
    def _citas_mcp(salida) -> list[tuple[str, str]]:
        """Extrae (título, url) de la salida de una herramienta MCP (JSON con
        ``results[].contentUrl``)."""
        encontradas: list[tuple[str, str]] = []
        bloques = []
        if isinstance(salida, str):
            bloques = [salida]
        elif isinstance(salida, (list, tuple)):
            for it in salida:
                t = it.get("text") if isinstance(it, dict) else getattr(it, "text", None)
                if t:
                    bloques.append(t)
        elif isinstance(salida, dict):
            bloques = [json.dumps(salida)]
        for bloque in bloques:
            try:
                datos = json.loads(bloque)
            except (ValueError, TypeError):
                continue
            for res in datos.get("results", []) if isinstance(datos, dict) else []:
                if isinstance(res, dict):
                    url = res.get("contentUrl") or res.get("url") or ""
                    if url:
                        encontradas.append((res.get("title", ""), url))
        return encontradas

    @staticmethod
    def _referencia_por_defecto(especialista: Especialista) -> Cita:
        titulo, url = _REFERENCIA_OFICIAL.get(especialista) or _REFERENCIA_OFICIAL[Especialista.CONCIERGE]
        return Cita(titulo=titulo, url=url, fuente="learn")

    @staticmethod
    def _tarjeta_por_defecto(especialista: Especialista, mensaje: str) -> dict | None:
        tipo = _ESPECIALISTA_A_FASE.get(especialista)
        if tipo == "caf":
            fase = buscar_fase_caf(mensaje)
            return {
                "tipo": "caf",
                "titulo": "Cloud Adoption Framework · Adopción de IA",
                "foco": fase["nombre"] if fase else "",
                "fases": [fase] if fase else FASES_CAF,
            }
        if tipo == "waf":
            pilar = buscar_pilar_waf(mensaje)
            return {
                "tipo": "waf",
                "titulo": "Well-Architected · Cargas de trabajo de IA",
                "foco": pilar["nombre"] if pilar else "",
                "pilares": [pilar] if pilar else PILARES_WAF,
            }
        if tipo == "ciclo":
            etapa = buscar_etapa_ciclo(mensaje)
            return {
                "tipo": "ciclo",
                "titulo": "Ciclo de vida de la solución de IA",
                "foco": etapa["nombre"] if etapa else "",
                "etapas": [etapa] if etapa else CICLO_VIDA,
            }
        return None

    @staticmethod
    def _construir_pasos(especialista: Especialista, coleccion: list[dict], uso: dict[str, bool]) -> list[Paso]:
        pasos = [Paso(titulo=f"Enrutado a {especialista.titulo}")]
        tipos = {c.get("tipo") for c in coleccion}
        etiquetas = {
            "caf": "Marco CAF",
            "waf": "Pilares WAF",
            "ciclo": "Ciclo de vida",
            "estandares": "Estándares GA",
            "lineamientos": "Lineamientos propios",
            "arquitectura": "Diagrama .drawio",
        }
        for tipo, etiqueta in etiquetas.items():
            if tipo in tipos:
                pasos.append(Paso(titulo=etiqueta, detalle="tarjeta"))
        if uso.get("learn"):
            pasos.append(Paso(titulo="Microsoft Learn", detalle="herramienta nativa"))
        if uso.get("web"):
            pasos.append(Paso(titulo="Búsqueda Web", detalle="herramienta nativa"))
        return pasos

    async def cerrar(self) -> None:
        try:
            self._credential.close()
        except Exception:  # noqa: BLE001
            pass
