/*
1. ec2 instane resource
2. new security group
    - 22 (ssh)
    - 443 (https)
    - 5000 (flask)

    */

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}

resource "aws_instance" "tf_ec2_instance" {
  ami           = "ami-091f18e98bc129c4e" #ubuntu image variable found in the variables file
  instance_type = "t2.micro"
  associate_public_ip_address = true
  vpc_security_group_ids = [aws_security_group.tf_ec2_sg.id] # this returns the id of the security group and associates it with the instance
  key_name = "terraform-ec2"
  #depends_on = [ s3bucket ] #this ensures that the s3 bucket is created before the ec2 instance is created
user_data = <<-EOF
#!/bin/bash

# Update and install dependencies
sudo apt update -y
sudo apt install -y python3-pip python3-venv mysql-client git

# Clone the Flask app from GitHub
git clone https://github.com/Younes-22/booking_system_python-main.git /home/ubuntu/flask-app
cd flask-app/


# Set up virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install Flask gunicorn pymysql python-dotenv

# Create .env file with environment variables
#echo "SECRET_KEY=" | sudo tee .env
echo "DB_HOST=${local.rds_endpoint}" | sudo tee .env #this is the endpoint of the rds instance
echo "DB_USER=${aws_db_instance.tf_rds_instance.username}" | sudo tee -a .env
echo "DB_PASSWORD=${aws_db_instance.tf_rds_instance.password}" | sudo tee -a .env
echo "DB_NAME=${aws_db_instance.tf_rds_instance.db_name}" | sudo tee -a .env
#table name?
echo "GMAIL_EMAIL=room.city.booking@gmail.com" | sudo tee -a .env
echo "GMAIL_PASSWORD=qfrjlkudstbojawp" | sudo tee -a .env

# Allow Flask traffic on port 5000
sudo ufw allow 5000

# Start Flask app using Gunicorn
nohup /home/ubuntu/flask-app/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app > flask.log 2>&1 &


EOF
  user_data_replace_on_change = true # whenever the user data changes, the instance will be replaced with a new one

  tags = {
    Name = "flask-server"
  }
}

#security group
resource  "aws_security_group" "tf_ec2_sg" {
  name        = "flask-server-sg"
  description = "Allow SSH and HTTP traffic"
  vpc_id = "vpc-0d955d1a7cdcf6473" #my account has a default vpc available

  #inbound rules (ingress) is all the traffic allowed to travel into the instance
  #so we would want to open ports 22 (ssh), 443 (https), 5000 (flask)

  #outbound (egress) rules is all the traffic allowed to travel out of the instance
  #because want the instance to be able to talk to the internet we want to open all ports

  ingress {
    description = "TLS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] #open to all IP addresses
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "flask TCP"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress { #outbound rule
    description = "Allow all traffic out"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"] # this isnt secure, but for the purpose of this demo it is fine
  }
}
  #output
  output "ec2_public_ip" { #everytime the instance is created, the public ip address is outputted
    value = "ssh -i terraform-ec2.pem ubuntu@${aws_instance.tf_ec2_instance.public_ip}"
  }

/*# ec2 security group module
module "tf_module_ec2_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.3.0"

  ingress_rules = ["ssh-tcp", "https-443-tcp", "http-80-tcp"]
  
  ingress_cidr_blocks = [{
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  },{
    rule        = "ssh-tcp"
    cidr_blocks = "0.0.0.0/0"
  },{
    rule        = "https-443-tcp"
    cidr_blocks = "0.0.0.0/0"
  },
  {
    rule        = "http-80-tcp"
    cidr_blocks = "0.0.0.0/0"
  }
  
  ]
}
*/