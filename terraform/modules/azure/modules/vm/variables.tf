variable "resource_group_name" {
  type        = string
  description = "The name of the resource group."
}

variable "location" {
  type        = string
  description = "The Azure region for the virtual machine."
}

variable "vm_name" {
  type        = string
  description = "The name of the virtual machine."
}

variable "subnet_id" {
  type        = string
  description = "The ID of the subnet where the network interface will be placed."
}

variable "ssh_public_key" {
  type        = string
  description = "SSH public key to access the virtual machine."
}

variable "vm_size" {
  type        = string
  description = "The size of the virtual machine."
  default     = "Standard_B1s"
}

variable "admin_username" {
  type        = string
  description = "The local administrator username."
  default     = "azureuser"
}
