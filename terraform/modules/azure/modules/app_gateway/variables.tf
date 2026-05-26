variable "resource_group_name" {
  type        = string
  description = "The name of the resource group."
}

variable "location" {
  type        = string
  description = "The Azure region for the Application Gateway."
}

variable "subnet_id" {
  type        = string
  description = "The ID of the BackendSubnet subnet where the Application Gateway will connect."
}

variable "autohub_vm_private_ip" {
  type        = string
  description = "Private IP address of the AutoHub Python backend VM."
}

variable "kitchenos_vm_private_ip" {
  type        = string
  description = "Private IP address of the KitchenOS Node.js backend VM."
}

variable "appgw_name" {
  type        = string
  description = "The name of the Application Gateway."
  default     = "appgw-multicloud-prod"
}

variable "public_ip_name" {
  type        = string
  description = "The name of the Application Gateway Public IP resource."
  default     = "pip-app-gateway"
}
