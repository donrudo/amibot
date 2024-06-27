resource "aws_ecs_cluster" "botfarm" {
  name = "${var.ecs_cluster}${var.project_name}-${var.env}"
}

resource aws_ecs_service "amibot" {
  name = var.ecs_service
  desired_count = var.scale_min

  cluster = aws_ecs_cluster.botfarm.id
  task_definition = aws_ecs_task_definition.tsk_amibot.arn
  network_configuration {
    subnets = []
  }

}

resource aws_ecs_task_definition "tsk_amibot" {
  family = "${var.project_name}${var.env}"

  requires_compatibilities = ["FARGATE"]
  execution_role_arn = aws_iam_role.container_role.arn
  container_definitions = jsonencode([
    {
      name = "${var.project_name}${var.env}"
      essential = true
      cpu = tonumber(var.specs_cpu)
      memory = tonumber(var.specs_ram)
      image = "${var.image}:${var.image_version}"
      entryPoint: ["scripts/start.sh", var.s3_uri]
    }
  ])

}

