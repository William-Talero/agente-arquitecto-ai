#!/usr/bin/env bash
# Provisiona el grupo de recursos y la infraestructura Foundry del Arquitecto de
# Soluciones AI, asigna el rol de datos al usuario actual y genera backend/.env.
set -euo pipefail

LOCATION="${LOCATION:-eastus2}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-arquitecto-ai}"
PREFIX="${PREFIX:-arqai}"
MODEL_NAME="${MODEL_NAME:-gpt-5.1}"
MODEL_VERSION="${MODEL_VERSION:-2025-11-13}"
MODEL_SKU="${MODEL_SKU:-GlobalStandard}"
MODEL_CAPACITY="${MODEL_CAPACITY:-30}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BICEP_FILE="${ROOT_DIR}/infra/main.bicep"
ENV_FILE="${ROOT_DIR}/backend/.env"

echo "==> Suscripción activa:"
az account show --query "{name:name, id:id}" -o table

PRINCIPAL_ID="$(az ad signed-in-user show --query id -o tsv)"
echo "==> Usuario (objectId): ${PRINCIPAL_ID}"

echo "==> Creando grupo de recursos '${RESOURCE_GROUP}' en '${LOCATION}'..."
az group create -n "${RESOURCE_GROUP}" -l "${LOCATION}" -o none

echo "==> Validando plantilla Bicep..."
az deployment group validate \
  -g "${RESOURCE_GROUP}" \
  -f "${BICEP_FILE}" \
  -p prefix="${PREFIX}" modelName="${MODEL_NAME}" modelVersion="${MODEL_VERSION}" \
     modelSku="${MODEL_SKU}" modelCapacity="${MODEL_CAPACITY}" \
     principalId="${PRINCIPAL_ID}" principalType=User \
  -o none

echo "==> Desplegando infraestructura (puede tardar unos minutos)..."
OUTPUTS="$(az deployment group create \
  --name arquitecto-ai-infra \
  -g "${RESOURCE_GROUP}" \
  -f "${BICEP_FILE}" \
  -p prefix="${PREFIX}" modelName="${MODEL_NAME}" modelVersion="${MODEL_VERSION}" \
     modelSku="${MODEL_SKU}" modelCapacity="${MODEL_CAPACITY}" \
     principalId="${PRINCIPAL_ID}" principalType=User \
  --query properties.outputs -o json)"

PROJECT_ENDPOINT="$(echo "${OUTPUTS}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["projectEndpoint"]["value"])')"
MODEL_DEPLOYMENT="$(echo "${OUTPUTS}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["modelDeploymentName"]["value"])')"

echo "==> Escribiendo ${ENV_FILE}"
cat > "${ENV_FILE}" <<EOF
FOUNDRY_PROJECT_ENDPOINT=${PROJECT_ENDPOINT}
FOUNDRY_MODEL=${MODEL_DEPLOYMENT}
WEB_SEARCH_ENABLED=true
LEARN_MCP_ENABLED=true
LEARN_MCP_URL=https://learn.microsoft.com/api/mcp
EOF

echo ""
echo "==> Listo."
echo "    FOUNDRY_PROJECT_ENDPOINT=${PROJECT_ENDPOINT}"
echo "    FOUNDRY_MODEL=${MODEL_DEPLOYMENT}"
echo "    La propagación del rol RBAC puede tardar 1-5 minutos."
