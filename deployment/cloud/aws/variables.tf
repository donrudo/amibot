## These need to be set manually at your CI/CD provider as secrets or masked values

variable "organization" {
  type=string
}

variable "project_name" {
  type=string
}

variable "current_dir" {
  type=string
}

variable "bucket_name" {
  type=string
}