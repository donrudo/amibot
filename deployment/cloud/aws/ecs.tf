resource "aws_ecs_cluster" "botfarm" {
  name = "${var.ecs_cluster}${var.project_name}-${var.env}"
}

resource aws_ecs_service "amibot" {
  name = var.ecs_service
  desired_count = var.scale_min

  cluster = aws_ecs_cluster.botfarm.id
  task_definition = aws_ecs_task_definition.tsk_amibot.arn

}

resource aws_ecs_task_definition "tsk_amibot" {
  family = "${var.project_name}${var.env}"

  cpu = var.specs_cpu
  memory = var.specs_ram

  requires_compatibilities = ["FARGATE"]
  execution_role_arn = aws_iam_role.container_role.arn
  container_definitions = jsonencode([
    {
      essential = true
      image = "${var.image}:${var.image_version}"
      entryPoint: ["scripts/start.sh", var.s3_uri]
    }
  ])

}

