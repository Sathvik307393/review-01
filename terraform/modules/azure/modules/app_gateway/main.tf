resource "azurerm_public_ip" "this" {
  name                = var.public_ip_name
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_application_gateway" "this" {
  name                = var.appgw_name
  resource_group_name = var.resource_group_name
  location            = var.location

  sku {
    name     = "Standard_v2"
    tier     = "Standard_v2"
    capacity = 1
  }

  gateway_ip_configuration {
    name      = "appgw-gw-ip-config"
    subnet_id = var.subnet_id
  }

  frontend_port {
    name = "http-port-80"
    port = 80
  }

  frontend_ip_configuration {
    name                 = "appgw-public-ip-config"
    public_ip_address_id = azurerm_public_ip.this.id
  }

  backend_address_pool {
    name         = "autohub-pool"
    ip_addresses = [var.autohub_vm_private_ip]
  }

  backend_address_pool {
    name         = "kitchenos-pool"
    ip_addresses = [var.kitchenos_vm_private_ip]
  }

  backend_http_settings {
    name                  = "http-setting-port-80"
    cookie_based_affinity = "Disabled"
    port                  = 80
    protocol              = "Http"
    request_timeout       = 60
  }

  http_listener {
    name                           = "listener-autohub-wildcard"
    frontend_ip_configuration_name = "appgw-public-ip-config"
    frontend_port_name             = "http-port-80"
    protocol                       = "Http"
    host_names                     = ["*.sathvikdevops.site"]
  }

  http_listener {
    name                           = "listener-kitchenos-wildcard"
    frontend_ip_configuration_name = "appgw-public-ip-config"
    frontend_port_name             = "http-port-80"
    protocol                       = "Http"
    host_names                     = ["*.sathvikdevops.online"]
  }

  request_routing_rule {
    name                       = "rule-autohub"
    rule_type                  = "Basic"
    http_listener_name         = "listener-autohub-wildcard"
    backend_address_pool_name  = "autohub-pool"
    backend_http_settings_name = "http-setting-port-80"
    priority                   = 100
  }

  request_routing_rule {
    name                       = "rule-kitchenos"
    rule_type                  = "Basic"
    http_listener_name         = "listener-kitchenos-wildcard"
    backend_address_pool_name  = "kitchenos-pool"
    backend_http_settings_name = "http-setting-port-80"
    priority                   = 110
  }
}
