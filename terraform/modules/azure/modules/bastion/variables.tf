variable "resource_group_name" {
  type        = string
  description = "The name of the resource group."
}

variable "location" {
  type        = string
  description = "The Azure region for the bastion host."
}

variable "bastion_subnet_id" {
  type        = string
  description = "The ID of the AzureBastionSubnet subnet."
}

variable "bastion_host_name" {
  type        = string
  description = "The name of the Bastion Host."
  default     = "bastion-azure"
}

variable "public_ip_name" {
  type        = string
  description = "The name of the Bastion Public IP resource."
  default     = "pip-bastion"
}
