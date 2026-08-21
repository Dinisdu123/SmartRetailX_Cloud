# One Multi-AZ Postgres instance hosting both userdb and orderdb.
# (Cheaper for coursework; split into two instances later if you need
# per-service blast-radius isolation.)

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnets"
  subnet_ids = aws_subnet.private[*].id
  tags       = { Name = "${var.project_name}-db-subnets" }
}

resource "aws_db_instance" "postgres" {
  identifier     = "${var.project_name}-postgres"
  engine         = "postgres"
  engine_version = "15.14"
  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "smartretailx"
  username = var.db_username
  password = var.db_password

  multi_az               = true
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  backup_retention_period = 7          # RPO target: <= 24h, daily automated snaps + PITR
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:03:30-sun:04:30"

  deletion_protection = false # flip to true before any real submission/demo
  skip_final_snapshot = true  # flip to false + set final_snapshot_identifier for prod

  performance_insights_enabled = true

  tags = { Name = "${var.project_name}-postgres" }
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}
