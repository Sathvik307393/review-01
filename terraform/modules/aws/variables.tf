variable "aws_region" {
  type        = string
  description = "The AWS region to provision resources in."
}

variable "ssh_public_key" {
  type        = string
  description = "SSH public key for accessing the EC2 database instances."
}

variable "azure_vpn_gw_ip" {
  type        = string
  description = "The public IP of the Azure VPN Gateway to connect the AWS Customer Gateway to."
}

variable "vpc_cidr" {
  type        = string
  description = "The CIDR block for the AWS VPC."
  default     = "192.16.0.0/16"
}

variable "subnet_cidr" {
  type        = string
  description = "The CIDR block for the private database subnet."
  default     = "192.16.0.0/24"
}

variable "autohub_db_ip" {
  type        = string
  description = "The static private IP for the AutoHub MongoDB instance."
  default     = "192.16.0.101"
}

variable "kitchenos_db_ip" {
  type        = string
  description = "The static private IP for the KitchenOS MongoDB instance."
  default     = "192.16.0.244"
}

variable "azure_vnet_cidr" {
  type        = string
  description = "The CIDR block of the Azure VNet for security group rules and routing."
  default     = "10.10.0.0/16"
}
