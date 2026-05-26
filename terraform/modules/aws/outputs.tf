output "tunnel1_address" {
  description = "The public IP of the first VPN tunnel."
  value       = aws_vpn_connection.this.tunnel1_address
}

output "tunnel1_preshared_key" {
  description = "The pre-shared key of the first VPN tunnel."
  value       = aws_vpn_connection.this.tunnel1_preshared_key
  sensitive   = true
}

output "tunnel2_address" {
  description = "The public IP of the second VPN tunnel."
  value       = aws_vpn_connection.this.tunnel2_address
}

output "tunnel2_preshared_key" {
  description = "The pre-shared key of the second VPN tunnel."
  value       = aws_vpn_connection.this.tunnel2_preshared_key
  sensitive   = true
}

output "autohub_mongo_private_ip" {
  description = "The private IP of the AutoHub MongoDB instance."
  value       = aws_instance.autohub_mongo.private_ip
}

output "kitchenos_mongo_private_ip" {
  description = "The private IP of the KitchenOS MongoDB instance."
  value       = aws_instance.kitchenos_mongo.private_ip
}
