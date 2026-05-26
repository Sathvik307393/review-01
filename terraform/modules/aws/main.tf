# AWS Infrastructure resources

# VPC
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "vpc-aws-prod"
  }
}

# Subnet
resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.subnet_cidr
  availability_zone = "${var.aws_region}a"

  tags = {
    Name = "PrivateDatabaseSubnet"
  }
}

# Route Table & Propagation for VPN
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "rt-aws-private-prod"
  }
}

resource "aws_route_table_association" "private" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.private.id
}

resource "aws_vpn_gateway_route_propagation" "this" {
  vpn_gateway_id = aws_vpn_gateway.this.id
  route_table_id = aws_route_table.private.id
}

# Security Group
resource "aws_security_group" "mongodb" {
  name        = "sg-mongodb-prod"
  description = "Security group for MongoDB EC2 instances"
  vpc_id      = aws_vpc.this.id

  # Inbound Rule 1: Port 27017 from Azure VNet
  ingress {
    description = "Allow MongoDB traffic from Azure Backend"
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    cidr_blocks = [var.azure_vnet_cidr]
  }

  # Inbound Rule 2: Port 22 from AWS VPC Private Space
  ingress {
    description = "Allow SSH from AWS VPC"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Default Outbound Rule
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "sg-mongodb-prod"
  }
}

# SSH Key Pair
resource "aws_key_pair" "deployer" {
  key_name   = "deployer-key-prod"
  public_key = var.ssh_public_key
}

# Find Ubuntu 22.04 LTS AMI dynamically
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# EC2 Instance 1 (AutoHub Database)
resource "aws_instance" "autohub_mongo" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.private.id
  private_ip    = var.autohub_db_ip

  vpc_security_group_ids = [aws_security_group.mongodb.id]
  key_name               = aws_key_pair.deployer.key_name

  tags = {
    Name = "autohub_mongo"
  }
}

# EC2 Instance 2 (KitchenOS Database)
resource "aws_instance" "kitchenos_mongo" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.private.id
  private_ip    = var.kitchenos_db_ip

  vpc_security_group_ids = [aws_security_group.mongodb.id]
  key_name               = aws_key_pair.deployer.key_name

  tags = {
    Name = "kitchenos_mongo"
  }
}

# VPN Gateway
resource "aws_vpn_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "vgw-aws-to-azure"
  }
}

# Customer Gateway
resource "aws_customer_gateway" "this" {
  bgp_asn    = 65000
  ip_address = var.azure_vpn_gw_ip
  type       = "ipsec.1"

  tags = {
    Name = "cgw-to-azure"
  }
}

# Site-to-Site VPN Connection
resource "aws_vpn_connection" "this" {
  vpn_gateway_id      = aws_vpn_gateway.this.id
  customer_gateway_id = aws_customer_gateway.this.id
  type                = "ipsec.1"
  static_routes_only  = true

  tags = {
    Name = "vpn-aws-azure"
  }
}

# Static VPN Route for Azure VNet Range
resource "aws_vpn_connection_route" "azure" {
  destination_cidr_block = var.azure_vnet_cidr
  vpn_connection_id      = aws_vpn_connection.this.id
}
