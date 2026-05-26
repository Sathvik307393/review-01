output "vnet_id" {
  description = "The ID of the virtual network."
  value       = azurerm_virtual_network.this.id
}

output "vnet_name" {
  description = "The name of the virtual network."
  value       = azurerm_virtual_network.this.name
}

output "gateway_subnet_id" {
  description = "The ID of the gateway subnet."
  value       = azurerm_subnet.gateway.id
}

output "bastion_subnet_id" {
  description = "The ID of the bastion subnet."
  value       = azurerm_subnet.bastion.id
}

output "backend_subnet_id" {
  description = "The ID of the backend subnet."
  value       = azurerm_subnet.backend.id
}
