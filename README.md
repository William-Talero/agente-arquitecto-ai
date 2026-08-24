# 🏗️ Arquitecto de Soluciones AI · Azure AI Foundry (Prompt Agents)

Asesor conversacional para clientes de Microsoft que apoya **todo el ciclo de vida
de soluciones de IA** —análisis de conceptos de arquitectura, desarrollo,
planteamiento, levantamiento, mejora y operación— alineado al **Cloud Adoption
Framework (CAF)**, al **Well-Architected Framework (WAF)** y a las **mejores
prácticas e IA responsable de Microsoft**.

Los especialistas trabajan bajo una **política de vigencia**: recomiendan siempre lo
último en **disponibilidad general (GA)** de Microsoft —por ejemplo **Microsoft Agent
Framework** como sucesor GA de Semantic Kernel y AutoGen—, marcan explícitamente lo
que está en *Preview* y avisan cuando algo quedó obsoleto o retirado, proponiendo la
ruta de migración oficial. Además puedes **cargar los lineamientos propios de tu
negocio** (estándares internos, servicios aprobados, redes, nomenclatura, seguridad,
costos) para que las reglas de arquitectura se personalicen con las prácticas de tu
organización.

La solución combina una **interfaz web profesional en React + shadcn/ui**, con un
diseño **estilo Microsoft (Fluent) en blanco y negro**, y un backend en **Python**
construido sobre **Microsoft Foundry** con **prompt agents persistentes** (visibles
en el portal de Foundry) invocados por la **Responses API**. Los
especialistas priorizan las **herramientas nativas de Foundry**: **Web** (búsqueda
en tiempo real) y **Microsoft Learn** (documentación oficial vía MCP), y citan sus
fuentes. Además, puedes **adjuntar imágenes o archivos de arquitecturas**
(PNG/JPG, `.drawio`, `.xml`, `.json`, `.bicep`, `.tf`) y el asesor los **evalúa con
visión** según el Well-Architected Framework. También puede **generar diagramas de
arquitectura en draw.io** con iconos oficiales de Azure, estilo de arquitectura de
referencia y estructura basada en la **Azure AI Landing Zone**, listos para descargar.
La interfaz centra el chat, con **historial de conversaciones** (guardado en el
navegador) y modales para especialistas, marcos y lineamientos propios. Los agentes
usan un modelo **GPT‑5** (flagship) en Microsoft Foundry.

```
Agente_Arquitecto_AI/
├── infra/                  # Infraestructura como código (Bicep) + despliegue
│   ├── main.bicep          #   Foundry (AIServices) + proyecto + modelo + RBAC
│   └── deploy.sh           #   Crea el grupo de recursos y genera backend/.env
├── backend/                # Python · arquitectura hexagonal (prompt agents Foundry)
│   └── app/
│       ├── domain/         #   Núcleo puro: modelos, CAF/WAF/ciclo + estándares GA
│       ├── application/    #   Puertos + casos de uso + enrutador de especialistas
│       ├── infrastructure/ #   Adaptador Foundry (Web + Learn) + repo de lineamientos
│       └── interfaces/     #   Controladores HTTP (FastAPI) + DTOs
└── frontend/               # React + Vite + TypeScript + Tailwind + shadcn/ui
```

## 🧠 Arquitectura de agentes

Un **enrutador determinista** (capa de aplicación) selecciona un especialista por
palabras clave. Cada especialista es un **prompt agent persistente y versionado**
creado en el proyecto de Foundry (`project.agents.create_version`) — por eso
**aparecen en el portal de Foundry** (Build › Agents) — e invocado por la
**Responses API** (`agent_reference`), con herramientas **nativas de Foundry** más
herramientas **locales de conocimiento** que generan tarjetas visuales.

| Especialista | Enfoque | Tools nativas | Tools de conocimiento |
|---|---|---|---|
| Estrategia y adopción | CAF (estrategia, plan, gobierno) | Web · Microsoft Learn | `marco_caf`, `ciclo_vida_ai`, `estandares_microsoft`, `lineamientos_negocio` |
| Arquitectura | Well-Architected (5 pilares para IA) | Web · Microsoft Learn | `pilares_waf`, `ciclo_vida_ai`, `estandares_microsoft`, `lineamientos_negocio`, `generar_diagrama_arquitectura` |
| Implementación | RAG, agentes, evaluación, Microsoft Agent Framework | Web · Microsoft Learn | `ciclo_vida_ai`, `marco_caf`, `estandares_microsoft`, `lineamientos_negocio`, `generar_diagrama_arquitectura` |
| Operación e IA responsable | LLMOps, observabilidad, seguridad de contenido | Web · Microsoft Learn | `pilares_waf`, `ciclo_vida_ai`, `estandares_microsoft`, `lineamientos_negocio` |
| Asesor general | Orientación de extremo a extremo | Web · Microsoft Learn | todas |

### 🆕 Política de vigencia (siempre lo último en GA)

Todos los especialistas comparten una política obligatoria (`domain/estandares.py`):

- **Prioriza GA.** Si algo está en *Preview*, se marca como tal, se explica el riesgo y
  se ofrece la alternativa GA.
- **Nunca recomienda tecnología retirada.** Microsoft Agent Framework en lugar de
  Semantic Kernel o AutoGen; Foundry Agent Service en lugar de la API de Assistants;
  Bicep/Terraform con **Azure Verified Modules** en lugar de ARM JSON a mano;
  identidades administradas de Entra ID en lugar de claves.
- **Revalida en tiempo real.** La línea base local es solo un punto de partida: cada
  recomendación se contrasta contra Microsoft Learn (MCP) antes de responder.
- **Traza el estado.** Toda tabla comparativa incluye una columna `Estado`
  (GA / Preview / Retirado).

La herramienta local `estandares_microsoft` expone esa línea base y pinta una tarjeta
con lo vigente, lo que hay que evitar y el enlace oficial.

### 🛡️ Lineamientos propios del negocio

Desde el botón **Lineamientos** de la cabecera puedes subir documentos de texto
(`.md`, `.txt`, `.json`, `.yaml`, `.csv`, `.xml`, `.bicep`, `.tf`…) o escribir reglas
puntuales. Cada documento tiene un **ámbito**: *todos los especialistas* o uno en
concreto.

- Se persisten en `backend/data/lineamientos/` (configurable con `LINEAMIENTOS_DIR`).
- Se inyectan como mensaje `developer` al especialista correspondiente y quedan
  disponibles para la herramienta local `lineamientos_negocio`.
- El agente los aplica como **restricciones de diseño** y declara cuáles usó; si un
  lineamiento contradice la guía oficial de Microsoft en seguridad, cumplimiento o IA
  responsable, **lo señala en vez de acatarlo en silencio**.

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/lineamientos` | Lista los documentos y los ámbitos disponibles |
| `POST` | `/api/lineamientos` | Carga un documento (`nombre`, `ambito`, `categoria`, `texto`) |
| `DELETE` | `/api/lineamientos/{id}` | Elimina un documento |

> **Prioridad de herramientas nativas.** La información autoritativa y en tiempo
> real proviene de **Microsoft Learn** (`https://learn.microsoft.com/api/mcp`) y de
> la **búsqueda Web** de Foundry. Las herramientas locales solo estructuran marcos
> (CAF/WAF/ciclo de vida) como tarjetas. Si el modelo no invoca una tool local, el
> adaptador emite una tarjeta determinista de respaldo para mantener la UI rica.

### Arquitectura hexagonal (puertos y adaptadores)

- **`domain/`** — modelos, conocimiento del negocio (CAF/WAF/ciclo de vida) y la línea
  base de estándares vigentes. Sin dependencias de Azure, Foundry ni frameworks web.
  Es el corazón testeable.
- **`application/`** — define los **puertos** `AsesorPort` y `LineamientosPort`, los
  casos de uso `AsesoriaService` y `LineamientosService`, y el `EspecialistaRouter`.
  Depende solo del dominio.
- **`infrastructure/`** — `FoundryAdvisorAdapter` implementa el puerto creando los
  prompt agents persistentes y llamándolos por la Responses API;
  `LineamientosRepositorio` persiste los documentos del cliente en disco. Adaptadores
  reemplazables sin tocar el dominio.
- **`interfaces/`** — controladores FastAPI y DTOs. Traducen HTTP ↔ casos de uso.
- **`main.py`** — punto de composición: ensambla las capas e inyecta dependencias.

## ☁️ Infraestructura (nuevo grupo de recursos)

`infra/main.bicep` provisiona en un grupo de recursos nuevo:

- **Microsoft Foundry** (`Microsoft.CognitiveServices/accounts`, kind `AIServices`)
  con gestión de proyectos e identidad administrada, y `disableLocalAuth` (solo
  Entra ID).
- **Proyecto de Foundry** (`.../projects`).
- **Deployment de modelo** de chat (`gpt-5.1`, flagship GPT‑5).
- **Asignación de rol** `Azure AI User` (plano de datos) al usuario que despliega.

```bash
# Requiere: az login, Azure CLI, permisos para crear recursos.
LOCATION=eastus2 RESOURCE_GROUP=rg-arquitecto-ai bash infra/deploy.sh
```

El script crea el grupo, despliega la plantilla, asigna RBAC y genera
`backend/.env` con `FOUNDRY_PROJECT_ENDPOINT` y `FOUNDRY_MODEL`.

> Recursos ya desplegados en este entorno: grupo `rg-arquitecto-ai` (eastus2),
> proyecto `arqai-proyecto`, modelo `gpt-5.1`.

## ✅ Requisitos

- **Python 3.10+** (probado con 3.13)
- **Node.js 18+**
- **Azure CLI** con `az login` y acceso al proyecto de Foundry
- La propagación del rol RBAC puede tardar 1–5 minutos tras el despliegue.

## ⚙️ Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# backend/.env lo genera infra/deploy.sh (o cópialo de .env.example)

uvicorn app.main:app --reload --port 8050
```

- Salud: `GET http://localhost:8050/api/health`
- Catálogo (marcos, especialistas y estándares vigentes): `GET /api/catalogo`
- Chat: `POST /api/chat` `{ "session_id": "...", "message": "..." }`
- Lineamientos propios: `GET|POST /api/lineamientos`, `DELETE /api/lineamientos/{id}`
- Métricas Prometheus: `GET /metrics`

## 🎨 Frontend

```bash
cd frontend
npm install
npm run dev            # http://localhost:5186 (proxy /api → :8050)
```

## ▶️ Arranque rápido (backend + frontend)

```bash
bash run.sh
```

## 💬 Ejemplos de consulta

- "¿Cómo estructuro la adopción de IA con el CAF?"
- "Evalúa una arquitectura RAG con el Well-Architected Framework"
- "Diseña un agente con Microsoft Agent Framework sobre Foundry (solo GA)"
- "¿Qué estoy usando que ya esté obsoleto y cómo migro?"
- "Buenas prácticas de IA responsable y seguridad de contenido en producción"
- "¿Qué patrón conviene: RAG, fine-tuning o agentes con herramientas?"

## 🔐 Notas de seguridad y buenas prácticas de IA

- **Sin claves**: autenticación con identidad de Entra ID (`DefaultAzureCredential`)
  y `disableLocalAuth` en el recurso.
- **Grounding y citación**: las respuestas se apoyan en Microsoft Learn y la web,
  y muestran las fuentes.
- **Vigencia**: se prioriza siempre lo que está en disponibilidad general (GA) y se
  marca explícitamente cualquier dependencia en Preview.
- **Lineamientos del cliente**: los documentos de negocio se guardan en local
  (`backend/data/`, excluido de Git) y nunca sustituyen a los controles de seguridad,
  cumplimiento e IA responsable de Microsoft: los conflictos se reportan.
- **Trazabilidad**: cada respuesta indica el especialista, el runtime, los pasos y los
  lineamientos propios aplicados.
- **Observabilidad**: métricas de latencia, uso de tools, tarjetas emitidas y
  lineamientos cargados.
- El contenido de asesoría es orientativo; valida siempre contra la documentación
  oficial de Microsoft y los requisitos del cliente.
