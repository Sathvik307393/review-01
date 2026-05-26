variable "resource_group_name" {
  type        = string
  description = "The name of the resource group."
}

variable "location" {
  type        = string
  description = "The location of the virtual network."
}

variable "vnet_name" {
  type        = string
  description = "The name of the virtual network."
}

variable "vnet_cidr" {
  type        = string
  description = "The address space for the virtual network."
}

variable "gateway_subnet_cidr" {
  type        = string
  description = "The address prefix for the GatewaySubnet."
}

variable "bastion_subnet_cidr" {
  type        = string
  description = "The address prefix for the AzureBastionSubnet."
}

variable "backend_subnet_cidr" {
  type        = string
  description = "The address prefix for the BackendSubnet."
}
