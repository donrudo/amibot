## These need to be set manually at your CI/CD provider as secrets or masked values

variable "organization" {
  type=string
}

variable "project_name" {
  type=string
}

variable "s3_uri" {
  type=string
}

variable "aws_region" {
  type=string
}