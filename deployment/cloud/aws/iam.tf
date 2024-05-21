data "aws_iam_policy_document" "policy" {

  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject",]
    resources = [
      replace(var.s3_uri, "s3://","arn:aws:s3:::")
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
  name = "policy${var.project_name}_${var.env}"
  policy = data.aws_iam_policy_document.policy.json
}

resource "aws_iam_role" "container_role" {
  name = "role${var.project_name}_${var.env}"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

resource "aws_iam_policy_attachment" "s3_ro" {
  name = "attachment${var.project_name}_${var.env}"
  roles = [aws_iam_role.container_role.name]
  policy_arn = aws_iam_policy.policy.arn
}