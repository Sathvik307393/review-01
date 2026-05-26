output "bastion_host_id" {
  description = "The ID of the Bastion Host."
  value       = azurerm_bastion_host.this.id
}

output "public_ip_address" {
  description = "The public IP address of the Bastion Host."
  value       = azurerm_public_ip.this.ip_address
}
