@description('Región de Azure para todos los recursos.')
param location string = resourceGroup().location

@description('Nombre base (prefijo) para componer nombres únicos de recursos.')
@minLength(3)
@maxLength(12)
param prefix string = 'arqai'

@description('Nombre del deployment de modelo de chat que usarán los agentes.')
param modelName string = 'gpt-5.1'

@description('Versión del modelo de chat.')
param modelVersion string = '2025-11-13'

@description('SKU del deployment del modelo.')
param modelSku string = 'GlobalStandard'

@description('Capacidad (miles de TPM) del deployment del modelo.')
param modelCapacity int = 30

@description('ObjectId (Entra ID) del principal que usará el proyecto; recibe el rol de datos "Azure AI User".')
param principalId string = ''

@description('Tipo de principal para la asignación de rol.')
@allowed(['User', 'ServicePrincipal', 'Group'])
param principalType string = 'User'

@description('Versión del runtime de Python del App Service que hospeda el backend.')
param pythonVersion string = '3.12'

@description('SKU del plan de App Service (Linux) que sirve backend + frontend.')
param appServiceSku string = 'B1'

@description('Activa el modo de red privada: Foundry y App Service sin acceso público, con VNet integration y private endpoints.')
param privateNetworking bool = false

@description('ResourceId de la subred (delegada a Microsoft.Web/serverFarms) para la integración VNet regional del App Service.')
param appIntegrationSubnetId string = ''

@description('ResourceId de la subred donde se crean los private endpoints.')
param privateEndpointSubnetId string = ''

@description('ResourceId de la Private DNS Zone privatelink.services.ai.azure.com (obligatoria en modo privado).')
param dnsZoneServicesAiId string = ''

@description('ResourceId de la Private DNS Zone privatelink.openai.azure.com (recomendada en modo privado).')
param dnsZoneOpenAiId string = ''

@description('ResourceId de la Private DNS Zone privatelink.cognitiveservices.azure.com (recomendada en modo privado).')
param dnsZoneCognitiveId string = ''

@description('ResourceId de la Private DNS Zone privatelink.azurewebsites.net (para el private endpoint del App Service).')
param dnsZoneSitesId string = ''

var suffix = uniqueString(resourceGroup().id)
var accountName = toLower('${prefix}${suffix}')
var projectName = '${prefix}-proyecto'
var azureAiUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d'
var planName = '${prefix}-plan'
var webAppName = toLower('${prefix}-app-${suffix}')
var publicAccess = privateNetworking ? 'Disabled' : 'Enabled'
var foundryDnsZoneIds = filter([dnsZoneServicesAiId, dnsZoneOpenAiId, dnsZoneCognitiveId], z => !empty(z))
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

resource account 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: accountName
  location: location
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: accountName
    publicNetworkAccess: publicAccess
    disableLocalAuth: true
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: account
  name: projectName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: 'Arquitecto de Soluciones AI'
    description: 'Proyecto Foundry para el asesor CAF/WAF y ciclo de vida de soluciones AI.'
  }
}

resource chatModel 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: account
  name: modelName
  sku: {
    name: modelSku
    capacity: modelCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}

resource dataPlaneRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  name: guid(account.id, principalId, azureAiUserRoleId)
  scope: account
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureAiUserRoleId)
    principalId: principalId
    principalType: principalType
  }
}

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
          value: 'https://${account.name}.services.ai.azure.com/api/projects/${project.name}'
        }
        {
          name: 'FOUNDRY_MODEL'
          value: chatModel.name
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

resource webAppDataRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(account.id, webApp.id, azureAiUserRoleId)
  scope: account
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureAiUserRoleId)
    principalId: webApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource accountPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = if (privateNetworking) {
  name: '${accountName}-pe'
  location: location
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${accountName}-conn'
        properties: {
          privateLinkServiceId: account.id
          groupIds: [
            'account'
          ]
        }
      }
    ]
  }
}

resource accountPrivateDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = if (privateNetworking) {
  parent: accountPrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [for (zoneId, i) in foundryDnsZoneIds: {
      name: 'zone${i}'
      properties: {
        privateDnsZoneId: zoneId
      }
    }]
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

output accountName string = account.name
output projectName string = project.name
output projectEndpoint string = 'https://${account.name}.services.ai.azure.com/api/projects/${project.name}'
output modelDeploymentName string = chatModel.name
output webAppName string = webApp.name
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
