terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "5.88.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      Name = "Prod"
    }
  }
}
provider "aws" {
  region = "us-east-2"
  alias = "my-dr"
  default_tags {
    tags = {
      Name = "DR"
    }
  }
}



# Create a VPC
resource "aws_vpc" "Aadarsh" {
  cidr_block = "192.168.10.0/24"
}
resource "aws_vpc" "Ritika" {
  cidr_block = "192.168.10.0/24"
  provider = aws.my-dr
}
 