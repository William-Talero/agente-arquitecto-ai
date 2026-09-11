// Componente FRONTEND: App Service (Node) que sirve el SPA compilado y hace de proxy inverso
// hacia el backend (/api y /metrics). Se despliega tras el backend; recibe su hostname por parámetro.

@description('Región de Azure.')
param location string = resourceGroup().location

@description('Prefijo para nombres únicos.')
@minLength(3)
@maxLength(12)
param prefix string = 'arqai'

@description('SKU del plan (Linux). B1+ para modo privado; F1 solo para pruebas públicas.')
param appServiceSku string = 'B1'
param nodeVersion string = '20-lts'

@description('URL del backend a la que el frontend hace proxy (del estado del componente backend).')
param backendUrl string

@description('Modo de red privada: sin acceso público + VNet integration + private endpoint.')
param privateNetworking bool = false
@description('Subred delegada a Microsoft.Web/serverFarms para la integración VNet.')
param appIntegrationSubnetId string = ''
@description('Subred para el private endpoint del App Service.')
param privateEndpointSubnetId string = ''
@description('Private DNS Zone privatelink.azurewebsites.net.')
param dnsZoneSitesId string = ''

@description('DNS del App Service en modo privado. 168.63.129.16 = Azure DNS (zonas enlazadas al spoke); vacío = hereda el DNS de la VNet (p.ej. DNS Private Resolver del hub).')
param dnsServer string = '168.63.129.16'

var suffix = uniqueString(resourceGroup().id)
var planName = '${prefix}-fe-plan'
var webAppName = toLower('${prefix}-fe-${suffix}')
var publicAccess = privateNetworking ? 'Disabled' : 'Enabled'
var routeAllSetting = privateNetworking ? [
  {
    name: 'WEBSITE_VNET_ROUTE_ALL'
    value: '1'
  }
] : []
var dnsServerSetting = (privateNetworking && !empty(dnsServer)) ? [
  {
    name: 'WEBSITE_DNS_SERVER'
    value: dnsServer
  }
] : []
var privateAppSettings = concat(routeAllSetting, dnsServerSetting)

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
      linuxFxVersion: 'NODE|${nodeVersion}'
      appCommandLine: 'node server.mjs'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      vnetRouteAllEnabled: privateNetworking
      appSettings: concat([
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'BACKEND_URL'
          value: backendUrl
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
