terraform {
    cloud { }

    required_providers {
        aws = {
          source = "hashicorp/aws"
          version = ""
        }
    }
}

provider "aws" {
  # Configuration options
  region = "us-west-2"
}
