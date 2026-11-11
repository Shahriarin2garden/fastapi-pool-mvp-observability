output "instance_id" {
  value       = aws_instance.demo.id
  description = "EC2 instance id (used by stop/resume scripts)."
}

output "public_ip" {
  value       = aws_instance.demo.public_ip
  description = "Public IP of the demo instance (changes on stop/resume)."
}

output "app_url" {
  value       = "http://${aws_instance.demo.public_ip}:8001/health"
  description = "FastAPI health endpoint."
}

output "grafana_url" {
  value       = "http://${aws_instance.demo.public_ip}:3000"
  description = "Grafana UI."
}

output "ssh_command" {
  value       = "ssh -i fastapi-pool-mvp-demo-key.pem ${var.ssh_user}@${aws_instance.demo.public_ip}"
  description = "SSH command (save the private key from the sensitive output first)."
}

output "private_key_pem" {
  value       = tls_private_key.demo.private_key_pem
  sensitive   = true
  description = "SSH private key. Save as fastapi-pool-mvp-demo-key.pem and chmod 600."
}

output "grafana_admin_password" {
  value       = random_password.grafana_pass.result
  sensitive   = true
  description = "Grafana admin password."
}

output "db_password" {
  value       = random_password.db_pass.result
  sensitive   = true
  description = "Postgres password."
}
