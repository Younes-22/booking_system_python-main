terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "5.91.0"
    }
  }
}

provider "aws" {
  region = "eu-west-2"
  shared_credentials_files = ["C:/Users/youne/OneDrive/Documents/aws/credentials.txt"] # Use forward slashes
  profile = "UserYounes"
}