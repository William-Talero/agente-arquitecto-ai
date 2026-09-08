// Componente FOUNDRY: cuenta AIServices + proyecto + modelo + RBAC (+ private endpoint opcional).
// Se despliega de forma independiente. Sus outputs alimentan al backend.

@description('Región de Azure.')
param location string = resourceGroup().location

@description('Prefijo para nombres únicos.')
@minLength(3)
@maxLength(12)
param prefix string = 'arqai'

@description('Nombre del deployment de modelo de chat.')
param modelName string = 'gpt-5.1'
param modelVersion string = '2025-11-13'
param modelSku string = 'GlobalStandard'
param modelCapacity int = 30

@description('ObjectId que recibe el rol de datos "Azure AI User" (opcional, para acceso humano/local).')
param principalId string = ''
@allowed(['User', 'ServicePrincipal', 'Group'])
param principalType string = 'User'

@description('Modo de red privada: sin acceso público + private endpoint.')
param privateNetworking bool = false

@description('ResourceId de la subred para los private endpoints.')
param privateEndpointSubnetId string = ''

@description('Private DNS Zone privatelink.services.ai.azure.com (obligatoria en modo privado).')
param dnsZoneServicesAiId string = ''
@description('Private DNS Zone privatelink.openai.azure.com (recomendada).')
param dnsZoneOpenAiId string = ''
@description('Private DNS Zone privatelink.cognitiveservices.azure.com (recomendada).')
param dnsZoneCognitiveId string = ''

var suffix = uniqueString(resourceGroup().id)
var accountName = toLower('${prefix}${suffix}')
var projectName = '${prefix}-proyecto'
var azureAiUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d'
var publicAccess = privateNetworking ? 'Disabled' : 'Enabled'
var foundryDnsZoneIds = filter([dnsZoneServicesAiId, dnsZoneOpenAiId, dnsZoneCognitiveId], z => !empty(z))

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

output accountName string = account.name
output accountId string = account.id
output projectName string = project.name
output projectEndpoint string = 'https://${account.name}.services.ai.azure.com/api/projects/${project.name}'
output modelDeploymentName string = chatModel.name
