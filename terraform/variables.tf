variable "aws_region" {
  default     = "eu-west-1"
  description = "AWS Region"
}

variable "repo_name" {
  default     = "notary-app-ecr-repo"
  description = "Name of the ECR repository"
}

variable "image_count" {
  default     = 14
  description = "Number of images to keep in ECR"
}