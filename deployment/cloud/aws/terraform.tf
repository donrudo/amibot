terraform {
    cloud { }

    required_providers {
        aws = {
          source = "hashicorp/aws"
          version = "5.50.0"
        }
    }
}

provider "aws" {
  # Configuration options
  region = "us-west-2"
}
