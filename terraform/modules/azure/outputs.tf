output "vpn_gw_public_ip" {
  description = "The public IP address of the Azure Virtual Network Gateway."
  value       = azurerm_public_ip.pip_vpn_gw.ip_address
}

output "appgw_public_ip" {
  description = "The public IP address of the Azure Application Gateway."
  value       = azurerm_public_ip.pip_appgw.ip_address
}

output "bastion_public_ip" {
  description = "The public IP address of the Azure Bastion Host."
  value       = azurerm_public_ip.pip_bastion.ip_address
}

output "autohub_backend_private_ip" {
  description = "The private IP address of the AutoHub Python backend VM."
  value       = azurerm_network_interface.nic_autohub.private_ip_address
}

output "kitchenos_backend_private_ip" {
  description = "The private IP address of the KitchenOS Node.js backend VM."
  value       = azurerm_network_interface.nic_kitchenos.private_ip_address
}
