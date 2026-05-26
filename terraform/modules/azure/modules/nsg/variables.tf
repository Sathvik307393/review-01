variable "resource_group_name" {
  type        = string
  description = "The name of the resource group."
}

variable "location" {
  type        = string
  description = "The location of the Network Security Group."
}

variable "nsg_name" {
  type        = string
  description = "The name of the Network Security Group."
  default     = "nsg-backend"
}

variable "gateway_subnet_cidr" {
  type        = string
  description = "The address prefix for the GatewaySubnet."
}

variable "bastion_subnet_cidr" {
  type        = string
  description = "The address prefix for the AzureBastionSubnet."
}

variable "aws_vpc_cidr" {
  type        = string
  description = "The CIDR block of the AWS VPC."
}

variable "subnet_id" {
  type        = string
  description = "The ID of the subnet to associate with this Network Security Group."
}
