"""Generador de diagramas de arquitectura de Azure en formato draw.io (.drawio).

Produce XML válido con **iconos oficiales de Azure** (bundle ``azure2`` de draw.io),
estilo de **arquitectura de referencia de Microsoft** (lienzo blanco, contenedores
de borde fino con etiqueta superior izquierda, iconos sin caja de fondo, flechas
ortogonales delgadas) y estructura basada en la **Azure AI Landing Zone**.

Los nombres de iconos están verificados contra el bundle de draw.io; un nombre
inválido se renderiza como caja vacía, por eso solo se usan rutas confirmadas.
"""
from __future__ import annotations

import json
from xml.sax.saxutils import quoteattr

FF = "Segoe UI"
INK = "#0E2133"
INK2 = "#283D52"
LINE = "#93A6BA"
LINE2 = "#AEBECE"
AZ = "#0078D4"
ARROW = "#3E5670"
CANVAS = "#FFFFFF"
TINT = "#F1F6FB"

# --- Iconos Azure (rutas verificadas en img/lib/azure2/) --------------------
ICONOS: dict[str, str] = {
    "users": "identity/Users.svg",
    "usuarios": "identity/Users.svg",
    "browser": "general/Browser.svg",
    "cliente": "general/Browser.svg",
    "mobile": "general/Mobile.svg",
    "front_door": "networking/Front_Doors.svg",
    "waf": "networking/Web_Application_Firewall_Policies_WAF.svg",
    "firewall": "networking/Firewalls.svg",
    "app_gateway": "networking/Application_Gateways.svg",
    "application_gateway": "networking/Application_Gateways.svg",
    "ddos": "networking/DDoS_Protection_Plans.svg",
    "bastion": "networking/Bastions.svg",
    "vnet": "networking/Virtual_Networks.svg",
    "virtual_network": "networking/Virtual_Networks.svg",
    "subnet": "networking/Subnet.svg",
    "private_link": "networking/Private_Link.svg",
    "private_endpoint": "networking/Private_Link.svg",
    "load_balancer": "networking/Load_Balancers.svg",
    "dns": "networking/DNS_Zones.svg",
    "vpn_gateway": "networking/Virtual_Network_Gateways.svg",
    "expressroute": "networking/Virtual_Network_Gateways.svg",
    "gateway": "networking/Virtual_Network_Gateways.svg",
    "apim": "app_services/API_Management_Services.svg",
    "api_management": "app_services/API_Management_Services.svg",
    "app_service": "app_services/App_Services.svg",
    "web_app": "app_services/App_Services.svg",
    "function": "compute/Function_Apps.svg",
    "functions": "compute/Function_Apps.svg",
    "aks": "containers/Kubernetes_Services.svg",
    "kubernetes": "containers/Kubernetes_Services.svg",
    "container_apps": "containers/App_Services.svg",
    "aca": "containers/App_Services.svg",
    "acr": "containers/Container_Registries.svg",
    "container_registry": "containers/Container_Registries.svg",
    "aci": "containers/Container_Instances.svg",
    "container_instance": "containers/Container_Instances.svg",
    "vm": "compute/Virtual_Machine.svg",
    "virtual_machine": "compute/Virtual_Machine.svg",
    "ai_foundry": "ai_machine_learning/AI_Studio.svg",
    "foundry": "ai_machine_learning/AI_Studio.svg",
    "ai_studio": "ai_machine_learning/AI_Studio.svg",
    "ai_hub": "ai_machine_learning/AI_Studio.svg",
    "openai": "ai_machine_learning/Azure_OpenAI.svg",
    "azure_openai": "ai_machine_learning/Azure_OpenAI.svg",
    "aoai": "ai_machine_learning/Azure_OpenAI.svg",
    "cognitive": "ai_machine_learning/Cognitive_Services.svg",
    "cognitive_services": "ai_machine_learning/Cognitive_Services.svg",
    "ai_services": "ai_machine_learning/Cognitive_Services.svg",
    "content_safety": "ai_machine_learning/Content_Safety.svg",
    "machine_learning": "ai_machine_learning/Machine_Learning.svg",
    "aml": "ai_machine_learning/Machine_Learning.svg",
    "ml": "ai_machine_learning/Machine_Learning.svg",
    "bot": "ai_machine_learning/Bot_Services.svg",
    "bot_service": "ai_machine_learning/Bot_Services.svg",
    "document_intelligence": "ai_machine_learning/Form_Recognizers.svg",
    "form_recognizer": "ai_machine_learning/Form_Recognizers.svg",
    "speech": "ai_machine_learning/Speech_Services.svg",
    "language": "ai_machine_learning/Language_Services.svg",
    "ai_search": "app_services/Search_Services.svg",
    "search": "app_services/Search_Services.svg",
    "cognitive_search": "app_services/Search_Services.svg",
    "cosmos": "databases/Azure_Cosmos_DB.svg",
    "cosmos_db": "databases/Azure_Cosmos_DB.svg",
    "sql": "databases/Azure_SQL.svg",
    "azure_sql": "databases/Azure_SQL.svg",
    "sql_database": "databases/Azure_SQL.svg",
    "redis": "databases/Cache_Redis.svg",
    "cache": "databases/Cache_Redis.svg",
    "storage": "storage/Storage_Accounts.svg",
    "storage_account": "storage/Storage_Accounts.svg",
    "blob": "storage/Storage_Accounts.svg",
    "data_lake": "storage/Storage_Accounts.svg",
    "event_hub": "analytics/Event_Hubs.svg",
    "event_hubs": "analytics/Event_Hubs.svg",
    "event_grid": "integration/Event_Grid_Topics.svg",
    "service_bus": "integration/Service_Bus.svg",
    "logic_app": "integration/Logic_Apps.svg",
    "entra": "identity/Azure_Active_Directory.svg",
    "entra_id": "identity/Azure_Active_Directory.svg",
    "aad": "identity/Azure_Active_Directory.svg",
    "active_directory": "identity/Azure_Active_Directory.svg",
    "managed_identity": "identity/Managed_Identities.svg",
    "key_vault": "security/Key_Vaults.svg",
    "keyvault": "security/Key_Vaults.svg",
    "defender": "security/Azure_Defender.svg",
    "sentinel": "security/Azure_Sentinel.svg",
    "monitor": "management_governance/Monitor.svg",
    "log_analytics": "management_governance/Log_Analytics_Workspaces.svg",
    "app_insights": "devops/Application_Insights.svg",
    "application_insights": "devops/Application_Insights.svg",
    "policy": "management_governance/Policy.svg",
    "resource_group": "general/Resource_Groups.svg",
}


def _grp_style(dash: int = 0) -> str:
    return (
        f"swimlane;html=1;whiteSpace=wrap;startSize=34;swimlaneLine=0;rounded=1;arcSize=3;"
        f"fillColor=none;strokeColor={LINE};strokeWidth=1;"
        + ("dashed=1;dashPattern=8 5;" if dash else "dashed=0;")
        + f"swimlaneFillColor={CANVAS};fontSize=14;fontStyle=1;fontColor={INK};"
        f"fontFamily={FF};align=left;spacingLeft=12;verticalAlign=middle;collapsible=0;"
    )


def _vnet_style() -> str:
    """Contenedor de red virtual (VNet): borde azul punteado con etiqueta y CIDR."""
    return (
        "swimlane;html=1;whiteSpace=wrap;startSize=32;rounded=1;arcSize=2;fillColor=none;"
        "strokeColor=#3E6FA3;strokeWidth=1.6;dashed=1;dashPattern=8 5;swimlaneFillColor=#FBFDFF;"
        f"fontSize=13;fontStyle=1;fontColor=#1F3B57;fontFamily={FF};align=left;spacingLeft=12;"
        "verticalAlign=middle;collapsible=0;"
    )


def _subnet_style() -> str:
    """Contenedor de subred anidada dentro de una VNet."""
    return (
        "swimlane;html=1;whiteSpace=wrap;startSize=26;rounded=1;arcSize=5;fillColor=#EEF4FA;"
        "strokeColor=#9DB6CE;strokeWidth=1;dashed=1;dashPattern=4 3;swimlaneFillColor=#F4F8FC;"
        f"fontSize=11;fontStyle=1;fontColor=#2C4A66;fontFamily={FF};align=left;spacingLeft=8;"
        "verticalAlign=middle;collapsible=0;"
    )


def _icon_style(path: str) -> str:
    return (
        f"aspect=fixed;html=1;points=[];image;image=img/lib/azure2/{path};"
        f"verticalLabelPosition=bottom;verticalAlign=top;labelPosition=center;align=center;"
        f"fontSize=12;fontColor={INK2};fontFamily={FF};"
    )


def _box_style() -> str:
    return (
        f"rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor={TINT};strokeColor={LINE2};"
        f"strokeWidth=1;fontSize=12;fontColor={INK};fontFamily={FF};verticalAlign=middle;align=center;"
    )


def _cap_style() -> str:
    return (
        f"text;html=1;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=none;fontFamily={FF};"
        f"fontSize=12;fontColor={INK2};align=center;verticalAlign=top;spacing=0;"
    )


def _edge_style(dash: int = 0) -> str:
    return (
        f"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;jettySize=auto;orthogonalLoop=1;"
        f"strokeColor={ARROW};strokeWidth=1.4;"
        + ("dashed=1;dashPattern=6 4;" if dash else "dashed=0;")
        + f"fontSize=11;fontColor={INK2};fontFamily={FF};endArrow=blockThin;endFill=1;endSize=6;"
        f"labelBackgroundColor=#FFFFFF;"
    )


def _title_style(size: int, bold: int, color: str) -> str:
    return (
        f"text;html=1;fontFamily={FF};fontSize={size};fontStyle={bold};fontColor={color};"
        f"align=left;verticalAlign=middle;strokeColor=none;fillColor=none;"
    )


class _Builder:
    def __init__(self) -> None:
        self.cells: list[str] = []
        self.caps: list[str] = []
        self._n = 1

    def _id(self) -> str:
        self._n += 1
        return f"c{self._n}"

    def vertex(self, value: str, style: str, x: float, y: float, w: float, h: float, parent: str) -> str:
        cid = self._id()
        self.cells.append(
            f'<mxCell id="{cid}" value={quoteattr(value)} style={quoteattr(style)} vertex="1" '
            f'parent="{parent}"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
        )
        return cid

    def caption(self, value: str, x: float, y: float, w: float, h: float) -> None:
        cid = self._id()
        self.caps.append(
            f'<mxCell id="{cid}" value={quoteattr(value)} style={quoteattr(_cap_style())} vertex="1" '
            f'parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
        )

    def edge(self, source: str, target: str, label: str = "") -> None:
        cid = self._id()
        self.cells.append(
            f'<mxCell id="{cid}" value={quoteattr(label)} style={quoteattr(_edge_style())} edge="1" '
            f'parent="1" source="{source}" target="{target}"><mxGeometry relative="1" as="geometry"/></mxCell>'
        )

    def xml(self, titulo: str, width: int, height: int) -> str:
        modelo = (
            f'<mxGraphModel dx="1200" dy="800" grid="0" gridSize="10" guides="1" tooltips="1" '
            f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{width}" '
            f'pageHeight="{height}" math="0" shadow="0"><root><mxCell id="0"/>'
            f'<mxCell id="1" parent="0"/>' + "".join(self.cells) + "".join(self.caps) +
            "</root></mxGraphModel>"
        )
        return (
            f'<mxfile host="app.diagrams.net" agent="arqai-arquitecto">'
            f'<diagram id="arqai" name={quoteattr(titulo[:40] or "Arquitectura")}>{modelo}</diagram></mxfile>'
        )


X0 = 40
CW = 1520
ICON_W = 50
CAP_H = 34
ROW_H = ICON_W + CAP_H + 20
HEADER = 34
PAD = 16
ROW_MAX = 6

# Subredes anidadas dentro de una VNet (disposición horizontal).
SUB_HEADER = 30
SUB_ICON = 44
SUB_ROW = 88
SUB_TOP = 12
SUB_MIN_W = 150
SUB_MAX_W = 210
SUB_GAP = 16

# Palabras clave -> tipo de icono (específicas antes que genéricas).
_PALABRAS_TIPO: list[tuple[str, str]] = [
    ("azure openai", "openai"), ("openai", "openai"), ("gpt", "openai"),
    ("ai search", "ai_search"), ("cognitive search", "ai_search"), ("búsqueda", "ai_search"),
    ("ai foundry", "ai_foundry"), ("foundry", "ai_foundry"), ("ai studio", "ai_foundry"), ("ai hub", "ai_foundry"),
    ("content safety", "content_safety"), ("document intelligence", "document_intelligence"),
    ("form recognizer", "document_intelligence"), ("machine learning", "machine_learning"),
    ("speech", "speech"), ("language", "language"), ("bot", "bot"), ("cognitive", "cognitive"),
    ("api management", "apim"), ("apim", "apim"),
    ("application gateway", "app_gateway"), ("app gateway", "app_gateway"),
    ("front door", "front_door"), ("web application firewall", "waf"), ("waf", "waf"),
    ("firewall", "firewall"), ("ddos", "ddos"), ("bastion", "bastion"),
    ("private endpoint", "private_link"), ("private link", "private_link"),
    ("load balancer", "load_balancer"), ("virtual network", "vnet"), ("vnet", "vnet"),
    ("subnet", "subnet"), ("dns", "dns"), ("vpn", "vpn_gateway"), ("expressroute", "vpn_gateway"),
    ("function", "function"), ("kubernetes", "aks"), ("aks", "aks"),
    ("container app", "container_apps"), ("container registry", "acr"), ("container instance", "aci"),
    ("app service", "app_service"), ("web app", "app_service"), ("virtual machine", "vm"),
    ("cosmos", "cosmos"), ("sql", "sql"), ("redis", "redis"), ("cache", "redis"),
    ("data lake", "storage"), ("blob", "storage"), ("storage", "storage"),
    ("event hub", "event_hub"), ("event grid", "event_grid"), ("service bus", "service_bus"),
    ("logic app", "logic_app"),
    ("managed identity", "managed_identity"), ("entra", "entra"), ("active directory", "entra"),
    ("azure ad", "entra"), ("key vault", "key_vault"), ("defender", "defender"), ("sentinel", "sentinel"),
    ("log analytics", "log_analytics"), ("application insights", "app_insights"), ("app insights", "app_insights"),
    ("monitor", "monitor"), ("policy", "policy"), ("resource group", "resource_group"),
    ("gateway", "vpn_gateway"), ("usuario", "users"), ("user", "users"), ("cliente", "browser"),
    ("browser", "browser"), ("mobile", "mobile"), ("móvil", "mobile"),
]


def _inferir_tipo(nombre: str) -> str:
    n = (nombre or "").lower()
    for sub, tipo in _PALABRAS_TIPO:
        if sub in n:
            return tipo
    return ""


def _normalizar_servicio(serv, idx: int) -> dict:
    if isinstance(serv, str):
        return {"id": f"s{idx}", "tipo": _inferir_tipo(serv), "nombre": serv}
    if isinstance(serv, dict):
        nombre = serv.get("nombre") or serv.get("name") or serv.get("tipo") or serv.get("type") or f"Servicio {idx}"
        tipo = str(serv.get("tipo") or serv.get("type") or "").strip().lower() or _inferir_tipo(str(nombre))
        return {"id": str(serv.get("id") or f"s{idx}"), "tipo": tipo, "nombre": str(nombre)}
    return {"id": f"s{idx}", "tipo": "", "nombre": str(serv)}


def _normalizar_zonas(zonas) -> list[dict]:
    salida: list[dict] = []
    contador = 0

    def _norm_servicios(raw) -> list[dict]:
        nonlocal contador
        out = []
        for s in raw or []:
            out.append(_normalizar_servicio(s, contador))
            contador += 1
        return out

    for zona in zonas or []:
        if isinstance(zona, str):
            salida.append({"nombre": zona, "cidr": "", "servicios": [], "subredes": []})
            continue
        if not isinstance(zona, dict):
            continue
        nombre = str(zona.get("nombre") or zona.get("name") or "Zona")
        cidr = str(zona.get("cidr") or zona.get("rango") or "").strip()
        subredes_raw = zona.get("subredes") or zona.get("subnets") or zona.get("subred") or []
        subredes = []
        for sr in subredes_raw:
            if not isinstance(sr, dict):
                continue
            subredes.append({
                "nombre": str(sr.get("nombre") or sr.get("name") or "Subred"),
                "cidr": str(sr.get("cidr") or sr.get("rango") or "").strip(),
                "servicios": _norm_servicios(sr.get("servicios") or sr.get("services") or []),
            })
        servicios = _norm_servicios(zona.get("servicios") or zona.get("services") or [])
        salida.append({"nombre": nombre, "cidr": cidr, "servicios": servicios, "subredes": subredes})
    return salida


def construir_diagrama(spec: dict) -> dict:
    titulo = spec.get("titulo") or "Arquitectura de referencia · Azure AI Landing Zone"
    zonas = _normalizar_zonas(spec.get("zonas"))
    conexiones = spec.get("conexiones") or []

    # Ancho efectivo: se ensancha si alguna VNet tiene muchas subredes.
    cw = CW
    for zona in zonas:
        subredes = zona.get("subredes") or []
        if subredes:
            n = len(subredes)
            necesario = 2 * PAD + n * SUB_MIN_W + (n - 1) * SUB_GAP
            cw = max(cw, necesario)

    b = _Builder()
    b.vertex(titulo, _title_style(22, 1, INK), X0, 24, cw, 30, "1")
    b.vertex(
        "Arquitectura de referencia · iconos de Azure · alineada a CAF, Well-Architected y Azure AI Landing Zone",
        _title_style(12, 0, INK2), X0, 54, cw, 20, "1",
    )

    ids: dict[str, str] = {}
    ids_nombre: dict[str, str] = {}
    servicios_total = 0
    y = 92
    inner = cw - 2 * PAD

    def _registrar(serv: dict, cell: str) -> None:
        nonlocal servicios_total
        sid = serv.get("id") or f"s{servicios_total}"
        ids[sid] = cell
        nom = (serv.get("nombre") or "").strip().lower()
        if nom:
            ids_nombre[nom] = cell
        servicios_total += 1

    for zona in zonas:
        subredes = zona.get("subredes") or []
        etiqueta = zona.get("nombre", "Zona")
        if zona.get("cidr"):
            etiqueta += f"   ·   {zona['cidr']}"

        if subredes:
            # VNet con subredes dispuestas horizontalmente.
            n = len(subredes)
            sub_w = min(SUB_MAX_W, (inner - (n - 1) * SUB_GAP) / n)
            total_w = n * sub_w + (n - 1) * SUB_GAP
            start_x = PAD + max(0.0, (inner - total_w) / 2)
            max_serv = max((len(s["servicios"]) for s in subredes), default=1)
            sub_h = SUB_HEADER + SUB_TOP + max(1, max_serv) * SUB_ROW + 6
            zona_h = HEADER + 10 + sub_h + 12
            lane = b.vertex(etiqueta, _vnet_style(), X0, y, cw, zona_h, "1")
            for i, sr in enumerate(subredes):
                sx = start_x + i * (sub_w + SUB_GAP)
                sub_label = sr["nombre"] + (f"  ·  {sr['cidr']}" if sr.get("cidr") else "")
                subcell = b.vertex(sub_label, _subnet_style(), round(sx, 1), HEADER + 8, round(sub_w, 1), sub_h, lane)
                for j, serv in enumerate(sr["servicios"]):
                    tipo = (serv.get("tipo") or "").strip().lower()
                    nombre = serv.get("nombre") or tipo
                    path = ICONOS.get(tipo)
                    iy = SUB_HEADER + SUB_TOP + j * SUB_ROW
                    if path:
                        ix = (sub_w - SUB_ICON) / 2
                        cell = b.vertex(nombre, _icon_style(path), round(ix, 1), iy, SUB_ICON, SUB_ICON, subcell)
                    else:
                        bw = min(sub_w - 16, 160)
                        cell = b.vertex(nombre, _box_style(), round((sub_w - bw) / 2, 1), iy + 4, round(bw, 1), 40, subcell)
                    _registrar(serv, cell)
            y += zona_h + 22
        else:
            # Zona plana (iconos en filas). Usa estilo VNet si trae CIDR.
            servicios = zona.get("servicios") or []
            filas = max(1, (len(servicios) + ROW_MAX - 1) // ROW_MAX)
            zona_h = HEADER + 14 + filas * ROW_H
            estilo = _vnet_style() if zona.get("cidr") else _grp_style()
            lane = b.vertex(etiqueta, estilo, X0, y, cw, zona_h, "1")
            for idx, serv in enumerate(servicios):
                fila, col = divmod(idx, ROW_MAX)
                en_fila = min(ROW_MAX, len(servicios) - fila * ROW_MAX)
                step = inner / en_fila
                cx = PAD + step * (col + 0.5)
                iy = HEADER + 14 + fila * ROW_H
                tipo = (serv.get("tipo") or "").strip().lower()
                nombre = serv.get("nombre") or tipo
                path = ICONOS.get(tipo)
                if path:
                    cell = b.vertex("", _icon_style(path), round(cx - ICON_W / 2, 1), iy, ICON_W, ICON_W, lane)
                    ancho = min(step - 8, 180)
                    b.caption(nombre, round(X0 + cx - ancho / 2, 1), y + iy + ICON_W + 2, round(ancho, 1), CAP_H)
                else:
                    ancho = min(step - 8, 150)
                    cell = b.vertex(nombre, _box_style(), round(X0 + cx - ancho / 2, 1), y + iy + 6, round(ancho, 1), 38, "1")
                _registrar(serv, cell)
            y += zona_h + 22

    def _resolver(clave: str):
        c = ids.get(clave)
        return c if c else ids_nombre.get((clave or "").strip().lower())

    for con in conexiones:
        if not isinstance(con, dict):
            continue
        src = _resolver(con.get("desde") or con.get("from") or con.get("source"))
        dst = _resolver(con.get("hacia") or con.get("to") or con.get("target"))
        if src and dst:
            b.edge(src, dst, str(con.get("etiqueta") or con.get("label") or ""))

    altura = y + 20
    return {
        "xml": b.xml(titulo, cw + 2 * X0, int(altura)),
        "titulo": titulo,
        "zonas": [z.get("nombre", "Zona") for z in zonas],
        "n_servicios": servicios_total,
        "n_conexiones": len(conexiones),
    }


PLANTILLA_AI_LANDING_ZONE: dict = {
    "zonas": [
        {
            "nombre": "Identidad y usuarios",
            "servicios": [
                {"id": "user", "tipo": "users", "nombre": "Usuarios"},
                {"id": "entra", "tipo": "entra", "nombre": "Microsoft Entra ID"},
                {"id": "mi", "tipo": "managed_identity", "nombre": "Managed Identity"},
            ],
        },
        {
            "nombre": "Conectividad · Hub VNet",
            "cidr": "10.0.0.0/16",
            "subredes": [
                {
                    "nombre": "Perímetro",
                    "cidr": "10.0.1.0/24",
                    "servicios": [
                        {"id": "fd", "tipo": "front_door", "nombre": "Front Door"},
                        {"id": "waf", "tipo": "waf", "nombre": "WAF"},
                        {"id": "fw", "tipo": "firewall", "nombre": "Azure Firewall"},
                    ],
                },
                {
                    "nombre": "GatewaySubnet",
                    "cidr": "10.0.2.0/24",
                    "servicios": [
                        {"id": "agw", "tipo": "app_gateway", "nombre": "App Gateway"},
                        {"id": "bastion", "tipo": "bastion", "nombre": "Bastion"},
                    ],
                },
            ],
        },
        {
            "nombre": "Aplicación · Spoke VNet",
            "cidr": "10.1.0.0/16",
            "subredes": [
                {
                    "nombre": "APIM subnet",
                    "cidr": "10.1.1.0/24",
                    "servicios": [{"id": "apim", "tipo": "apim", "nombre": "API Management"}],
                },
                {
                    "nombre": "Compute subnet",
                    "cidr": "10.1.2.0/24",
                    "servicios": [
                        {"id": "aca", "tipo": "container_apps", "nombre": "Container Apps"},
                        {"id": "func", "tipo": "function", "nombre": "Functions"},
                    ],
                },
                {
                    "nombre": "AI Foundry subnet",
                    "cidr": "10.1.3.0/24",
                    "servicios": [
                        {"id": "foundry", "tipo": "ai_foundry", "nombre": "Azure AI Foundry"},
                        {"id": "aoai", "tipo": "openai", "nombre": "Azure OpenAI"},
                        {"id": "search", "tipo": "ai_search", "nombre": "AI Search"},
                        {"id": "safety", "tipo": "content_safety", "nombre": "Content Safety"},
                    ],
                },
                {
                    "nombre": "Private Endpoints",
                    "cidr": "10.1.4.0/24",
                    "servicios": [
                        {"id": "pe", "tipo": "private_link", "nombre": "Private Endpoints"},
                        {"id": "kv", "tipo": "key_vault", "nombre": "Key Vault"},
                    ],
                },
            ],
        },
        {
            "nombre": "Datos · Spoke VNet",
            "cidr": "10.2.0.0/16",
            "subredes": [
                {
                    "nombre": "Database subnet",
                    "cidr": "10.2.1.0/24",
                    "servicios": [
                        {"id": "cosmos", "tipo": "cosmos", "nombre": "Cosmos DB"},
                        {"id": "sql", "tipo": "sql", "nombre": "Azure SQL"},
                        {"id": "redis", "tipo": "redis", "nombre": "Cache Redis"},
                    ],
                },
                {
                    "nombre": "Ingest / Storage subnet",
                    "cidr": "10.2.2.0/24",
                    "servicios": [
                        {"id": "storage", "tipo": "storage", "nombre": "Storage / Data Lake"},
                        {"id": "eh", "tipo": "event_hub", "nombre": "Event Hubs"},
                    ],
                },
            ],
        },
        {
            "nombre": "Observabilidad y gobierno",
            "servicios": [
                {"id": "mon", "tipo": "monitor", "nombre": "Azure Monitor"},
                {"id": "log", "tipo": "log_analytics", "nombre": "Log Analytics"},
                {"id": "ai", "tipo": "app_insights", "nombre": "App Insights"},
                {"id": "def", "tipo": "defender", "nombre": "Defender for Cloud"},
                {"id": "pol", "tipo": "policy", "nombre": "Azure Policy"},
            ],
        },
    ],
    "conexiones": [
        {"desde": "user", "hacia": "fd", "etiqueta": "HTTPS"},
        {"desde": "fd", "hacia": "waf"},
        {"desde": "waf", "hacia": "agw"},
        {"desde": "agw", "hacia": "apim"},
        {"desde": "apim", "hacia": "aca"},
        {"desde": "aca", "hacia": "foundry", "etiqueta": "privado"},
        {"desde": "foundry", "hacia": "aoai"},
        {"desde": "foundry", "hacia": "search"},
        {"desde": "aca", "hacia": "cosmos"},
        {"desde": "search", "hacia": "storage"},
        {"desde": "aca", "hacia": "redis"},
    ],
}
