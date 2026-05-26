output "vm_id" {
  description = "The ID of the Virtual Machine."
  value       = azurerm_linux_virtual_machine.this.id
}

output "vm_name" {
  description = "The name of the Virtual Machine."
  value       = azurerm_linux_virtual_machine.this.name
}

output "private_ip_address" {
  description = "The private IP address of the Virtual Machine."
  value       = azurerm_network_interface.this.private_ip_address
}

output "network_interface_id" {
  description = "The ID of the Network Interface."
  value       = azurerm_network_interface.this.id
}
