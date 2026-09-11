#!/usr/bin/env bash
# Orquestador de despliegue FRAGMENTADO del Arquitecto de Soluciones AI.
# Despliega por separado: foundry | backend | frontend, los conecta (RBAC + proxy),
# valida conexiones y guarda el estado en .deploy/state.json para despliegues incrementales.
#
# Uso:  ./deploy.sh <comando>
#   foundry     Despliega Foundry (cuenta AI + proyecto + modelo).
#   backend     Despliega el backend (App Service API). Requiere foundry en el estado.
#   frontend    Despliega el frontend (App Service SPA + proxy). Requiere backend en el estado.
#   connect     Conecta backend->foundry (RBAC Azure AI User) y guarda el cableado.
#   validate    Valida salud y conexiones de lo desplegado.
#   status      Muestra el estado guardado (.deploy/state.json).
#   all         foundry -> backend -> frontend -> connect -> validate.
#   destroy     Elimina el grupo de recursos (pide confirmación) y reinicia el estado.
#
# Config por variables de entorno (o .deploy/config.env):
#   SUBSCRIPTION LOCATION RESOURCE_GROUP PREFIX
#   MODEL_NAME MODEL_VERSION MODEL_SKU MODEL_CAPACITY
#   APP_SERVICE_SKU     (B1 por defecto; F1 para pruebas públicas sin cuota de VMs)
#   PRIVATE_NETWORKING=true + (BYO) APP_INTEGRATION_SUBNET_ID PRIVATE_ENDPOINT_SUBNET_ID
#     DNS_ZONE_SERVICES_AI_ID DNS_ZONE_SITES_ID [DNS_ZONE_OPENAI_ID DNS_ZONE_COGNITIVE_ID]
#   DNS_SERVER=<ip|inherit>  (privado) por defecto 168.63.129.16 (Azure DNS); 'inherit' = DNS de la VNet (resolver del hub)
#   FOUNDRY_RG BACKEND_RG FRONTEND_RG (y *_LOCATION)  RG/región por componente (hub-and-spoke multi-RG)
#   SKIP_PUBLISH=true   (modo privado: genera el zip y no publica desde fuera de la VNET)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${ROOT_DIR}/infra"
STATE_DIR="${ROOT_DIR}/.deploy"
STATE_FILE="${STATE_DIR}/state.json"
export STATE_FILE
mkdir -p "$STATE_DIR"
[ -f "$STATE_FILE" ] || echo '{}' > "$STATE_FILE"
[ -f "${STATE_DIR}/config.env" ] && source "${STATE_DIR}/config.env"

LOCATION="${LOCATION:-eastus2}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-arquitecto-ai}"
PREFIX="${PREFIX:-arqai}"
MODEL_NAME="${MODEL_NAME:-gpt-5.1}"
MODEL_VERSION="${MODEL_VERSION:-2025-11-13}"
MODEL_SKU="${MODEL_SKU:-GlobalStandard}"
MODEL_CAPACITY="${MODEL_CAPACITY:-30}"
APP_SERVICE_SKU="${APP_SERVICE_SKU:-B1}"
PRIVATE_NETWORKING="${PRIVATE_NETWORKING:-false}"
AZURE_AI_USER_ROLE="53ca6127-db72-4b80-b1b0-d745d6d5456d"
# RG y región por componente (por defecto, los globales) — útil en hub-and-spoke multi-RG.
FOUNDRY_RG="${FOUNDRY_RG:-$RESOURCE_GROUP}";   FOUNDRY_LOCATION="${FOUNDRY_LOCATION:-$LOCATION}"
BACKEND_RG="${BACKEND_RG:-$RESOURCE_GROUP}";   BACKEND_LOCATION="${BACKEND_LOCATION:-$LOCATION}"
FRONTEND_RG="${FRONTEND_RG:-$RESOURCE_GROUP}"; FRONTEND_LOCATION="${FRONTEND_LOCATION:-$LOCATION}"

c_ok(){ printf '\033[0;32m%s\033[0m\n' "$*"; }
c_info(){ printf '\033[0;36m%s\033[0m\n' "$*"; }
c_warn(){ printf '\033[0;33m%s\033[0m\n' "$*"; }
c_err(){ printf '\033[0;31m%s\033[0m\n' "$*" >&2; }
die(){ c_err "ERROR: $*"; exit 1; }
now(){ date -u +%Y-%m-%dT%H:%M:%SZ; }
need(){ command -v "$1" >/dev/null 2>&1 || die "falta '$1'. Instálalo y reintenta."; }

# --- Estado (JSON) ---
st_get(){ python3 - "$1" <<'PY'
import json,os,sys
d=json.load(open(os.environ['STATE_FILE']))
v=d
for k in sys.argv[1].split('.'):
    v=v.get(k) if isinstance(v,dict) else None
    if v is None: break
print('' if v is None else v)
PY
}
st_set(){ python3 - "$1" "$2" <<'PY'
import json,os,sys
f=os.environ['STATE_FILE']; d=json.load(open(f)); d[sys.argv[1]]=sys.argv[2]
json.dump(d,open(f,'w'),indent=2,ensure_ascii=False)
PY
}
st_set_component(){ python3 - "$1" "$2" <<'PY'
import json,os,sys
f=os.environ['STATE_FILE']; d=json.load(open(f)); d[sys.argv[1]]=json.loads(sys.argv[2])
json.dump(d,open(f,'w'),indent=2,ensure_ascii=False)
PY
}
py_obj(){ python3 - "$@" <<'PY'
import json,sys
a=sys.argv[1:]
print(json.dumps({a[i]:a[i+1] for i in range(0,len(a),2)}, ensure_ascii=False))
PY
}
get_out(){ printf '%s' "$1" | python3 -c "import sys,json;print(json.load(sys.stdin)['$2']['value'])"; }

require_azure(){
  need az; need python3
  if ! az account show >/dev/null 2>&1; then
    c_info "No hay sesión de Azure. Abriendo 'az login'..."; az login >/dev/null
  fi
  [ -n "${SUBSCRIPTION:-}" ] && az account set --subscription "$SUBSCRIPTION"
  st_set subscription "$(az account show --query id -o tsv)"
  st_set location "$LOCATION"; st_set resourceGroup "$RESOURCE_GROUP"
  st_set prefix "$PREFIX"; st_set privateNetworking "$PRIVATE_NETWORKING"
}

ensure_rg(){ # ensure_rg <rg> <location>
  local rg="$1" loc="$2"
  az group show -n "$rg" >/dev/null 2>&1 || {
    c_info "Creando grupo de recursos '$rg' en '$loc'..."
    az group create -n "$rg" -l "$loc" -o none
  }
}

# Parámetros de red privada para backend/frontend (App Service)
private_params_appservice(){
  [[ "$PRIVATE_NETWORKING" == "true" ]] || { echo ""; return; }
  : "${APP_INTEGRATION_SUBNET_ID:?Falta APP_INTEGRATION_SUBNET_ID (subred delegada a Microsoft.Web/serverFarms)}"
  : "${PRIVATE_ENDPOINT_SUBNET_ID:?Falta PRIVATE_ENDPOINT_SUBNET_ID}"
  : "${DNS_ZONE_SITES_ID:?Falta DNS_ZONE_SITES_ID (privatelink.azurewebsites.net)}"
  local dns="${DNS_SERVER:-168.63.129.16}"; [ "$dns" = "inherit" ] && dns=""
  echo "privateNetworking=true appIntegrationSubnetId=${APP_INTEGRATION_SUBNET_ID} privateEndpointSubnetId=${PRIVATE_ENDPOINT_SUBNET_ID} dnsZoneSitesId=${DNS_ZONE_SITES_ID} dnsServer=${dns}"
}

publish_zip(){ # publish_zip <rg> <webapp> <zip> <label>
  local rg="$1" name="$2" pkg="$3" label="$4"
  if [[ "$PRIVATE_NETWORKING" == "true" ]]; then
    c_warn "  [$label] App Service PRIVADO: la publicación requiere línea de vista a la VNET."
  fi
  if [[ "${SKIP_PUBLISH:-false}" == "true" ]]; then
    local outpkg="${ROOT_DIR}/${label}-package.zip"; cp "$pkg" "$outpkg"
    c_warn "  [$label] SKIP_PUBLISH=true. Paquete: ${outpkg}"
    c_warn "  Publica desde la VNET: az webapp deploy -g ${rg} -n ${name} --src-path ${outpkg} --type zip"
    return
  fi
  az webapp deploy --resource-group "$rg" --name "$name" --src-path "$pkg" --type zip -o none
}

# ------------------------- FOUNDRY -------------------------
cmd_foundry(){
  require_azure; ensure_rg "$FOUNDRY_RG" "$FOUNDRY_LOCATION"
  local extra=""
  if [[ "$PRIVATE_NETWORKING" == "true" ]]; then
    : "${PRIVATE_ENDPOINT_SUBNET_ID:?Falta PRIVATE_ENDPOINT_SUBNET_ID}"
    : "${DNS_ZONE_SERVICES_AI_ID:?Falta DNS_ZONE_SERVICES_AI_ID (privatelink.services.ai.azure.com)}"
    extra="privateNetworking=true privateEndpointSubnetId=${PRIVATE_ENDPOINT_SUBNET_ID} dnsZoneServicesAiId=${DNS_ZONE_SERVICES_AI_ID} dnsZoneOpenAiId=${DNS_ZONE_OPENAI_ID:-} dnsZoneCognitiveId=${DNS_ZONE_COGNITIVE_ID:-}"
  fi
  local pid; pid="$(az ad signed-in-user show --query id -o tsv 2>/dev/null || echo '')"
  c_info "==> [foundry] Desplegando cuenta AI + proyecto + modelo (${MODEL_NAME})..."
  local out
  out="$(az deployment group create --name arqai-foundry -g "$FOUNDRY_RG" -f "${INFRA_DIR}/foundry.bicep" \
    -p prefix="$PREFIX" location="$FOUNDRY_LOCATION" modelName="$MODEL_NAME" modelVersion="$MODEL_VERSION" \
       modelSku="$MODEL_SKU" modelCapacity="$MODEL_CAPACITY" principalId="$pid" principalType=User \
       ${extra} --query properties.outputs -o json)"
  local acc accid ep model proj
  acc="$(get_out "$out" accountName)"; accid="$(get_out "$out" accountId)"
  ep="$(get_out "$out" projectEndpoint)"; model="$(get_out "$out" modelDeploymentName)"; proj="$(get_out "$out" projectName)"
  st_set_component foundry "$(py_obj deployedAt "$(now)" resourceGroup "$FOUNDRY_RG" accountName "$acc" accountId "$accid" projectName "$proj" projectEndpoint "$ep" modelDeploymentName "$model")"
  c_ok "==> [foundry] OK  endpoint=$ep  modelo=$model"
}

# ------------------------- BACKEND -------------------------
cmd_backend(){
  require_azure; ensure_rg "$BACKEND_RG" "$BACKEND_LOCATION"
  local ep model; ep="$(st_get foundry.projectEndpoint)"; model="$(st_get foundry.modelDeploymentName)"
  [ -n "$ep" ] || die "No hay estado de 'foundry'. Ejecuta primero: ./deploy.sh foundry"
  local extra; extra="$(private_params_appservice)"
  c_info "==> [backend] Desplegando App Service (API)..."
  local out
  out="$(az deployment group create --name arqai-backend -g "$BACKEND_RG" -f "${INFRA_DIR}/backend.bicep" \
    -p prefix="$PREFIX" location="$BACKEND_LOCATION" appServiceSku="$APP_SERVICE_SKU" \
       foundryProjectEndpoint="$ep" foundryModel="$model" ${extra} --query properties.outputs -o json)"
  local name url host pid
  name="$(get_out "$out" webAppName)"; url="$(get_out "$out" url)"; host="$(get_out "$out" hostname)"; pid="$(get_out "$out" principalId)"
  st_set_component backend "$(py_obj deployedAt "$(now)" resourceGroup "$BACKEND_RG" webAppName "$name" url "$url" hostname "$host" principalId "$pid")"
  c_info "==> [backend] Empaquetando y publicando código..."
  local staging pkgdir pkg
  staging="$(mktemp -d)"; pkgdir="$(mktemp -d)"; pkg="${pkgdir}/backend.zip"
  cp -R "${ROOT_DIR}/backend/app" "${staging}/app"
  cp -R "${ROOT_DIR}/backend/data" "${staging}/data" 2>/dev/null || true
  cp "${ROOT_DIR}/backend/requirements.txt" "${staging}/requirements.txt"
  find "$staging" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
  ( cd "$staging" && zip -r -q "$pkg" . )
  publish_zip "$BACKEND_RG" "$name" "$pkg" "backend"
  rm -rf "$staging" "$pkgdir"
  c_ok "==> [backend] OK  $url"
}

# ------------------------- FRONTEND ------------------------
cmd_frontend(){
  require_azure; ensure_rg "$FRONTEND_RG" "$FRONTEND_LOCATION"
  local beurl; beurl="$(st_get backend.url)"
  [ -n "$beurl" ] || die "No hay estado de 'backend'. Ejecuta primero: ./deploy.sh backend"
  local extra; extra="$(private_params_appservice)"
  c_info "==> [frontend] Desplegando App Service (SPA + proxy -> $beurl)..."
  local out
  out="$(az deployment group create --name arqai-frontend -g "$FRONTEND_RG" -f "${INFRA_DIR}/frontend.bicep" \
    -p prefix="$PREFIX" location="$FRONTEND_LOCATION" appServiceSku="$APP_SERVICE_SKU" backendUrl="$beurl" ${extra} --query properties.outputs -o json)"
  local name url host
  name="$(get_out "$out" webAppName)"; url="$(get_out "$out" url)"; host="$(get_out "$out" hostname)"
  st_set_component frontend "$(py_obj deployedAt "$(now)" resourceGroup "$FRONTEND_RG" webAppName "$name" url "$url" hostname "$host")"
  need node; need npm
  c_info "==> [frontend] Compilando SPA..."
  npm --prefix "${ROOT_DIR}/frontend" ci
  npm --prefix "${ROOT_DIR}/frontend" run build
  c_info "==> [frontend] Empaquetando y publicando..."
  local staging pkgdir pkg
  staging="$(mktemp -d)"; pkgdir="$(mktemp -d)"; pkg="${pkgdir}/frontend.zip"
  cp -R "${ROOT_DIR}/frontend/dist" "${staging}/dist"
  cp "${ROOT_DIR}/frontend/server.mjs" "${staging}/server.mjs"
  cat > "${staging}/package.json" <<'PJ'
{
  "name": "arqai-frontend-server",
  "private": true,
  "type": "module",
  "scripts": { "start": "node server.mjs" }
}
PJ
  ( cd "$staging" && zip -r -q "$pkg" . )
  publish_zip "$FRONTEND_RG" "$name" "$pkg" "frontend"
  rm -rf "$staging" "$pkgdir"
  c_ok "==> [frontend] OK  $url"
}

# ------------------------- CONNECT -------------------------
cmd_connect(){
  require_azure
  local accid pid; accid="$(st_get foundry.accountId)"; pid="$(st_get backend.principalId)"
  [ -n "$accid" ] || die "Falta 'foundry' en el estado."
  [ -n "$pid" ] || die "Falta 'backend' en el estado."
  c_info "==> [connect] Asignando 'Azure AI User' a la identidad del backend sobre Foundry..."
  if az role assignment create --assignee-object-id "$pid" --assignee-principal-type ServicePrincipal \
       --role "$AZURE_AI_USER_ROLE" --scope "$accid" -o none 2>/dev/null; then
    c_ok "  rol asignado."
  else
    c_warn "  rol ya existente o sin permiso para crearlo (revisa manualmente)."
  fi
  # Reiniciar el backend para que su asesor reintente la conexión con el RBAC ya asignado.
  local bname brg; bname="$(st_get backend.webAppName)"; brg="$(st_get backend.resourceGroup)"; [ -n "$brg" ] || brg="$RESOURCE_GROUP"
  if [ -n "$bname" ]; then
    c_info "  reiniciando backend '$bname' para reintentar la conexión a Foundry..."
    az webapp restart -g "$brg" -n "$bname" -o none 2>/dev/null || true
  fi
  st_set_component connect "$(py_obj connectedAt "$(now)" backendPrincipalId "$pid" foundryAccountId "$accid")"
  c_ok "==> [connect] OK (propagación RBAC 1-5 min)"
}

# ------------------------- VALIDATE ------------------------
cmd_validate(){
  require_azure
  local rc=0
  c_info "== VALIDACIÓN DE CONEXIONES =="
  local acc accid frg; acc="$(st_get foundry.accountName)"; accid="$(st_get foundry.accountId)"; frg="$(st_get foundry.resourceGroup)"; [ -n "$frg" ] || frg="$RESOURCE_GROUP"
  if [ -n "$acc" ]; then
    local pstate; pstate="$(az cognitiveservices account show -g "$frg" -n "$acc" --query properties.provisioningState -o tsv 2>/dev/null || echo '?')"
    echo "  Foundry ($acc): provisioningState=$pstate"; [ "$pstate" = "Succeeded" ] || rc=1
    if [[ "$PRIVATE_NETWORKING" == "true" && -n "$accid" ]]; then
      local pe; pe="$(az network private-endpoint-connection list --id "$accid" --query "[].properties.privateLinkServiceConnectionState.status" -o tsv 2>/dev/null | tr '\n' ',' )"
      echo "    private endpoint status: ${pe:-(ninguno)}"
    fi
  else echo "  Foundry: (no desplegado)"; fi
  local bpid; bpid="$(st_get backend.principalId)"
  if [ -n "$accid" ] && [ -n "$bpid" ]; then
    local ra; ra="$(az role assignment list --assignee "$bpid" --scope "$accid" --query "length([?contains(roleDefinitionId, '$AZURE_AI_USER_ROLE')])" -o tsv 2>/dev/null || echo 0)"
    if [ "${ra:-0}" != "0" ]; then echo "  RBAC backend->foundry (Azure AI User): OK"; else echo "  RBAC backend->foundry (Azure AI User): FALTA"; rc=1; fi
  fi
  if [[ "$PRIVATE_NETWORKING" == "true" ]]; then
    c_warn "  (modo privado: la salud HTTP se valida desde dentro de la VNET; aquí solo control-plane)"
    local comp n crg
    for comp in backend frontend; do
      n="$(st_get ${comp}.webAppName)"; crg="$(st_get ${comp}.resourceGroup)"; [ -n "$crg" ] || crg="$RESOURCE_GROUP"
      [ -n "$n" ] && echo "  ${comp} state: $(az webapp show -g "$crg" -n "$n" --query state -o tsv 2>/dev/null || echo '?')"
    done
  else
    local beurl feurl
    beurl="$(st_get backend.url)"; feurl="$(st_get frontend.url)"
    if [ -n "$beurl" ]; then
      local h; h="$(curl -s -m 25 "$beurl/api/health" || echo '')"
      echo "  Backend $beurl/api/health -> ${h:-(sin respuesta)}"
      echo "$h" | grep -q '"status":"ok"' || rc=1
    fi
    if [ -n "$feurl" ]; then
      local code; code="$(curl -s -m 25 -o /dev/null -w '%{http_code}' "$feurl/" || echo 000)"
      echo "  Frontend $feurl/ -> HTTP $code"; [ "$code" = "200" ] || rc=1
      local fh; fh="$(curl -s -m 25 "$feurl/api/health" || echo '')"
      echo "  Frontend proxy /api/health -> ${fh:-(sin respuesta)}"
      echo "$fh" | grep -q '"status":"ok"' || rc=1
    fi
  fi
  if [ $rc -eq 0 ]; then c_ok "== VALIDACIÓN OK =="; else c_warn "== VALIDACIÓN con observaciones (ver arriba) =="; fi
  return $rc
}

cmd_status(){ [ -f "$STATE_FILE" ] && python3 -m json.tool "$STATE_FILE" || echo '{}'; }

cmd_destroy(){
  require_azure
  local rgs
  rgs="$(python3 - <<'PY'
import json,os
d=json.load(open(os.environ['STATE_FILE']))
s=[]
for c in ('foundry','backend','frontend'):
    rg=(d.get(c) or {}).get('resourceGroup')
    if rg and rg not in s: s.append(rg)
if not s and d.get('resourceGroup'): s=[d['resourceGroup']]
print('\n'.join(s))
PY
)"
  [ -n "$rgs" ] || rgs="$RESOURCE_GROUP"
  c_warn "Esto ELIMINA estos grupos de recursos y TODO su contenido:"
  echo "$rgs" | sed 's/^/  - /'
  if [[ "${1:-}" != "--yes" && "${AUTO_YES:-false}" != "true" ]]; then
    read -r -p "Escribe 'ELIMINAR' para confirmar: " ans
    [ "$ans" = "ELIMINAR" ] || die "cancelado."
  fi
  while IFS= read -r rg; do
    [ -n "$rg" ] || continue
    c_info "Eliminando '$rg'..."
    az group delete -n "$rg" --yes -o none
  done <<< "$rgs"
  echo '{}' > "$STATE_FILE"
  c_ok "Grupos eliminados y estado reiniciado."
}

cmd="${1:-help}"; shift || true
case "$cmd" in
  foundry)  cmd_foundry "$@";;
  backend)  cmd_backend "$@";;
  frontend) cmd_frontend "$@";;
  connect)  cmd_connect "$@";;
  validate) cmd_validate "$@";;
  status)   cmd_status "$@";;
  all)      cmd_foundry; cmd_backend; cmd_frontend; cmd_connect; cmd_validate || true;;
  destroy)  cmd_destroy "$@";;
  help|-h|--help) awk 'NR>1 && /^#/{sub(/^# ?/,"");print;next} NR>1{exit}' "$0";;
  *) die "comando desconocido: '$cmd' (usa: foundry|backend|frontend|connect|validate|status|all|destroy)";;
esac
