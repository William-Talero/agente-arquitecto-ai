#!/usr/bin/env bash
# Despliega y publica TODA la solución (Foundry + App Service + backend + frontend).
# Pregunta el destino (suscripción, región, grupo de recursos, prefijo), crea la
# infraestructura con Bicep, compila el frontend y publica el backend que sirve el SPA.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BICEP_FILE="${ROOT_DIR}/infra/main.bicep"

# Valores por defecto (cualquiera se puede sobreescribir con variables de entorno).
LOCATION="${LOCATION:-eastus2}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-arquitecto-ai}"
PREFIX="${PREFIX:-arqai}"
MODEL_NAME="${MODEL_NAME:-gpt-5.1}"
MODEL_VERSION="${MODEL_VERSION:-2025-11-13}"
MODEL_SKU="${MODEL_SKU:-GlobalStandard}"
MODEL_CAPACITY="${MODEL_CAPACITY:-30}"
APP_SERVICE_SKU="${APP_SERVICE_SKU:-B1}"

# Modo de red privada (BYO VNET + Private DNS Zones existentes). Off por defecto.
PRIVATE_NETWORKING="${PRIVATE_NETWORKING:-false}"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "ERROR: falta '$1'. Instálalo y reintenta." >&2; exit 1; }
}
need az; need node; need npm; need python3; need zip

# --- Sesión de Azure ---
if ! az account show >/dev/null 2>&1; then
  echo "==> No hay sesión de Azure. Abriendo 'az login'..."
  az login >/dev/null
fi

prompt_default() {
  local label="$1" cur="$2" ans
  if [[ -t 0 ]]; then
    read -r -p "${label} [${cur}]: " ans
    printf '%s' "${ans:-$cur}"
  else
    printf '%s' "$cur"
  fi
}

echo "==> Suscripción activa:"
az account show --query "{nombre:name, id:id}" -o table

if [[ -n "${AZURE_SUBSCRIPTION:-}" ]]; then
  az account set --subscription "${AZURE_SUBSCRIPTION}"
elif [[ -t 0 ]]; then
  read -r -p "¿Usar esta suscripción? (Enter=sí, o pega un ID/nombre): " sub
  [[ -n "${sub:-}" ]] && az account set --subscription "$sub"
fi

# --- Preguntar dónde desplegar ---
LOCATION="$(prompt_default "Región de Azure" "$LOCATION")"
RESOURCE_GROUP="$(prompt_default "Grupo de recursos" "$RESOURCE_GROUP")"
PREFIX="$(prompt_default "Prefijo de nombres" "$PREFIX")"

PRINCIPAL_ID="$(az ad signed-in-user show --query id -o tsv)"

# --- Parámetros de red privada (si aplica) ---
EXTRA_PARAMS=""
if [[ "${PRIVATE_NETWORKING}" == "true" ]]; then
  : "${APP_INTEGRATION_SUBNET_ID:?Falta APP_INTEGRATION_SUBNET_ID (subred delegada a Microsoft.Web/serverFarms)}"
  : "${PRIVATE_ENDPOINT_SUBNET_ID:?Falta PRIVATE_ENDPOINT_SUBNET_ID (subred para los private endpoints)}"
  : "${DNS_ZONE_SERVICES_AI_ID:?Falta DNS_ZONE_SERVICES_AI_ID (privatelink.services.ai.azure.com)}"
  : "${DNS_ZONE_SITES_ID:?Falta DNS_ZONE_SITES_ID (privatelink.azurewebsites.net)}"
  echo "==> Modo de red privada ACTIVADO (Foundry y App Service sin acceso público)."
  EXTRA_PARAMS="privateNetworking=true"
  EXTRA_PARAMS="${EXTRA_PARAMS} appIntegrationSubnetId=${APP_INTEGRATION_SUBNET_ID}"
  EXTRA_PARAMS="${EXTRA_PARAMS} privateEndpointSubnetId=${PRIVATE_ENDPOINT_SUBNET_ID}"
  EXTRA_PARAMS="${EXTRA_PARAMS} dnsZoneServicesAiId=${DNS_ZONE_SERVICES_AI_ID}"
  EXTRA_PARAMS="${EXTRA_PARAMS} dnsZoneOpenAiId=${DNS_ZONE_OPENAI_ID:-}"
  EXTRA_PARAMS="${EXTRA_PARAMS} dnsZoneCognitiveId=${DNS_ZONE_COGNITIVE_ID:-}"
  EXTRA_PARAMS="${EXTRA_PARAMS} dnsZoneSitesId=${DNS_ZONE_SITES_ID}"
fi

echo "==> Creando grupo de recursos '${RESOURCE_GROUP}' en '${LOCATION}'..."
az group create -n "$RESOURCE_GROUP" -l "$LOCATION" -o none

echo "==> Desplegando infraestructura (Foundry + modelo + App Service + RBAC)..."
OUTPUTS="$(az deployment group create \
  --name arquitecto-ai-infra \
  -g "$RESOURCE_GROUP" \
  -f "$BICEP_FILE" \
  -p prefix="$PREFIX" location="$LOCATION" \
     modelName="$MODEL_NAME" modelVersion="$MODEL_VERSION" \
     modelSku="$MODEL_SKU" modelCapacity="$MODEL_CAPACITY" \
     appServiceSku="$APP_SERVICE_SKU" \
     principalId="$PRINCIPAL_ID" principalType=User \
     ${EXTRA_PARAMS} \
  --query properties.outputs -o json)"

get() { printf '%s' "$OUTPUTS" | python3 -c "import sys,json;print(json.load(sys.stdin)['$1']['value'])"; }
PROJECT_ENDPOINT="$(get projectEndpoint)"
MODEL_DEPLOYMENT="$(get modelDeploymentName)"
WEBAPP_NAME="$(get webAppName)"
WEBAPP_URL="$(get webAppUrl)"

# --- backend/.env para desarrollo local ---
echo "==> Escribiendo backend/.env (uso local)"
cat > "${ROOT_DIR}/backend/.env" <<EOF
FOUNDRY_PROJECT_ENDPOINT=${PROJECT_ENDPOINT}
FOUNDRY_MODEL=${MODEL_DEPLOYMENT}
WEB_SEARCH_ENABLED=true
LEARN_MCP_ENABLED=true
LEARN_MCP_URL=https://learn.microsoft.com/api/mcp
EOF

# --- Compilar frontend ---
echo "==> Compilando el frontend..."
npm --prefix "${ROOT_DIR}/frontend" ci
npm --prefix "${ROOT_DIR}/frontend" run build

# --- Empaquetar backend + SPA compilado ---
echo "==> Empaquetando la aplicación..."
STAGING="$(mktemp -d)"
PKG_DIR="$(mktemp -d)"
PKG="${PKG_DIR}/app.zip"
trap 'rm -rf "$STAGING" "$PKG_DIR"' EXIT

cp -R "${ROOT_DIR}/backend/app" "${STAGING}/app"
cp -R "${ROOT_DIR}/backend/data" "${STAGING}/data"
cp "${ROOT_DIR}/backend/requirements.txt" "${STAGING}/requirements.txt"
cp -R "${ROOT_DIR}/frontend/dist" "${STAGING}/webroot"
find "$STAGING" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true

( cd "$STAGING" && zip -r -q "$PKG" . )

if [[ "${PRIVATE_NETWORKING}" == "true" ]]; then
  echo "==> NOTA (red privada): el App Service tiene acceso entrante PRIVADO."
  echo "    La publicación solo funciona desde un host con línea de vista a la VNET"
  echo "    (agente self-hosted, jumpbox, VPN o Bastion). Fuera de la red, exporta"
  echo "    SKIP_PUBLISH=true y publica el paquete desde dentro de la VNET."
fi

if [[ "${SKIP_PUBLISH:-false}" == "true" ]]; then
  OUT_PKG="${ROOT_DIR}/app-package.zip"
  cp "$PKG" "$OUT_PKG"
  echo "==> SKIP_PUBLISH=true. Paquete listo en: ${OUT_PKG}"
  echo "    Publícalo desde un host con acceso a la VNET con:"
  echo "    az webapp deploy -g ${RESOURCE_GROUP} -n ${WEBAPP_NAME} --src-path ${OUT_PKG} --type zip"
else
  echo "==> Publicando en App Service '${WEBAPP_NAME}'..."
  az webapp deploy \
    --resource-group "$RESOURCE_GROUP" \
    --name "$WEBAPP_NAME" \
    --src-path "$PKG" --type zip -o none
fi

echo ""
echo "==> Listo. Solución publicada:"
echo "    App (web):  ${WEBAPP_URL}"
echo "    Health:     ${WEBAPP_URL}/api/health"
echo "    Foundry:    ${PROJECT_ENDPOINT}"
echo "    Modelo:     ${MODEL_DEPLOYMENT}"
echo "    Nota: el primer arranque tarda 1-2 min (Oryx instala dependencias) y la"
echo "          propagación del rol RBAC puede tardar 1-5 min."
