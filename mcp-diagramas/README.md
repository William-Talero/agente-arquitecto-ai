# MCP de diagramas de arquitectura (Azure draw.io) para Copilot Studio

Servidor **MCP (Streamable HTTP)** que genera diagramas `.drawio` con iconos
oficiales de Azure. Cubre el único hueco que Copilot Studio **no** tiene de fábrica.
Reutiliza `backend/app/infrastructure/diagram.py` (fuente única).

## Herramientas expuestas
- `generar_diagrama_arquitectura(titulo, zonas, conexiones)` → XML `.drawio`.
- `tipos_de_icono_disponibles()` → 92 claves de icono válidas.
- `plantilla_ai_landing_zone()` → spec de ejemplo (zonas/servicios/conexiones).

## 1) Ejecutar localmente
```bash
cd mcp-diagramas
../backend/.venv/bin/pip install -r requirements.txt   # o tu propio venv
../backend/.venv/bin/python server.py
# → endpoint MCP en http://127.0.0.1:8071/mcp
```

## 2) Exponer con una URL pública (Copilot Studio necesita HTTPS)
```bash
# devtunnel (Microsoft) o cualquier túnel HTTPS
devtunnel host -p 8071 --allow-anonymous
# usa la URL https://<algo>.devtunnels.ms/mcp
```

## 3) Conectarlo en Copilot Studio
1. Abre tu agente en https://copilotstudio.microsoft.com → pestaña **Tools**.
2. **Add a tool → New tool → Model Context Protocol**.
3. Rellena:
   - **Server name**: `Diagramas Azure`
   - **Server description**: `Genera diagramas de arquitectura .drawio con iconos oficiales de Azure a partir de zonas, servicios y conexiones.`
   - **Server URL**: `https://<tu-devtunnel>/mcp`
   - **Authentication**: `None`
4. **Add** → Copilot Studio hace el handshake y lista las 3 tools → **Save**.
5. En **Preview**, pide: *"Genera la arquitectura de un chat RAG con Azure OpenAI y AI Search"* y revisa el *activity trace*.

## Resto del agente en Copilot Studio (sin código)
- **Grounding en Microsoft Learn**: Tools → Add a tool → **Model Context Protocol**,
  Server URL `https://learn.microsoft.com/api/mcp`, Auth `None`.
- **Búsqueda web**: activa la capacidad de *web search* del agente.
- **Conocimiento**: añade como *Knowledge* los sitios de CAF/WAF
  (`https://learn.microsoft.com/azure/cloud-adoption-framework/`,
  `https://learn.microsoft.com/azure/well-architected/`). Las citas se muestran solas.

### Instrucciones sugeridas del agente (pegar en "Instructions")
```
Eres un arquitecto de soluciones de IA de Microsoft. Asesoras sobre diseño, adopción,
implementación y operación de soluciones de IA en Azure, alineado a CAF, Well-Architected,
las mejores prácticas y la IA responsable. Responde SIEMPRE en español, claro y accionable.
Antes de afirmar cualquier concepto, guía o práctica, valida la información con la herramienta
de Microsoft Learn y cita las fuentes. Si el usuario pide crear, dibujar o diseñar una
arquitectura o diagrama, usa la herramienta generar_diagrama_arquitectura del servidor
"Diagramas Azure" (primero puedes consultar tipos_de_icono_disponibles) y entrega el .drawio.
No inventes URLs.
```
