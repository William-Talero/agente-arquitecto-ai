// Componente BACKEND: App Service (FastAPI, solo API) + VNet integration + private endpoint opcional.
// Se despliega tras Foundry. Recibe el endpoint del proyecto por parámetro (desde el estado).
// El RBAC de su identidad hacia Foundry se hace en el paso 'connect' (desacoplado / cross-RG).

@description('Región de Azure.')
param location string = resourceGroup().location

@description('Prefijo para nombres únicos.')
@minLength(3)
@maxLength(12)
param prefix string = 'arqai'

@description('SKU del plan (Linux). B1+ para modo privado; F1 solo para pruebas públicas.')
param appServiceSku string = 'B1'
param pythonVersion string = '3.12'

@description('Endpoint del proyecto Foundry (del estado del componente foundry).')
param foundryProjectEndpoint string
@description('Nombre del deployment de modelo (del estado del componente foundry).')
param foundryModel string

@description('Modo de red privada: sin acceso público + VNet integration + private endpoint.')
param privateNetworking bool = false
@description('Subred delegada a Microsoft.Web/serverFarms para la integración VNet.')
param appIntegrationSubnetId string = ''
@description('Subred para el private endpoint del App Service.')
param privateEndpointSubnetId string = ''
@description('Private DNS Zone privatelink.azurewebsites.net.')
param dnsZoneSitesId string = ''

var suffix = uniqueString(resourceGroup().id)
var planName = '${prefix}-be-plan'
var webAppName = toLower('${prefix}-be-${suffix}')
var publicAccess = privateNetworking ? 'Disabled' : 'Enabled'
var privateAppSettings = privateNetworking ? [
  {
    name: 'WEBSITE_DNS_SERVER'
    value: '168.63.129.16'
  }
  {
    name: 'WEBSITE_VNET_ROUTE_ALL'
    value: '1'
  }
] : []

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: planName
  location: location
  sku: {
    name: appServiceSku
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: webAppName
  location: location
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    publicNetworkAccess: publicAccess
    virtualNetworkSubnetId: privateNetworking ? appIntegrationSubnetId : null
    siteConfig: {
      linuxFxVersion: 'PYTHON|${pythonVersion}'
      appCommandLine: 'python -m uvicorn app.main:app --host 0.0.0.0 --port 8000'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      vnetRouteAllEnabled: privateNetworking
      appSettings: concat([
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'FOUNDRY_PROJECT_ENDPOINT'
          value: foundryProjectEndpoint
        }
        {
          name: 'FOUNDRY_MODEL'
          value: foundryModel
        }
        {
          name: 'WEB_SEARCH_ENABLED'
          value: 'true'
        }
        {
          name: 'LEARN_MCP_ENABLED'
          value: 'true'
        }
        {
          name: 'LEARN_MCP_URL'
          value: 'https://learn.microsoft.com/api/mcp'
        }
      ], privateAppSettings)
    }
  }
}

resource webAppPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = if (privateNetworking && !empty(dnsZoneSitesId)) {
  name: '${webAppName}-pe'
  location: location
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${webAppName}-conn'
        properties: {
          privateLinkServiceId: webApp.id
          groupIds: [
            'sites'
          ]
        }
      }
    ]
  }
}

resource webAppPrivateDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = if (privateNetworking && !empty(dnsZoneSitesId)) {
  parent: webAppPrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'sites'
        properties: {
          privateDnsZoneId: dnsZoneSitesId
        }
      }
    ]
  }
}

output webAppName string = webApp.name
output webAppId string = webApp.id
output hostname string = webApp.properties.defaultHostName
output url string = 'https://${webApp.properties.defaultHostName}'
output principalId string = webApp.identity.principalId
