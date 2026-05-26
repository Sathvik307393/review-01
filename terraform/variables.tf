variable "azure_subscription_id" {
  type        = string
  description = "Azure subscription ID. Can also be set via ARM_SUBSCRIPTION_ID environment variable."
  default     = ""
  sensitive   = true
}

variable "azure_tenant_id" {
  type        = string
  description = "Azure tenant ID. Can also be set via ARM_TENANT_ID environment variable."
  default     = ""
  sensitive   = true
}

variable "azure_region" {
  type        = string
  description = "The Azure region to deploy the web application resources into."
  default     = "Central India"
}

variable "ssh_public_key" {
  type        = string
  description = "The SSH public key used to access Azure virtual machines. Replace with your actual public key."
  default     = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC3dummykeyplaceholder"
}

# AWS VPN Tunnel Configuration Variables (Obtained after manual AWS VPN provisioning)
variable "aws_tunnel_1_ip" {
  type        = string
  description = "The public IP of AWS VPN Tunnel 1. Required to configure Azure Local Network Gateway."
  default     = "1.1.1.1" # Dummy default for validation; user should override
}

variable "aws_tunnel_1_key" {
  type        = string
  description = "The pre-shared key of AWS VPN Tunnel 1. Required to configure Azure VPN connection."
  sensitive   = true
  default     = "dummy_shared_key_1" # Dummy default for validation
}

variable "aws_tunnel_2_ip" {
  type        = string
  description = "The public IP of AWS VPN Tunnel 2. Required to configure Azure Local Network Gateway."
  default     = "2.2.2.2" # Dummy default for validation
}

variable "aws_tunnel_2_key" {
  type        = string
  description = "The pre-shared key of AWS VPN Tunnel 2. Required to configure Azure VPN connection."
  sensitive   = true
  default     = "dummy_shared_key_2" # Dummy default for validation
}
