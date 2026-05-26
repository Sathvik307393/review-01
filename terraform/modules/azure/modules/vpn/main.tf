resource "azurerm_public_ip" "this" {
  name                = var.public_ip_name
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_virtual_network_gateway" "this" {
  name                = var.vpn_gw_name
  location            = var.location
  resource_group_name = var.resource_group_name

  type     = "Vpn"
  vpn_type = "RouteBased"

  active_active = false
  enable_bgp    = false
  sku           = "VpnGw1"

  ip_configuration {
    name                          = "vnetGatewayConfig"
    public_ip_address_id          = azurerm_public_ip.this.id
    private_ip_allocation_method = "Dynamic"
    subnet_id                     = var.gateway_subnet_id
  }
}

resource "azurerm_local_network_gateway" "lng_tunnel1" {
  name                = "lng-aws-tunnel-1"
  location            = var.location
  resource_group_name = var.resource_group_name
  gateway_address     = var.aws_tunnel_1_ip
  address_space       = [var.aws_vpc_cidr]
}

resource "azurerm_local_network_gateway" "lng_tunnel2" {
  name                = "lng-aws-tunnel-2"
  location            = var.location
  resource_group_name = var.resource_group_name
  gateway_address     = var.aws_tunnel_2_ip
  address_space       = [var.aws_vpc_cidr]
}

resource "azurerm_virtual_network_gateway_connection" "conn_tunnel1" {
  name                = "conn-to-aws-t1"
  location            = var.location
  resource_group_name = var.resource_group_name

  type                       = "IPsec"
  virtual_network_gateway_id = azurerm_virtual_network_gateway.this.id
  local_network_gateway_id   = azurerm_local_network_gateway.lng_tunnel1.id
  shared_key                 = var.aws_tunnel_1_key
}

resource "azurerm_virtual_network_gateway_connection" "conn_tunnel2" {
  name                = "conn-to-aws-t2"
  location            = var.location
  resource_group_name = var.resource_group_name

  type                       = "IPsec"
  virtual_network_gateway_id = azurerm_virtual_network_gateway.this.id
  local_network_gateway_id   = azurerm_local_network_gateway.lng_tunnel2.id
  shared_key                 = var.aws_tunnel_2_key
}
