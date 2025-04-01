/*
1. rds resource
2. security group
    - 3306
        - security-grp => tf_ec2_sg
        - cidr_block => ["local ip"]

3. outputs
*/

#rds resource
resource "aws_db_instance" "tf_rds_instance" {
  allocated_storage    = 10
  db_name              = "room_booking_system"# name of the database within the instance
  identifier = "room-booking-system-sql" #name of the instance
  engine               = "mysql"
  engine_version       = "8.0"
  instance_class       = "db.t3.micro"
  username             = "admin"
  password             = "admin123"
  parameter_group_name = "default.mysql8.0"
  skip_final_snapshot  = true
  publicly_accessible = true
  vpc_security_group_ids = [aws_security_group.tf_rds_sg.id]
}

resource "aws_security_group" "tf_rds_sg" {
  name = "tf_rds_sg"
  description = "security group for rds"
  vpc_id = "vpc-0d955d1a7cdcf6473"

  ingress {
    description = "allowing 3306" #mysql port
    from_port = 3306
    to_port = 3306
    protocol = "tcp"
    cidr_blocks = ["80.43.78.75/32"] #Local IP address why /32?
    security_groups = [aws_security_group.tf_ec2_sg.id] # Allow traffic from the ec2 instance through the ec2 security group
  }

  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  

}

#local
locals {
  rds_endpoint = element(split(":", aws_db_instance.tf_rds_instance.endpoint), 0) #splits the host name from the port number
}

#outputs

output "rds_endpoint" {
  value = local.rds_endpoint
}
output "rds_username" {
  value = aws_db_instance.tf_rds_instance.username
}
output "db_name" {
  value = aws_db_instance.tf_rds_instance.db_name
}