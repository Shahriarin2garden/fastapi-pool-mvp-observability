locals {
  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    repo_url     = var.repo_url
    repo_branch  = var.repo_branch
    db_pass      = random_password.db_pass.result
    grafana_pass = random_password.grafana_pass.result
    alert_recip  = var.alert_recipient
  })

  tags = {
    Project   = var.project
    ManagedBy = "terraform"
    Component = "ec2-demo"
  }

  igw_id = var.internet_gateway_id != "" ? var.internet_gateway_id : aws_internet_gateway.this[0].id
}

# DescribeImages is denied by the sandbox SCP, so the AMI id is supplied
# explicitly (default: Amazon Linux 2023 x86_64, taken from the console).
resource "aws_subnet" "demo" {
  vpc_id                  = var.vpc_id
  cidr_block              = var.subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true

  tags = merge(local.tags, { Name = "${var.project}-demo-subnet" })
}

resource "aws_internet_gateway" "this" {
  count = var.internet_gateway_id == "" ? 1 : 0

  tags = merge(local.tags, { Name = "${var.project}-igw" })
}

resource "aws_route_table" "public" {
  vpc_id = var.vpc_id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = local.igw_id
  }

  tags = merge(local.tags, { Name = "${var.project}-public-rt" })
}

resource "aws_route_table_association" "demo" {
  subnet_id      = aws_subnet.demo.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "demo" {
  name_prefix = "${var.project}-demo-"
  description = "SSH + API + Grafana for the EC2 demo stack"
  vpc_id      = var.vpc_id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_cidr
  }

  ingress {
    description = "FastAPI order API"
    from_port   = 8001
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = var.web_cidr
  }

  ingress {
    description = "Grafana"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = var.web_cidr
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "${var.project}-demo-sg" })
}

resource "tls_private_key" "demo" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "demo" {
  key_name   = "${var.project}-demo-key"
  public_key = tls_private_key.demo.public_key_openssh

  tags = local.tags
}

resource "random_password" "db_pass" {
  length  = 24
  special = false
}

resource "random_password" "grafana_pass" {
  length  = 24
  special = false
}

resource "aws_instance" "demo" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.demo.id
  associate_public_ip_address = true
  key_name                    = aws_key_pair.demo.key_name
  vpc_security_group_ids      = [aws_security_group.demo.id]

  root_block_device {
    volume_size = var.root_volume_gb
    volume_type = "gp3"
  }

  user_data                   = local.user_data
  user_data_replace_on_change = true

  tags = merge(local.tags, { Name = "${var.project}-demo" })
}
