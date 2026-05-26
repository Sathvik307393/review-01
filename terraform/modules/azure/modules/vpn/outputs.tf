output "vpn_gw_id" {
  description = "The ID of the Virtual Network Gateway."
  value       = azurerm_virtual_network_gateway.this.id
}

output "vpn_gw_public_ip" {
  description = "The public IP address of the Virtual Network Gateway."
  value       = azurerm_public_ip.this.ip_address
}
