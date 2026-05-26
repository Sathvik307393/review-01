variable "azure_region" {
  type        = string
  description = "The Azure region to provision resources in."
}

variable "ssh_public_key" {
  type        = string
  description = "SSH public key for accessing the Azure Virtual Machines."
}

variable "aws_tunnel_1_ip" {
  type        = string
  description = "The public IP of AWS VPN Tunnel 1."
}

variable "aws_tunnel_1_key" {
  type        = string
  description = "The pre-shared key of AWS VPN Tunnel 1."
  sensitive   = true
}

variable "aws_tunnel_2_ip" {
  type        = string
  description = "The public IP of AWS VPN Tunnel 2."
}

variable "aws_tunnel_2_key" {
  type        = string
  description = "The pre-shared key of AWS VPN Tunnel 2."
  sensitive   = true
}

variable "resource_group_name" {
  type        = string
  description = "The name of the Azure Resource Group."
  default     = "rg-multicloud-prod"
}

variable "vnet_name" {
  type        = string
  description = "The name of the Azure Virtual Network."
  default     = "vnet-azure-prod"
}

variable "vnet_cidr" {
  type        = string
  description = "The CIDR block for the Azure Virtual Network."
  default     = "10.10.0.0/16"
}

variable "gateway_subnet_cidr" {
  type        = string
  description = "The CIDR block for the VPN Gateway subnet."
  default     = "10.10.0.0/27"
}

variable "bastion_subnet_cidr" {
  type        = string
  description = "The CIDR block for the Bastion subnet."
  default     = "10.10.1.0/26"
}

variable "backend_subnet_cidr" {
  type        = string
  description = "The CIDR block for the backend application subnet."
  default     = "10.10.2.0/24"
}

variable "appgw_subnet_cidr" {
  type        = string
  description = "The CIDR block for the Application Gateway subnet."
  default     = "10.10.3.0/24"
}

variable "aws_vpc_cidr" {
  type        = string
  description = "The CIDR block of the AWS VPC for routing and security rules."
  default     = "192.16.0.0/16"
}
