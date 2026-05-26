# Root Terraform Configuration

module "azure" {
  source         = "./modules/azure"
  azure_region   = var.azure_region
  ssh_public_key = var.ssh_public_key

  # VPN tunnel configuration (from manual AWS VPN setup)
  aws_tunnel_1_ip  = var.aws_tunnel_1_ip
  aws_tunnel_1_key = var.aws_tunnel_1_key
  aws_tunnel_2_ip  = var.aws_tunnel_2_ip
  aws_tunnel_2_key = var.aws_tunnel_2_key
}
