data "aws_iam_policy_document" "policy" {

  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject",]
    resources = [
      "arn:aws:s3:::${var.bucket_name}",
      "arn:aws:s3:::${var.bucket_name}/${var.project_name}/*",
    ]
  }
}

data "aws_iam_policy_document" "assume" {
  statement {
    effect = "Allow"
    principals {
      identifiers = ["ecs.amazonaws.com"]
      type        = "Service"
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_policy" "policy" {
  name = "policy.${var.project_name}.${var.env}"
  policy = data.aws_iam_policy_document.policy
}

resource "aws_iam_role" "container_role" {
  name = "role.${var.project_name}.${var.env}"
  assume_role_policy = data.aws_iam_policy_document.assume
}

resource "aws_iam_policy_attachment" "s3_ro" {
  name = "attachment.${var.project_name}.${var.env}"
  roles = [aws_iam_role.container_role]
  policy_arn = aws_iam_policy.policy.arn
}