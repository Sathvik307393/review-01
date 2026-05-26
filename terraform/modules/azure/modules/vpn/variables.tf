variable "resource_group_name" {
  type        = string
  description = "The name of the resource group."
}

variable "location" {
  type        = string
  description = "The Azure region for the VPN resources."
}

variable "gateway_subnet_id" {
  type        = string
  description = "The ID of the GatewaySubnet subnet where the VPN Gateway will connect."
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

variable "aws_vpc_cidr" {
  type        = string
  description = "The CIDR block of the AWS VPC."
  default     = "192.16.0.0/16"
}

variable "vpn_gw_name" {
  type        = string
  description = "The name of the Virtual Network Gateway."
  default     = "vgw-azure-to-aws"
}

variable "public_ip_name" {
  type        = string
  description = "The name of the VPN Gateway Public IP resource."
  default     = "pip-azure-vpn-gw"
}
