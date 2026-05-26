# Azure Infrastructure Resources

# Resource Group
resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.azure_region
}

# Virtual Network
resource "azurerm_virtual_network" "this" {
  name                = var.vnet_name
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  address_space       = [var.vnet_cidr]
}

# Subnets
resource "azurerm_subnet" "gateway" {
  name                 = "GatewaySubnet"
  resource_group_name  = azurerm_resource_group.this.name
  virtual_network_name = azurerm_virtual_network.this.name
  address_prefixes     = [var.gateway_subnet_cidr]
}

resource "azurerm_subnet" "bastion" {
  name                 = "AzureBastionSubnet"
  resource_group_name  = azurerm_resource_group.this.name
  virtual_network_name = azurerm_virtual_network.this.name
  address_prefixes     = [var.bastion_subnet_cidr]
}

resource "azurerm_subnet" "backend" {
  name                 = "BackendSubnet"
  resource_group_name  = azurerm_resource_group.this.name
  virtual_network_name = azurerm_virtual_network.this.name
  address_prefixes     = [var.backend_subnet_cidr]
}

resource "azurerm_subnet" "appgw" {
  name                 = "AppGatewaySubnet"
  resource_group_name  = azurerm_resource_group.this.name
  virtual_network_name = azurerm_virtual_network.this.name
  address_prefixes     = [var.appgw_subnet_cidr]
}

# Network Security Group & Rules
resource "azurerm_network_security_group" "nsg_backend" {
  name                = "nsg-backend"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
}

resource "azurerm_network_security_rule" "allow_http_from_gateway" {
  name                        = "allow-http-from-gateway"
  priority                    = 100
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "80"
  source_address_prefix       = var.appgw_subnet_cidr
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.this.name
  network_security_group_name = azurerm_network_security_group.nsg_backend.name
}

resource "azurerm_network_security_rule" "allow_ssh_from_bastion" {
  name                        = "allow-ssh-from-bastion"
  priority                    = 110
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "22"
  source_address_prefix       = var.bastion_subnet_cidr
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.this.name
  network_security_group_name = azurerm_network_security_group.nsg_backend.name
}

resource "azurerm_network_security_rule" "deny_all_inbound" {
  name                        = "deny-all-inbound"
  priority                    = 900
  direction                   = "Inbound"
  access                      = "Deny"
  protocol                    = "*"
  source_port_range           = "*"
  destination_port_range      = "*"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.this.name
  network_security_group_name = azurerm_network_security_group.nsg_backend.name
}

resource "azurerm_network_security_rule" "allow_mongo_out_to_aws" {
  name                        = "allow-mongo-out-to-aws"
  priority                    = 100
  direction                   = "Outbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "27017"
  source_address_prefix       = "*"
  destination_address_prefix  = var.aws_vpc_cidr
  resource_group_name         = azurerm_resource_group.this.name
  network_security_group_name = azurerm_network_security_group.nsg_backend.name
}

resource "azurerm_network_security_rule" "allow_appgw_backend" {
  name                        = "allow-appgw-backend"
  priority                    = 200
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "65200-65535"
  source_address_prefix       = "Internet"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.this.name
  network_security_group_name = azurerm_network_security_group.nsg_backend.name
}

resource "azurerm_network_security_rule" "allow_http_https_out_to_internet" {
  name                        = "allow-http-https-out-to-internet"
  priority                    = 110
  direction                   = "Outbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_ranges     = ["80", "443"]
  source_address_prefix       = "*"
  destination_address_prefix  = "Internet"
  resource_group_name         = azurerm_resource_group.this.name
  network_security_group_name = azurerm_network_security_group.nsg_backend.name
}

resource "azurerm_subnet_network_security_group_association" "backend" {
  subnet_id                 = azurerm_subnet.backend.id
  network_security_group_id = azurerm_network_security_group.nsg_backend.id
}

# Network Interfaces for Backend VMs
resource "azurerm_network_interface" "nic_autohub" {
  name                = "nic-autohub-backend"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.backend.id
    private_ip_address_allocation = "Dynamic"
  }
}

resource "azurerm_network_interface" "nic_kitchenos" {
  name                = "nic-kitchenos-backend"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.backend.id
    private_ip_address_allocation = "Dynamic"
  }
}

# Backend VMs
resource "azurerm_linux_virtual_machine" "vm_autohub" {
  name                = "vm-autohub-backend"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  size                = "Standard_B2als_v2"
  admin_username      = "azureuser"
  admin_password      = "Sathviknbmath@1234"
  disable_password_authentication = false
  network_interface_ids = [
    azurerm_network_interface.nic_autohub.id,
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }

  tags = {
    Name = "vm-autohub-backend"
  }
}

resource "azurerm_linux_virtual_machine" "vm_kitchenos" {
  name                = "vm-kitchenos-backend"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  size                = "Standard_B2als_v2"
  admin_username      = "azureuser"
  admin_password      = "Sathviknbmath@1234"
  disable_password_authentication = false
  network_interface_ids = [
    azurerm_network_interface.nic_kitchenos.id,
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }

  tags = {
    Name = "vm-kitchenos-backend"
  }
}

# Azure Bastion Host Setup
resource "azurerm_public_ip" "pip_bastion" {
  name                = "pip-bastion"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_bastion_host" "bastion" {
  name                = "bastion-azure"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name

  ip_configuration {
    name                 = "configuration"
    subnet_id            = azurerm_subnet.bastion.id
    public_ip_address_id = azurerm_public_ip.pip_bastion.id
  }
}

# Azure Application Gateway Setup
resource "azurerm_public_ip" "pip_appgw" {
  name                = "pip-app-gateway"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_application_gateway" "appgw" {
  name                = "appgw-multicloud-prod"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location

  sku {
    name     = "Standard_v2"
    tier     = "Standard_v2"
    capacity = 1
  }

  gateway_ip_configuration {
    name      = "appgw-gw-ip-config"
    subnet_id = azurerm_subnet.appgw.id
  }

  frontend_port {
    name = "http-port-80"
    port = 80
  }

  frontend_ip_configuration {
    name                 = "appgw-public-ip-config"
    public_ip_address_id = azurerm_public_ip.pip_appgw.id
  }

  backend_address_pool {
    name         = "autohub-pool"
    ip_addresses = [azurerm_network_interface.nic_autohub.private_ip_address]
  }

  backend_address_pool {
    name         = "kitchenos-pool"
    ip_addresses = [azurerm_network_interface.nic_kitchenos.private_ip_address]
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

# Azure VPN Gateway Public IP
resource "azurerm_public_ip" "pip_vpn_gw" {
  name                = "pip-azure-vpn-gw"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  allocation_method   = "Static"
  sku                 = "Standard"
  # zones               = ["1", "2", "3"]
}

# Azure Virtual Network Gateway (VPN)
resource "azurerm_virtual_network_gateway" "vpn_gw" {
  name                = "vgw-azure-to-aws"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name

  type     = "Vpn"
  vpn_type = "RouteBased"

  active_active = false
  bgp_enabled    = false
  sku           = "VpnGw1AZ"

  ip_configuration {
    name                          = "vnetGatewayConfig"
    public_ip_address_id          = azurerm_public_ip.pip_vpn_gw.id

    subnet_id                     = azurerm_subnet.gateway.id
  }
}

# Local Network Gateways for AWS Tunnels
resource "azurerm_local_network_gateway" "lng_tunnel1" {
  name                = "lng-aws-tunnel-1"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  gateway_address     = var.aws_tunnel_1_ip
  address_space       = [var.aws_vpc_cidr]
}

resource "azurerm_local_network_gateway" "lng_tunnel2" {
  name                = "lng-aws-tunnel-2"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  gateway_address     = var.aws_tunnel_2_ip
  address_space       = [var.aws_vpc_cidr]
}

# VPN Gateway Connections (Site-to-Site IPsec)
resource "azurerm_virtual_network_gateway_connection" "conn_tunnel1" {
  name                = "conn-to-aws-t1"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name

  type                       = "IPsec"
  virtual_network_gateway_id = azurerm_virtual_network_gateway.vpn_gw.id
  local_network_gateway_id   = azurerm_local_network_gateway.lng_tunnel1.id
  shared_key                 = var.aws_tunnel_1_key
}

resource "azurerm_virtual_network_gateway_connection" "conn_tunnel2" {
  name                = "conn-to-aws-t2"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name

  type                       = "IPsec"
  virtual_network_gateway_id = azurerm_virtual_network_gateway.vpn_gw.id
  local_network_gateway_id   = azurerm_local_network_gateway.lng_tunnel2.id
  shared_key                 = var.aws_tunnel_2_key
}
