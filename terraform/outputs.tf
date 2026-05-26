output "vpn_gw_public_ip" {
  description = "The public IP of the Azure VPN Gateway. Enter this into your AWS Customer Gateway configuration."
  value       = module.azure.vpn_gw_public_ip
}

output "appgw_public_ip" {
  description = "The public IP of the Azure Application Gateway."
  value       = module.azure.appgw_public_ip
}

output "bastion_public_ip" {
  description = "The public IP of the Azure Bastion Host."
  value       = module.azure.bastion_public_ip
}

output "autohub_backend_private_ip" {
  description = "The private IP of the AutoHub Python backend VM."
  value       = module.azure.autohub_backend_private_ip
}

output "kitchenos_backend_private_ip" {
  description = "The private IP of the KitchenOS Node.js backend VM."
  value       = module.azure.kitchenos_backend_private_ip
}
