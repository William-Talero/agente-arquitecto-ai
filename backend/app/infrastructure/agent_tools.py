"""Herramientas locales (function tools) y definición de los especialistas.

Las herramientas locales exponen la base de conocimiento CAF/WAF/ciclo de vida
como tarjetas visuales. Se combinan con las **herramientas nativas de Foundry**
(Web y Microsoft Learn), que se adjuntan en el adaptador. Se priorizan las
herramientas nativas para la información en tiempo real y autoritativa.
"""
from __future__ import annotations

import contextvars
import inspect
import json
import re

from ..domain.estandares import ESTANDARES_VIGENTES, POLITICA_VIGENCIA, REVISADO, buscar_estandar
from ..domain.knowledge import (
    CICLO_VIDA,
    FASES_CAF,
    PILARES_WAF,
    buscar_etapa_ciclo,
    buscar_fase_caf,
    buscar_pilar_waf,
)
from ..domain.models import Especialista
from . import cards
from . import diagram

# Lineamientos propios del negocio aplicables a la consulta en curso. El adaptador
# los publica al iniciar cada asesoría para que la herramienta local pueda leerlos.
_lineamientos_activos: contextvars.ContextVar = contextvars.ContextVar(
    "lineamientos_activos", default=None
)


def publicar_lineamientos(items: list[dict]) -> None:
    """Publica los lineamientos vigentes para la petición actual."""
    _lineamientos_activos.set(items)


def _dumps(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False)


def marco_caf(fase: str = "") -> str:
    """Estructura una recomendación con las fases del Cloud Adoption Framework (CAF)
    para adopción de IA: Estrategia, Plan, Preparar, Gobernar y Gestionar. Úsala
    para preguntas de estrategia, caso de negocio, hoja de ruta o gobierno.

    :param fase: Fase específica a resaltar (opcional): estrategia, plan, preparar, gobernar, gestionar.
    :return: JSON con la(s) fase(s) del CAF relevantes.
    """
    fase_match = buscar_fase_caf(fase)
    seleccion = [fase_match] if fase_match else FASES_CAF
    cards.emitir({
        "tipo": "caf",
        "titulo": "Cloud Adoption Framework · Adopción de IA",
        "foco": fase_match["nombre"] if fase_match else "",
        "fases": seleccion,
    })
    return _dumps({"fases": [f["nombre"] for f in seleccion]})


def pilares_waf(pilar: str = "") -> str:
    """Evalúa una carga de IA contra los cinco pilares del Well-Architected
    Framework (WAF): Confiabilidad, Seguridad, Optimización de costos, Excelencia
    operativa y Eficiencia del rendimiento. Úsala para preguntas de arquitectura,
    diseño, resiliencia, seguridad, costos o rendimiento.

    :param pilar: Pilar específico a resaltar (opcional).
    :return: JSON con el/los pilar(es) del WAF relevantes.
    """
    pilar_match = buscar_pilar_waf(pilar)
    seleccion = [pilar_match] if pilar_match else PILARES_WAF
    cards.emitir({
        "tipo": "waf",
        "titulo": "Well-Architected · Cargas de trabajo de IA",
        "foco": pilar_match["nombre"] if pilar_match else "",
        "pilares": seleccion,
    })
    return _dumps({"pilares": [p["nombre"] for p in seleccion]})


def ciclo_vida_ai(etapa: str = "") -> str:
    """Traza el ciclo de vida de una solución de IA: caso de uso, datos, diseño,
    desarrollo, evaluación, despliegue y operación. Úsala para planear el trabajo,
    listas de verificación o pasos siguientes de una iniciativa de IA.

    :param etapa: Etapa específica a resaltar (opcional).
    :return: JSON con la(s) etapa(s) del ciclo de vida.
    """
    etapa_match = buscar_etapa_ciclo(etapa)
    seleccion = [etapa_match] if etapa_match else CICLO_VIDA
    cards.emitir({
        "tipo": "ciclo",
        "titulo": "Ciclo de vida de la solución de IA",
        "foco": etapa_match["nombre"] if etapa_match else "",
        "etapas": seleccion,
    })
    return _dumps({"etapas": [e["nombre"] for e in seleccion]})


def estandares_microsoft(area: str = "") -> str:
    """Consulta la línea base de estándares y tecnologías VIGENTES (GA) de Microsoft y
    qué está retirado o sucedido por otra opción. Úsala SIEMPRE antes de recomendar un
    framework, SDK, servicio o patrón, y cuando el usuario mencione Semantic Kernel,
    AutoGen, Assistants API, ARM JSON u otra tecnología potencialmente obsoleta. El
    resultado es una línea base: valida el estado actual con microsoft_docs_search.

    :param area: Área a consultar (opcional): agentes, plataforma, interoperabilidad, identidad, iac, observabilidad, ia-responsable, marcos.
    :return: JSON con lo vigente en GA, lo que se debe evitar y la referencia oficial.
    """
    match = buscar_estandar(area)
    seleccion = [match] if match else ESTANDARES_VIGENTES
    cards.emitir({
        "tipo": "estandares",
        "titulo": "Estándares vigentes de Microsoft (GA)",
        "foco": match["area"] if match else "",
        "revisado": REVISADO,
        "estandares": seleccion,
    })
    return _dumps({
        "revisado": REVISADO,
        "aviso": "Línea base; verifica el estado actual (GA/Preview/retirado) en Microsoft Learn.",
        "estandares": [
            {"area": e["area"], "vigente": e["vigente"], "evitar": e["evitar"], "url": e["url"]}
            for e in seleccion
        ],
    })


def lineamientos_negocio(tema: str = "") -> str:
    """Recupera los lineamientos, estándares y buenas prácticas PROPIAS del negocio que el
    cliente cargó en la plataforma. Úsala SIEMPRE que vayas a proponer, evaluar o corregir
    una arquitectura, para que tus recomendaciones cumplan las reglas internas de la
    organización además de las de Microsoft.

    :param tema: Palabra clave para filtrar los lineamientos (opcional).
    :return: JSON con los lineamientos aplicables y su contenido.
    """
    items = _lineamientos_activos.get() or []
    consulta = (tema or "").strip().lower()
    if consulta:
        filtrados = [
            l for l in items
            if consulta in l.get("nombre", "").lower()
            or consulta in l.get("categoria", "").lower()
            or consulta in l.get("texto", "").lower()
        ]
        items = filtrados or items
    if not items:
        return _dumps({
            "lineamientos": [],
            "mensaje": "El cliente no ha cargado lineamientos propios; aplica solo las buenas prácticas de Microsoft.",
        })
    cards.emitir({
        "tipo": "lineamientos",
        "titulo": "Lineamientos propios aplicados",
        "foco": tema,
        "lineamientos": [
            {
                "id": l.get("id", ""),
                "nombre": l.get("nombre", ""),
                "ambito": l.get("ambito", ""),
                "categoria": l.get("categoria", ""),
                "caracteres": len(l.get("texto", "")),
            }
            for l in items
        ],
    })
    return _dumps({
        "lineamientos": [
            {
                "nombre": l.get("nombre", ""),
                "ambito": l.get("ambito", ""),
                "categoria": l.get("categoria", ""),
                "contenido": l.get("texto", "")[:6000],
            }
            for l in items
        ]
    })


def generar_diagrama_arquitectura(titulo: str = "", especificacion: str = "") -> str:
    """Genera un diagrama de arquitectura de Azure en formato draw.io (.drawio) con
    iconos oficiales de Microsoft, estilo de arquitectura de referencia y componentes
    de Azure, alineado a CAF, al Well-Architected Framework y a la Azure AI Landing
    Zone. Úsala SIEMPRE que el usuario pida crear, generar, dibujar, diseñar o
    proponer una arquitectura, un diagrama o un diseño de solución.

    Diseña una arquitectura completa y coherente para la petición del usuario y pásala
    en el parámetro `especificacion` como JSON. Estructura como arquitectura de
    REFERENCIA de Microsoft: agrupa por redes virtuales (VNet) con subredes (subnet)
    anidadas y define conexiones entre servicios. Forma:
    {"zonas": [
        {"nombre": "Aplicación · Spoke VNet", "cidr": "10.1.0.0/16", "subredes": [
            {"nombre": "APIM subnet", "cidr": "10.1.1.0/24", "servicios": [
                {"id": "apim", "tipo": "apim", "nombre": "API Management"}]},
            {"nombre": "AI Foundry subnet", "cidr": "10.1.3.0/24", "servicios": [
                {"id": "aoai", "tipo": "openai", "nombre": "Azure OpenAI"}]}]},
        {"nombre": "Identidad y usuarios", "servicios": [
            {"id": "user", "tipo": "users", "nombre": "Usuarios"}]}],
     "conexiones": [{"desde": "agw", "hacia": "apim", "etiqueta": "HTTPS"}]}

    Reglas de estructura:
    - Una zona con `subredes` se dibuja como una VNet (borde azul punteado) que contiene
      cada subred; una zona con solo `servicios` se dibuja como carril simple. Añade
      `cidr` a VNets y subredes (p. ej. "10.1.0.0/16", "10.1.1.0/24").
    - Coloca cada servicio en la subred correcta (perímetro, GatewaySubnet, APIM, Compute,
      AI Foundry, Private Endpoints, Database, Ingest/Storage, etc.).
    - Define `conexiones` que reflejen el flujo real (usuario → Front Door → WAF → App
      Gateway → APIM → cómputo → Foundry/OpenAI → datos), referenciando los `id`.

    Los `id` son únicos y se referencian en `conexiones`. Valores válidos de `tipo`:
    users, browser, mobile, front_door, waf, firewall, app_gateway, ddos, bastion,
    vnet, subnet, private_link, load_balancer, dns, vpn_gateway, apim, app_service,
    function, aks, container_apps, acr, aci, vm, ai_foundry, openai, cognitive,
    content_safety, machine_learning, bot, document_intelligence, speech, language,
    ai_search, cosmos, sql, redis, storage, event_hub, event_grid, service_bus,
    logic_app, entra, managed_identity, key_vault, defender, sentinel, monitor,
    log_analytics, app_insights, policy, resource_group.

    Aplica buenas prácticas de seguridad (Entra ID, identidades administradas, Private
    Endpoints, Key Vault, WAF/Firewall) y de Well-Architected. Si no aportas
    especificación, se usa una plantilla base de AI Landing Zone con VNets y subredes.

    :param titulo: Título descriptivo de la arquitectura.
    :param especificacion: JSON con zonas (VNets), subredes, servicios y conexiones.
    :return: JSON con el resumen del diagrama generado.
    """
    spec = _parse_spec(especificacion)
    datos = {"titulo": titulo, **spec} if spec.get("zonas") else {"titulo": titulo, **diagram.PLANTILLA_AI_LANDING_ZONE}
    resultado = diagram.construir_diagrama(datos)
    cards.emitir({
        "tipo": "arquitectura",
        "titulo": resultado["titulo"],
        "drawio": resultado["xml"],
        "zonas": resultado["zonas"],
        "n_servicios": resultado["n_servicios"],
        "n_conexiones": resultado["n_conexiones"],
    })
    return _dumps({
        "ok": True,
        "titulo": resultado["titulo"],
        "zonas": resultado["zonas"],
        "servicios": resultado["n_servicios"],
        "mensaje": "Diagrama .drawio generado con iconos de Azure y estilo de arquitectura de referencia.",
    })


def _parse_spec(texto: str) -> dict:
    if not texto or not texto.strip():
        return {}
    try:
        datos = json.loads(texto)
        return datos if isinstance(datos, dict) else {}
    except (ValueError, TypeError):
        inicio, fin = texto.find("{"), texto.rfind("}")
        if 0 <= inicio < fin:
            try:
                datos = json.loads(texto[inicio : fin + 1])
                return datos if isinstance(datos, dict) else {}
            except (ValueError, TypeError):
                return {}
        return {}


HERRAMIENTAS_LOCALES = {
    "marco_caf": marco_caf,
    "pilares_waf": pilares_waf,
    "ciclo_vida_ai": ciclo_vida_ai,
    "estandares_microsoft": estandares_microsoft,
    "lineamientos_negocio": lineamientos_negocio,
    "generar_diagrama_arquitectura": generar_diagrama_arquitectura,
}

FUNCTION_REGISTRY = HERRAMIENTAS_LOCALES


def function_schema(fn) -> dict:
    """Construye el JSON Schema de parámetros de una función desde su firma y su
    docstring (líneas ``:param nombre: descripción``)."""
    sig = inspect.signature(fn)
    descripciones = dict(re.findall(r":param (\w+):\s*(.+)", fn.__doc__ or ""))
    tipos = {int: "integer", float: "number", bool: "boolean", str: "string"}
    propiedades: dict = {}
    requeridos: list[str] = []
    for nombre, param in sig.parameters.items():
        prop = {"type": tipos.get(param.annotation, "string")}
        if nombre in descripciones:
            prop["description"] = descripciones[nombre].strip()
        propiedades[nombre] = prop
        if param.default is inspect.Parameter.empty:
            requeridos.append(nombre)
    return {"type": "object", "properties": propiedades, "required": requeridos, "additionalProperties": False}


def function_tool_spec(fn) -> dict:
    """Especificación de FunctionTool (Responses/PromptAgentDefinition)."""
    return {
        "name": fn.__name__,
        "description": (fn.__doc__ or "").strip().split("\n")[0],
        "parameters": function_schema(fn),
        "strict": False,
    }


_BASE = (
    "Eres el mejor arquitecto de soluciones de IA de Microsoft. Asesoras a clientes sobre el "
    "diseño, desarrollo, adopción, mejora y operación de soluciones de IA en Azure, "
    "alineado al Cloud Adoption Framework (CAF), al Well-Architected Framework (WAF) y a "
    "las mejores prácticas y a la IA responsable de Microsoft. Respondes SIEMPRE en español, "
    "con tono técnico, claro y accionable. REGLA OBLIGATORIA E INNEGOCIABLE: antes de "
    "redactar CUALQUIER respuesta DEBES invocar la herramienta de Microsoft Learn "
    "(microsoft_docs_search) al menos una vez para validar TODA la información, conceptos, "
    "guías y prácticas; cuando necesites profundidad usa además microsoft_docs_fetch sobre la "
    "página oficial. Tienes acceso a TODO Microsoft Learn: realiza tantas búsquedas como "
    "necesites para cubrir cada tema de la consulta. Nunca respondas solo de memoria: "
    "fundamenta cada afirmación en la documentación oficial de Microsoft Learn. Si necesitas "
    "información reciente o comparativa, complementa con la herramienta de búsqueda web. CITA "
    "SIEMPRE las fuentes con sus enlaces reales devueltos por las herramientas y prioriza "
    "Microsoft Learn. No inventes URLs; usa solo las que devuelvan las herramientas. "
    + POLITICA_VIGENCIA +
    " Apóyate en la herramienta estandares_microsoft para conocer la línea base de lo vigente "
    "en GA y lo que está retirado, y contrástala siempre con Microsoft Learn. "
    "LINEAMIENTOS PROPIOS DEL CLIENTE: la organización puede haber cargado sus propios "
    "estándares, políticas y buenas prácticas. Invoca lineamientos_negocio antes de proponer o "
    "evaluar cualquier arquitectura y aplícalos como restricciones de diseño; indica en la "
    "respuesta qué lineamiento interno aplicaste y por qué. Si un lineamiento interno "
    "contradice la guía oficial de Microsoft en seguridad, cumplimiento o IA responsable, "
    "señala el conflicto de forma explícita, explica el riesgo y propone la alternativa "
    "alineada a Microsoft en lugar de acatarlo en silencio. "
    "RESPUESTAS ILUSTRATIVAS (nunca solo texto): haz que cada respuesta sea visual y guíe al "
    "usuario. Incluye diagramas Mermaid en bloques de código ```mermaid para ilustrar flujos, "
    "árboles de decisión, secuencias, mapas mentales o bocetos de arquitectura (usa flowchart, "
    "sequenceDiagram o mindmap; sintaxis válida y nodos con etiquetas claras). Usa tablas para "
    "comparar opciones, servicios o pilares, y emojis como anclas visuales de sección de forma "
    "sobria y profesional (p. ej. 🏗️ 🔐 💰 📊 ✅ ⚠️ 🚀). Estructura con encabezados y pasos "
    "numerados. GUÍA DE CREACIÓN: cuando el usuario quiera construir o diseñar una arquitectura, "
    "acompáñalo paso a paso (1. objetivo y requisitos, 2. lineamientos internos aplicables, "
    "3. patrón de referencia, 4. servicios de Azure en GA, 5. seguridad y redes, 6. costos y "
    "operación, 7. diagrama), mostrando en cada paso un pequeño Mermaid o una tabla, y cierra "
    "proponiendo el siguiente paso. Cuando estructures "
    "marcos (CAF/WAF/ciclo de vida), invoca la herramienta local correspondiente para generar "
    "una tarjeta visual que complementa tu respuesta. Si el usuario adjunta una "
    "imagen o diagrama de arquitectura, analízalo con detalle (componentes, servicios de Azure, "
    "flujos de datos e integraciones) y evalúalo según el Well-Architected Framework y los "
    "lineamientos propios del cliente, señalando "
    "fortalezas, riesgos y recomendaciones priorizadas en una tabla, validando cada criterio con "
    "Microsoft Learn. Si el usuario pide crear, generar, "
    "dibujar o diseñar una arquitectura o un diagrama, llama a la herramienta "
    "generar_diagrama_arquitectura con un diseño completo (zonas, servicios y conexiones) "
    "basado en la Azure AI Landing Zone y las buenas prácticas de CAF y Well-Architected; el "
    "diagrama .drawio complementa (no reemplaza) el boceto Mermaid y la guía."
)

SPECIALISTS: dict[Especialista, dict] = {
    Especialista.ESTRATEGIA: {
        "nombre": "arqai-estrategia",
        "instructions": _BASE + (
            " Te especializas en ESTRATEGIA Y ADOPCIÓN (CAF): motivaciones de negocio, "
            "casos de uso, caso de negocio, hoja de ruta, madurez y gobierno de la adopción "
            "de IA. Usa la herramienta marco_caf para estructurar las fases y considera el "
            "impacto de adoptar solo capacidades en disponibilidad general (GA) frente a "
            "preview en el plan de adopción y en el análisis de riesgo."
        ),
        "tools": ["marco_caf", "ciclo_vida_ai", "estandares_microsoft", "lineamientos_negocio"],
    },
    Especialista.ARQUITECTURA: {
        "nombre": "arqai-arquitectura",
        "instructions": _BASE + (
            " Te especializas en ARQUITECTURA (Well-Architected): evalúas y diseñas cargas de "
            "IA según los cinco pilares. Usa la herramienta pilares_waf para estructurar el "
            "análisis y recomienda patrones de arquitectura de referencia de Azure vigentes. "
            "Toda decisión tecnológica debe estar en GA salvo justificación explícita, y toda "
            "arquitectura debe cumplir los lineamientos propios del cliente (servicios "
            "aprobados, regiones, nomenclatura, redes, cifrado). Cuando te "
            "pidan generar, dibujar o diseñar una arquitectura, usa generar_diagrama_arquitectura."
        ),
        "tools": [
            "pilares_waf",
            "ciclo_vida_ai",
            "estandares_microsoft",
            "lineamientos_negocio",
            "generar_diagrama_arquitectura",
        ],
    },
    Especialista.IMPLEMENTACION: {
        "nombre": "arqai-implementacion",
        "instructions": _BASE + (
            " Te especializas en IMPLEMENTACIÓN Y DESARROLLO: RAG, agentes, orquestación, "
            "herramientas, embeddings y evaluación. El framework de referencia para construir "
            "agentes es el MICROSOFT AGENT FRAMEWORK (sucesor GA de Semantic Kernel y AutoGen): "
            "úsalo en todos los ejemplos de código y propón la ruta de migración oficial si el "
            "cliente aún usa Semantic Kernel, AutoGen, la API de Assistants o los workflows del "
            "portal de Foundry (en retiro). Alinea la plataforma a Microsoft Foundry (Foundry "
            "Agent Service, hosted agents, toolboxes, Foundry IQ) y las herramientas a MCP. "
            "Antes de mostrar código verifica la API vigente en Microsoft Learn: no uses APIs "
            "de versiones anteriores. Usa ciclo_vida_ai para ubicar la etapa y da pasos "
            "concretos y ejemplos. Cuando te pidan generar o dibujar una arquitectura, usa "
            "generar_diagrama_arquitectura."
        ),
        "tools": [
            "ciclo_vida_ai",
            "marco_caf",
            "estandares_microsoft",
            "lineamientos_negocio",
            "generar_diagrama_arquitectura",
        ],
    },
    Especialista.OPERACION: {
        "nombre": "arqai-operacion",
        "instructions": _BASE + (
            " Te especializas en OPERACIÓN E IA RESPONSABLE: LLMOps, observabilidad con "
            "OpenTelemetry y Foundry Observability (tracing y evaluaciones en GA), evaluación "
            "continua, red teaming, seguridad de contenido, costos y cumplimiento en producción. "
            "Exige que lo que llegue a producción esté en GA y que las dependencias en preview "
            "estén documentadas y aprobadas. Usa "
            "pilares_waf (excelencia operativa y seguridad) para estructurar recomendaciones y "
            "verifica los umbrales y políticas contra los lineamientos propios del cliente."
        ),
        "tools": ["pilares_waf", "ciclo_vida_ai", "estandares_microsoft", "lineamientos_negocio"],
    },
    Especialista.CONCIERGE: {
        "nombre": "arqai-asesor",
        "instructions": _BASE + (
            " Actúas como asesor general: orientas al cliente por el ciclo de vida completo y "
            "derivas a marcos CAF/WAF cuando aplica. Usa las herramientas locales y nativas "
            "según la pregunta, empezando por estandares_microsoft y lineamientos_negocio para "
            "encuadrar la respuesta en lo vigente y en las reglas de la organización. Si piden "
            "generar o dibujar una arquitectura, usa generar_diagrama_arquitectura."
        ),
        "tools": [
            "marco_caf",
            "pilares_waf",
            "ciclo_vida_ai",
            "estandares_microsoft",
            "lineamientos_negocio",
            "generar_diagrama_arquitectura",
        ],
    },
}
